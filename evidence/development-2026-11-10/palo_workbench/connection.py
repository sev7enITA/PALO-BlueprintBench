import json
import copy
import hashlib
import os
import re
import time
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlsplit
import httpx
from .models import Connection


def validate_connection(cfg):
    url = urlsplit(cfg.base_url)
    if url.username or url.password or url.query or url.fragment:
        raise ValueError('Endpoint must not contain credentials, query parameters or fragments')
    openrouter = url.hostname == 'openrouter.ai' and url.port in (None,443) and url.path.rstrip('/') == '/api/v1'
    if not url.hostname or (url.path not in ('', '/', '/v1', '/v1/') and not openrouter):
        raise ValueError('Use an endpoint origin or /v1 base path; deployment-specific APIs need an adapter')
    if cfg.mode == 'local':
        if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.port not in (11434, 1234, 8080, *range(11435, 11445)):
            raise ValueError('Local mode only permits http://127.0.0.1 on an approved local inference port')
        if cfg.api_key_env:
            raise ValueError('Local pilot does not send credentials')
        if any(x in cfg.model.lower() for x in ('cloud', ':online', 'http:', 'https:')):
            raise ValueError('Cloud model identifiers are not permitted in local mode')
    elif url.scheme != 'https' or cfg.runtime != 'openai':
        raise ValueError('Enterprise mode requires an HTTPS OpenAI-compatible endpoint')
    if cfg.api_key_env and not re.fullmatch(r'[A-Z][A-Z0-9_]{1,100}', cfg.api_key_env):
        raise ValueError('API key field must be an environment variable name, such as PALO_MODEL_API_KEY')
    if not cfg.model.strip() or len(cfg.model) > 160:
        raise ValueError('Enter a model identifier')
    return cfg


def is_openrouter(cfg):
    u = urlsplit(cfg.base_url)
    return cfg.mode == 'enterprise' and u.hostname == 'openrouter.ai' and u.path.rstrip('/') == '/api/v1'


def refresh_prices(cfg):
    if not is_openrouter(cfg) or not cfg.provider:
        raise ValueError('Select https://openrouter.ai/api/v1 and an exact provider slug to refresh prices')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.:-]+', cfg.model):
        raise ValueError('Use a catalog model identifier without routing suffixes')
    data = request(cfg, '/models/' + cfg.model + '/endpoints', timeout=20)
    endpoints = data.get('data', {}).get('endpoints', [])
    selected = [e for e in endpoints if e.get('tag') == cfg.provider]
    if len(selected) != 1:
        raise ValueError('Provider slug does not uniquely identify an endpoint for this model')
    e = selected[0]
    supported=set(e.get('supported_parameters', []))
    missing={'structured_outputs','response_format','max_tokens'}-supported
    if missing:
        raise ValueError('Endpoint cannot support the bounded extraction contract: '+', '.join(sorted(missing)))
    if cfg.reasoning_effort and not supported.intersection({'reasoning','reasoning_effort'}):
        raise ValueError('Endpoint does not advertise configurable reasoning')
    check_profile(cfg)
    pricing = e['pricing']
    tiers = [pricing, *pricing.get('overrides', [])]
    def rate(keys):
        values = [Decimal(str(t[k])) * 1000000 for t in tiers for k in keys if k in t]
        if not values or any(not x.is_finite() or x < 0 for x in values):
            raise ValueError('Catalog price is missing or unsupported')
        return float(max(values))
    # Reserve the highest listed context/cache tier; never assume a cache discount.
    policy = cfg.finops.model_copy(update={
        'input_per_million': rate(('prompt','input_cache_write','input_cache_write_1h')),
        'output_per_million': rate(('completion',)), 'price_model': cfg.model,
        'price_provider': cfg.provider, 'price_checked_at': datetime.now(timezone.utc).isoformat(),
        'price_source': 'https://openrouter.ai/api/v1/models/' + cfg.model + '/endpoints'})
    # Validate computed values using the same bounds as user-entered settings.
    return type(policy).model_validate(policy.model_dump())


def check_profile(cfg):
    # Verified against the actual serving API, 10 November 2026. Catalogue model
    # settings are not a substitute for endpoint-specific compatibility tests.
    if is_openrouter(cfg) and cfg.model == 'mistralai/mistral-large-4-0' and cfg.provider.startswith('mistral/'):
        if cfg.reasoning_effort not in ('','low','medium','high'):
            raise ValueError('This Mistral endpoint accepts low, medium or high reasoning; choose one explicitly. No automatic substitution was made.')


def provider_schema(cfg, schema):
    """Project only provider-unsupported size keywords; callers validate originals."""
    if not (is_openrouter(cfg) and cfg.provider.startswith('cohere/')):
        return schema
    def project(node):
        if isinstance(node,dict):
            return {k:project(v) for k,v in node.items() if k not in ('minItems','maxItems','minLength','maxLength')}
        if isinstance(node,list):return [project(v) for v in node]
        return node
    return project(copy.deepcopy(schema))


def endpoint(cfg, path):
    base = cfg.base_url.rstrip('/')
    if cfg.runtime == 'ollama':
        if base.endswith('/v1'): base = base[:-3]
        return base + path
    if not base.endswith('/v1'): base += '/v1'
    return base + path


def request(cfg, path, payload=None, timeout=180):
    validate_connection(cfg)
    if cfg.mode == 'enterprise' and not cfg.enterprise_confirmed:
        raise ValueError('Confirm the enterprise processing boundary before contacting this endpoint')
    headers = {}
    if cfg.api_key_env:
        secret = os.environ.get(cfg.api_key_env)
        if not secret:
            raise ValueError(f'Set {cfg.api_key_env} in the server environment and restart')
        headers['Authorization'] = 'Bearer ' + secret
    try:
        # Ignore HTTP(S)_PROXY; never redirect source data to another host.
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=httpx.Timeout(timeout, connect=5)) as client:
            with client.stream('POST' if payload is not None else 'GET', endpoint(cfg, path), json=payload, headers=headers) as response:
                if response.status_code >= 300:
                    raise ValueError(f'Model endpoint returned HTTP {response.status_code}; no fallback was attempted')
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 2_000_000:
                        raise ValueError('Model response exceeded 2 MB')
                return json.loads(data)
    except httpx.TimeoutException:
        raise ValueError(f'Model request timed out (read limit {timeout}s, connection limit 5s). Completed batches are saved; retry resumes them. No fallback was attempted.') from None
    except httpx.ConnectError:
        raise ValueError('Cannot connect to the configured model. Start or prepare the local engine, then resume. No fallback was attempted.') from None
    except httpx.HTTPError:
        raise ValueError('The connection to the model was interrupted. Completed batches are saved; retry resumes them. No fallback was attempted.') from None
    except json.JSONDecodeError:
        raise ValueError('The model endpoint returned an invalid JSON envelope. Completed batches are saved. No fallback was attempted.') from None


def available(cfg):
    data = request(cfg, '/api/tags' if cfg.runtime == 'ollama' else '/models', timeout=10)
    if cfg.runtime == 'ollama':
        return [m['name'] for m in data.get('models', []) if 'cloud' not in m.get('name','').lower() and not m.get('remote_host')]
    return [m['id'] for m in data.get('data', []) if 'embedding' not in m['id'].lower()]


class ModelOutputError(ValueError):
    """A bounded output failure that the pipeline may recover by splitting input."""
    def __init__(self, message, metadata):
        super().__init__(message)
        self.metadata = metadata


def completion_metadata(content, reason, counts, started, max_tokens):
    raw = content.encode('utf-8') if isinstance(content, str) else b''
    allowed = ('prompt_tokens', 'completion_tokens', 'total_tokens', 'input_tokens', 'output_tokens')
    usage = {k: v for k, v in (counts or {}).items() if k in allowed and isinstance(v, (int, float))}
    return {'finish_reason': reason if reason in ('stop','length','content_filter','tool_calls','function_call') else 'unknown',
            'tokens': usage, 'seconds': round(time.monotonic()-started, 3), 'max_tokens': max_tokens,
            'content_bytes': len(raw), 'content_sha256': hashlib.sha256(raw).hexdigest()}


def infer(cfg, messages, schema, max_tokens=None, ledger=None, case_id='connection-test'):
    validate_connection(cfg)
    check_profile(cfg)
    if cfg.mode=='enterprise' and not cfg.enterprise_confirmed:
        raise ValueError('Confirm the enterprise processing boundary before contacting this endpoint')
    max_tokens = cfg.max_output_tokens if max_tokens is None else max_tokens
    started = time.monotonic()
    if cfg.runtime == 'ollama':
        # A local socket can proxy a cloud model. Check Ollama's model metadata too.
        metadata = request(cfg, '/api/show', {'model': cfg.model}, timeout=15)
        if metadata.get('remote_host') or metadata.get('remote_model'):
            raise ValueError('Ollama reports a remote model. Local mode refuses it.')
        payload = {'model': cfg.model, 'messages': messages, 'stream': False, 'format': schema,
                   'options': {'temperature': 0, 'num_ctx': 16384, 'num_predict': max_tokens}}
        response = request(cfg, '/api/chat', payload)
        if response.get('done_reason') == 'length':
            raise ModelOutputError('Local model reached its output limit; partial output was discarded.', completion_metadata(response.get('message',{}).get('content'), 'length', {'input_tokens':response.get('prompt_eval_count'),'output_tokens':response.get('eval_count')}, started, max_tokens))
        if response.get('done') is not True or response.get('done_reason') != 'stop':
            raise ValueError('Local model did not finish normally; partial output was discarded')
        content = response['message']['content']
        counts = {'input_tokens': response.get('prompt_eval_count'), 'output_tokens': response.get('eval_count')}
    else:
        output_format = {'type': 'json_object'}
        # LM Studio accepts json_schema or text, but rejects json_object.
        # This is an endpoint contract, not a Liquid-only model feature.
        if cfg.mode == 'local' or is_openrouter(cfg):
            output_format = {'type':'json_schema','json_schema':{'name':'palo_output','strict':True,'schema':provider_schema(cfg,schema)}}
        payload = {'model': cfg.model, 'messages': messages,
            'temperature': 0, 'max_tokens': max_tokens, 'stream': False,
            'response_format': output_format}
        if is_openrouter(cfg):
            # Some structured-output endpoints do not accept sampling controls.
            payload.pop('temperature', None)
            if not cfg.provider:
                raise ValueError('Select an explicit OpenRouter provider; automatic fallback is disabled')
            payload['provider'] = {'only': [cfg.provider], 'allow_fallbacks': False, 'require_parameters': True,
                'max_price': {'prompt': cfg.finops.input_per_million, 'completion': cfg.finops.output_per_million}}
            payload['usage'] = {'include': True}
            if cfg.reasoning_effort: payload['reasoning'] = {'effort': cfg.reasoning_effort}
        reservation = None
        if cfg.mode == 'enterprise':
            if ledger is None: raise ValueError('Enterprise inference requires a persistent FinOps ledger')
            if cfg.api_key_env and not os.environ.get(cfg.api_key_env):
                raise ValueError(f'Set {cfg.api_key_env} in the server environment and restart')
            reservation = ledger.reserve(cfg, messages, schema, max_tokens, case_id)
        try:
            response = request(cfg, '/chat/completions', payload)
        except Exception:
            if reservation: ledger.complete(reservation)
            raise
        if reservation: ledger.complete(reservation, response)
        try:
            choice = response['choices'][0]
            reason = choice['finish_reason']
            content = choice['message']['content']
            counts = response.get('usage', {})
        except (KeyError, IndexError, TypeError, AttributeError):
            raise ValueError('Model returned an invalid completion envelope; no output was accepted') from None
        if reason == 'length':
            raise ModelOutputError(f'Model reached the output limit ({max_tokens} tokens) for this batch. Partial output was discarded and completed batches are saved. Repeating the same request may fail again; the pipeline will try smaller requests within its recovery budget.', completion_metadata(content, reason, counts, started, max_tokens))
        if reason != 'stop':
            # Do not display arbitrary provider text or partially generated source data.
            known_reason = reason if reason in ('content_filter', 'tool_calls', 'function_call') else 'unknown'
            raise ValueError(f'Model did not finish normally (reason: {known_reason}); partial output was discarded')
    try:
        result = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        raise ModelOutputError('Model did not return valid structured output; nothing was approved', completion_metadata(content, 'stop', counts, started, max_tokens)) from None
    accounting = {k:response[k] for k in ('id','provider') if k in response}
    if cfg.mode == 'enterprise': accounting['usage'] = response.get('usage', {})
    return result, {**completion_metadata(content, 'stop', counts, started, max_tokens), 'model': cfg.model,
                    'accounting': accounting}


def probe(cfg, ledger=None):
    models = available(cfg)
    if cfg.model not in models:
        return {'ok': False, 'models': models, 'message': 'Choose an available model, save, then test again. No model was downloaded.'}
    schema = {'type': 'object', 'properties': {'status': {'type': 'string', 'enum': ['ok']}}, 'required': ['status'], 'additionalProperties': False}
    # Reasoning may consume the same allowance as the visible answer. A fixed
    # 60-token probe incorrectly rejected working reasoning endpoints.
    result, metrics = infer(cfg, [{'role':'user','content':'Synthetic connectivity check. Return only JSON: {"status":"ok"}'}], schema, min(cfg.max_output_tokens,8192), **({'ledger':ledger} if ledger else {}))
    return {'ok': result == {'status':'ok'}, 'models': models, 'message': 'Synthetic inference completed. No documents were used.', 'metrics': metrics}

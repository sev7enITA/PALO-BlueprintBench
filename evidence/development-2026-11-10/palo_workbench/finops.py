"""Workbench admission ledger. USD micros; provider charges are not invoices.

A deliberately bounded adapter to PALO FinOps principles. This is not the full
billing/allocation module and not a provider-enforced spending cap.
"""
import json
import os
import threading
import uuid
import fcntl
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
from pathlib import Path


def micros(value):
    d = Decimal(str(value))
    if not d.is_finite() or d < 0:
        raise ValueError('Cost must be a finite non-negative USD amount')
    return int((d * 1000000).to_integral_value(rounding=ROUND_CEILING))


def token_cost(tokens, rate):
    return int((Decimal(tokens) * Decimal(str(rate))).to_integral_value(rounding=ROUND_CEILING))


def prices(cfg):
    p = cfg.finops
    if (p.input_per_million is None or p.output_per_million is None
            or p.price_model != cfg.model or p.price_provider != cfg.provider or not p.price_source):
        raise ValueError('Refresh the price estimate for this exact model and provider before using enterprise AI')
    try:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(p.price_checked_at)).total_seconds()
    except (ValueError, TypeError):
        raise ValueError('Refresh the dated price snapshot before using enterprise AI') from None
    if not 0 <= age <= 7 * 86400:
        raise ValueError('The price snapshot is older than seven days. Refresh prices before spending')
    return p


def estimate(cfg, messages, schema, max_tokens=None):
    max_tokens=cfg.max_output_tokens if max_tokens is None else max_tokens
    if cfg.mode == 'local':
        return {'input_tokens_approx': 0, 'input_tokens_reservation': 0,
                'input_microusd': 0, 'output_microusd': 0, 'reservation_microusd': 0}
    p = prices(cfg)
    # Text-only upper proxy includes schema and chat framing; not a tokenizer guarantee.
    size = len(json.dumps([messages, schema], ensure_ascii=False).encode('utf-8')) + 1024
    inp = token_cost(size, p.input_per_million)
    out = token_cost(max_tokens, p.output_per_million)
    return {'input_tokens_approx': (size + 3) // 4, 'input_tokens_reservation': size,
            'input_microusd': inp, 'output_microusd': out, 'reservation_microusd': inp + out}


class Ledger:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.depth = 0
        self.entries = []
        with self.transaction():
            # Conservatively block on another process's pending charge too.
            for e in self.entries:
                if e['state'] == 'pending': e['state'] = 'unknown'
            if self.entries: self.save()

    @contextmanager
    def transaction(self):
        with self.lock:
            if self.depth:
                yield
                return
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path.with_suffix('.lock'),os.O_CREAT|os.O_RDWR,0o600)
            try:
                fcntl.flock(fd,fcntl.LOCK_EX)
                self.entries=json.loads(self.path.read_text())['entries'] if self.path.exists() else []
                self.depth=1
                yield
            finally:
                self.depth=0
                fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump({'version': 1, 'currency': 'USD', 'entries': self.entries}, f)
            f.flush(); os.fsync(f.fileno())
        os.replace(temp, self.path)

    def summary(self, cfg, case_id=None):
        with self.transaction():
            rows = [e for e in self.entries if case_id is None or e['case_id'] == case_id]
            known = sum(e.get('charged_microusd', 0) for e in rows if e['state'] == 'reported')
            reserved = sum(e['reservation_microusd'] for e in rows if e['state'] != 'reported')
            def count(key, detail=None):
                total=0
                for e in rows:
                    u=e.get('usage',{})
                    if detail: u=u.get(detail) or {}
                    n=u.get(key) if isinstance(u,dict) else None
                    if isinstance(n,int) and not isinstance(n,bool) and n>=0:total+=n
                return total
            return {'currency': 'USD', 'scope': 'workspace' if case_id is None else 'case',
                    'budget_microusd': micros(cfg.finops.budget_usd),
                    'reported_microusd': known, 'reserved_microusd': reserved,
                    'committed_microusd': known + reserved,
                    'unknown_requests': sum(e['state'] == 'unknown' for e in rows),
                    'unresolved': [{k:e.get(k) for k in ('id','model','provider','created_at','generation_id','reservation_microusd')}
                                   for e in rows if e['state']=='unknown'],
                    'requests': len(rows), 'invoice_reconciled': False,
                    'tokens': {'input':count('prompt_tokens'), 'output_including_reasoning':count('completion_tokens'),
                      'cached_input_subset':count('cached_tokens','prompt_tokens_details'),
                      'reasoning_output_subset':count('reasoning_tokens','completion_tokens_details')},
                    'cost_basis': 'Provider-reported API charges, including failed outputs. Not an invoice.',
                    'components': {'retrieved_context': 'Included in input tokens, not an additional fee',
                      'reasoning': 'Included in completion tokens, not an additional fee',
                      'cache': 'Included in provider total; savings not assumed in reservations',
                      'embeddings': 'Not used', 'reranking': 'Not used', 'vector_storage': 'Not used',
                      'web_search': 'Not enabled', 'remote_ocr': 'Not used',
                      'local_compute': 'Not priced', 'human_review': 'Not priced',
                      'taxes_and_credit_purchase_fees': 'Not included; reconcile separately'}}

    def reserve(self, cfg, messages, schema, max_tokens, case_id):
        with self.transaction():
            amount = estimate(cfg, messages, schema, max_tokens)
            s = self.summary(cfg)
            if s['unknown_requests']:
                raise ValueError('An earlier request has an unknown charge. Reconcile it before further enterprise spending')
            if s['committed_microusd'] + amount['reservation_microusd'] > s['budget_microusd']:
                raise ValueError('Workspace AI budget reached. Completed work is saved; no new request was sent')
            entry = {'id': str(uuid.uuid4()), 'case_id': case_id, 'model': cfg.model,
                     'provider': cfg.provider, 'endpoint':cfg.base_url, 'created_at': datetime.now(timezone.utc).isoformat(),
                     'state': 'pending', 'price_snapshot': cfg.finops.model_dump(), **amount}
            self.entries.append(entry); self.save()
            return entry['id']

    def complete(self, identifier, response=None):
        with self.transaction():
            e = next(x for x in self.entries if x['id'] == identifier)
            if e['state'] == 'reported': return
            response = response if isinstance(response, dict) else {}
            usage = response.get('usage') or {}
            if not isinstance(usage,dict):usage={}
            cost = usage.get('cost')
            try: charge = micros(cost) if cost is not None and not isinstance(cost, bool) else None
            except (ValueError, TypeError, ArithmeticError): charge = None
            e.update(state='reported' if charge is not None else 'unknown')
            if charge is not None: e['charged_microusd'] = charge
            # Keep only accounting metadata, never the prompt or answer.
            e['generation_id'] = str(response.get('id', ''))[:200]
            e['actual_provider'] = str(response.get('provider', ''))[:120]
            e['usage'] = {k: usage[k] for k in ('prompt_tokens','completion_tokens','total_tokens',
                 'prompt_tokens_details','completion_tokens_details','cost_details') if k in usage}
            self.save()

    def reconcile(self, identifier, receipt, matched=False):
        """Provider receipt plus explicit operator matching for an unknown call.

        Matching without an original generation ID remains an operator assertion;
        model and time checks narrow mistakes but cannot prove request identity.
        """
        with self.transaction():
            e=next((x for x in self.entries if x['id']==identifier),None)
            if e is None or e['state']!='unknown':raise ValueError('Choose an unresolved request')
            if not matched:raise ValueError('Match this request in provider activity before reconciling')
            gid=receipt.get('id')
            if not gid or (e.get('generation_id') and e['generation_id']!=gid):
                raise ValueError('Generation identifier does not match the recorded request')
            if any(x['id']!=identifier and x.get('generation_id')==gid for x in self.entries):
                raise ValueError('This generation receipt has already been used')
            model=receipt.get('model','')
            if model!=e['model'] and not model.startswith(e['model']+'-20'):
                raise ValueError('Receipt model does not match the request')
            try:
                start=datetime.fromisoformat(e['created_at']);reported=datetime.fromisoformat(receipt['created_at'].replace('Z','+00:00'))
                if abs((reported-start).total_seconds())>300:raise ValueError('Receipt time does not match the request')
                cost=micros(receipt['total_cost'])
            except (KeyError,TypeError):raise ValueError('Receipt lacks a dated provider charge') from None
            original=e['state']
            e.update(state='reported',generation_id=gid,charged_microusd=cost,
                actual_provider=receipt.get('provider_name',''),reconciliation={
                  'previous_state':original,'matched_in_provider_activity':True,
                  'at':datetime.now(timezone.utc).isoformat(),'receipt_created_at':receipt['created_at'],
                  'source':'OpenRouter generation API','identity_basis':'Operator matched; model/time checked'})
            self.save()


def plan(cfg, chunks, request_parts, ledger):
    state = ledger.summary(cfg)
    if cfg.mode == 'local':
        return {'mode': 'local', 'estimate_microusd': 0, 'reservation_microusd': 0,
                'note': 'No inference API charge. Electricity, hardware and review time are not priced.',
                'ledger': state}
    try:
        rows = [estimate(cfg, *request_parts(c)) for c in chunks]
        upper = sum(r['reservation_microusd'] for r in rows)
        typical = sum(token_cost(r['input_tokens_approx'], cfg.finops.input_per_million)
                      + r['output_microusd'] // 2 for r in rows)
        return {'mode': 'enterprise', 'estimate_microusd': typical, 'reservation_microusd': upper,
                'input_reservation_microusd': sum(r['input_microusd'] for r in rows),
                'output_reservation_microusd': sum(r['output_microusd'] for r in rows),
                'can_start': not state['unknown_requests'] and state['committed_microusd'] < state['budget_microusd'],
                'note': 'Planning estimate uses about 4 bytes per input token and half the output cap. '
                        'Reservation uses one token per byte plus framing and the full output cap. '
                        'Retries and recovery splits cost extra and are admitted one request at a time. '
                        'This is a local admission control, not a provider-enforced cap.', 'ledger': state}
    except ValueError as e:
        return {'mode': 'enterprise', 'can_start': False, 'error': str(e), 'ledger': state}

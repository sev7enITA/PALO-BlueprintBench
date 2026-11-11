from typing import Literal
from .limits import MAX_BYTES, MAX_FILES
from pydantic import BaseModel, ConfigDict, Field
from .liquid import MODEL

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')

class FinOpsPolicy(Strict):
    budget_usd: float = Field(default=1, gt=0, le=10000, allow_inf_nan=False)
    input_per_million: float | None = Field(default=None, ge=0, le=10000, allow_inf_nan=False)
    output_per_million: float | None = Field(default=None, ge=0, le=10000, allow_inf_nan=False)
    price_model: str = ''
    price_provider: str = ''
    price_checked_at: str = ''
    price_source: str = ''

class ReconcileCharge(Strict):
    request_id: str = Field(min_length=36, max_length=36)
    generation_id: str = Field(pattern=r'^gen-[A-Za-z0-9-]{8,160}$')
    matched_in_provider_activity: bool = Field(strict=True)

class Connection(Strict):
    mode: Literal['local', 'enterprise'] = 'local'
    runtime: Literal['ollama', 'openai'] = 'openai'
    base_url: str = 'http://127.0.0.1:8080'
    model: str = MODEL
    api_key_env: str = ''
    enterprise_confirmed: bool = False
    provider: str = Field(default='', max_length=120, pattern=r'^[a-zA-Z0-9_./-]*$')
    reasoning_effort: Literal['', 'none', 'low', 'medium', 'high', 'max'] = ''
    max_output_tokens: int = Field(default=2400, ge=256, le=16384, strict=True)
    extraction_profile: Literal['compact', 'grounded_graph'] = 'compact'
    finops: FinOpsPolicy = Field(default_factory=FinOpsPolicy)

class LiquidDeclaration(Strict):
    revenue_band: Literal['below_10m_usd', 'at_or_above_10m_usd', 'unknown']
    confirmed: bool = Field(strict=True)

class Source(Strict):
    unit_id: str = Field(min_length=1, max_length=100)
    quote: str = Field(min_length=2, max_length=1200)

class Claim(Strict):
    kind: Literal['entity', 'attribute', 'relationship', 'step', 'rule', 'term']
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=800)
    entity: str = Field(default='', max_length=120)
    target: str = Field(default='', max_length=120)
    datatype: Literal['', 'string', 'number', 'boolean', 'date', 'unknown'] = ''
    cardinality: Literal['', 'one-to-one', 'one-to-many', 'many-to-one', 'many-to-many', 'unknown'] = ''
    sensitivity: Literal['internal', 'confidential', 'unknown'] = 'unknown'
    sources: list[Source] = Field(min_length=1, max_length=5)

class Extraction(Strict):
    claims: list[Claim] = Field(max_length=60)
    uncertainties: list[str] = Field(default_factory=list, max_length=30)

class UploadFile(Strict):
    name: str = Field(min_length=1, max_length=200)
    data: str = Field(max_length=4*((MAX_BYTES+2)//3))

class CaseInput(Strict):
    name: str = Field(default='New document case', min_length=1, max_length=120)
    files: list[UploadFile] = Field(min_length=1, max_length=MAX_FILES)

class ClaimCorrection(Strict):
    kind: Literal['entity', 'attribute', 'relationship', 'step', 'rule', 'term']
    name: str = Field(min_length=1, max_length=120)
    entity: str = Field(default='', max_length=120)
    target: str = Field(default='', max_length=120)

class Review(Strict):
    reviewer_type: Literal['local_user', 'automated_assistant_audit'] = 'local_user'
    claim_id: str
    decision: Literal['include', 'exclude']
    replacement: str = Field(default='', max_length=800)
    correction: ClaimCorrection | None = None

class Export(Strict):
    reviewer_type: Literal['local_user', 'automated_assistant_audit'] = 'local_user'
    preview_digest: str = Field(default='', max_length=64)
    reviewer: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=200)
    purpose: str = Field(min_length=1, max_length=500)
    acknowledge_confidentiality: bool = False
    acknowledge_extraction_limits: bool = False


class SourcePageReview(Strict):
    reviewer_type: Literal['local_user', 'automated_assistant_audit'] = 'local_user'
    key: str = Field(min_length=66, max_length=80)
    reason: str = Field(min_length=10, max_length=800)
    confirmed: bool = Field(strict=True)


class ExcludeFailed(Strict):
    claim_ids: list[str] = Field(min_length=1, max_length=5000)
    confirmed: bool = Field(strict=True)
    reviewer_type: Literal['local_user','automated_assistant_audit'] = 'local_user'

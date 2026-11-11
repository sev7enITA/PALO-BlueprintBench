"""Pinned Liquid model and self-declared commercial eligibility policy."""
from datetime import datetime, timezone

MODEL = 'hf.co/LiquidAI/LFM3-1.7B-GGUF:Q4_K_M'
LICENSE_URL = 'https://www.liquid.ai/lfm-license'
LICENSE_VERSION = 'LFM Open License v1.0'
POLICY_VERSION = 'palo-liquid-2026-11-09'


def is_liquid(model):
    return 'liquidai' in model.lower() or 'lfm' in model.lower()


def eligibility(record):
    """A declaration is not verification of revenue or a legal entitlement."""
    try:
        stamp = datetime.fromisoformat(record['declared_at'])
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
        current = 0 <= age <= 365 * 86400
    except (KeyError, TypeError, ValueError):
        current = False
    eligible = bool(current and record.get('policy_version') == POLICY_VERSION
                    and record.get('revenue_band') == 'below_10m_usd'
                    and record.get('confirmed') is True)
    return {'eligible': eligible, 'declaration': record, 'license_url': LICENSE_URL,
            'license_version': LICENSE_VERSION, 'policy_version': POLICY_VERSION,
            'message': ('Self-declared eligibility recorded. Update this declaration if your organisation changes.' if eligible
                        else 'Confirm that your organisation, including its controlling and controlled group, has annual revenue below US$10 million. At or above this amount, or if unsure, verify the Liquid licence before activation.')}

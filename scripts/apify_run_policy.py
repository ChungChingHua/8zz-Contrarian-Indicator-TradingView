"""Current Apify run options: no application cost or monthly-start ceiling. MPL-2.0."""
from decimal import Decimal,InvalidOperation


def run_options(max_items=50):
    # No maxTotalChargeUsd: provider/account limits remain provider-controlled.
    return {'timeout':180,'memory':512,'maxItems':max_items,'restartOnError':'false'}


def provider_charge_limited(run):
    """Keep incomplete-window protection for a limit actually returned by Apify."""
    message=str(run.get('statusMessage','')).lower()
    if any(s in message for s in ('max total charge','maximum total charge','max charge','insufficient credit','usage limit exceeded')):return True
    options=run.get('options')
    if not isinstance(options,dict):return False
    try:
        raw=options.get('maxTotalChargeUsd')
        if isinstance(raw,bool):return False
        cap=Decimal(str(raw))
        if not cap.is_finite() or cap<=0:return False
    except (InvalidOperation,ValueError,TypeError):return False
    for key in ('usageTotalUsd','externalChargedTotalUsd'):
        try:
            raw=run.get(key)
            if isinstance(raw,bool):continue
            value=Decimal(str(raw))
            if value.is_finite() and value>=cap:return True
        except (InvalidOperation,ValueError,TypeError):continue
    return False

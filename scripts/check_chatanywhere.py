"""Read-only account model preflight; never silently select another model. MPL-2.0."""
from ai_provider import credentials
from social_pipeline import ROOT, request_json, write


def main():
    report={'provider':'chatanywhere','generation_requests':0,'remaining_quota':None,
            'quota_note':'No documented account quota API confirmed; dashboard check required. Model listing does not prove a key is free-tier.'}
    try:
        c,headers=credentials()
        if c['provider']!='chatanywhere':raise ValueError('ChatAnywhere provider required')
        result=request_json(c['base']+'/models',headers,retries=1)
        models=sorted(x['id'] for x in result.get('data',[]) if isinstance(x.get('id'),str) and x['id'].startswith('gpt-5'))
        report.update(available_gpt5_models=models,requested_model=c['model'],model_listed=c['model'] in models,
                      remaining_headers=result.get('_transport_metadata',{}),free_tier='User must supply a dedicated FREE ChatAnywhere key; no paid fallback')
        if c['model'] not in models:raise ValueError('gpt-5-mini unavailable; report listed GPT-5 models without switching')
        report['preflight_passed']=True
    except Exception as exc:
        report.update(preflight_passed=False,error_type=type(exc).__name__,http_status=getattr(exc,'status',None))
        write(ROOT/'data/social_chatanywhere_preflight.json',report)
        raise SystemExit('ChatAnywhere preflight blocked; see sanitized report / configure CHATANYWHERE_API_KEY') from None
    write(ROOT/'data/social_chatanywhere_preflight.json',report)

if __name__=='__main__':main()

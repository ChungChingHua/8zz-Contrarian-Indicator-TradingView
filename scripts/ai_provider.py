"""Explicit provider/key/host isolation. MPL-2.0. No automatic fallback."""
import os
from pathlib import Path
import json


def assert_online_enabled():
    flag=Path(__file__).resolve().parents[1]/"data/online_paused.json"
    if not flag.exists() or json.loads(flag.read_text()).get("paused") is not False:
        raise RuntimeError("Online features paused for security review; no credentials or network used")



def config():
    provider=os.getenv('AI_PROVIDER','openai')
    if provider=='chatanywhere':
        model=os.getenv('CHATANYWHERE_MODEL','gpt-5-mini')
        if model!='gpt-5-mini':
            raise ValueError('Only the requested free-tier candidate gpt-5-mini is enabled; report other available GPT-5 models without switching')
        effort=os.getenv('CHATANYWHERE_REASONING_EFFORT','low')
        if effort not in ('minimal','low','medium','high'):raise ValueError('invalid reasoning effort')
        return dict(provider=provider,base='https://api.chatanywhere.org/v1',secret='CHATANYWHERE_API_KEY',model=model,effort=effort)
    if provider=='openai':
        return dict(provider=provider,base='https://api.openai.com/v1',secret='OPENAI_API_KEY',model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),effort=None)
    raise ValueError('Unknown AI_PROVIDER; no fallback')


def credentials():
    assert_online_enabled()
    c=config()
    key=os.getenv(c['secret'])
    if not key:raise RuntimeError('Missing '+c['secret']+'; no provider call made')
    return c,{'Authorization':'Bearer '+key,'Content-Type':'application/json'}

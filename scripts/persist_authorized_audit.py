"""Persist only the sanitized one-shot audit to its PR branch; no AI key access. MPL-2.0."""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from authorized_chatanywhere_smoke import REPORT,SCOPE
from social_pipeline import NoAuthRedirect,write


def main():
    if os.getenv('GITHUB_REF')!='refs/heads/codex/social-pipeline-20261106' or os.getenv('GITHUB_RUN_ATTEMPT')!='1':raise SystemExit('Wrong branch or rerun')
    if not REPORT.exists():
        print('No audit file; no provider state published');return
    report=json.loads(REPORT.read_text())
    if report.get('scope')!=SCOPE or report.get('consumed') is not True:raise SystemExit('Audit scope mismatch')
    base='https://api.github.com/repos/ChungChingHua/8zz-Contrarian-Indicator-TradingView/contents/data/'+REPORT.name
    headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
    opener=urllib.request.build_opener(NoAuthRedirect())
    sha=None
    try:
        with opener.open(urllib.request.Request(base+'?ref=codex%2Fsocial-pipeline-20261106',headers=headers),timeout=30) as res:sha=json.load(res)['sha']
    except urllib.error.HTTPError as exc:
        if exc.code!=404:raise SystemExit('GitHub metadata HTTP '+str(exc.code)) from None
    report['control_plane_note']='GitHub Actions checkout/artifact internals excluded from provider HTTP counts; audit persistence uses one GitHub contents GET and one PUT attempt.'
    write(REPORT,report)
    body={'message':'data: record authorized two-post ChatAnywhere technical smoke and stop','branch':'codex/social-pipeline-20261106','content':base64.b64encode(REPORT.read_bytes()).decode()}
    if sha:body['sha']=sha
    try:
        with opener.open(urllib.request.Request(base,headers=headers,data=json.dumps(body).encode(),method='PUT'),timeout=30) as res:
            res.read(1000)
    except urllib.error.HTTPError as exc:raise SystemExit('GitHub audit persistence HTTP '+str(exc.code)) from None
    print('Sanitized one-shot audit persisted; global pause remains true')

if __name__=='__main__':main()

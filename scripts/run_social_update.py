"""Paid-run gate, monthly attempt budget, and small first validation. MPL-2.0."""
import os
import subprocess
import sys
from datetime import datetime, timezone
from social_pipeline import ROOT, read, write


def main():
    if not os.getenv('APIFY_TOKEN') or not os.getenv('GOOGLE_API_KEY'):
        raise SystemExit('Required GitHub Secrets: APIFY_TOKEN and GOOGLE_API_KEY (values never printed)')
    mode=os.getenv('MODE','smoke')
    limit=int(os.getenv('POST_LIMIT','5')); ai=int(os.getenv('AI_LIMIT','2'))
    if not 1<=limit<=50 or not 0<=ai<=50:raise SystemExit('Limits must be posts 1..50 / AI 0..50')
    if mode=='smoke':limit=2;ai=2
    month=datetime.now(timezone.utc).strftime('%Y-%m')
    usage=read(ROOT/'data/usage.json',{})
    budget=usage.setdefault(month,{'apify_runs':0,'ai_attempts':0})
    runs=0 if mode=='classify-only' else 2
    # Reserve attempts before network calls: crashes consume budget conservatively.
    if budget['apify_runs']+runs>70 or budget['ai_attempts']+ai>400:
        raise SystemExit('Monthly budget exhausted (70 Apify runs / 400 AI attempts)')
    budget['apify_runs']+=runs;budget['ai_attempts']+=ai
    write(ROOT/'data/usage.json',usage)
    if mode!='classify-only':
        cmd=[sys.executable,'scripts/fetch_social.py','--limit',str(limit)]
        if mode=='smoke':cmd.append('--smoke')
        subprocess.run(cmd,cwd=ROOT,check=True)
    before=read(ROOT/'data/social_posts.json',{})
    done_before=sum(p['analysis']['status']=='done' for p in before.values())
    subprocess.run([sys.executable,'scripts/social_pipeline.py','--classify-limit',str(ai)],cwd=ROOT,check=True)
    after=read(ROOT/'data/social_posts.json',{})
    done_after=sum(p['analysis']['status']=='done' for p in after.values())
    if mode=='smoke':
        acquisition=read(ROOT/'data/acquisition.json',{})
        passed=done_after-done_before==2 and all(acquisition.get(s,{}).get('last_counts',{}).get('accepted',0)>0 for s in ('facebook','threads'))
        write(ROOT/'data/social_validation.json',{'passed':passed,'tested_at':datetime.now(timezone.utc).isoformat(),
              'new_ai_successes':done_after-done_before,'scope':'2 posts per platform; 2 multimodal classifications; not full historical validation'})
        if not passed:raise SystemExit('Smoke failed; schedule remains gated; see pending/retry records')

if __name__=='__main__':main()

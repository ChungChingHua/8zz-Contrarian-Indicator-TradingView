"""Paid-run gate, monthly attempt budget, and small first validation. MPL-2.0."""
import os
import subprocess
import sys
from datetime import datetime, timezone
from social_pipeline import ROOT, read, write


def main():
    mode=os.getenv('MODE','smoke')
    if not os.getenv('OPENAI_API_KEY'):
        raise SystemExit('Missing GitHub Secret OPENAI_API_KEY; no paid API calls made')
    validation=read(ROOT/'data/social_validation.json',{})
    if mode!='smoke' and not (validation.get('passed') and validation.get('provider')=='openai' and validation.get('model')==os.getenv('OPENAI_MODEL','gpt-4.1-mini')):
        raise SystemExit('Run OpenAI smoke for this model before processing batches')
    limit=int(os.getenv('POST_LIMIT','5')); ai=int(os.getenv('AI_LIMIT','2'))
    if not 1<=limit<=50 or not 0<=ai<=50:raise SystemExit('Limits must be posts 1..50 / AI 0..50')
    if mode=='smoke':limit=2;ai=2
    month=datetime.now(timezone.utc).strftime('%Y-%m')
    usage=read(ROOT/'data/usage.json',{})
    budget=usage.setdefault(month,{'apify_runs':0,'ai_attempts':0})
    runs=0 if mode in ('classify-only','smoke') else 2
    if runs and not os.getenv('APIFY_TOKEN'):
        raise SystemExit('Missing GitHub Secret APIFY_TOKEN')
    reserved_ai=ai if os.getenv('OPENAI_API_KEY') else 0
    # Reserve attempts before network calls: crashes consume budget conservatively.
    ai_budget=int(os.getenv('MONTHLY_AI_LIMIT','400'))
    if not 1<=ai_budget<=2000:raise SystemExit('MONTHLY_AI_LIMIT must be 1..2000')
    if budget['apify_runs']+runs>70 or budget['ai_attempts']+reserved_ai>ai_budget:
        raise SystemExit(f'Monthly budget exhausted (70 Apify runs / {ai_budget} AI attempts)')
    budget['apify_runs']+=runs;budget['ai_attempts']+=reserved_ai
    write(ROOT/'data/usage.json',usage)
    if mode not in ('classify-only','smoke'):
        cmd=[sys.executable,'scripts/fetch_social.py','--limit',str(limit)]
        if mode=='smoke':cmd.append('--smoke')
        subprocess.run(cmd,cwd=ROOT,check=True)
    if not os.getenv('OPENAI_API_KEY'):
        write(ROOT/'data/social_validation.json',{'passed':False,'reason':'Apify tested independently; missing OPENAI_API_KEY'})
        raise SystemExit('Missing GitHub Secret OPENAI_API_KEY; AI not called; schedule stays gated')
    before=read(ROOT/'data/social_posts.json',{})
    done_before=sum(p['analysis']['status']=='done' for p in before.values())
    cmd=[sys.executable,'scripts/social_pipeline.py','--classify-limit',str(ai)]
    if mode=='smoke':cmd.append('--smoke')
    subprocess.run(cmd,cwd=ROOT,check=True)
    after=read(ROOT/'data/social_posts.json',{})
    done_after=sum(p['analysis']['status']=='done' for p in after.values())
    if mode=='smoke':
        acquisition=read(ROOT/'data/acquisition.json',{})
        report=read(ROOT/'data/social_report.json',{})
        passed=report.get('completed')==2 and report.get('image_successes',0)>=1 and all(acquisition.get(s,{}).get('last_counts',{}).get('accepted',0)>0 for s in ('facebook','threads'))
        write(ROOT/'data/social_validation.json',{'passed':passed,'provider':'openai','model':os.getenv('OPENAI_MODEL','gpt-4.1-mini'),'usage':report.get('usage',[]),'tested_at':datetime.now(timezone.utc).isoformat(),
              'new_ai_successes':report.get('completed',0),'scope':'2 posts per platform; 2 multimodal classifications; not full historical validation'})
        if not passed:raise SystemExit('Smoke failed; schedule remains gated; see pending/retry records')

if __name__=='__main__':main()

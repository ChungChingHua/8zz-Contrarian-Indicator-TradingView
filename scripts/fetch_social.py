#!/usr/bin/env python3
"""Bounded Apify acquisition. Persist run IDs before polling; never retry POST blindly."""
import argparse
import os
import sys
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from social_pipeline import ROOT, read, write, request_json, ingest, APIError

BASE='https://api.apify.com/v2'


def fetch(source, limit, smoke=False):
    token=os.getenv('APIFY_TOKEN')
    if not token:raise RuntimeError('Missing GitHub Secret APIFY_TOKEN')
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
    state_path=ROOT/'data/acquisition.json'
    state=read(state_path,{})
    s=state.setdefault(source,{})
    # Cursor is the END of the last fully completed window, not newest post.
    # Saturated windows retain cursor and paginate backward on the next invocation.
    now=datetime.now(timezone.utc)
    if smoke and s.get('last_run_id') and s.get('last_counts',{}).get('accepted',0)>0 and s.get('window_end') and not s.get('run_id'):
        if (now-datetime.fromisoformat(s['window_end'])).total_seconds()<86400:
            print(source, 'reusing successful bounded acquisition from past 24h')
            return s['last_counts']
    start=s.get('window_start') or ((datetime.fromisoformat(s['completed_until'])-timedelta(days=2)).isoformat() if s.get('completed_until') else (now-timedelta(days=2)).isoformat())
    end=s.get('page_before') or s.get('window_end') or now.isoformat()
    if not s.get('run_id'):
        if s.get('submission_uncertain'):
            raise RuntimeError('Apify submission uncertain: inspect Console and set run_id in acquisition.json before retry; no duplicate paid run started')
        if source=='facebook':
            actor='apify~facebook-posts-scraper'
            body={'startUrls':[{'url':'https://www.facebook.com/DieWithoutBang'}],
                  'resultsLimit':limit,'onlyPostsNewerThan':start.replace('+00:00','Z'),'onlyPostsOlderThan':end.replace('+00:00','Z')}
        else:
            actor='automation-lab~threads-scraper'
            body={'mode':'posts','usernames':['banini31'],'maxPosts':limit,'includeProfile':False,
                  'postedAfter':start,'postedBefore':end}
        s.update(window_start=start,window_end=s.get('window_end',end),submission_uncertain=True)
        write(state_path,state)
        query=urllib.parse.urlencode({'timeout':180,'memory':512,'maxItems':limit,'maxTotalChargeUsd':0.10})
        # POST may have succeeded even if the connection fails. Leave uncertain marker.
        try:
            run=request_json(f'{BASE}/acts/{actor}/runs?{query}',headers,body,retries=1)['data']
        except APIError as exc:
            if exc.status in (400,401,402,403,404,422):
                # Explicit rejected submission did not create a paid run.
                s['submission_uncertain']=False
                s['last_rejected_http_status']=exc.status
                write(state_path,state)
            raise
        s.update(run_id=run['id'],submission_uncertain=False)
        write(state_path,state)
    for _ in range(45):
        run=request_json(f'{BASE}/actor-runs/{s["run_id"]}',headers)['data']
        if run['status'] in ('SUCCEEDED','FAILED','TIMED-OUT','ABORTED'):break
        time.sleep(4)
    if run['status']!='SUCCEEDED':
        # Keep ID for inspection/recovery; do not silently resubmit paid failures.
        raise RuntimeError('Apify run not successful; saved run ID retained')
    rows=[]
    offset=0
    while True:
        page=request_json(f'{BASE}/datasets/{run["defaultDatasetId"]}/items?format=json&offset={offset}&limit=100',headers)
        rows.extend(page)
        if len(page)<100:break
        offset+=len(page)
    archive=read(ROOT/'data/social_posts.json',{})
    counts=ingest(rows,source,archive)
    write(ROOT/'data/social_posts.json',archive)
    s['last_counts']=counts
    write(state_path,state)
    if counts['accepted']==0 and rows:
        raise RuntimeError('No accepted posts; inspect actor schema; run ID and cursor retained')
    dates=[r.get('time') or r.get('date') for r in rows if r.get('time') or r.get('date')]
    saturated=len(rows)>=limit
    if saturated and dates:
        # Oldest boundary remains inclusive on Facebook and may duplicate; IDs dedupe.
        boundary=(datetime.fromisoformat(min(dates).replace('Z','+00:00'))+timedelta(seconds=1)).isoformat()
        if boundary==s.get('page_before'):
            raise RuntimeError('Pagination made no progress; cursor retained for review')
        s['page_before']=boundary
    elif not smoke:
        s['completed_until']=s['window_end']
        for k in ('window_start','window_end','page_before'):s.pop(k,None)
    s.pop('run_id',None)
    s['last_counts']=counts
    s['last_run_id']=run['id']
    s['saturated']=saturated
    write(state_path,state)
    print(source,counts,'saturated=',saturated)
    return counts


def main():
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=5);p.add_argument('--smoke',action='store_true')
    a=p.parse_args()
    if not 1<=a.limit<=50:p.error('limit must be 1..50')
    failures=[]
    for source in ('facebook','threads'):
        try:fetch(source,a.limit,a.smoke)
        except Exception as exc:
            # Only our sanitized error types get logged; no provider response/URL.
            print(source, str(exc) if isinstance(exc,RuntimeError) else 'Acquisition failed; state retained')
            failures.append(source)
    if failures:sys.exit(1)

if __name__=='__main__':main()

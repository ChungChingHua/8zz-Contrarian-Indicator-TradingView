"""Incremental live queue using existing Apify client, author worker and GitHub CAS.
Default disabled. No history generation. MPL-2.0 © hansai-art / Group.G.
"""
import argparse
import copy
import json
import os
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import history_worker as h
import history_completion as hc
import history_incremental as acq
from history_batch_02 import prepare
from history_plan import select, normalized, media_identity
from trading_calendar import due_slot, refresh, PATH as CALENDAR
from telegram_notify import Telegram, deliver
ROOT=h.ROOT
CONTROL='data/live_control.json'
POSTS='data/live_posts.json'
OUTBOX='data/telegram_outbox.json'
RULE=hc.RULE

class Documents:
    """Cache initial GitHub content SHAs: never reload before a write to conceal CAS conflicts."""
    def __init__(self,token):self.token=token;self.stores={};self.loaded={}
    def load(self,path,default=None):
        if path not in self.stores:
            store=h.GitHubStore(self.token,path);value=store.load();self.stores[path]=store;self.loaded[path]=value
        return copy.deepcopy(self.loaded[path] if self.loaded[path] is not None else default)
    def save(self,path,value):
        if path not in self.stores:self.load(path)
        self.stores[path].save(value) # Remote ACK first; CAS conflict stops execution, never retries.
        self.loaded[path]=copy.deepcopy(value);h.s.write(ROOT/path,value)
    def document(self,path):
        parent=self
        class Document:
            def load(self):return parent.load(path)
            def save(self,value):return parent.save(path,value)
        return Document()

def initial_state():
    old=h.s.read(ROOT/hc.CONTROL,{})
    sources={s:{'completed_until':old.get('sources',{}).get(s,{}).get('completed_until')} for s in ('facebook','threads')}
    return {'version':1,'sources':sources,'rounds':{},'ai_stop':old.get('stop_reason') or 'free_quota_requires_operator_resume',
        'history_queue_enabled':False,'rule_sha256':RULE}

def acquire(source,state,docs,client,now,raw):
    """One bounded page per platform/round. Saturation retains active window for later pages."""
    s=state['sources'][source]
    if not s.get('completed_until'):raise ValueError('missing_successful_platform_cutoff')
    if s.get('blocked'):return
    if not s.get('window'):
        s['window']={'start':(datetime.fromisoformat(s['completed_until'])-timedelta(hours=2)).isoformat(),
            'end':now.isoformat()}
    w=s['window'];active=w.get('active')
    def save():docs.save(CONTROL,state)
    if active and active.get('submission_unknown') and not active.get('run_id'):
        s['blocked']='apify_submission_unknown';save();return
    if not active:
        usage=docs.load('data/usage.json',{});month=now.astimezone(timezone.utc).strftime('%Y-%m')
        budget=usage.setdefault(month,{'apify_runs':0,'ai_attempts':0})
        if budget['apify_runs']>=70:s['last_error']='existing_monthly_apify_budget_exhausted';save();return
        budget['apify_runs']+=1;docs.save('data/usage.json',usage)
        active=w['active']={'submission_unknown':True,'reserved_at':now.isoformat(),'cap_usd':0.10,'max_items':50}
        save() # Durable reservation before POST. No retry of ambiguous submission.
        start=w['start'];end=w.get('page_before',w['end'])
        if source=='facebook':
            actor='apify~facebook-posts-scraper'
            body={'startUrls':[{'url':'https://www.facebook.com/DieWithoutBang'}],'resultsLimit':50,
                'onlyPostsNewerThan':start.replace('+00:00','Z'),'onlyPostsOlderThan':end.replace('+00:00','Z')}
        else:
            actor='automation-lab~threads-scraper'
            body={'mode':'posts','usernames':['banini31'],'maxPosts':50,'includeProfile':False,
                'postedAfter':start.replace('+00:00','Z'),'postedBefore':end.replace('+00:00','Z')}
        try:
            run=client.request('/acts/'+actor+'/runs?'+urllib.parse.urlencode({'timeout':180,'memory':512,'maxItems':50,'maxTotalChargeUsd':0.10}),body)['data']
            active.update(run_id=run['id'],submission_unknown=False);save()
        except acq.AcquisitionError as exc:
            if exc.status in (400,401,402,403,404,422):active['submission_unknown']=False
            s.update(blocked='apify_submission_rejected' if not active['submission_unknown'] else 'apify_submission_unknown',http_status=exc.status);save();return
    for attempt in range(25):
        run=client.request('/actor-runs/'+active['run_id'])['data']
        if run['status'] not in ('READY','RUNNING'):break
        if attempt<24:time.sleep(2)
    active['status']=run['status'];save()
    # Avoid blocking poll loops. A running Actor is picked up next round without a new POST.
    if run['status'] in ('READY','RUNNING'):return
    if run['status']!='SUCCEEDED':s['blocked']='apify_run_not_successful';save();return
    cost={k:run[k] for k in ('usageTotalUsd','externalChargedTotalUsd') if isinstance(run.get(k),(int,float))}
    active['reported_cost']=cost
    if any(v>=.10 for v in cost.values()) or any(x in str(run.get('statusMessage','')).lower() for x in ('max total charge','maximum total charge','max charge')):
        s['blocked']='apify_cost_cap_may_have_truncated_window';save();return
    rows=[];offset=0
    while True:
        page=client.request('/datasets/'+run['defaultDatasetId']+'/items?format=json&offset='+str(offset)+'&limit=100')
        if not isinstance(page,list):raise ValueError('invalid_dataset_shape')
        rows.extend(page)
        if len(page)<100:break
        offset+=len(page)
        if offset>1000:raise ValueError('dataset_exceeds_bounded_run')
    posts=docs.load(POSTS,{})
    archive=hc.archive();archive.update(posts)
    dates=[];counts={'fetched':len(rows),'new':0,'overlap':0,'excluded':{}}
    for row in rows:
        p,reason=h.s.normalize(row,source)
        if p is None:
            counts['excluded'][reason]=counts['excluded'].get(reason,0)+1
            # Identity/schema failures cannot prove a complete window. Replies/other authors are expected exclusions.
            expected_exclusion=reason in ('other_author','before_start') or (reason=='reply_repost_or_unknown' and (row.get('isReply') is True or row.get('isRepost') is True))
            if not expected_exclusion:
                s['incomplete_row']=True
            continue
        dt=datetime.fromisoformat(p['published_at'])
        if not datetime.fromisoformat(w['start'])<=dt<datetime.fromisoformat(w['end']):continue
        dates.append(dt);p['fetched_at']=now.isoformat()
        if p['key'] in archive:
            if any(archive[p['key']][k]!=p[k] for k in ('text','source','post_id','published_at','quoted_content')):
                s['blocked']='existing_post_changed';save();return
            counts['overlap']+=1
        else:posts[p['key']]=p;counts['new']+=1
        raw[p['key']]=p # Signed media stays private/in-memory; public_safe applied on remote save.
    docs.save(POSTS,posts) # ACK posts before advancing successful cutoff.
    s['last_counts']=counts;s['last_run_id']=active['run_id'];s['last_fetched_at']=now.isoformat()
    if s.pop('incomplete_row',False):s['blocked']='unrecognized_rows_window_incomplete';save();return
    if len(rows)>=50:
        if not dates:s['blocked']='saturated_window_without_valid_dates';save();return
        boundary=(min(dates)+timedelta(seconds=1)).isoformat()
        if datetime.fromisoformat(boundary)>=datetime.fromisoformat(w.get('page_before',w['end'])):
            s['blocked']='incremental_pagination_no_progress';save();return
        w['page_before']=boundary;w.pop('active')
    else:
        s['completed_until']=w['end'];s.pop('window');s.pop('last_error',None)
    save()

def classify(state,docs,key,raw,now):
    rows,_=hc.ledger_records()
    if any(r['status']=='unknown' for r in rows.values()):
        state['ai_stop']='unknown_request_requires_manual_reconciliation';docs.save(CONTROL,state);return
    for path in sorted((ROOT/'data/live_progress').glob('*.json')):
        saved=h.s.read(path,{})
        if saved.get('stopped') and saved.get('updated_at','')>state.get('ai_resumed_at',''):
            state['ai_stop']=saved.get('stop_reason') or 'prior_live_worker_stopped';docs.save(CONTROL,state);return
    if state.get('ai_stop'):return
    archive=hc.archive();archive.update(docs.load(POSTS,{}))
    excluded,_=hc.exclusions(archive)
    # Live queue only. Historical pending posts are excluded, not silently marked done.
    live=docs.load(POSTS,{})
    excluded.update(k for k in archive if k not in live)
    for path in sorted((ROOT/'data/live_progress').glob('*.json')):
        for r in h.s.read(path,{}).get('records',[]):
            if r['status']!='not_started':
                excluded.add(r['key']);excluded.update(m['key'] for m in r.get('members',[]))
    # Exact cross-platform duplicates of already-dispatched posts reuse their saved outcome.
    aliases=docs.load('data/live_duplicates.json',{})
    dispatched={m['key']:r for r in rows.values() for m in r.get('members',[])}
    for k,p in live.items():
        if k in excluded:continue
        for member,r in dispatched.items():
            prior=archive.get(member)
            if prior and p['source']!=prior['source'] and normalized(p['text']) and normalized(p['text'])==normalized(prior['text']) and abs(p['unix_ms']-prior['unix_ms'])<=172800000 and p['quoted_content']==prior['quoted_content'] and media_identity(p)==media_identity(prior):
                aliases[k]={'record_key':r['key'],'status':r['status'],'reason':'exact_cross_platform_duplicate_reuses_saved_result'};excluded.add(k);break
    if aliases:docs.save('data/live_duplicates.json',aliases)
    groups,_=select(archive,excluded,5)
    if not groups:return # No provider/key/media requests without unclassified live articles.
    if not key:state['ai_stop']='CHATANYWHERE_API_KEY 未設定';docs.save(CONTROL,state);return
    # Existing 400-attempt monthly cap is preserved; include durable author ledgers, not only legacy counters.
    usage=docs.load('data/usage.json',{});month=now.strftime('%Y-%m')
    budget=usage.setdefault(month,{'apify_runs':0,'ai_attempts':0})
    durable=sum(r.get('attempts',0) for r in rows.values() if str(r.get('dispatch_reserved_at','')).startswith(month))
    accounted=max(budget.get('ai_attempts',0),durable)
    allowance=min(5,len(groups),400-accounted)
    if allowance<=0:state['ai_stop']='existing_monthly_ai_attempt_budget_exhausted';docs.save(CONTROL,state);return
    groups=groups[:allowance]
    budget['ai_attempts']=accounted+allowance;docs.save('data/usage.json',usage)
    bid='live-'+now.strftime('%Y%m%dT%H%M%S%fZ')
    plan=hc.frozen_plan(groups,1);plan.update(batch_id=bid,max_generations=allowance)
    path='data/live_progress/'+bid+'.json'
    h.BATCH_ID=bid
    docs.save('data/live_plans/'+bid+'.json',plan)
    # Existing pending live batches with possible sends are never reconstructed/replayed.
    posts=[copy.deepcopy(raw.get(g[0]['key']) or archive[g[0]['key']]) for g in groups]
    worker=h.Worker(docs.document(path),h.Provider(key),plan,prepare=prepare,secrets=(key,docs.token),
        local=ROOT/path,generation_limit=allowance,continue_isolated_failures=True)
    if state.get('consecutive_isolated_failures'):
        worker.state['consecutive_isolated_failures']=state['consecutive_isolated_failures'];worker.save()
    worker.run(posts)
    state['consecutive_isolated_failures']=worker.state.get('consecutive_isolated_failures',0)
    if worker.state['stopped']:state['ai_stop']=worker.state.get('stop_reason')
    docs.save(CONTROL,state)

def refresh_outputs(docs):
    # Uses unchanged saved judgments, never generates. Same events feed Telegram and website.
    hc.report()
    import build_audited_dashboard as dashboard
    for path in ('data/history_completion_inventory.json','data/history_completion_summary.json',
                 'candidates/8zz-history-latest.checks.json','candidates/8zz-strategy-latest.checks.json','candidates/8zz-pine-delivery.json'):
        docs.save(path,h.s.read(ROOT/path,{}))
    for path in ('candidates/8zz-history-latest.pine','candidates/8zz-strategy-latest.pine'):
        hc.publish_text(docs,path,(ROOT/path).read_text())
    dashboard.publish_saved_dashboard(docs)

def run(action,docs,apify=None,ai_key='',telegram=None,chat_id='',now=None,calendar=None):
    now=now or datetime.now(timezone.utc)
    state=docs.load(CONTROL,initial_state())
    if state.get('rule_sha256')!=h.policy.fingerprint() or h.policy.fingerprint()!=RULE:raise ValueError('author_policy_mismatch')
    if action=='resume-ai':
        # Resume only unsent live rows in a new plan. Existing completed/review/failure/unknown remain untouched.
        if any(r['status']=='unknown' for r in hc.ledger_records()[0].values()):raise ValueError('unknown_request_requires_manual_reconciliation')
        state['previous_ai_stop']=state.get('ai_stop');state['ai_stop']=None;state['consecutive_isolated_failures']=0;state['ai_resumed_at']=h.now();docs.save(CONTROL,state);return
    if action=='retry-notifications':
        outbox=docs.load(OUTBOX,{'records':{}})
        for r in outbox['records'].values():
            if r['status']=='failed':r.update(status='pending',previous_failure=r.get('reason'))
        docs.save(OUTBOX,outbox);return # Does not send, fetch or classify.
    if action=='run':
        slot=due_slot(now,calendar)
        if not slot:return
        if slot in state['rounds']:return
        state['rounds'][slot]={'status':'reserved','started_at':now.isoformat()};docs.save(CONTROL,state)
        raw={}
        for source in ('facebook','threads'):
            try:
                if not apify:raise ValueError('APIFY_TOKEN_missing')
                acquire(source,state,docs,apify,now,raw)
            except Exception as exc:
                # May include checkpoint failures: never continue to AI after losing durable storage.
                if isinstance(exc,RuntimeError):raise
                state['sources'][source]['last_error']=type(exc).__name__;docs.save(CONTROL,state)
        refresh_outputs(docs) # Publish saved pending posts before any judgment request.
        classify(state,docs,ai_key,raw,now)
        state['rounds'][slot].update(status='finished',finished_at=h.now());docs.save(CONTROL,state)
        refresh_outputs(docs)
    elif action=='refresh-market':
        from build_audited_dashboard import fetch_market
        fetch_market();docs.save('data/dashboard_market.json',h.s.read(ROOT/'data/dashboard_market.json',{}));refresh_outputs(docs)
    events=docs.load('data/signal_events.json',[])
    if action in ('run','notify'):
        deliver(events,docs.document(OUTBOX),telegram,chat_id)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','notify','resume-ai','refresh-market','retry-notifications']);a=p.parse_args()
    if not h.s.read(ROOT/'data/live_settings.json',{}).get('enabled') or os.getenv('LIVE_PIPELINE_ENABLED')!='true' or not (os.getenv('GITHUB_REF')=='refs/heads/'+h.BRANCH or (os.getenv('GITHUB_EVENT_NAME')=='schedule' and os.getenv('GITHUB_REF')=='refs/heads/main')):
        raise SystemExit('正式流程未啟用或分支不符；沒有外部抓取、判讀或通知')
    gh=os.environ.pop('GH_TOKEN','')
    if not gh:raise SystemExit('Missing checkpoint credential; no external work')
    apify=os.environ.pop('APIFY_TOKEN','');key=os.environ.pop('CHATANYWHERE_API_KEY','')
    token=os.environ.pop('TELEGRAM_BOT_TOKEN','');chat=os.environ.pop('TELEGRAM_CHAT_ID','')
    try:
        docs=Documents(gh)
        calendar=None
        if a.action=='run':
            try:calendar=refresh()
            except Exception:raise ValueError('official_calendar_fetch_failed_no_acquisition') from None
            docs.save('data/trading_calendar.json',calendar)
        run(a.action,docs,acq.Client(apify) if apify else None,key,Telegram(token) if token else None,chat,calendar=calendar)
    except Exception as exc:
        if isinstance(exc,ValueError) and str(exc) in ('official_calendar_fetch_failed_no_acquisition','official_trading_calendar_missing_or_wrong_year','official_trading_calendar_expired','author_policy_mismatch','unknown_request_requires_manual_reconciliation'):
            print(str(exc))
        # Transport exception strings may contain URLs/credentials. Durable reservations remain intact.
        raise SystemExit('流程停止：外部服務／設定／checkpoint 異常；保留帳本，不自動重送。請核對 live_control 與 outbox。') from None
if __name__=='__main__':main()

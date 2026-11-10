"""Authorized after-the-fact trading-day acquisition cost replay. MPL-2.0.
Public posts only; no classification, notifications, production cursor reads or writes.
"""
import csv
import io
import json
import os
import re
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo
import apify_cost_test as t

ID = 'apify-day-replay-20261110-01'
LEDGER = 'data/cost_tests/' + ID + '.json'
POSTS = 'data/cost_tests/' + ID + '-posts.json'
TAIPEI = ZoneInfo('Asia/Taipei')
INITIAL = datetime(2026, 11, 9, 13, 30, tzinfo=TAIPEI).astimezone(timezone.utc)
FIRST = datetime(2026, 11, 10, 8, 45, tzinfo=TAIPEI).astimezone(timezone.utc)
SLOTS = [FIRST + timedelta(minutes=15*i) for i in range(20)]
OPTIONS = {'timeout': 180, 'memory': 512, 'maxItems': 50, 'maxTotalChargeUsd': '0.10', 'restartOnError': 'false'}
CAP_WORDS = ('maximum total charge', 'max total charge', 'max charge', 'max paid', 'maximum number of items')


def now(): return datetime.now(timezone.utc)
def stamp(dt): return dt.isoformat()
def taipei(value): return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(TAIPEI).isoformat()


class Documents(t.Docs):
    def formal_shas(self):
        # Read only the Git tree (hashes), never production cursors or production post bodies.
        store = t.h.GitHubStore(self.token, LEDGER)
        result = store._request('GET', 'https://api.github.com/repos/ChungChingHua/8zz-Contrarian-Indicator-TradingView/git/trees/' + t.h.BRANCH + '?recursive=1')
        if result.get('truncated'): raise ValueError('formal_tree_truncated')
        return {e['path']:e['sha'] for e in result['tree'] if e['type']=='blob' and
            (e['path'].endswith('.pine') or e['path'].startswith('data/') or
             e['path'] in ('docs/social-status.json','.github/workflows/live-update.yml')) and
            not e['path'].startswith('data/cost_tests/') and e['path'] != 'data/usage.json'}


def limited(entry):
    return (entry.get('result_count', 0) >= 50 or entry.get('cap_message', False) or
            any(entry.get(k) is not None and Decimal(str(entry[k])) >= t.CAP
                for k in ('usageTotalUsd', 'externalChargedTotalUsd')))


def capture(entry, run, phase):
    t.record_run(entry, run)
    entry['cap_message'] = entry.get('cap_message',False) or any(w in str(run.get('statusMessage','')).lower() for w in CAP_WORDS)
    entry.setdefault('cost_snapshots', []).append(dict(phase=phase,
        observed_at=entry['cost_observed_at'], **{k:entry.get(k) for k in
            ('usageTotalUsd','usageUsd','externalChargedTotalUsd','chargedEventCounts','accountedChargedEventCounts')}))
    entry['cost_basis'] = 'usageTotalUsd only; other fee fields are not added again'


def inspect_rows(rows, source, start, end, posts, entry):
    counts = {'result_count':len(rows), 'valid_posts':0, 'diagnostic_rows':0, 'duplicates':0,
              'first_new':0, 'outside_window':0, 'excluded':{}, 'diagnostic_codes':{}, 'uncertain_rows':0}
    found=[]
    for row in rows:
        if not isinstance(row,dict): counts['uncertain_rows']+=1; continue
        if row.get('error') and not row.get('postId'):
            counts['diagnostic_rows'] += 1
            code = row.get('error')
            safe = code if isinstance(code,str) and re.fullmatch('[A-Za-z0-9_-]{1,80}',code) else 'unrecognized'
            counts['diagnostic_codes'][safe] = counts['diagnostic_codes'].get(safe,0)+1
            if safe != 'no_items': counts['uncertain_rows'] += 1
            message=(str(code)+' '+str(row.get('errorDescription',''))).lower()
            if any(w in message for w in ('quota','insufficient','credit','balance','unauthorized','forbidden','authentication','access denied','rate limit')):
                entry['diagnostic_service_block']=True
            continue
        p,reason = t.h.s.normalize(t.plain(row),source)
        if p is None:
            counts['excluded'][reason] = counts['excluded'].get(reason,0)+1
            expected = reason in ('other_author','before_start') or (reason=='reply_repost_or_unknown' and
                (row.get('isReply') is True or row.get('isRepost') is True))
            if not expected: counts['uncertain_rows']+=1
            continue
        dt=datetime.fromisoformat(p['published_at'])
        if not start <= dt < end: counts['outside_window']+=1; continue
        counts['valid_posts']+=1; found.append(p['key'])
        if p['key'] in posts:
            counts['duplicates']+=1
            # Preserve first-seen version; changes must be visible, not silently overwritten.
            if posts[p['key']]['text'] != p['text']:
                entry.setdefault('changed_post_keys',[]).append(p['key']); counts['uncertain_rows']+=1
        else:
            counts['first_new']+=1
            p=t.h.s.public_safe(p)
            p['analysis']={'status':'cost_test_only','reason':'未呼叫 AI；不寫入正式事件'}
            p['replay_first_seen_round']=entry['round'];p['fetched_at']=stamp(now())
            posts[p['key']]=p
    entry.update(counts,post_keys=found)
    entry['coverage_warning']='After-the-fact replay; cannot establish realtime completeness or detection latency.'


def reconcile_coverage(state):
    """Re-evaluate test cursors using final costs; preserve queried windows as actually sent."""
    for source in t.ACTORS:
        cursor=INITIAL
        for entry in state['runs']:
            if entry['source'] != source: continue
            reasons=[]
            if entry.get('status') != 'SUCCEEDED': reasons.append('run_not_successful')
            if entry.get('result_count') is None: reasons.append('dataset_not_saved')
            if limited(entry): reasons.append('result_or_cost_limit_possible_truncation')
            if entry.get('uncertain_rows'): reasons.append('unrecognized_rows_or_changed_content')
            if datetime.fromisoformat(entry['query_start_utc']) > cursor:
                reasons.append('gap_after_earlier_incomplete_window')
            entry['incomplete_reasons']=reasons
            entry['cursor_advanced_final']=not reasons
            if not reasons: cursor=max(cursor,datetime.fromisoformat(entry['query_end_utc']))
        state['test_cursors'][source]=stamp(cursor)
    state['incomplete_windows']=[{k:e.get(k) for k in ('round','source','query_start_utc','query_end_utc','incomplete_reasons')}
        for e in state['runs'] if e.get('incomplete_reasons')]
    completed={(e['round'],e['source']) for e in state['runs']}
    state['unattempted']=[{'round':i+1,'source':s,'simulated_cutoff_utc':stamp(slot)}
        for i,slot in enumerate(SLOTS) for s in t.ACTORS if (i+1,s) not in completed]


def totals(state):
    sums={s:Decimal(0) for s in t.ACTORS};missing=[]
    for e in state['runs']:
        if e.get('usageTotalUsd') is None: missing.append({'round':e['round'],'source':e['source']})
        else: sums[e['source']]+=Decimal(str(e['usageTotalUsd']))
    total=sum(sums.values(),Decimal(0))
    state['costs']={'platform_usd':t.plain(sums),'observed_total_usd':str(total),
        'missing_costs':missing,'basis':'Sum usageTotalUsd once per run; do not add usageUsd/event charges/externalChargedTotalUsd.',
        'billing_finality':'API observations only; not independently settled invoice. Zero does not establish free service.',
        'monthly_estimates_usd':{str(n):str(total*n) for n in (20,22,23)} if not missing and len(state['runs'])==40 else None}


def execute(docs, client, pause=time.sleep):
    prior=docs.load(LEDGER)
    if prior is not None: return prior  # Never re-submit any portion of an existing authorized replay.
    state={'test_id':ID,'status':'preflight','created_at':stamp(now()),'maximum_starts':40,
        'cap_usd_per_start':'0.10','maximum_authorized_usd':'4.00','automatic_retries':0,
        'initial_test_cutoff_utc':stamp(INITIAL),'simulated_cutoffs_utc':[stamp(x) for x in SLOTS],
        'test_cursors':{s:stamp(INITIAL) for s in t.ACTORS},'runs':[],'pricing':{},'reserved_starts':0,
        'after_the_fact':True,'posts_ledger':POSTS,'formal_shas_before':docs.formal_shas()}
    posts={};usage=None;month=None
    def save():
        state['apify_http_requests']=dict(client.counts);state['updated_at']=stamp(now())
        docs.save(LEDGER,state)
    def chargebook():
        if usage is None: return
        reservation=usage[month].setdefault('cost_test_reservations',{}).setdefault(ID,{})
        reservation.update(ledger=LEDGER,authorized_max_starts=40,authorized_maximum_usd='4.00',
            reserved_starts=state['reserved_starts'],started_run_ids=[e['id'] for e in state['runs'] if e.get('id')],
            observed_cost=state.get('costs',{}),unresolved_submissions=sum(e.get('status')=='submission_unknown' for e in state['runs']))
        docs.save('data/usage.json',usage)
    save()
    try:
        usage=docs.load('data/usage.json') or {};month=now().strftime('%Y-%m')
        budget=usage.setdefault(month,{'apify_runs':0,'ai_attempts':0})
        state['monthly_runs_before']=budget['apify_runs']
        if budget['apify_runs']+40>70: raise t.Failure('monthly_70_run_guard_insufficient_for_40_no_start')
        for source,actor in t.ACTORS.items():
            meta=client.request('/acts/'+actor)['data']
            state['pricing'][source]={'actor':actor,'pricing':t.pricing(meta,now()),'defaultRunOptions':t.plain(meta.get('defaultRunOptions',{}))}
        state['status']='running';save()
        for i,end in enumerate(SLOTS):
            for source,actor in t.ACTORS.items():
                if state['reserved_starts']>=40: raise t.Failure('authorized_start_limit')
                base=datetime.fromisoformat(state['test_cursors'][source]);start=base-timedelta(hours=2)
                entry={'round':i+1,'source':source,'actor':actor,'simulated_cutoff_taipei':end.astimezone(TAIPEI).isoformat(),
                    'base_start_utc':stamp(base),'query_start_utc':stamp(start),'query_end_utc':stamp(end),
                    'query_start_taipei':start.astimezone(TAIPEI).isoformat(),'query_end_taipei':end.astimezone(TAIPEI).isoformat(),
                    'input':t.inputs(source,stamp(start),stamp(end)),'requested_options':OPTIONS.copy(),'status':'reserved_not_submitted'}
                state['runs'].append(entry)
                if budget['apify_runs']>=70: raise t.Failure('monthly_70_run_guard')
                budget['apify_runs']+=1;state['reserved_starts']+=1
                chargebook();save() # Shared budget ACK before submission intent.
                entry['status']='submission_unknown';save() # Intent ACK before POST; ambiguous never re-sent.
                try:
                    run=client.request('/acts/'+actor+'/runs?'+urllib.parse.urlencode(OPTIONS),entry['input'])['data']
                except t.Failure as exc:
                    if exc.status in (400,401,402,403,404,422): entry['status']='submission_rejected'
                    entry.update(error_code=exc.code,http_status=exc.status);raise
                capture(entry,run,'submission');save()
                opts=run.get('options',{})
                if Decimal(str(opts.get('maxTotalChargeUsd','-1'))) != t.CAP or opts.get('isMaxTotalChargeUsdSetByUser') is not True:
                    client.request('/actor-runs/'+run['id']+'/abort',{})
                    raise t.Failure('cap_not_acknowledged_abort_no_new_start')
                if opts.get('restartOnError') is not False: raise t.Failure('restart_policy_not_acknowledged')
                for attempt in range(50):
                    run=client.request('/actor-runs/'+entry['id'])['data']
                    if run['status'] not in ('READY','RUNNING','TIMING-OUT','ABORTING'): break
                    if attempt<49: pause(5)
                capture(entry,run,'completed_preliminary');save()
                if run['status']!='SUCCEEDED': raise t.Failure('actor_service_failure_stop')
                # Read stored dataset pages only. Never start pagination or backfill Actors.
                rows=[];offset=0
                while True:
                    page=client.request('/datasets/'+run['defaultDatasetId']+'/items?format=json&offset='+str(offset)+'&limit=100')
                    if not isinstance(page,list): raise t.Failure('invalid_dataset_shape')
                    rows.extend(page)
                    if len(page)<100: break
                    offset+=len(page)
                    if offset>1000: raise t.Failure('bounded_dataset_exceeded')
                inspect_rows(rows,source,start,end,posts,entry)
                docs.save(POSTS,posts) # Save independent post/dedup ledger before advancing test cursor.
                if entry.get('diagnostic_service_block'): raise t.Failure('actor_diagnostic_quota_auth_or_access_stop')
                streak=state.setdefault('uncertain_streak',{})
                streak[source]=streak.get(source,0)+1 if entry['uncertain_rows'] else 0
                if streak[source]>=2: raise t.Failure('persistent_unrecognized_dataset_stop')
                if entry.get('usageTotalUsd') is not None and Decimal(str(entry['usageTotalUsd']))>t.CAP:
                    raise t.Failure('reported_cost_exceeds_authorized_cap_stop')
                if not limited(entry) and not entry['uncertain_rows']: state['test_cursors'][source]=stamp(end)
                else: entry['cursor_not_advanced']=True
                save()
        state['status']='completed'
    except Exception as exc:
        state.update(status='stopped',error_code=getattr(exc,'code',type(exc).__name__),http_status=getattr(exc,'status',None))
        save()
    # No new Actor starts below this point, including on errors. One final GET per known run.
    for entry in state['runs']:
        if not entry.get('id'): continue
        try:
            finished=entry.get('finishedAt')
            if finished:
                age=(now()-datetime.fromisoformat(finished.replace('Z','+00:00'))).total_seconds()
                if age<12: pause(12-age)
            run=client.request('/actor-runs/'+entry['id'])['data']
            capture(entry,run,'final_readonly_refresh');entry['final_cost_refreshed']=True;save()
        except Exception as exc:
            state['billing_refresh_error']={'code':getattr(exc,'code',type(exc).__name__),'http_status':getattr(exc,'status',None)}
            save();break # No repeated reads on auth/quota/service failure.
    reconcile_coverage(state);totals(state)
    state['monthly_runs_after']=usage[month]['apify_runs'] if usage is not None and month else None
    state['formal_shas_after']=docs.formal_shas()
    state['formal_state_unchanged']=state['formal_shas_before']==state['formal_shas_after']
    state['unique_posts']=len(posts)
    chargebook();save()
    return state


def write_reports(state, root):
    fields=['round','source','simulated_cutoff_taipei','base_start_utc','query_start_taipei','query_end_taipei','actor',
        'buildNumber','buildId','id','status','duration_seconds','result_count','valid_posts','diagnostic_rows',
        'duplicates','first_new','outside_window','usageTotalUsd','externalChargedTotalUsd','cost_observed_at',
        'cursor_advanced_final','incomplete_reasons']
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');writer.writeheader()
    for e in state['runs']:
        row={k:e.get(k) for k in fields};row['incomplete_reasons']=';'.join(e.get('incomplete_reasons',[]));writer.writerow(row)
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    (root/(ID+'.csv')).write_text(out.getvalue())
    (root/(ID+'.json')).write_text(json.dumps(t.plain(state),ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    if os.getenv('AUTHORIZED_DAY_REPLAY')!=ID: raise SystemExit('replay authorization missing')
    key=os.environ['APIFY_TOKEN'];token=os.environ['GH_TOKEN']
    if not key or not token: raise SystemExit('required secret missing; no requests')
    result=execute(Documents(token),t.Client(key))
    write_reports(result,'cost-test-artifacts')
    print(json.dumps({k:result.get(k) for k in ('test_id','status','error_code','reserved_starts','costs','apify_http_requests','formal_state_unchanged')}))

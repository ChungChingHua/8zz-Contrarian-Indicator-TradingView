"""Offline next-stage plan and quota guards. No network, key access or executor. MPL-2.0."""
import argparse
import copy
import json
import re
import math
from pathlib import Path
DEFAULT_LIMIT=5
HARD_LIMIT=10


def build_plan(records,limit=DEFAULT_LIMIT,monthly_remaining=50):
    if type(limit) is not int or not 1<=limit<=HARD_LIMIT:raise ValueError('batch_limit_must_be_1_to_10')
    if type(monthly_remaining) is not int or monthly_remaining<0:raise ValueError('invalid_attempt_budget')
    selected=[];skipped=[];seen=set()
    for row in records:
        key=row['key']
        if key in seen:raise ValueError('duplicate_post_in_plan')
        seen.add(key)
        if row['status']!='unprocessed':
            skipped.append({'key':key,'reason':'existing_result_or_review_requires_manual_action'});continue
        if len(selected)>=min(limit,monthly_remaining):break
        if not re.fullmatch(r'[0-9a-f]{64}',row.get('content_hash','')):raise ValueError('content_hash_required')
        selected.append({'key':key,'content_hash':row['content_hash']})
    return {'mode':'offline_plan_only','online_execution_enabled':False,'default_limit':DEFAULT_LIMIT,'hard_limit':HARD_LIMIT,
        'max_generation_requests':len(selected),'max_requests_per_post':1,'automatic_retries':0,'max_output_tokens_per_request':3000,
        'monthly_attempts_remaining_declared':monthly_remaining,'selected':selected,'skipped':skipped,
        'quota_confirmation_required':True,'remaining_free_points':None,
        'notes':'Attempt limits are not free-point/token/dollar guarantees. Future worker must persist reservations before network and obtain separate authorization; no fallback or formal Pine writes.'}


def reserve(ledger,batch_id,plan,quota_confirmed=False):
    """Pure reservation draft. Future caller must durably commit it before any network."""
    if quota_confirmed is not True:raise ValueError('confirm_free_allowance_before_execution')
    state=copy.deepcopy(ledger)
    batches=state.setdefault('batches',{})
    if batch_id in batches:raise ValueError('batch_already_reserved_no_rerun')
    attempted=state.setdefault('attempted_post_hashes',[])
    ids=[p['key']+'@'+p['content_hash'] for p in plan['selected']]
    if any(k in attempted for k in ids):raise ValueError('post_hash_already_reserved_no_automatic_retry')
    available=min(state.get('monthly_attempts_remaining',plan['monthly_attempts_remaining_declared']),plan['monthly_attempts_remaining_declared'])
    if len(ids)>min(HARD_LIMIT,plan['max_generation_requests'],available):raise ValueError('attempt_budget_exhausted')
    state['monthly_attempts_remaining']=available-len(ids)
    state['attempted_post_hashes']+=ids
    batches[batch_id]={'status':'reserved_before_network','posts':ids,'reserved_attempts':len(ids),'retry_on_crash':False}
    return state


def stop_reason(http_status,error_code=None,response_valid=True,remaining_requests=None,remaining_points=None):
    if error_code in ('insufficient_quota','billing_hard_limit_reached','rate_limit_exceeded'):return 'quota_or_rate_limit'
    if http_status not in range(200,300):return 'http_or_transport_error'
    if not response_valid:return 'invalid_required_response'
    if any(v is not None and (type(v) not in (int,float) or not math.isfinite(v)) for v in (remaining_requests,remaining_points)):return 'invalid_allowance_metadata'
    if remaining_requests is not None and remaining_requests<=0:return 'request_allowance_exhausted'
    if remaining_points is not None and remaining_points<=0:return 'free_points_exhausted'
    return None  # None quota values mean unknown, never "zero deducted".


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state-file',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--limit',type=int,default=DEFAULT_LIMIT);p.add_argument('--monthly-remaining',type=int,default=50)
    a=p.parse_args();data=json.loads(a.state_file.read_text())
    result=build_plan(data['records'],a.limit,a.monthly_remaining)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'offline_only':True,'planned_requests':result['max_generation_requests'],'skipped':len(result['skipped'])}))

if __name__=='__main__':main()

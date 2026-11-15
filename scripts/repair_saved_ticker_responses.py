"""Offline repair of six complete responses; no provider calls or changed prompts. MPL-2.0."""
import copy,hashlib,json
from pathlib import Path
import history_completion as hc
import history_worker as h
import original_author as p

EXPECTED={'facebook:1711515410333047','facebook:1700739848077270','facebook:1700801464737775','threads:3958223690278707712','threads:4023406251229152584','facebook:1634810338003555'}
AUDIT='data/offline_ticker_repair_20261115.json'

def main():
    if (hc.ROOT/AUDIT).exists():raise SystemExit('Existing offline audit; no duplicate repair')
    before=hc.h.s.read(hc.ROOT/'data/history_completion_summary.json',{})
    control=h.s.read(hc.ROOT/hc.CONTROL,{})
    if not control.get('closed'):raise ValueError('online_session_still_active')
    data=hc.archive();changed={};audit=[]
    for path in sorted((hc.ROOT/'data/history_progress').glob('*.json')):
        if path.name.endswith('.uncommitted.json'):continue
        ledger=h.s.read(path,{})
        for r in ledger.get('records',[]):
            if r['key'] not in EXPECTED or r.get('status')=='not_started':continue
            if r.get('status')!='technical_failure' or r.get('reason')!='invalid_ticker_format' or r.get('http_status')!=200 or r.get('attempts')!=1:raise ValueError('only_saved_complete_ticker_failures_authorized')
            raw_before=copy.deepcopy(r['raw_response']);attempts=ledger['reserved_generation_attempts']
            scope=r.get('media_scope',{})
            answer=p.parse(raw_before['json'],scope.get('images_supplied',0),scope.get('unanalysed_media',[]))
            processed=p.process(data[r['key']],answer)
            if not answer.get('ticker_resolution') or answer['ticker']!='':raise ValueError('metadata_was_not_cleared_without_guessing')
            row={'key':r['key'],'ledger':str(path.relative_to(hc.ROOT)),'from_status':r['status'],'raw_response_sha256':h.digest(raw_before),
                'original_ai_ticker':answer['original_ai_ticker'],'direction':processed['direction'],'strength':processed['strength'],
                'to_status':'completed_signal' if processed['status']=='done' else 'pending_confirmation' if processed['status']=='review' else 'completed_no_signal'}
            r.setdefault('local_validation_history',[]).append({'status':r['status'],'reason':r['reason'],'error_type':r.get('error_type'),
                'resolution':'Offline ticker metadata clear; all other schema, direction, model, reasoning and image-coverage validations rerun. No new generation.',
                'audit':AUDIT,'at':h.now()})
            r.update(status=row['to_status'],processed=processed,offline_reprocessed_at=h.now())
            r.pop('reason',None);r.pop('error_type',None)
            if r['raw_response']!=raw_before or ledger['reserved_generation_attempts']!=attempts or r['attempts']!=1:raise ValueError('response_or_attempts_changed')
            audit.append(row);changed[path]=ledger
    if {r['key'] for r in audit}!=EXPECTED or len(audit)!=6:raise ValueError('exact_six_saved_responses_required')
    # Preserve the closed online session's original result: offline recovery is not a new paid batch.
    old=control.pop('current_session',None)
    if old:
        old=copy.deepcopy(old);old['result']=copy.deepcopy(before.get('current_session',{}));old['closed']=True
        if not any(s.get('id')==old['id'] for s in control.get('session_history',[])):control.setdefault('session_history',[]).append(old)
        control['last_online_session_id']=old['id']
    proof={'id':'offline-ticker-metadata-20261115','at':h.now(),'provider_requests':0,'reused_responses':6,'rule_sha256':p.fingerprint(),
        'raw_responses_unchanged':True,'generation_attempts_unchanged':True,'audit':AUDIT,'recovered_technical_failures':6}
    control.setdefault('offline_repair_history',[]).append(proof)
    for path,ledger in changed.items():h.s.write(path,ledger)
    h.s.write(hc.ROOT/hc.CONTROL,control);h.s.write(hc.ROOT/AUDIT,{**proof,'records':audit})
    summary=hc.report()
    if summary['new_generation_attempts']!=before['new_generation_attempts'] or summary['service_reported_usage']!=before['service_reported_usage']:raise ValueError('offline_repair_changed_usage')
    inv=h.s.read(hc.ROOT/'data/history_completion_inventory.json',[])
    remaining=[r for r in inv if r['status'] not in ('completed_signal','completed_no_signal')]
    h.s.write(hc.ROOT/'data/history_unresolved_after_offline_ticker_20261115.json',{'total':len(remaining),'status_counts':summary['post_status_counts'],'items':remaining})
    print(json.dumps({'provider_requests':0,'restored':len(audit),'events':summary['pine']['total_events'],'statuses':summary['post_status_counts']},ensure_ascii=False))

if __name__=='__main__':main()

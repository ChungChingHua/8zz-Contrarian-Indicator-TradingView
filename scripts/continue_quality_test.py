"""Only unattempted rows 6..10 after known Video input block, same authorization. MPL-2.0."""
import copy
import os
from datetime import datetime,timezone
import authorized_quality_test as t
import quality_protocol as q
SCOPE='2026-11-07-independent-quality-unattempted-only-v1'


def validate_resume(report,plan):
    if report.get('scope')!=t.SCOPE or report.get('continuation_consumed'):raise ValueError('continuation_not_available')
    if report.get('protocol_sha256')!=q.digest() or report.get('plan_sha256')!=t.plan_hash(plan):raise ValueError('same_protocol_required')
    if report.get('http_counts',{}).get('generation')!=4 or report.get('stop_sample')!=5:raise ValueError('unexpected_request_history')
    rows=report.get('samples',[])
    if len(rows)!=10:raise ValueError('wrong_sample_count')
    for i,row in enumerate(rows):
        if row['key']!=plan['samples'][i]['key']:raise ValueError('sample_identity_mismatch')
        if i<4:
            if row['status']!='evaluated_test_only' or row['generation_attempts']!=1 or row['api_status']!=200:raise ValueError('service_anomaly_no_continuation')
        elif i==4:
            if row['status']!='input_review' or row['generation_attempts']!=0 or row.get('api_status') is not None or row.get('error_reason')!='video_or_unknown_media_requires_review':raise ValueError('only_known_video_input_block_permitted')
        elif row['status']!='not_attempted' or row['generation_attempts']!=0:raise ValueError('only_unattempted_remaining_samples')


def main():
    if os.getenv('AUTHORIZED_QUALITY_SCOPE')!=SCOPE or os.getenv('GITHUB_REF')!='refs/heads/codex/social-pipeline-20261106' or os.getenv('GITHUB_RUN_ATTEMPT')!='1':raise SystemExit('Continuation scope missing or rerun refused')
    plan=t.s.read(t.PLAN,{})
    if os.getenv('AUTHORIZED_PROTOCOL_SHA256')!=q.digest() or os.getenv('AUTHORIZED_PLAN_SHA256')!=t.plan_hash(plan):raise SystemExit('Frozen protocol/input mismatch')
    report=t.s.read(t.REPORT,{})
    validate_resume(report,plan)
    key=os.getenv('CHATANYWHERE_API_KEY')
    if not key:raise SystemExit('Missing dedicated Secret; no requests')
    audit=t.Audit.__new__(t.Audit)
    audit.key=key;audit.path=t.REPORT;audit.current=None
    audit.transport=lambda *args:t.OldTransport.http(audit,*args)
    audit.report=copy.deepcopy(report)
    audit.report.update(continuation_consumed=True,continuation_scope=SCOPE,continuation_at=datetime.now(timezone.utc).isoformat(),
        continuation_reason='Known non-image Video input blocked before generation, no provider anomaly; reuse same-protocol successful rows 1..4, skip blocked row5, only unattempted rows6..10. Total budget10 unchanged.',
        stopped=False,initial_input_stop_sample=5,input_blocked_samples=[5],stop_sample=None)
    audit.save()
    t.run(audit,t.selected_posts(plan))
    print('Remaining authorized samples processed; no prior generation retried; combined evidence saved')
    if audit.report['stopped']:raise SystemExit(1)

if __name__=='__main__':main()

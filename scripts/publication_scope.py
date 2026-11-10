"""Apply the owner's publication boundary before website simulation. MPL-2.0."""
from collections import Counter
from datetime import datetime
import copy

STATUSES=('completed_signal','completed_no_signal','pending_confirmation','technical_failure','input_failure','unknown','not_started')
def scope(events,inventory,market,policy):
    limit=datetime.fromisoformat(policy['published_before'])
    if limit.tzinfo is None:raise ValueError('publication_limit_needs_timezone')
    ms=int(limit.timestamp()*1000)
    ev=copy.deepcopy([e for e in events if e['unix_ms']<ms])
    rows=copy.deepcopy([r for r in inventory if datetime.fromisoformat(r['display_time'])<limit])
    # Do not change IDs: the website and saved shared-event keys remain reconcilable.
    market=copy.deepcopy(market)
    market['series']={interval:[b for b in bars if b['time']<ms] for interval,bars in market['series'].items()}
    counts=Counter(r['status'] for r in rows)
    summary={'post_status_counts':{s:counts[s] for s in STATUSES},'archive_posts':len(rows),
             'remaining_not_started_groups':counts['not_started'],
             'latest_signal_date':max((e['time'] for e in ev if e['direction']),default=None)}
    return ev,rows,market,summary,{'before':limit.isoformat(),'label':policy['label'],'update_mode':'依使用者要求更新','remaining_count_basis':'尚未處理篇數，非跨平台去重群組數'}

def assert_boundary(data):
    publication=data.get('publication')
    if not publication:raise ValueError('missing_publication_boundary')
    limit=datetime.fromisoformat(publication['before']);ms=int(limit.timestamp()*1000)
    if any(e['unix_ms']>=ms for e in data['events']):raise ValueError('out_of_scope_event')
    if any(datetime.fromisoformat(r['display_time'])>=limit for r in data['inventory']):raise ValueError('out_of_scope_post')
    if any(b['time']>=ms for bars in data['market']['series'].values() for b in bars):raise ValueError('out_of_scope_market')
    for modes in (data['modes'],data['available_modes']):
        for m in modes.values():
            if any(p['time']>=ms for p in m['curve']):raise ValueError('out_of_scope_curve')
            for t in m['trades']:
                for key in ('entry','exit','mark'):
                    if t.get(key) and t[key]['time']>=ms:raise ValueError('out_of_scope_trade')

    for name,instrument in data.get('instruments',{}).items():
        if name=='TXF':
            from zoneinfo import ZoneInfo
            def check_daytime(ts):
                t=datetime.fromtimestamp(ts/1000,ZoneInfo('Asia/Taipei'))
                if not 525<t.hour*60+t.minute<=825:raise ValueError('out_of_daytime_futures_price')
            for bars in instrument['market']['series'].values():
                for bar in bars:check_daytime(bar['time'])
            for modes in (instrument['modes'],instrument['available_modes']):
                for m in modes.values():
                    for point in m['curve']:check_daytime(point['time'])
                    for trade in m['trades']:
                        for key in ('entry','exit','mark'):
                            if trade.get(key):check_daytime(trade[key]['time'])
        child=dict(data,market=instrument['market'],modes=instrument['modes'],available_modes=instrument['available_modes'])
        child.pop('instruments',None)
        assert_boundary(child)

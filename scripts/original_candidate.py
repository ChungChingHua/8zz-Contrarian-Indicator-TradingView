"""Complete candidate Pine from preserved history plus canonical author-policy results. MPL-2.0."""
import json,re
from pathlib import Path
import original_author as policy
from update_pine_script import build_push_block,EVENT_PATTERN,HEADER_COUNT_PATTERN,apply_indicator_title
from pine_initialization import split_initialization,check_initialization
ROOT=policy.ROOT
OUT=ROOT/'candidates/8zz-original-author-batch-01.pine'

def build(ledger):
    text=(ROOT/'data/historical-indicator.pine').read_text();lines=text.splitlines(keepends=True);added=0
    for r in ledger['records']:
        a=r.get('processed',{})
        if r['status']!='completed_signal' or not policy.event_eligible(a):continue
        tip=f"{a['action']}\n指標: {'偏多 ▲' if a['direction']==1 else '偏空 ▼'} | 強度: {a['strength']}\n{r['display_time']} {r['text']}\n{a['reasoning']}\n"+'\n'.join(m['url'] for m in r['members'])
        block=build_push_block({'unix_ms':r['unix_ms'],'direction':a['direction'],'strength':a['strength'],'ticker':a['ticker'],'tooltip':tip})
        index=next((i for i,line in enumerate(lines) if (m:=re.search(r'array\.push\(evt_time, (\d+)',line)) and int(m[1])>r['unix_ms']),None)
        if index is None:index=max(i for i,l in enumerate(lines) if 'array.push(evt_ticker,' in l)+1
        lines.insert(index,block);added+=1
    from pine_accounting import apply_accounting
    candidate=apply_indicator_title(apply_accounting(split_initialization(''.join(lines))))
    count=len(EVENT_PATTERN.findall(candidate))
    dates=[r['display_time'][:7].replace('-','/') for r in ledger['records'] if r['status']=='completed_signal']
    if dates:candidate=HEADER_COUNT_PATTERN.sub(lambda m:m[1]+str(count)+m[3]+max(m[4],*dates),candidate,count=1)
    for event in EVENT_PATTERN.finditer(text):
        if event.group() not in candidate:raise ValueError('historical_event_changed')
    matches=list(EVENT_PATTERN.finditer(candidate))
    times=[int(m.group(1)) for m in matches]
    paired=all(candidate.count('array.push('+name+',')==count for name in ('evt_time','evt_dir','evt_str','evt_tips','evt_ticker'))
    ordered=times==sorted(times)
    valid=all(int(m.group(2)) in (-1,0,1) and int(m.group(3)) in (1,2,3) for m in matches)
    if not (paired and ordered and valid):raise ValueError('candidate_structure_invalid')
    return candidate,{'historical_events':len(EVENT_PATTERN.findall(text)),'added_events':added,'total_events':count,
        'historical_blocks_preserved':True,'historical_neutral_events_preserved':sum(int(m.group(2))==0 for m in EVENT_PATTERN.finditer(text)),'new_events_nonzero':True,'arrays_paired':paired,'timestamps_ordered':ordered,'directions_strengths_valid':valid,'tradingview_compiled':False,**check_initialization(candidate)}

def main():
    from history_worker import LOCAL
    ledger=json.loads(LOCAL.read_text());text,stats=build(ledger)
    OUT.parent.mkdir(exist_ok=True);OUT.write_text(text)
    (OUT.with_suffix('.checks.json')).write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(stats))
if __name__=='__main__':main()

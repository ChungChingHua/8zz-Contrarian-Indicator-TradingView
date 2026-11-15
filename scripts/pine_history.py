"""Apply the user-supplied published history to the immutable fork seed. MPL-2.0."""
import hashlib,json
from pathlib import Path
from update_pine_script import EVENT_PATTERN,HEADER_COUNT_PATTERN
from pine_initialization import initialization_span
ROOT=Path(__file__).resolve().parents[1]

def reconcile_history(text):
    manifest=json.loads((ROOT/'data/author_history_reconciliation.json').read_text())
    reference=(ROOT/manifest['reference_file']).read_text()
    if hashlib.sha256(text.encode()).hexdigest()!=manifest['fork_base_sha256']:raise ValueError('fork_history_source_changed')
    if hashlib.sha256(reference.encode()).hexdigest()!=manifest['reference_sha256']:raise ValueError('published_history_source_changed')
    fork=list(EVENT_PATTERN.finditer(text));author=list(EVENT_PATTERN.finditer(reference))
    if len(author)!=manifest['reference_event_count']:raise ValueError('published_history_count_changed')
    original={int(m[1]):m for m in fork};published={int(m[1]):m for m in author}
    if len(original)!=len(fork) or len(published)!=len(author):raise ValueError('duplicate_reference_timestamp')
    merged={ts:m.group() for ts,m in original.items()};changes=[]
    aliases={x['reference_unix_ms']:x['fork_unix_ms'] for x in manifest['retimed_events']}
    for ts,m in published.items():
        old_ts=ts if ts in original else aliases.get(ts)
        if old_ts is None:
            changes.append({'kind':'insert','reference_unix_ms':ts,'before':None,'after':list(m.groups())})
        else:
            if old_ts not in original:raise ValueError('missing_explicit_retime_source')
            previous=original[old_ts]
            if previous.groups()!=m.groups():
                changes.append({'kind':'retime' if old_ts!=ts else 'update','fork_unix_ms':old_ts,'reference_unix_ms':ts,'before':list(previous.groups()),'after':list(m.groups())})
            merged.pop(old_ts)
        merged[ts]=m.group()
    start,body_start,end=initialization_span(text)
    body=text[body_start:end]
    if EVENT_PATTERN.sub('',body).strip():raise ValueError('unexpected_fork_initialization_logic')
    data=''.join('    '+merged[ts]+'\n' for ts in sorted(merged))+'\n'
    result=text[:body_start]+data+text[end:]
    result=HEADER_COUNT_PATTERN.sub(lambda m:m[1]+str(len(merged))+m[3]+m[4],result,count=1)
    tuples=EVENT_PATTERN.findall(result)
    if any(m.groups() not in tuples for m in author):raise ValueError('published_event_not_preserved')
    changed_old={x['fork_unix_ms'] for x in changes if x.get('fork_unix_ms')}
    if any(m.groups() not in tuples for ts,m in original.items() if ts not in changed_old):raise ValueError('unrelated_history_changed')
    audit={'version':manifest['version'],'reference_file':manifest['reference_file'],'reference_sha256':manifest['reference_sha256'],
       'archived_fork_source_unchanged':True,'fork_base_events':len(fork),'author_reference_events':len(author),
       'historical_events':len(tuples),'updated_events':sum(c['kind']=='update' for c in changes),
       'retimed_events':sum(c['kind']=='retime' for c in changes),'inserted_events':sum(c['kind']=='insert' for c in changes),
       'unchanged_fork_events':len(fork)-len(changed_old),'changes':changes}
    return result,audit

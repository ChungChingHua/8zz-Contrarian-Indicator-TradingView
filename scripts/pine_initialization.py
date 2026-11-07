"""Bound event initialization scopes without changing event bytes. MPL-2.0."""
import re
from update_pine_script import EVENT_PATTERN

CHUNK_EVENTS=20
BEGIN='// BEGIN GENERATED EVENT INITIALIZATION'
END='// END GENERATED EVENT INITIALIZATION'
FUNCTION=re.compile(r'^initEvtChunk\d+\(\) =>\n((?:    [^\n]*\n)+)',re.M)

def initialization_span(text):
    match=re.search(r'^if barstate\.isfirst\n',text,re.M)
    if not match:raise ValueError('missing_event_initialization')
    end=match.end()
    for line in text[match.end():].splitlines(keepends=True):
        if line.strip() and not line.startswith((' ','\t')):break
        end+=len(line)
    return match.start(),match.end(),end

def split_initialization(text):
    """Only pure five-push event initializers are transformed; fail on other logic."""
    if BEGIN in text or END in text:
        check_initialization(text)
        return text
    start,body_start,end=initialization_span(text)
    body=text[body_start:end];events=list(EVENT_PATTERN.finditer(body))
    rest=EVENT_PATTERN.sub('',body)
    if any(line.strip() and not line.lstrip().startswith('//') for line in rest.splitlines()):
        raise ValueError('non_event_logic_in_initializer')
    if not events:raise ValueError('empty_event_initializer')
    comments=[line.strip() for line in rest.splitlines() if line.lstrip().startswith('//')]
    names=[];out=[BEGIN+'\n']
    out.extend(comment+'\n' for comment in comments)
    for offset in range(0,len(events),CHUNK_EVENTS):
        name=f'initEvtChunk{len(names)+1:03d}';names.append(name)
        out.append(name+'() =>\n')
        out.extend('    '+event.group()+'\n' for event in events[offset:offset+CHUNK_EVENTS])
        out.append('    0\n\n')  # Stable int return; mutate array contents, never global references.
    out.append('if barstate.isfirst\n')
    out.extend('    '+name+'()\n' for name in names)
    out.append(END+'\n\n')
    result=text[:start]+''.join(out)+text[end:]
    if EVENT_PATTERN.findall(result)!=EVENT_PATTERN.findall(text):raise ValueError('event_data_changed')
    check_initialization(result)
    return result

def check_initialization(text):
    start,body_start,end=initialization_span(text)
    if text.count(BEGIN)!=1 or text.count(END)!=1:raise ValueError('invalid_initialization_markers')
    functions=list(FUNCTION.finditer(text));names=re.findall(r'^(initEvtChunk\d+)\(\) =>$',text,re.M)
    calls=re.findall(r'^    (initEvtChunk\d+)\(\)$',text[body_start:end],re.M)
    if not functions or names!=calls or len(set(names))!=len(names):raise ValueError('initialization_call_order_mismatch')
    sizes=[len(EVENT_PATTERN.findall(fn.group(1))) for fn in functions]
    if any(not 1<=n<=CHUNK_EVENTS for n in sizes):raise ValueError('initialization_chunk_too_large')
    if sum(sizes)!=len(EVENT_PATTERN.findall(text)):raise ValueError('events_outside_initialization_functions')
    # Every call is gated by the first bar; the conditional contains no data pushes.
    if any(line.strip() and not re.fullmatch(r'initEvtChunk\d+\(\)',line.strip()) for line in text[body_start:end].splitlines()):
        raise ValueError('unexpected_first_bar_statement')
    if any(fn.end()>start for fn in functions):raise ValueError('initialization_function_not_global_before_call')
    return {'initialization_functions':len(functions),'max_events_per_function':max(sizes),
            'first_bar_calls':len(calls),'event_initialization_chunk_limit':CHUNK_EVENTS}

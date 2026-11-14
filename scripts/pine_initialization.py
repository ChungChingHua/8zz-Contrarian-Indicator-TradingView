"""Bound packed event payloads and validate exact runtime round trips. MPL-2.0."""
import json,re
from update_pine_script import EVENT_PATTERN,escape_pine_string

CHUNK_EVENTS=20
MAX_PAYLOAD_BYTES=30000 # Below Pine's 40,960-character string limit, including Unicode.
BEGIN='// BEGIN GENERATED EVENT INITIALIZATION'
END='// END GENERATED EVENT INITIALIZATION'
ENCODING='// EVENT ENCODING: packed-v1'
FUNCTION=re.compile(r'^initEvtChunk\d+\(\) =>\n((?:    [^\n]*\n)+)',re.M)
PAYLOAD=re.compile(r'^    loadEvtRows\("((?:[^"\\]|\\.)*)"\)\s*$',re.M)
ESCAPES=(('%','%25'),('|','%7C'),('~','%7E'),('\n','%0A'),('\t','%09'))

def literal(value):return json.loads('"'+value+'"',strict=False)
def pack_field(value):
    if '\r' in value:raise ValueError('carriage_return_must_be_normalized_before_encoding')
    for old,new in ESCAPES:value=value.replace(old,new)
    return value
def unpack_field(value):
    for old,new in reversed(ESCAPES):value=value.replace(new,old)
    return value
def decoded_event(fields):
    return (*fields[:3],literal(fields[3]),literal(fields[4]))
def pack_event(fields):
    return '|'.join(pack_field(x) for x in decoded_event(fields))
def unpack_rows(payload):
    rows=[]
    for row in payload.split('~'):
        fields=row.split('|')
        if len(fields)!=5:raise ValueError('invalid_packed_event_columns')
        rows.append(tuple(unpack_field(x) for x in fields))
    return rows

DECODER='''decodeEvtField(string field) =>
    string value = str.replace_all(field, "%09", "\\t")
    value := str.replace_all(value, "%0A", "\\n")
    value := str.replace_all(value, "%7E", "~")
    value := str.replace_all(value, "%7C", "|")
    str.replace_all(value, "%25", "%")

loadEvtRows(string packed) =>
    array<string> rows = str.split(packed, "~")
    for row in rows
        array<string> fields = str.split(row, "|")
        array.push(evt_time, int(str.tonumber(array.get(fields, 0))))
        array.push(evt_dir, int(str.tonumber(array.get(fields, 1))))
        array.push(evt_str, int(str.tonumber(array.get(fields, 2))))
        array.push(evt_tips, decodeEvtField(array.get(fields, 3)))
        array.push(evt_ticker, decodeEvtField(array.get(fields, 4)))
    0

'''

def initialization_span(text):
    match=re.search(r'^if barstate\.isfirst\n',text,re.M)
    if not match:raise ValueError('missing_event_initialization')
    end=match.end()
    for line in text[match.end():].splitlines(keepends=True):
        if line.strip() and not line.startswith((' ','\t')):break
        end+=len(line)
    return match.start(),match.end(),end

def split_initialization(text):
    """Keep canonical tuples in comments; only shared decoder writes runtime arrays."""
    if BEGIN in text or END in text:
        check_initialization(text)
        if ENCODING in text:return text
        # Upgrade the earlier bounded five-push representation, including its runtime suffix.
        start=text.index(BEGIN);end=text.index(END)+len(END)
        events=list(EVENT_PATTERN.finditer(text[start:end]))
        body='if barstate.isfirst\n'+''.join('    '+e.group()+'\n' for e in events)
        return split_initialization(text[:start]+body+text[end:])
    start,body_start,end=initialization_span(text)
    body=text[body_start:end];events=list(EVENT_PATTERN.finditer(body))
    rest=EVENT_PATTERN.sub('',body)
    if any(line.strip() and not line.lstrip().startswith('//') for line in rest.splitlines()):
        raise ValueError('non_event_logic_in_initializer')
    if not events:raise ValueError('empty_event_initializer')
    comments=[line.strip() for line in rest.splitlines() if line.lstrip().startswith('//')]
    chunks=[];current=[];size=0
    for event in events:
        packed=pack_event(event.groups());length=len(packed.encode('utf-8'))
        if length>MAX_PAYLOAD_BYTES:raise ValueError('event_payload_exceeds_safe_string_limit')
        if current and (len(current)==CHUNK_EVENTS or size+1+length>MAX_PAYLOAD_BYTES):
            chunks.append(current);current=[];size=0
        current.append((event,packed));size+=length+(1 if len(current)>1 else 0)
    if current:chunks.append(current)
    names=[];out=[BEGIN+'\n',ENCODING+'\n',DECODER]
    out.extend(comment+'\n' for comment in comments)
    for chunk in chunks:
        name=f'initEvtChunk{len(names)+1:03d}';names.append(name)
        out.append(name+'() =>\n')
        # Comments are lossless audit metadata, excluded from Pine's compiled IL.
        for event,_ in chunk:out.append('    // @event '+re.sub(r'\s*\n\s*',' ',event.group())+'\n')
        out.append('    loadEvtRows("'+escape_pine_string('~'.join(p for _,p in chunk))+'")\n')
        out.append('    0\n\n')
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
    functions=list(FUNCTION.finditer(text));names=re.findall(r'^(initEvtChunk\d+)\(\) =>$' ,text,re.M)
    calls=re.findall(r'^    (initEvtChunk\d+)\(\)$',text[body_start:end],re.M)
    if not functions or names!=calls or len(set(names))!=len(names):raise ValueError('initialization_call_order_mismatch')
    sizes=[len(EVENT_PATTERN.findall(fn.group(1))) for fn in functions]
    if any(not 1<=n<=CHUNK_EVENTS for n in sizes):raise ValueError('initialization_chunk_too_large')
    if sum(sizes)!=len(EVENT_PATTERN.findall(text)):raise ValueError('events_outside_initialization_functions')
    if any(line.strip() and not re.fullmatch(r'initEvtChunk\d+\(\)',line.strip()) for line in text[body_start:end].splitlines()):
        raise ValueError('unexpected_first_bar_statement')
    if any(fn.end()>start for fn in functions):raise ValueError('initialization_function_not_global_before_call')
    checks={'initialization_functions':len(functions),'max_events_per_function':max(sizes),
            'first_bar_calls':len(calls),'event_initialization_chunk_limit':CHUNK_EVENTS}
    if ENCODING in text:
        region=text[text.index(BEGIN):text.index(END)]
        if region.count(ENCODING)!=1 or region.count(DECODER)!=1:raise ValueError('modified_packed_decoder')
        lengths=[]
        for fn in functions:
            payloads=PAYLOAD.findall(fn.group(1))
            if len(payloads)!=1:raise ValueError('invalid_packed_payload_count')
            payload=literal(payloads[0]);lengths.append(len(payload.encode('utf-8')))
            if lengths[-1]>MAX_PAYLOAD_BYTES:raise ValueError('packed_payload_too_large')
            expected=[decoded_event(e) for e in EVENT_PATTERN.findall(fn.group(1))]
            if unpack_rows(payload)!=expected:raise ValueError('packed_runtime_event_mismatch')
            statements=[line.strip() for line in fn.group(1).splitlines() if line.strip() and not line.lstrip().startswith('//')]
            if len(statements)!=2 or not statements[0].startswith('loadEvtRows("') or statements[1]!='0':raise ValueError('unexpected_packed_chunk_statement')
        executable='\n'.join(line for line in region.splitlines() if not line.lstrip().startswith('//'))
        if sum(executable.count('array.push('+name+',') for name in ('evt_time','evt_dir','evt_str','evt_tips','evt_ticker'))!=5:raise ValueError('unexpected_executable_event_pushes')
        checks.update(event_encoding='packed-v1',packed_event_round_trip=True,max_payload_bytes=max(lengths),
            payload_byte_limit=MAX_PAYLOAD_BYTES,executable_array_push_statements=5,il_tokens_measured=False)
    return checks


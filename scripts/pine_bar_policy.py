"""Coalesce one bar's saved signals before filters, labels or accounting. MPL-2.0."""
import re
MARKER='// SAME BAR POLICY: latest-post-v1'
SELECTOR=MARKER+'''
int latestEventIndex = na
if array.size(evt_time) > 0
    for i = 0 to array.size(evt_time) - 1
        if time_close > array.get(evt_time, i) and time_close[1] <= array.get(evt_time, i) and array.get(evt_dir, i) != 0
            if na(latestEventIndex) or array.get(evt_time, i) >= array.get(evt_time, latestEventIndex)
                latestEventIndex := i
'''

def apply_latest_post_policy(text):
    if re.search(r'(?m)^'+re.escape(MARKER)+r'$',text):return text
    prefix='''if array.size(evt_time) > 0
    for i = 0 to array.size(evt_time) - 1
        if time_close > array.get(evt_time, i) and time_close[1] <= array.get(evt_time, i)
'''
    if text.count(prefix)!=1:raise ValueError('unknown_indicator_event_loop')
    start=text.index(prefix);end=text.index('\ncolor bgCol = na',start)
    body=text[start+len(prefix):end]
    lines=body.splitlines(keepends=True)
    if any(line.strip() and not line.startswith('            ') for line in lines):raise ValueError('unexpected_event_body_indentation')
    dedented=''.join(line[8:] if line.strip() else line for line in lines)
    text=text[:start]+SELECTOR+'\nif not na(latestEventIndex)\n    int i = latestEventIndex\n'+dedented+text[end:]
    # Recompute background/panel age after applying the selected event on this bar.
    age_start=text.index('int barsSinceSignal = ')
    age_end=text.index('bool flipSignalNow = ',age_start)
    age=text[age_start:age_end]
    text=text[:age_start]+text[age_end:]
    end=text.index('color bgCol = na')
    return text[:end]+age+text[end:]


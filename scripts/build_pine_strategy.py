"""Create separate native TradingView strategy; preserve all event tuples. MPL-2.0."""
import hashlib,json
from datetime import datetime
from pathlib import Path
from update_pine_script import EVENT_PATTERN
from pine_initialization import check_initialization,END
ROOT=Path(__file__).resolve().parent.parent

def build():
    source=(ROOT/'candidates/8zz-history-latest.pine').read_text()
    start=source.index('var int[] evt_time')
    end=source.index(END)+len(END)
    events_block=source[start:end]
    header=(ROOT/'scripts/pine_templates/strategy_header.pine').read_text()
    engine=(ROOT/'scripts/pine_templates/strategy_engine.pine').read_text()
    result=header+events_block+'\n\n'+engine+'\n'
    before=EVENT_PATTERN.findall(source);after=EVENT_PATTERN.findall(result)
    if before!=after or not after:raise ValueError('strategy_changed_saved_events')
    cutoff=int(datetime.fromisoformat('2026-10-01T00:00:00+08:00').timestamp()*1000)
    if any(int(e[0])>=cutoff for e in after):raise ValueError('post_september_event')
    checks=check_initialization(result)
    checks.update(events=len(after),events_unchanged=True,source_sha256=hashlib.sha256(source.encode()).hexdigest(),strategy_sha256=hashlib.sha256(result.encode()).hexdigest(),tradingview_compiled=False,order_api='TradingView strategy broker emulator only')
    out=ROOT/'candidates/8zz-strategy-latest.pine';out.write_text(result)
    out.with_suffix('.checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(checks,ensure_ascii=False));return result
if __name__=='__main__':build()

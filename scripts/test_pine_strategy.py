"""Static strategy contracts. These do NOT replace TradingView compilation/execution."""
import hashlib,json,re,unittest
from pathlib import Path
from build_pine_strategy import build,ROOT
from update_pine_script import EVENT_PATTERN
from pine_initialization import check_initialization
class StrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=(ROOT/'candidates/8zz-strategy-latest.pine').read_text()
        cls.source=(ROOT/'candidates/8zz-history-latest.pine').read_text()
    def test_original_judgments_and_initializers_preserved(self):
        self.assertEqual(EVENT_PATTERN.findall(self.text),EVENT_PATTERN.findall(self.source))
        self.assertEqual(len(EVENT_PATTERN.findall(self.text)),294)
        self.assertEqual(check_initialization(self.text)['max_events_per_function'],20)
    def test_native_strategy_is_separate_and_reproducible(self):
        before=hashlib.sha256(self.source.encode()).hexdigest()
        self.assertIn('strategy("8zz',self.text);self.assertNotRegex(self.text,r'(?m)^indicator\(')
        self.assertEqual(build(),self.text)
        self.assertEqual(hashlib.sha256((ROOT/'candidates/8zz-history-latest.pine').read_bytes()).hexdigest(),before)
        self.assertFalse(json.loads((ROOT/'candidates/8zz-strategy-latest.checks.json').read_text())['tradingview_compiled'])
    def test_orders_have_explicit_execution_and_native_accounting(self):
        for declaration in ('pyramiding=0','process_orders_on_close=true','calc_on_every_tick=false','calc_on_order_fills=false','margin_long=100','margin_short=100'):
            self.assertIn(declaration,self.text)
        self.assertIn('strategy.entry("L", strategy.long',self.text)
        self.assertIn('strategy.entry("S", strategy.short',self.text)
        self.assertIn('strategy.closedtrades',self.text)
        self.assertNotIn('pnlSumA',self.text);self.assertNotIn('pnlSumB',self.text)
    def test_day_session_and_bar_confirmation_guards(self):
        self.assertIn('sessionStartHour = futuresProfile ? 8 : 9',self.text)
        self.assertIn('sessionStartMinute = futuresProfile ? 45 : 0',self.text)
        self.assertIn('sessionEndMinute = futuresProfile ? 45 : 30',self.text)
        self.assertIn('if barstate.isconfirmed and dayBar',self.text)
        self.assertIn('inWindow and not dayBar',self.text)
        self.assertIn('dayBarCount - entryDayBarA >= holdBars',self.text)
        self.assertIn('if eventTime >= time_close\n                break',self.text)
        self.assertIn('flipNow := signalDir != beforeDir',self.text)
    def test_cutoff_and_confirmed_htf_no_secret_or_network(self):
        self.assertIn('2026, 9, 30',self.text)
        self.assertIn('strategy.close_all(comment="回測截止日盤收盤"',self.text)
        self.assertIn('eventTime < publicationBefore',self.text)
        self.assertIn('close[1], lookahead=barmerge.lookahead_on',self.text)
        self.assertNotIn('SHIOAJI',self.text);self.assertNotIn('api_key',self.text.lower())
        self.assertNotIn('alertcondition(',self.text)
        self.assertNotIn('alert(',self.text)

    def test_regular_equity_bars_are_not_rebased_to_futures_session(self):
        self.assertIn('input.string("自動依圖表"',self.text)
        self.assertIn('chartIsFutures = syminfo.type == "futures"',self.text)
        self.assertIn('time >= dayStart and time < dayEnd and time_close <= dayEnd',self.text)
        self.assertNotIn('time(timeframe.period, daySession',self.text)
        self.assertNotIn('time_close(timeframe.period, daySession',self.text)
        self.assertIn('futuresProfile != chartIsFutures',self.text)
        self.assertIn('str.format_time(time, "yyyy-MM-dd HH:mm", tz)',self.text)

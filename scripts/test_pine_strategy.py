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
        expected=EVENT_PATTERN.findall(self.source)
        self.assertEqual(EVENT_PATTERN.findall(self.text),expected)
        self.assertGreater(len(expected),0)
        self.assertEqual(check_initialization(self.text)['max_events_per_function'],20)
        self.assertEqual(check_initialization(self.text)['event_encoding'],'packed-v1')
    def test_native_strategy_is_separate_and_reproducible(self):
        before=hashlib.sha256(self.source.encode()).hexdigest()
        self.assertIn('strategy("8zz',self.text);self.assertNotRegex(self.text,r'(?m)^indicator\(')
        self.assertEqual(build(),self.text)
        self.assertEqual(hashlib.sha256((ROOT/'candidates/8zz-history-latest.pine').read_bytes()).hexdigest(),before)
        self.assertFalse(json.loads((ROOT/'candidates/8zz-strategy-latest.checks.json').read_text())['tradingview_compiled'])
    def test_orders_have_explicit_execution_and_native_accounting(self):
        for declaration in ('pyramiding=0','process_orders_on_close=true','calc_on_every_tick=false','calc_on_order_fills=false','margin_long=0','margin_short=0'):
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
        self.assertIn('if eventTime >= decisionClose\n                break',self.text)
        self.assertIn('flipNow := signalDir != beforeDir',self.text)
    def test_cutoff_and_confirmed_htf_no_secret_or_network(self):
        self.assertIn('int finishAt = requestedEnd',self.text)
        self.assertNotIn('hardEnd',self.text)
        self.assertIn('strategy.close_all(comment="回測截止日盤收盤"',self.text)
        self.assertNotIn('publicationBefore',self.text)
        self.assertIn('close[1], lookahead=barmerge.lookahead_on',self.text)
        self.assertNotIn('SHIOAJI',self.text);self.assertNotIn('api_key',self.text.lower())
        self.assertNotIn('alertcondition(',self.text)
        self.assertNotIn('alert(',self.text)

    def test_regular_equity_bars_are_not_rebased_to_futures_session(self):
        self.assertIn('bool futuresProfile = true',self.text)
        self.assertIn('chartIsFutures = syminfo.type == "futures"',self.text)
        self.assertIn('time >= dayStart and time < dayEnd and (time_close <= dayEnd or closingMinuteMarker)',self.text)
        self.assertNotIn('time(timeframe.period, daySession',self.text)
        self.assertNotIn('time_close(timeframe.period, daySession',self.text)
        self.assertIn('if not correctContract',self.text)
        self.assertIn('str.format_time(time, "yyyy-MM-dd HH:mm", tz)',self.text)

    def _eval_session_expressions(self, profile, day, opening, closing, cutoff_day=None):
        # Evaluate the actual generated Pine's pure timestamp/boolean expressions,
        # using concrete RTH boundary fixtures; this is not a Pine broker emulator.
        from datetime import datetime
        from zoneinfo import ZoneInfo
        tz=ZoneInfo('Asia/Taipei')
        stamp=lambda d,t:int(datetime.fromisoformat(d+'T'+t).replace(tzinfo=tz).timestamp()*1000)
        start='08:45' if profile=='TXF' else '09:00';end='13:45' if profile=='TXF' else '13:30'
        scope={'time':stamp(day,opening),'time_close':stamp(day,closing),'dayStart':stamp(day,start),'dayEnd':stamp(day,end),'weekday':datetime.fromisoformat(day).weekday()<5,'startAt':stamp('2025-12-01','00:00'),'finishAt':stamp(cutoff_day or day,end)}
        for name in ('closingMinuteMarker','dayBar','decisionClose','inWindow'):
            expr=re.search(r'^(?:bool|int) '+name+r' = (.+)$',self.text,re.M)[1]
            if '?' in expr:
                condition,body=expr.split('?',1);yes,no=body.split(':',1);expr=f'({yes}) if ({condition}) else ({no})'
            scope[name]=eval(expr,{'__builtins__':{}},scope)
        return scope
    def test_user_reported_rth_1315_to_1346_is_accepted(self):
        x=self._eval_session_expressions('TXF','2025-12-01','13:15','13:46')
        self.assertTrue(x['closingMinuteMarker']);self.assertTrue(x['dayBar']);self.assertTrue(x['inWindow'])
        self.assertEqual(x['decisionClose'],x['dayEnd'])
        self.assertGreater(x['time_close'],x['decisionClose']) # Never pretend native fill is 13:45.
    def test_real_night_and_broader_overrun_still_rejected(self):
        for opening,closing in [('15:00','15:30'),('00:30','01:00'),('13:45','14:15'),('13:15','13:47')]:
            self.assertFalse(self._eval_session_expressions('TXF','2025-12-01',opening,closing)['dayBar'])
        self.assertFalse(self._eval_session_expressions('TXF','2025-12-06','13:15','13:46')['dayBar'])
    def test_stock_regular_and_auction_marker(self):
        self.assertTrue(self._eval_session_expressions('ETF','2025-12-01','09:00','09:30')['dayBar'])
        self.assertTrue(self._eval_session_expressions('ETF','2025-12-01','13:00','13:31')['dayBar'])
        self.assertFalse(self._eval_session_expressions('ETF','2025-12-01','08:45','09:15')['dayBar'])
    def test_cutoff_tail_bar_closes_and_is_not_cancelled_by_raw_close(self):
        x=self._eval_session_expressions('TXF','2026-09-30','13:15','13:46')
        self.assertTrue(x['inWindow']);self.assertEqual(x['decisionClose'],x['finishAt'])
        self.assertIn('if decisionClose == finishAt',self.text)
        self.assertIn('if barstate.isconfirmed and decisionClose > finishAt',self.text)
        self.assertFalse(self._eval_session_expressions('TXF','2026-10-01','09:15','09:45','2026-09-30')['inWindow'])

    def test_risk_orders_are_attached_to_both_entries_and_cancelled(self):
        for side in ('L','S'):
            self.assertIn('strategy.exit("'+side+'-risk", from_entry="'+side+'", stop=tickStop',self.text)
            self.assertIn('strategy.cancel("'+side+'-risk")',self.text)
        self.assertIn('if newRiskEntry',self.text)
        self.assertIn('else if strategy.position_size == 0',self.text)
        self.assertIn('and not exitSubmitted',self.text)
        self.assertIn('and inWindow and not cutoffReached',self.text)
    def test_risk_extremes_start_at_entry_close_not_entry_bar_high_low(self):
        entry=self.text.split('    if newRiskEntry\n')[1].split('    else if strategy.position_size == 0')[0]
        self.assertIn('entryRiskAtr := riskAtr',entry)
        self.assertIn('favorableExtreme := close',entry)
        self.assertIn('trailActive := false',entry)
        self.assertNotIn('high',entry);self.assertNotIn('low',entry)
        self.assertIn('else if riskDirection != 0',self.text)
        self.assertNotIn('trail_offset=',self.text)
    def test_actual_stop_formulas_long_and_short(self):
        # Evaluate generated arithmetic, not a separately implemented stop formula.
        import math
        hard=re.search(r'activeRiskStop := useAtrStop \? (.+) : na',self.text)[1]
        trail=re.search(r'float trailStop = (.+)',self.text)[1]
        trigger=re.search(r'if useTrailingStop and (riskDirection \* .+)',self.text)[1]
        for direction,entry,extreme,expected_hard,expected_trail in [(1,100,130,80,115),(-1,100,70,120,85)]:
            scope=dict(riskDirection=direction,riskEntryPrice=entry,entryRiskAtr=10,atrStopMult=2,trailActivationMult=1,trailDistanceMult=1.5,favorableExtreme=extreme)
            self.assertEqual(eval(hard,{},scope),expected_hard)
            self.assertEqual(eval(trail,{},scope),expected_trail)
            self.assertTrue(eval(trigger,{},scope))
            scope['favorableExtreme']=entry+direction*9
            self.assertFalse(eval(trigger,{},scope))
        self.assertIn('math.max(activeRiskStop, trailStop) : math.min(activeRiskStop, trailStop)',self.text)
        self.assertIn('math.max(activeRiskStop, hardStop) : math.min(activeRiskStop, hardStop)',self.text)
    def test_disabled_stops_and_tick_rounding_contract(self):
        self.assertIn('useAtrStop ? riskEntryPrice',self.text)
        self.assertIn('if useTrailingStop and trailActive',self.text)
        self.assertIn('math.floor(activeRiskStop / syminfo.mintick)',self.text)
        self.assertIn('math.ceil(activeRiskStop / syminfo.mintick)',self.text)
        self.assertIn('not useAtrStop and not useTrailingStop or not na(riskAtr)',self.text)

    def test_default_weekend_uses_saved_previous_open_session(self):
        from datetime import date
        from build_pine_strategy import previous_session
        calendar={'days':{'2026-11-06':{'open':True},'2026-11-07':{'open':False}}}
        self.assertEqual(previous_session(date(2026,11,7),calendar),date(2026,11,6))
        calendar['closure_overrides']={'2026-11-06':True}
        self.assertEqual(previous_session(date(2026,11,7),calendar),date(2026,11,5))
    def test_delivery_manifest_binds_both_complete_pines(self):
        manifest=json.loads((ROOT/'candidates/8zz-pine-delivery.json').read_text())
        self.assertEqual(manifest['events'],len(EVENT_PATTERN.findall(self.source)))
        self.assertTrue(manifest['same_event_tuples'])
        for kind in ('indicator','strategy'):
            self.assertEqual(hashlib.sha256((ROOT/manifest[kind]['path']).read_bytes()).hexdigest(),manifest[kind]['sha256'])
        from datetime import datetime
        october=int(datetime.fromisoformat('2026-10-01T00:00:00+08:00').timestamp()*1000)
        self.assertTrue(any(int(x[0])>=october for x in EVENT_PATTERN.findall(self.text)))
    def test_live_output_publication_includes_both_pines_and_manifest(self):
        from unittest.mock import Mock,patch
        import live_pipeline as live
        import build_audited_dashboard as dashboard
        docs=Mock()
        with patch.object(live.hc,'report') as report,patch.object(live.hc,'publish_text') as publish,patch.object(dashboard,'publish_saved_dashboard'):
            live.refresh_outputs(docs)
        report.assert_called_once_with()
        self.assertEqual([c.args[1] for c in publish.call_args_list],['candidates/8zz-history-latest.pine','candidates/8zz-strategy-latest.pine'])
        saved={c.args[0]:c.args[1] for c in docs.save.call_args_list}
        self.assertEqual(saved['candidates/8zz-pine-delivery.json']['events'],len(EVENT_PATTERN.findall(self.source)))

    def test_taiex_margin_costs_and_one_contract_defaults(self):
        self.assertIn('initial_capital=700000',self.text)
        self.assertIn('commission_type=strategy.commission.cash_per_contract, commission_value=250',self.text)
        self.assertIn('float orderQty = 1.0',self.text)
        self.assertIn('float marginPerContractTwd = 700000.0',self.text)
        self.assertNotIn('etfCapitalPct',self.text);self.assertNotIn('contractQty = input',self.text)
        # Native commissions, not duplicate manual equity/P&L deductions.
        fee=float(re.search(r'commission_value=(\d+)',self.text)[1])
        point=float(re.search(r'syminfo.pointvalue == (\d+)',self.text)[1])
        for direction in (1,-1):
            self.assertEqual(direction*(direction*100)*point-2*fee,19500)
            self.assertEqual(direction*(-direction*100)*point-2*fee,-20500)
        self.assertEqual(2*fee,500) # One round trip, also two contracts transacted on reversal.
    def test_fixed_opening_margin_boundary_and_low_equity_exits(self):
        expression=re.search(r'bool entryMarginReady = (.+)',self.text)[1].replace('strategy.equity','equity').replace('strategy.position_size','position').replace('math.abs','abs')
        for equity,position,expected in ((700000,0,True),(699999,0,False),(700250,0,True),(700000,1,False),(700250,1,True),(700250,-1,True)):
            self.assertEqual(eval(expression,{},dict(equity=equity,position=position,marginPerContractTwd=700000,fillCostPerContractTwd=250,orderQty=1)),expected)
        self.assertIn('not fixedExitNow and entryMarginReady',self.text)
        self.assertIn('strategy.close("S", comment="B：反向平空／保證金不足不開多"',self.text)
        self.assertIn('strategy.close("L", comment="B：反向平多／保證金不足不開空"',self.text)
        self.assertIn('strategy.close_all(comment="回測截止日盤收盤"',self.text)
    def test_only_twd_futures_with_200_point_value_pass_contract_guard(self):
        expression=re.search(r'bool correctContract = (.+)',self.text)[1].replace('syminfo.currency','currency').replace('syminfo.pointvalue','point')
        for is_future,currency,point,expected in ((True,'TWD',200,True),(True,'TWD',50,False),(True,'TWD',10,False),(False,'TWD',200,False),(True,'USD',200,False)):
            self.assertEqual(eval(expression,{},dict(chartIsFutures=is_future,currency=currency,point=point)),expected)

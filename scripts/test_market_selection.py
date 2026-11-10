import unittest
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from import_shioaji_market import aggregate
from futures_performance import simulate_futures,segment
TZ=ZoneInfo('Asia/Taipei')
class MarketTests(unittest.TestCase):
    def test_aggregate_end_stamped_complete_bars(self):
        t=datetime(2026,9,1,9,1,tzinfo=timezone.utc)
        raw={'ts':[int((t+timedelta(minutes=i)).timestamp()*1e9) for i in range(270) if i not in (265,266,267,268)],'Close':[100+i/100 for i in range(270) if i not in (265,266,267,268)]}
        bars,counts=aggregate(raw,'0050');self.assertEqual(len(bars['30m']),9);self.assertEqual(len(bars['1d']),1)
        close=datetime.fromtimestamp(bars['30m'][0]['time']/1000,TZ);self.assertEqual((close.hour,close.minute),(9,30))
        raw['ts'].pop();raw['Close'].pop();bars,counts=aggregate(raw,'0050');self.assertEqual(len(bars['30m']),8);self.assertEqual(len(bars['1d']),0)
    def test_settlement_week_and_cross_month_not_same_contract(self):
        ts=lambda d:int(datetime.fromisoformat(d).replace(tzinfo=TZ).timestamp()*1000)
        self.assertIsNone(segment(ts('2026-09-16T12:00:00')))
        self.assertNotEqual(segment(ts('2026-09-01T12:00:00')),segment(ts('2026-09-25T12:00:00')))
    def test_roll_gap_does_not_create_futures_pnl(self):
        ts=lambda d:int(datetime.fromisoformat(d).replace(tzinfo=TZ).timestamp()*1000)
        a=ts('2026-09-10T09:00:00');b=ts('2026-09-22T09:00:00')
        events=[{'id':1,'unix_ms':a-1,'direction':1,'is_flip':True},{'id':2,'unix_ms':b-1,'direction':-1,'is_flip':True}]
        bars=[{'time':a,'price':20000},{'time':b,'price':30000},{'time':b+1000,'price':29999}]
        r=simulate_futures(events,bars,'B');self.assertFalse(r['rows']['1']['trade']);self.assertTrue(r['rows']['1']['missing']);self.assertEqual(r['stats']['settled'],0)
    def test_daytime_filter_removes_night_and_rebuilds_gaps(self):
        from futures_performance import daytime_only
        ts=lambda s:int(datetime.fromisoformat(s).replace(tzinfo=TZ).timestamp()*1000)
        raw=[{'time':ts('2026-09-01T'+t),'price':100,'gap_before':True} for t in ('03:00:00','09:15:00','09:45:00','13:45:00','15:30:00','23:30:00')]
        result=daytime_only({'30m':raw,'1d':raw})
        self.assertEqual(len(result['30m']),3);self.assertEqual(len(result['1d']),1)
        self.assertNotIn('gap_before',result['30m'][0]);self.assertNotIn('gap_before',result['30m'][1]);self.assertTrue(result['30m'][2]['gap_before'])
    def test_published_futures_all_prices_and_trades_are_daytime(self):
        import json
        from build_audited_dashboard import ROOT
        data=json.loads((ROOT/'docs/dashboard-data.json').read_text())['instruments']['TXF']
        def check(ts):
            t=datetime.fromtimestamp(ts/1000,TZ);self.assertTrue(525<t.hour*60+t.minute<=825)
        for bars in data['market']['series'].values():
            for b in bars:check(b['time'])
        for modes in (data['modes'],data['available_modes']):
            for m in modes.values():
                for p in m['curve']:check(p['time'])
                for trade in m['trades']:
                    for key in ('entry','exit','mark'):
                        if trade.get(key):check(trade[key]['time'])

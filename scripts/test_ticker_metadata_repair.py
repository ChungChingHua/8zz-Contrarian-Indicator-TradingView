import copy,unittest
import original_author as p
from test_original_history import answer

class TickerMetadataTests(unittest.TestCase):
    def test_unsupported_ticker_never_blocks_a_coherent_emotion_or_invents_code(self):
        for ticker in ('創意','國巨','6282.TWO, 6269.TWO','APPL?','可轉換為1795.TW?'):
            raw=answer(direction=-1,strength=2,ticker=ticker);before=copy.deepcopy(raw)
            a=p.parse(raw,0)
            self.assertEqual((a['direction'],a['strength'],a['disposition']),(-1,2,'signal'))
            self.assertEqual(a['ticker'],'');self.assertEqual(a['original_ai_ticker'],ticker)
            self.assertTrue(a['ticker_resolution']['manual_verification_required']);self.assertEqual(raw,before)
    def test_existing_valid_and_empty_tickers_remain_unchanged(self):
        for ticker in ('','2330.TW','NVDA','^TWII'):
            a=p.parse(answer(ticker=ticker),0);self.assertEqual(a['ticker'],ticker);self.assertNotIn('ticker_resolution',a)
    def test_other_required_validation_is_not_relaxed(self):
        for raw,count,reason in ((answer(direction=1,disposition='pending_confirmation',ticker='創意'),0,'contradictory_output_fields'),(answer(ticker='創意'),1,'image_coverage_mismatch')):
            with self.assertRaisesRegex(ValueError,reason):p.parse(raw,count)
        raw=answer(ticker='創意');raw['text']['format']['strict']=False
        with self.assertRaisesRegex(ValueError,'strict_format_not_confirmed'):p.parse(raw,0)

class RepairAvailabilityTests(unittest.TestCase):
    def test_repaired_failures_are_not_backdated_to_old_http_completion(self):
        import history_completion as hc
        from build_audited_dashboard import events
        from datetime import datetime
        records,_=hc.ledger_records();available={e['unix_ms']:e for e in events()}
        repaired=[r for r in records.values() if r.get('offline_reprocessed_at')]
        self.assertEqual(len(repaired),6)
        for r in repaired:
            self.assertEqual(available[r['unix_ms']]['available_ms'],int(datetime.fromisoformat(r['offline_reprocessed_at']).timestamp()*1000))

if __name__=='__main__':unittest.main()

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import reprocess_quality as r
import review_rules as rules
import plan_quality_batch as batch
import social_pipeline as s
from test_openai import answer
from test_social_pipeline import post


class ReviewRuleTests(unittest.TestCase):
    def setUp(self):
        self.raw=json.loads(r.RAW.read_text())
        self.metadata=json.loads((r.ROOT/'data/quality_samples.json').read_text())
    def test_reprocess_immutable_and_separate_counts(self):
        before=copy.deepcopy(self.raw)
        result=r.reprocess(self.raw,self.metadata)
        self.assertEqual(self.raw,before)
        self.assertEqual(result['counts'],{'acceptable':6,'pending_confirmation':4,'technical_failure':0})
        self.assertEqual(result['model_response_only_counts'],{'acceptable':5,'pending_confirmation':4,'technical_failure':0})
        self.assertTrue(all(not row['formal_signal_written'] and not row['auto_retry'] for row in result['records']))
    def test_resignation_not_panic_and_full_text_matters(self):
        self.assertFalse(rules.panic_evidence('個股還沒停損，隨便他了')['explicit'])
        self.assertFalse(rules.panic_evidence('市場說不用停損，因為停不掉')['explicit'])
        self.assertTrue(rules.panic_evidence(self.raw['samples'][6]['text'])['strong'])
        out=r.reprocess(self.raw,self.metadata)['records']
        for number in (3,8):
            row=out[number-1]
            self.assertEqual(row['status'],'pending_confirmation');self.assertEqual(row['emotion'],'undetermined')
            self.assertIsNone(row['direction']);self.assertNotEqual(row['emotion'],'neutral')
        self.assertEqual(out[6]['direction'],1);self.assertEqual(out[6]['strength'],3)
    def test_asset_roles_code_conflict_and_bonus(self):
        rows=r.reprocess(self.raw,self.metadata)['records']
        self.assertEqual(rows[0]['asset_groups']['personal_assets'][0]['name'],'BTC')
        self.assertEqual(rows[0]['asset_groups']['image_quotes'][0]['name'],'TSM')
        self.assertFalse(rows[5]['asset_groups']['personal_assets'])
        target=next(t for t in rows[5]['asset_groups']['image_quotes'] if t['name']=='鴻海')
        self.assertEqual(target['ticker'],'');self.assertFalse(target['human_image_verified'])
        self.assertEqual(self.raw['samples'][5]['model_answer']['targets'][1]['ticker'],'HNHFP')
        self.assertFalse(rows[9]['asset_groups']['personal_assets'])
        self.assertEqual(rows[9]['asset_groups']['mentioned_targets'][0]['name'],'群創')
        self.assertEqual(rows[9]['direction'],0)
    def test_news_or_quote_never_proves_holding(self):
        target={'name':'台積電'};quote='新聞報導台積電上漲'
        bucket,_=rules.asset_bucket(quote,target,[{'source':'author_text','quote':quote}])
        self.assertEqual(bucket,'mentioned_targets')
    def test_video_text_only_without_fabricated_model_answer(self):
        row=r.reprocess(self.raw,self.metadata)['records'][4]
        self.assertEqual(row['status'],'acceptable');self.assertTrue(row['video_unanalysed'])
        self.assertFalse(row['model_answer_available']);self.assertEqual(row['decision_origin'],'offline_text_rule_no_model_response')
        self.assertEqual(row['relevance'],'unrelated');self.assertEqual(row['direction'],0)
        self.assertEqual(row['asset_groups']['personal_assets'],[])
    def test_real_classify_video_text_only_no_thumbnail_request(self):
        p=post(text=self.raw['samples'][4]['text']);p['attachments']=[{'__typename':'Video','thumbnail':'https://not-used.invalid/poster.jpg'}]
        with patch.object(s,'credentials',return_value=({'base':'https://api.openai.com/v1','provider':'openai','effort':None},{'Authorization':'Bearer offline'})),patch.object(s,'download_image',side_effect=AssertionError('must not fetch video poster')) as download,patch.object(s,'request_json',return_value=answer(investment_related=False,clear=False,direction=0,target='',ticker='',reason='確定無關投資，醫美業配')) as api:
            result=s.classify(p)
        self.assertIn('video_unanalysed',result['analysis_scope']);self.assertFalse(result['images_reviewed'])
        payload=api.call_args.args[2];content=payload['input'][0]['content']
        self.assertEqual([c['type'] for c in content],['input_text'])
        self.assertEqual(json.loads(content[0]['text'])['unanalysed_media'][0]['status'],'影片未分析')
        download.assert_not_called()
    def test_video_and_real_image_are_separate_sources(self):
        p=post(text='如圖');p['attachments']=[{'type':'video','thumbnail':'never-use'},{'type':'image'}]
        scope=rules.media_plan(p)
        self.assertTrue(scope['text_sufficient_for_preflight'])
        self.assertEqual(scope['image_attachment_indices'],[1]);self.assertEqual(len(scope['image_attachments']),1)
        self.assertEqual(scope['unanalysed_media'][0]['attachment_index'],0)

    def test_dependent_video_text_waits_without_api(self):
        p=post(text='請看影片，答案都在影片');p['attachments']=[{'type':'video'}]
        with patch.object(s,'credentials',return_value=({},{})),patch.object(s,'request_json') as api:
            a=s.classify(p)
        self.assertEqual(a['status'],'review');api.assert_not_called()
    def test_report_does_not_claim_video_is_image_or_preflight_is_generation(self):
        import os
        for analysis,completed in [({'status':'no_signal','generation_attempted':True,'images_supplied':0},1),({'status':'review','generation_attempted':False},0)]:
            with self.subTest(completed=completed),tempfile.TemporaryDirectory() as d,patch.object(s,'ROOT',Path(d)),patch.object(s,'generate',return_value=0),patch.object(s,'classify',return_value=analysis),patch.object(s,'assert_online_enabled'),patch.dict(os.environ,{'AI_PROVIDER':'openai'},clear=True),patch('sys.argv',['pipeline','--classify-limit','1']):
                p=post();p['attachments']=[{'type':'video'}];p['analysis']={'status':'pending'}
                s.write(Path(d)/'data/social_posts.json',{p['key']:p});s.main()
                report=s.read(Path(d)/'data/social_report.json',{})
                self.assertEqual(report['image_successes'],0);self.assertEqual(report['completed'],completed)

    def test_old_gate_no_longer_treats_stop_loss_action_as_fear(self):
        from semantic_gate import assess
        p=post(text='台積電股票還沒停損，隨便他了')
        a=json.loads(answer(target='台積電',ticker='',reason='因為尚未停損所以恐慌')['output'][0]['content'][0]['text'])
        a['status']='done'
        out=assess(p,a)
        self.assertEqual(out['status'],'review');self.assertEqual(out['direction'],0)
        self.assertEqual(out['model_candidate']['direction'],1)
    def test_missing_response_is_not_automatically_technical_failure(self):
        missing=copy.deepcopy(self.raw['samples'][4]);missing['text']='答案都在影片'
        out=r.process(missing,['Video'])
        self.assertEqual(out['status'],'pending_confirmation')
        self.assertFalse(out['model_answer_available'])


class BatchPreparationTests(unittest.TestCase):
    def test_skip_existing_reviews_and_bound_requests(self):
        reviewed=r.reprocess(json.loads(r.RAW.read_text()),json.loads((r.ROOT/'data/quality_samples.json').read_text()))
        self.assertEqual(batch.build_plan(reviewed['records'])['selected'],[])
        records=[{'key':str(i),'status':'unprocessed','content_hash':'a'*64} for i in range(12)]
        self.assertEqual(len(batch.build_plan(records)['selected']),5)
        self.assertEqual(len(batch.build_plan(records,limit=10,monthly_remaining=3)['selected']),3)
        with self.assertRaises(ValueError):batch.build_plan(records,limit=11)
    def test_reservation_blocks_duplicate_or_crash_rerun(self):
        plan=batch.build_plan([{'key':'one','status':'unprocessed','content_hash':'a'*64}])
        with self.assertRaises(ValueError):batch.reserve({},'batch1',plan)
        reserved=batch.reserve({},'batch1',plan,quota_confirmed=True)
        with self.assertRaises(ValueError):batch.reserve(reserved,'batch1',plan,quota_confirmed=True)
        with self.assertRaises(ValueError):batch.reserve(reserved,'batch2',plan,quota_confirmed=True)
        self.assertFalse(reserved['batches']['batch1']['retry_on_crash'])
    def test_monthly_budget_carries_across_batches(self):
        plan=batch.build_plan([{'key':'one','status':'unprocessed','content_hash':'a'*64}],monthly_remaining=1)
        ledger=batch.reserve({},'first',plan,quota_confirmed=True)
        other=batch.build_plan([{'key':'two','status':'unprocessed','content_hash':'b'*64}],monthly_remaining=1)
        with self.assertRaisesRegex(ValueError,'attempt_budget_exhausted'):batch.reserve(ledger,'second',other,quota_confirmed=True)
        self.assertEqual(ledger['monthly_attempts_remaining'],0)

    def test_stop_on_quota_invalid_response_or_service_errors(self):
        for args in ({'http_status':429},{'http_status':402},{'http_status':500},{'http_status':200,'error_code':'insufficient_quota'},
                     {'http_status':200,'response_valid':False},{'http_status':200,'remaining_points':0},{'http_status':200,'remaining_requests':0}):
            self.assertIsNotNone(batch.stop_reason(**args))
        self.assertIsNone(batch.stop_reason(200,remaining_points=None))

if __name__=='__main__':unittest.main()

"""Regression cases from observed smoke failures and adversarial contradictions."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import semantic_gate as g
import social_pipeline as s
from test_social_pipeline import post
from test_openai import answer


def candidate(**changes):
    a=json.loads(answer(**changes)['output'][0]['content'][0]['text']);a['status']='done'
    return a


class SemanticTests(unittest.TestCase):
    def test_grounded_panic_and_euphoria(self):
        for text,direction,reason,target in [('台積電股票停損，好恐慌',1,'投資恐慌','台積電'),('爽啦！喬喬賺錢了！加碼再賺！台股簡單啦',-1,'台股亢奮，爽啦賺錢','台股')]:
            a=g.assess(post(text=text),candidate(direction=direction,reason=reason,target=target,ticker=''))
            self.assertEqual(a['status'],'done');self.assertEqual(a['direction'],direction)
            self.assertEqual(a['semantic_check']['evidence']['target']['source'],'author_text')
    def test_traceable_target_and_ticker_independently(self):
        p=post(text='台積電股票好恐慌')
        a=g.assess(p,candidate())
        self.assertEqual(a['target'],'台積電');self.assertEqual(a['ticker'],'')
        self.assertEqual(a['status'],'review');self.assertFalse(a['auto_retry_eligible'])
        self.assertEqual(g.assess(p,a),a)
    def test_ticker_substrings_not_evidence(self):
        p=post(text='00500 股票好恐慌')
        a=g.assess(p,candidate(target='0050',ticker='0050'))
        self.assertEqual((a['target'],a['ticker']),('',''))
    def test_mixed_source_and_incidental_targets_not_signals(self):
        r=g.assess(post(text='台股股票恐慌！但是穩了，台股簡單啦'),candidate(target='台股',ticker=''))
        self.assertIn('mixed_source_sentiment',r['semantic_check']['issues']);self.assertEqual(r['direction'],0)
        r=g.assess(post(text='買欣興，投資自己做醫美'),candidate(investment_related=False,direction=0,target='欣興',ticker='',reason='確定無關投資，醫美業配'))
        self.assertEqual(r['decision_type'],'unrelated');self.assertEqual(r['target'],'')

    def test_smoke_facebook_does_not_invent_target(self):
        p=post(text='市場跟我說 孩子，你不用停損，因為你停不掉')
        a=g.assess(p,candidate(clear=False,direction=0,target='亞翔',ticker='6139',reason='單篇資訊不足、情緒模糊'))
        self.assertEqual((a['target'],a['ticker'],a['direction']),('','',0))
        self.assertEqual(a['decision_type'],'semantic_conflict')
        self.assertEqual(a['model_candidate']['target'],'亞翔')
    def test_smoke_watch_contradiction_not_signal(self):
        p=post(text='沒事，就是給大家看看我的新GShock，下週穩了')
        a=g.assess(p,candidate(clear=False,direction=0,target='',ticker='',reason='只有生活物品，沒有投資證據'))
        self.assertEqual(a['decision_type'],'semantic_conflict');self.assertEqual(a['status'],'review')
        self.assertIn('relevance_reason_conflict',a['semantic_check']['issues'])
    def test_unsupported_quote_not_third_party_article(self):
        p=post(text='台股股票好恐慌')
        a=g.assess(p,candidate(target='台股',ticker='',quoted_summary=p['text']))
        self.assertIn('quotation_without_source_boundary',a['semantic_check']['issues'])
    def test_direction_reason_and_relevance_conflicts(self):
        cases=[candidate(direction=-1,reason='投資恐慌'),candidate(investment_related=False),candidate(clear=False),candidate(reason='沒有恐慌或亢奮，無法確定立場'),candidate(reason='投資情緒中性'),candidate(reason='投資恐慌但也亢奮')]
        for a in cases:
            with self.subTest(a=a):
                result=g.assess(post(text='台積電股票恐慌 2330.TW'),a)
                self.assertEqual(result['status'],'review');self.assertEqual(result['direction'],0)
                self.assertFalse(result['auto_retry_eligible'])
    def test_no_signal_neutral_unrelated_vs_insufficient(self):
        cases=[('今天逛街看手錶',candidate(investment_related=False,direction=0,clear=False,target='',ticker='',reason='確定無關投資，是生活貼文'),'unrelated','no_signal'),
               ('持倉紀錄：0050 ETF 10張',candidate(direction=0,clear=True,target='0050',ticker='0050',reason='中性持倉紀錄，沒有明顯情緒'),'neutral','no_signal'),
               ('恐慌的睡不著',candidate(clear=False,direction=0,target='',ticker='',investment_related=False,reason='資訊不足，無法確定恐慌原因'),'insufficient_information','review')]
        for text,a,kind,status in cases:
            with self.subTest(kind=kind):
                r=g.assess(post(text=text),a)
                self.assertEqual(r['decision_type'],kind);self.assertEqual(r['status'],status)
                self.assertFalse(g.retry_candidate(r));self.assertEqual(r['direction'],0)
    def test_unverified_image_ocr_not_target_evidence(self):
        p=post(text='我的股票虧爛了');p['attachments']=[{'ocrText':'亞翔 6139'}]
        a=candidate(target='亞翔',ticker='6139',reason='投資恐慌，虧爛',images_reviewed=True)
        a['image_evidence']=[{'sha256':'a'*64}]
        r=g.assess(p,a)
        self.assertEqual((r['target'],r['ticker']),('',''));self.assertEqual(r['status'],'review')
        verified={p['key']:[{'reviewed':True,'reviewer':'human-reviewer','verified_at':'2026-11-07','sha256':'a'*64,'observed_text':'亞翔 6139'}]}
        r=g.assess(p,a,verified)
        self.assertEqual(r['status'],'done')
        verified[p['key']][0]['sha256']='b'*64
        self.assertEqual(g.assess(p,a,verified)['target'],'')
    def test_image_holding_without_author_emotion_no_signal(self):
        p=post(text='今天出門喝咖啡');p['attachments']=[{}]
        a=candidate(target='亞翔',ticker='6139',images_reviewed=True);a['image_evidence']=[{'sha256':'a'*64}]
        verified={p['key']:[{'reviewed':True,'reviewer':'human','verified_at':'2026-11-07','sha256':'a'*64,'observed_text':'亞翔 6139'}]}
        self.assertEqual(g.assess(p,a,verified)['status'],'review')
    def test_technical_failure_remains_distinct(self):
        r=g.assess(post(),{'status':'retry','http_status':429,'direction':-1})
        self.assertEqual(r['decision_type'],'technical_failure');self.assertTrue(g.retry_candidate(r));self.assertEqual(r['http_status'],429)
        self.assertEqual(g.assess(post(),{'status':'pending'})['decision_type'],'unprocessed')
    def test_classify_keeps_original_contradictory_candidate(self):
        with patch.object(s,'credentials',return_value=({'base':'https://api.openai.com/v1','provider':'openai','effort':None},{'Authorization':'Bearer offline'})),patch.object(s,'request_json',return_value=answer(investment_related=False,direction=1)):
            r=s.classify(post())
        self.assertEqual(r['model_candidate']['direction'],1);self.assertEqual(r['direction'],0)
        self.assertIn('unrelated_with_direction',r['semantic_check']['issues'])
    def test_no_signal_and_review_not_automatically_reclassified(self):
        with tempfile.TemporaryDirectory() as d,patch.object(s,'ROOT',Path(d)),patch.object(s,'generate',return_value=0),patch.object(s,'classify',side_effect=AssertionError('no API')) as classify,patch.object(s,'assert_online_enabled'),patch.dict(os.environ,{'AI_PROVIDER':'openai'},clear=True),patch('sys.argv',['pipeline','--classify-limit','2']):
            one=post(id='1');two=post(id='2')
            one['analysis']={'status':'no_signal'};two['analysis']={'status':'review'}
            s.write(Path(d)/'data/social_posts.json',{one['key']:one,two['key']:two});s.main();classify.assert_not_called()
    def test_static_input_issue_needs_review_not_another_paid_attempt(self):
        a=g.failure_state(ValueError('video_or_unknown_media_requires_review'))
        self.assertEqual(a['decision_type'],'insufficient_information')
        self.assertFalse(g.retry_candidate(a));self.assertFalse(a['auto_retry_eligible'])
        a=g.failure_state(s.APIError(500))
        self.assertEqual(a['decision_type'],'technical_failure');self.assertTrue(g.retry_candidate(a))

    def test_generate_rechecks_old_cached_signal(self):
        p=post(text='新GShock下週穩了');p['analysis']=candidate(target='台股',ticker='',direction=-1,reason='投資亢奮')
        with tempfile.TemporaryDirectory() as d,patch.object(s,'ROOT',Path(d)):
            root=Path(d);(root/'data').mkdir();original=(s.Path(__file__).resolve().parents[1]/'data/historical-indicator.pine').read_text()
            (root/'data/historical-indicator.pine').write_text(original)
            self.assertEqual(s.generate({p['key']:p}),0)
            self.assertNotIn('新GShock', (root/'8zz-indicator.pine').read_text())
            self.assertEqual(p['analysis']['direction'],-1)  # Cached raw source not overwritten.

if __name__=='__main__':unittest.main()

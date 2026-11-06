import json
import os
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path
import social_pipeline as s
import run_social_update as runner
from test_social_pipeline import post


def answer(**changes):
    a=dict(investment_related=True,clear=True,direction=1,strength=2,target='台積電',ticker='2330.TW',reason='投資恐慌',author_commentary='恐慌',quoted_summary='',images_reviewed=False)
    a.update(changes)
    return {'status':'completed','id':'resp_test','usage':{'input_tokens':100,'output_tokens':50},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(a)}]}]}


class OpenAITests(unittest.TestCase):
    def test_real_responses_contract_and_usage(self):
        p=post();p['attachments']=[{'type':'image'}]
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test'}),patch.object(s,'image_parts',return_value=[{'type':'input_image','image_url':'data:image/png;base64,AA=='}]),patch.object(s,'request_json',return_value=answer(images_reviewed=True)) as request:
            a=s.classify(p)
        url,headers,body=request.call_args.args
        self.assertEqual(url,'https://api.openai.com/v1/responses')
        self.assertEqual(headers['Authorization'],'Bearer test')
        self.assertFalse(body['store']);self.assertTrue(body['text']['format']['strict'])
        self.assertFalse(body['text']['format']['schema']['additionalProperties'])
        self.assertEqual(body['input'][0]['content'][1]['type'],'input_image')
        self.assertEqual(a['ticker'],'2330.TW');self.assertEqual(a['provider'],'openai')
        self.assertEqual(a['usage']['input_tokens'],100)

    def test_refusal_incomplete_and_malformed_never_complete(self):
        responses=[{'status':'incomplete'}, {'status':'completed','output':[{'type':'message','content':[{'type':'refusal','refusal':'no'}]}]}, {'status':'completed','output':[]},answer(ticker='bad ticker'),answer(direction=True),answer(strength=0)]
        for response in responses:
            with self.subTest(response=response),patch.dict(os.environ,{'OPENAI_API_KEY':'test'}),patch.object(s,'request_json',return_value=response):
                with self.assertRaises((ValueError,KeyError)):s.classify(post())

    def test_unknown_target_is_review_without_signal(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test'}),patch.object(s,'request_json',return_value=answer(target='')):
            a=s.classify(post())
        self.assertEqual(a['direction'],0);self.assertEqual(a['status'],'review')

    def test_missing_key_blocks_images_and_all_paid_work(self):
        with patch.dict(os.environ,{},clear=True),patch.object(s,'image_parts') as images,patch.object(s,'request_json') as api,patch.object(runner.subprocess,'run') as command:
            with self.assertRaises(RuntimeError):s.classify(post())
            with self.assertRaises(SystemExit):runner.main()
            images.assert_not_called();api.assert_not_called();command.assert_not_called()

    def test_failure_is_durably_retry(self):
        with TemporaryDirectory() as d,patch.object(s,'ROOT',Path(d)),patch.object(s,'generate',return_value=0),patch.object(s,'classify',side_effect=s.APIError(429)),patch('sys.argv',['pipeline','--classify-limit','1']):
            p=post();p['analysis']={'status':'pending'}
            s.write(Path(d)/'data/social_posts.json',{p['key']:p});s.main()
            a=s.read(Path(d)/'data/social_posts.json',{})[p['key']]['analysis']
            self.assertEqual(a['status'],'retry');self.assertEqual(a['attempts'],1)

if __name__=='__main__':unittest.main()

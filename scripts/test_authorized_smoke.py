import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import authorized_chatanywhere_smoke as a
from test_social_pipeline import post
from test_openai import answer


class OneShotTests(unittest.TestCase):
    def samples(self):
        out=[]
        for key,source in zip(a.KEYS,('facebook','threads')):
            p=post(source);p['key']=key;p['attachments']=[{'type':'image'}];out.append(p)
        return out
    def image(self,p):
        p['_image_evidence']=[{'bytes':10,'sha256':'offline','mime':'image/jpeg'}]
        return [{'type':'input_image','image_url':'data:image/jpeg;base64,/9j/2Q=='}]
    def response(self):
        r=answer(images_reviewed=True);r.update(model='gpt-5-mini',reasoning={'effort':'low'},text={'format':{'type':'json_schema','strict':True}})
        return r
    def test_exactly_two_requests_and_no_global_unpause(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere'},clear=True):
            replies=iter([(200,{}, {'data':[{'id':'gpt-5-mini'}]}),(200,{},self.response()),(200,{},self.response())])
            audit=a.Audit('sk-offline-fixture-00000',Path(d)/'report.json',lambda *args:next(replies))
            with patch.object(a.s,'image_parts',side_effect=self.image):a.run(audit,self.samples(),{'Authorization':'Bearer '+audit.key,'Content-Type':'application/json'})
            self.assertTrue(audit.report['passed']);self.assertEqual(audit.report['http_counts']['generation'],2)
            self.assertEqual(audit.report['http_counts']['model_queries'],1)
            with self.assertRaises(RuntimeError):a.s.assert_online_enabled()
            with self.assertRaises(ValueError):audit.call('https://api.chatanywhere.org/v1/responses',{},retries=2)
    def test_model_unavailable_means_no_generation(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere'},clear=True):
            audit=a.Audit('offline-fixture-key',Path(d)/'report.json',lambda *args:(200,{}, {'data':[{'id':'gpt-5-nano'}]}))
            with self.assertRaisesRegex(ValueError,'requested_model_not_listed'):a.run(audit,self.samples(),{'Authorization':'Bearer '+audit.key,'Content-Type':'application/json'})
            self.assertEqual(audit.report['http_counts']['generation'],0)
    def test_first_rejection_stops_without_retry(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere'},clear=True):
            replies=iter([(200,{}, {'data':[{'id':'gpt-5-mini'}]}),(429,{}, {'error':{'code':'insufficient_quota'}})])
            audit=a.Audit('offline-fixture-key',Path(d)/'report.json',lambda *args:next(replies))
            with patch.object(a.s,'image_parts',side_effect=self.image),self.assertRaises(a.s.APIError):a.run(audit,self.samples(),{'Authorization':'Bearer '+audit.key,'Content-Type':'application/json'})
            self.assertEqual(audit.report['http_counts']['generation'],1)
            self.assertEqual(audit.report['samples'][0]['status'],'retry')
    def test_provider_claims_are_not_schema_success(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere'},clear=True):
            r=self.response();r.pop('reasoning')
            replies=iter([(200,{}, {'data':[{'id':'gpt-5-mini'}]}),(200,{},r)])
            audit=a.Audit('offline-fixture-key',Path(d)/'report.json',lambda *args:next(replies))
            with patch.object(a.s,'image_parts',side_effect=self.image),self.assertRaisesRegex(ValueError,'reasoning_effort_unconfirmed'):a.run(audit,self.samples(),{'Authorization':'Bearer '+audit.key,'Content-Type':'application/json'})
            self.assertEqual(audit.report['http_counts']['generation'],1)
            self.assertFalse(audit.report['passed'])
    def test_official_host_and_extra_posts_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            audit=a.Audit('fixture-key',Path(d)/'report.json',lambda *args:self.fail('network forbidden'))
            with self.assertRaises(ValueError):audit.call('https://api.openai.com/v1/models')
            self.assertIsNone(a.candidate({'output':[]}))

if __name__=='__main__':unittest.main()

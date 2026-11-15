import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import authorized_threads_minimal as m
import test_authorized_smoke as fixtures

class MinimalTests(unittest.TestCase):
    def test_cached_fb_without_network(self):
        with patch.object(m.old.urllib.request,'urlopen',side_effect=AssertionError('network')):
            r=m.reused_facebook()
        self.assertEqual(r['service_candidate']['direction'],0)
        self.assertTrue(r['offline_fields_revalidated'])
        self.assertEqual(r['new_requests'],0)
    def test_one_generation_only(self):
        fixture=fixtures.OneShotTests();r=fixture.response();r['reasoning']['effort']='minimal'
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere','CHATANYWHERE_REASONING_EFFORT':'minimal'},clear=True):
            calls=[]
            def transport(*args):calls.append(args);return 200,{},r
            audit=m.ThreadsAudit('fixture-key',Path(d)/'audit.json',transport,expected_effort='minimal',max_generations=1)
            with patch.object(m.s,'image_parts',side_effect=fixture.image):m.run(audit,fixture.samples()[1],{'Authorization':'Bearer fixture-key','Content-Type':'application/json'})
            self.assertTrue(audit.report['passed']);self.assertEqual(len(calls),1)
            self.assertEqual(audit.report['http_counts']['model_queries'],0)
            with self.assertRaises(ValueError):audit.call('https://api.chatanywhere.tech/v1/responses',calls[0][1],calls[0][2])
            with self.assertRaises(ValueError):audit.call('https://api.chatanywhere.tech/v1/models')
            with self.assertRaises(RuntimeError):m.s.assert_online_enabled()
    def test_failure_not_completed_no_retry(self):
        fixture=fixtures.OneShotTests()
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere','CHATANYWHERE_REASONING_EFFORT':'minimal'},clear=True):
            audit=m.ThreadsAudit('fixture-key',Path(d)/'audit.json',lambda *args:(429,{}, {'error':{'code':'insufficient_quota'}}),expected_effort='minimal',max_generations=1)
            with patch.object(m.s,'image_parts',side_effect=fixture.image),self.assertRaises(m.s.APIError):m.run(audit,fixture.samples()[1],{'Authorization':'Bearer fixture-key','Content-Type':'application/json'})
            self.assertEqual(audit.current['status'],'retry');self.assertEqual(audit.report['http_counts']['generation'],1)

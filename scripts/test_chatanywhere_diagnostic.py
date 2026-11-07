import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
import diagnose_chatanywhere_403 as d


class DiagnosticTests(unittest.TestCase):
    def test_redacts_keys_and_urls_and_does_not_claim_auth_validity(self):
        key='sk-offline-secret-123456789'
        h=Message();h['Content-Type']='application/json';h['Server']='nginx'
        body={'error':{'type':'chatanywhere_error','code':'403 FORBIDDEN','message':'Key '+key+' forbidden; see https://example.test/?token=private'}}
        _,meta=d.evidence(403,h,json.dumps(body).encode(),key)
        self.assertEqual(meta['error_code'],'403 FORBIDDEN')
        self.assertNotIn(key,json.dumps(meta));self.assertNotIn('token=private',json.dumps(meta))
        self.assertFalse(meta['explicit_network_policy_block'])
    def test_network_policy_block_is_explicit(self):
        h=Message();h['Content-Type']='text/plain';h['x-mitmproxy-blocked-reason']='ROBOTS_DENIED'
        _,meta=d.evidence(403,h,b'Forbidden by network policy','offline-key')
        self.assertTrue(meta['explicit_network_policy_block'])
        self.assertEqual(meta['headers']['content_type'],'text/plain')
    def test_three_diagnostics_hard_cap(self):
        with tempfile.TemporaryDirectory() as td:
            audit=d.DiagnosticAudit('offline-secret-key',Path(td)/'audit.json')
            with patch.object(audit,'exchange',return_value=({}, {'http_status':403,'explicit_network_policy_block':False})) as http:
                for host,auth in ((d.HOSTS[0],True),(d.HOSTS[0],False),(d.HOSTS[1],True)):self.assertFalse(audit.diagnostic(host,auth))
                with self.assertRaisesRegex(ValueError,'budget'):audit.diagnostic(d.HOSTS[0],True)
                self.assertEqual(http.call_count,3)
                self.assertEqual(audit.report['http_counts']['generation'],0)
    def test_cached_models_do_not_add_http(self):
        with tempfile.TemporaryDirectory() as td:
            audit=d.DiagnosticAudit('offline-secret-key',Path(td)/'audit.json');audit.cached_models={'data':[{'id':'gpt-5-mini'}]}
            with patch.object(audit,'exchange',side_effect=AssertionError('no network')):
                self.assertEqual(audit.call(d.HOSTS[0]+'/v1/models')['data'][0]['id'],'gpt-5-mini')
            self.assertEqual(audit.report['diagnostic_requests'],0)
    def test_unknown_endpoint_refused_before_network(self):
        with tempfile.TemporaryDirectory() as td:
            audit=d.DiagnosticAudit('offline-secret-key',Path(td)/'audit.json')
            with self.assertRaisesRegex(ValueError,'unconfirmed_endpoint'):audit.exchange('https://unconfirmed.invalid/v1/models',{},None)

if __name__=='__main__':unittest.main()

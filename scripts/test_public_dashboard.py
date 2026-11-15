"""Offline publication and no-change regressions."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import build_audited_dashboard as dashboard
from public_dashboard import package,finalize,ASSETS
import pages_changed
class PublicTests(unittest.TestCase):
    def test_deterministic_rebuild_no_network(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('offline')):
            a=dashboard.build();before=(dashboard.ROOT/'docs/data-version.json').read_bytes();b=dashboard.build()
        self.assertEqual(a,b);self.assertEqual(before,(dashboard.ROOT/'docs/data-version.json').read_bytes())
    def test_allowlist_no_ledger_config_or_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'public';package(dashboard.ROOT/'docs',out)
            names={str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}
            self.assertEqual(names,set(ASSETS)|{'.nojekyll',json.loads((out/'data-version.json').read_text())['url']})
            d=json.loads((out/'dashboard-data.json').read_text())
            self.assertNotIn('service_reported_usage',d['history'])
            self.assertTrue(all(set(p)=={'url','display_time','status'} for p in d['inventory']))
    def test_version_changes_with_pending_progress_without_market_change(self):
        d=json.loads((dashboard.ROOT/'docs/dashboard-data.json').read_text());n=copy.deepcopy(d)
        n['inventory'].append({'url':'https://www.threads.com/@test/post/abc','display_time':'2026-11-10T10:00:00+08:00','status':'not_started'})
        n=finalize(n,dashboard.ROOT/'docs');self.assertNotEqual(n['version'],d['version']);self.assertEqual(n['market'],d['market']);self.assertEqual(n['events'],d['events'])
    def test_market_failure_retains_saved_bars(self):
        previous=dashboard.read('data/dashboard_market.json')
        with patch('urllib.request.urlopen',side_effect=OSError()),patch.object(Path,'write_text'):
            result=dashboard.fetch_market()
        self.assertEqual(result['series'],previous['series']);self.assertEqual(result['fetched_at'],previous['fetched_at']);self.assertEqual(len(result['errors']),2)
    def test_deploy_digest_no_change_and_changed(self):
        with patch.object(pages_changed,'gh',side_effect=[{'object':{'sha':'s'}},{'message':'pages-public-sha256:abc'}]):self.assertFalse(pages_changed.changed('owner/repo','abc'))
        with patch.object(pages_changed,'gh',side_effect=[{'object':{'sha':'s'}},{'message':'pages-public-sha256:old'}]):self.assertTrue(pages_changed.changed('owner/repo','new'))
        with patch.object(pages_changed,'gh',return_value=None):self.assertTrue(pages_changed.changed('owner/repo','first'))

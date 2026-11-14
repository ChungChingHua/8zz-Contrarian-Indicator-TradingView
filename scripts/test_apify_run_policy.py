"""Offline coverage of uncapped requests and provider-side truncation protection."""
import unittest
from apify_run_policy import run_options,provider_charge_limited

class RunPolicyTests(unittest.TestCase):
    def test_requests_have_no_monetary_ceiling_but_keep_execution_bounds(self):
        options=run_options(2)
        self.assertNotIn('maxTotalChargeUsd',options)
        self.assertEqual(options,dict(timeout=180,memory=512,maxItems=2,restartOnError='false'))
        options['maxItems']=99
        self.assertEqual(run_options()['maxItems'],50)

    def test_cost_above_old_ceiling_is_not_failure(self):
        for options in (None,{},dict(maxTotalChargeUsd=None)):
            self.assertFalse(provider_charge_limited(dict(options=options,usageTotalUsd='2.50')))

    def test_actual_provider_cap_keeps_incomplete_window_protection(self):
        for amount in ('.057529','1.50'):
            self.assertTrue(provider_charge_limited(dict(options=dict(maxTotalChargeUsd=amount),usageTotalUsd=amount)))
        self.assertFalse(provider_charge_limited(dict(options=dict(maxTotalChargeUsd='1.50'),usageTotalUsd='1.49')))

    def test_missing_or_invalid_total_does_not_hide_other_returned_cost(self):
        for total in (None,'invalid',True):
            self.assertTrue(provider_charge_limited(dict(options=dict(maxTotalChargeUsd='1'),usageTotalUsd=total,externalChargedTotalUsd='1')))

    def test_invalid_or_unlimited_provider_caps_do_not_restore_old_ceiling(self):
        for cap in (None,True,'0','-1','NaN','Infinity','invalid'):
            self.assertFalse(provider_charge_limited(dict(options=dict(maxTotalChargeUsd=cap),usageTotalUsd='5')))

    def test_provider_limit_messages_are_respected_even_without_cost(self):
        for message in ('Maximum total charge reached','Insufficient credit','Usage limit exceeded'):
            self.assertTrue(provider_charge_limited(dict(statusMessage=message)))

if __name__=='__main__':unittest.main()

"""One authorized, isolated 15-minute acquisition cost experiment. MPL-2.0.
No AI, notifications, cursor advancement or submission retries.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
import history_worker as h

TEST_ID = 'apify-15m-20261110-01'
PATH = 'data/cost_tests/' + TEST_ID + '.json'
ACTORS = {'facebook': 'apify~facebook-posts-scraper', 'threads': 'automation-lab~threads-scraper'}
CAP = Decimal('0.10')
DOC = 'https://docs.apify.com/api/v2/actors-runs-post'


def plain(value):
    if isinstance(value, Decimal): return str(value)
    if isinstance(value, dict): return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list): return [plain(v) for v in value]
    return value


class Client:
    def __init__(self, key):
        self.key = key
        self.counts = {'GET': 0, 'POST': 0}

    def request(self, path, payload=None):
        if not path.startswith('/') or '://' in path or '#' in path or 'token=' in path:
            raise ValueError('invalid_apify_path')
        method = 'GET' if payload is None else 'POST'
        self.counts[method] += 1
        req = urllib.request.Request('https://api.apify.com/v2' + path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.build_opener(h.StopRedirect()).open(req, timeout=90) as res:
                raw = res.read(4_000_001)
                if len(raw) > 4_000_000: raise ValueError('bounded_response_exceeded')
                if self.key.encode() in raw: raise ValueError('response_reflects_credential')
                return json.loads(raw, parse_float=Decimal)
        except urllib.error.HTTPError as exc:
            raise Failure('apify_http_error', exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise Failure('apify_transport_failure') from None


class Failure(Exception):
    def __init__(self, code, status=None): self.code = code; self.status = status


class Docs:
    def __init__(self, token): self.token = token; self.stores = {}
    def load(self, path):
        if path not in self.stores: self.stores[path] = h.GitHubStore(self.token, path)
        return self.stores[path].load()
    def save(self, path, value):
        if path not in self.stores: self.load(path)
        self.stores[path].save(plain(value))
    def formal_shas(self):
        paths = ['data/live_control.json', 'data/live_posts.json', 'data/telegram_outbox.json',
                 'data/history_completion_control.json', 'data/acquisition.json',
                 'data/social_posts.json', 'data/new_events.json', 'data/social_report.json',
                 'docs/social-status.json', '8zz-indicator.pine',
                 'candidates/8zz-original-author-batch-01.pine']
        result = {}
        for path in paths:
            store = h.GitHubStore(self.token, path)
            d = store._request('GET', store.url + '?ref=' + h.BRANCH)
            result[path] = None if d is None else d['sha']
        return result


def inputs(source, start, end):
    start = start.replace('+00:00', 'Z'); end = end.replace('+00:00', 'Z')
    if source == 'facebook':
        return {'startUrls': [{'url': 'https://www.facebook.com/DieWithoutBang'}],
                'resultsLimit': 50, 'onlyPostsNewerThan': start, 'onlyPostsOlderThan': end}
    return {'mode': 'posts', 'usernames': ['banini31'], 'maxPosts': 50, 'includeProfile': False,
            'postedAfter': start, 'postedBefore': end}


def pricing(actor, now):
    records = [p for p in actor.get('pricingInfos', [])
               if p.get('startedAt') and datetime.fromisoformat(p['startedAt'].replace('Z', '+00:00')) <= now]
    if not records: raise Failure('pricing_not_verifiable_no_start')
    p = max(records, key=lambda x: x['startedAt'])
    if p.get('minimalMaxTotalChargeUsd') is not None and Decimal(str(p['minimalMaxTotalChargeUsd'])) > CAP:
        raise Failure('actor_minimum_exceeds_authorized_cap_no_start')
    # Current API explicitly documents maxTotalChargeUsd for ALL pricing models.
    if p.get('pricingModel') not in ('PAY_PER_EVENT', 'PRICE_PER_DATASET_ITEM', 'FLAT_PRICE_PER_MONTH', 'FREE'):
        raise Failure('unknown_pricing_model_no_start')
    return {k: p[k] for k in ('pricingModel', 'startedAt', 'minimalMaxTotalChargeUsd',
        'isPPEPlatformUsagePaidByUser', 'pricingPerEvent', 'pricePerUnitUsd') if k in p}


def record_run(entry, run):
    for k in ('id', 'status', 'startedAt', 'finishedAt', 'buildId', 'buildNumber',
              'defaultDatasetId', 'options', 'usageTotalUsd', 'usageUsd',
              'externalChargedTotalUsd', 'chargedEventCounts', 'accountedChargedEventCounts'):
        if k in run: entry[k] = plain(run[k])
    entry['duration_seconds'] = plain(run.get('stats', {}).get('runTimeSecs'))
    entry['cost_observed_at'] = datetime.now(timezone.utc).isoformat()
    entry['billing_finality'] = 'not independently confirmed; zero is not proof of free execution'


def execute(docs, client, clock=lambda: datetime.now(timezone.utc), pause=time.sleep):
    prior = docs.load(PATH)
    if prior is not None: return prior  # Never resubmit this authorized test, including ambiguous starts.
    state = {'test_id': TEST_ID, 'status': 'preflight', 'actors': {}, 'cap_usd_per_run': '0.10',
             'cap_documentation': DOC, 'maximum_starts': 2, 'automatic_retries': 0}
    def save():
        state['http_requests'] = dict(client.counts)
        docs.save(PATH, state)
    state['formal_shas_before'] = docs.formal_shas(); save()
    try:
        for source, actor_id in ACTORS.items():
            actor = client.request('/acts/' + actor_id)['data']
            state['actors'][source] = {'actor': actor_id, 'pricing': pricing(actor, clock()),
                'defaultRunOptions': plain(actor.get('defaultRunOptions', {})), 'status': 'not_started'}
            save()
        # Freeze common window immediately before budget reservation / paid submissions.
        end = clock(); start = end - timedelta(minutes=15)
        state.update(start_utc=start.isoformat(), end_utc=end.isoformat(),
            start_taipei=start.astimezone(ZoneInfo('Asia/Taipei')).isoformat(),
            end_taipei=end.astimezone(ZoneInfo('Asia/Taipei')).isoformat())
        month = end.strftime('%Y-%m'); usage = docs.load('data/usage.json') or {}
        budget = usage.setdefault(month, {'apify_runs': 0, 'ai_attempts': 0})
        state['monthly_runs_before'] = budget['apify_runs']
        if budget['apify_runs'] + 2 > 70: raise Failure('existing_monthly_70_run_guard_no_start')
        budget['apify_runs'] += 2
        budget.setdefault('cost_test_reservations', {})[TEST_ID] = {'reserved_starts': 2,
            'maximum_total_usd': '0.20', 'ledger': PATH}
        docs.save('data/usage.json', usage)  # CAS remote ACK before any paid POST.
        state['reserved_starts'] = 2; state['monthly_runs_after'] = budget['apify_runs']; save()
        for source, entry in state['actors'].items():
            body = inputs(source, state['start_utc'], state['end_utc'])
            entry.update(status='submission_unknown', input=body); save()
            query = urllib.parse.urlencode({'timeout': 180, 'memory': 512, 'maxItems': 50,
                'maxTotalChargeUsd': '0.10', 'restartOnError': 'false'})
            run = client.request('/acts/' + entry['actor'] + '/runs?' + query, body)['data']
            record_run(entry, run); save()  # Run ID persisted before the next submission.
            options = run.get('options', {})
            if Decimal(str(options.get('maxTotalChargeUsd', '-1'))) != CAP:
                # No new starts; abort this known run to stop an unenforced cap.
                client.request('/actor-runs/' + run['id'] + '/abort', {})
                raise Failure('cap_not_acknowledged_run_aborted')
        for source, entry in state['actors'].items():
            for attempt in range(50):
                run = client.request('/actor-runs/' + entry['id'])['data']
                record_run(entry, run); save()
                if run['status'] not in ('READY', 'RUNNING', 'TIMING-OUT', 'ABORTING'): break
                if attempt < 49: pause(5)
            if run['status'] != 'SUCCEEDED': raise Failure('actor_not_successful_stop')
            rows = []; offset = 0
            while True:
                page = client.request('/datasets/' + run['defaultDatasetId'] +
                    '/items?format=json&offset=' + str(offset) + '&limit=100')
                if not isinstance(page, list): raise Failure('invalid_dataset_shape')
                rows.extend(page)
                if len(page) < 100: break
                offset += len(page)
                if offset > 1000: raise Failure('dataset_exceeds_bound')
            entry['result_count'] = len(rows)
            entry['cost_category'] = 'no_new_post_check' if len(rows) == 0 else 'results_present'
            entry['accepted_in_window'] = []
            exclusions = {}; lo = start; hi = end
            for row in rows:
                post, reason = h.s.normalize(row, source)
                if post is not None:
                    dt = datetime.fromisoformat(post['published_at'])
                    if not lo <= dt < hi: reason = 'outside_test_window'
                    else: entry['accepted_in_window'].append(h.s.public_safe(post)); continue
                exclusions[reason] = exclusions.get(reason, 0) + 1
            entry['excluded'] = exclusions
            entry['accepted_count'] = len(entry['accepted_in_window']); save()
        state['status'] = 'completed'
    except Exception as exc:
        state.update(status='stopped', error_code=getattr(exc, 'code', type(exc).__name__),
                     http_status=getattr(exc, 'status', None))
    state['formal_shas_after'] = docs.formal_shas()
    state['formal_state_unchanged'] = state['formal_shas_before'] == state['formal_shas_after']
    save()
    return state


if __name__ == '__main__':
    if os.getenv('AUTHORIZED_APIFY_COST_TEST') != TEST_ID: raise SystemExit('test authorization missing')
    key = os.environ['APIFY_TOKEN']; token = os.environ['GH_TOKEN']
    result = execute(Docs(token), Client(key))
    print(json.dumps({'test_id': TEST_ID, 'status': result['status'],
                      'error_code': result.get('error_code'), 'http_requests': result.get('http_requests')}))

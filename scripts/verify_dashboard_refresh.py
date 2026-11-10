"""Local browser contract: same open page, 60-second timer, atomic refresh and failure."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent
base=json.loads((ROOT/'docs/dashboard-data.json').read_text())
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for width,height,name in [(1440,1100,'desktop'),(390,844,'mobile')]:
        page=browser.new_page(viewport={'width':width,'height':height});errors=[];requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
        page.clock.install();state={'version':base['version'],'data':base,'fail':False,'bad':False}
        def version(route):
            if state['fail']:route.fulfill(status=503,body='unavailable');return
            route.fulfill(json={'schema':1,'version':state['version'],'url':'snapshots/'+state['version']+'.json'})
        def snapshot(route):route.fulfill(json={'version':state['version']} if state['bad'] else state['data'])
        page.route('**/data-version.json?*',version);page.route('**/snapshots/*.json?*',snapshot)
        page.goto('http://127.0.0.1:8000');page.wait_for_function("document.querySelector('#refresh-status').textContent.includes('每 60 秒')")
        initial_snapshots=sum('/snapshots/' in r for r in requests)
        page.locator('#direction').select_option('1');page.locator('#keyword').fill('台');page.locator('[data-basis="available"]').click();page.locator('[data-mode="A"]').click();page.locator('#pending-status').select_option('not_started',force=True)
        page.clock.fast_forward(60000);page.wait_for_timeout(50)
        assert sum('/snapshots/' in r for r in requests)==initial_snapshots
        next_data=copy.deepcopy(base);next_data['version']='a'*64;next_data['events'][-1]['summary']='台積電 · 自動更新驗證（模擬）';next_data['events'][-1]['direction']=1;next_data['inventory'].append({'url':'','display_time':'2026-11-10T10:00:00+08:00','status':'not_started'})
        for modes in ['modes','available_modes']:
            for mode in ['A','B']:
                next_data[modes][mode]['stats']['settled']=123
                next_data[modes][mode]['curve']=[{'time':1000,'equity':100,'benchmark':100},{'time':2000,'equity':101,'benchmark':102}]
        state.update(version=next_data['version'],data=next_data)
        page.clock.fast_forward(60000);page.wait_for_function("D.version==='a'.repeat(64)")
        assert page.locator('#keyword').input_value()=='台' and page.locator('#direction').input_value()=='1'
        assert page.locator('[data-mode="A"]').get_attribute('class')=='active' and page.locator('[data-basis="available"]').get_attribute('class')=='active'
        assert page.locator('#pending-status').input_value()=='not_started'
        assert '123' in page.locator('#metrics').inner_text() and page.locator('#chart svg').count()==1
        assert '台積電 · 自動更新驗證（模擬）' in page.locator('#event-rows').inner_text()
        state.update(fail=True);page.clock.fast_forward(60000);page.wait_for_function("document.querySelector('#refresh-status').textContent.includes('失敗')")
        assert page.evaluate('D.version')=='a'*64
        state.update(fail=False,bad=True,version='b'*64);page.clock.fast_forward(60000);page.wait_for_timeout(50);assert page.evaluate('D.version')=='a'*64
        stale=copy.deepcopy(next_data);stale.update(version='c'*64,built_at='2000-01-01T00:00:00+00:00')
        state.update(bad=False,version='c'*64,data=stale);page.clock.fast_forward(60000);page.wait_for_timeout(50);assert page.evaluate('D.version')=='a'*64
        state.update(bad=False,version=base['version'],data=base);page.clock.fast_forward(60000);page.wait_for_function("D.version!=='a'.repeat(64)")
        assert page.locator('#keyword').input_value()=='台'
        page.locator('.filters button').click();page.locator('[data-basis="published"]').click();page.locator('[data-mode="B"]').click();page.wait_for_timeout(50)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(ROOT/'docs/previews'/f'{name}.png'),full_page=True)
        assert not errors,errors
        assert all(url.startswith('http://127.0.0.1:8000/') for url in requests)
        results.append({'viewport':f'{width}x{height}','automatic_60s_refresh':True,'unchanged_version_no_snapshot':True,'filters_preserved':True,'stats_curve_list_updated':True,'http_and_invalid_snapshot_retained':True,'stale_cache_rejected':True,'recovery':True,'overflow':False,'page_errors':errors,'external_requests':0})
        page.close()
    browser.close()
(ROOT/'docs/previews/auto-refresh-validation.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))

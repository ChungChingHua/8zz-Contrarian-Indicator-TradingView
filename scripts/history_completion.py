"""One-time history completion, durable checkpoints, unchanged author policy. MPL-2.0."""
import copy,json,os,subprocess,sys
from collections import Counter
from datetime import datetime
from pathlib import Path
import history_worker as h
import original_author as policy
from history_plan import select
from history_batch_02 import prepare
from original_candidate import build
ROOT=policy.ROOT
SCOPE='history-completion-20261107'
CONTROL='data/history_completion_control.json'
DELTA='data/history_incremental_posts.json'
RAW=Path('/tmp/8zz-incremental-private.json')
RULE='8ccd8bbe6388705261e7240897417683f2dc6e2016f5db9d5eca462533837162'

class Remote:
    def __init__(self,token):self.token=token
    def save(self,path,value):
        store=h.GitHubStore(self.token,path);store.load();store.save(value)
        h.s.write(ROOT/path,value)
    def load(self,path,default=None):
        return h.GitHubStore(self.token,path).load() or default

def archive():
    data=h.s.read(ROOT/'data/social_posts.json',{})
    for k,v in h.s.read(ROOT/DELTA,{}).items():
        if k not in data:data[k]=v
    return data

def ledger_records():
    rows={};origins={}
    for path in sorted((ROOT/'data/history_progress').glob('*.json')):
        if path.name.endswith('.uncommitted.json'):continue
        for r in h.s.read(path,{}).get('records',[]):
            if r['status']=='not_started':continue
            if r['key'] in rows:raise ValueError('duplicate_dispatched_post')
            rows[r['key']]=r;origins[r['key']]=str(path.relative_to(ROOT))
    return rows,origins

def exclusions(data):
    rows,_=ledger_records();excluded=set()
    for r in rows.values():excluded.update(m['key'] for m in r['members'])
    # Explicitly preserve and list earlier tests; never silently convert different prompts.
    legacy={}
    for name in ('quality_samples.json','social_smoke_results.json','quality_cached_review.json'):
        d=h.s.read(ROOT/'data'/name,{})
        samples=d if isinstance(d,list) else d.get('samples',[])
        for r in samples:
            if isinstance(r,dict) and r.get('key') in data:
                legacy.setdefault(r['key'],[]).append('data/'+name);excluded.add(r['key'])
    for k in h.s.read(ROOT/'data/history_batch_01_plan.json',{}).get('excluded_keys',[]):
        if k in data:excluded.add(k);legacy.setdefault(k,[]).append('data/history_batch_01_plan.json')
    for r in h.s.read(ROOT/'data/history_batch_02_plan.json',{}).get('held_possible_duplicates',[]):
        if r['key'] in data:excluded.add(r['key']);legacy.setdefault(r['key'],[]).append('data/history_batch_02_plan.json:held_possible_duplicates')
    for k,p in data.items():
        if p['analysis'].get('status')!='pending':excluded.add(k);legacy.setdefault(k,[]).append('data/social_posts.json:analysis')
    return excluded,legacy

def frozen_plan(groups,number):
    posts=[]
    for i,g in enumerate(groups,1):
        p=g[0];r={k:p[k] for k in ('key','content_hash','post_id','source','url','published_at','display_time','unix_ms','text')}
        r.update(number=i,members=[{k:q[k] for k in ('key','source','url','published_at','post_id')} for q in g]);posts.append(r)
    return {'batch_id':SCOPE+'-'+str(number).zfill(3),'max_generations':25,'rule_version':policy.VERSION,'rule_sha256':policy.fingerprint(),'posts':posts}

def report(remote=None):
    data=archive();rows,origins=ledger_records();excluded,legacy=exclusions(data);by_member={}
    for key,r in rows.items():
        for member in r['members']:by_member[member['key']]=r
    quality={r['key']:r for r in h.s.read(ROOT/'data/quality_test_results.json',{}).get('samples',[])}
    inventory=[]
    for p in sorted(data.values(),key=lambda v:(v['unix_ms'],v['key'])):
        k=p['key'];r=by_member.get(k);raw_status=None
        if r:
            status=r['status'];reason=r.get('reason') or r.get('processed',{}).get('reasoning','');raw_status=status
            if status=='technical_failure' and reason=='contradictory_output_fields':status='pending_confirmation'
            origin=origins[r['key']]
        elif k in legacy:
            q=quality.get(k)
            status='technical_failure' if q and q.get('status')=='input_review' or p['analysis'].get('status')=='retry' and not q else 'pending_confirmation'
            reason='Previous test or review; original-author policy not re-generated or silently assumed validated'
            if q and q.get('error_reason'):reason+='; preserved input error: '+q['error_reason']
            elif p['analysis'].get('status')=='retry':reason+='; preserved archive error: '+str(p['analysis'].get('error_code') or p['analysis'].get('error_type') or p['analysis'].get('reason') or 'see source archive')
            origin=legacy[k]
        else:status='not_started';reason='';origin=None
        inventory.append({'key':k,'url':p['url'],'display_time':p['display_time'],'status':status,'stored_status':raw_status,'record_key':r['key'] if r else None,'evidence':origin,'reason':reason})
    candidates,checks=build({'records':sorted(rows.values(),key=lambda r:(r['unix_ms'],r['key']))})
    out=ROOT/'candidates/8zz-history-latest.pine';out.parent.mkdir(exist_ok=True);out.write_text(candidates)
    h.s.write(out.with_suffix('.checks.json'),checks)
    c=Counter(r['status'] for r in inventory)
    for status in ('completed_signal','completed_no_signal','pending_confirmation','technical_failure','input_failure','unknown','not_started'):c.setdefault(status,0)
    control=h.s.read(ROOT/CONTROL,{})
    new=[r for r in rows.values() if origins[r['key']].split('/')[-1].startswith(SCOPE)]
    usage={k:sum((r.get('service_response',{}).get('usage') or {}).get(k,0) or 0 for r in new) for k in ('input_tokens','output_tokens','total_tokens','reasoning_tokens')}
    pending=[r for r in inventory if r['status']=='not_started'];groups,_=select(data,{r['key'] for r in inventory if r['status']!='not_started'},len(data))
    last_terminal=max((r['display_time'] for r in inventory if r['status']!='not_started'),default=None)
    first_pending=min((r['display_time'] for r in pending),default=None)
    prefix=[r for r in inventory if first_pending is None or r['display_time']<first_pending]
    success_prefix=[]
    for r in inventory:
        if r['status'] not in ('completed_signal','completed_no_signal'):break
        success_prefix.append(r)
    latest_event=max((r['display_time'] for r in rows.values() if r['status']=='completed_signal'),default=None)
    summary={'scope':SCOPE,'cutoff_utc':control.get('cutoff_utc'),'cutoff_taipei':datetime.fromisoformat(control['cutoff_utc']).astimezone(h.s.TAIPEI).isoformat() if control.get('cutoff_utc') else None,'acquisition_completed':control.get('acquisition_completed',False),
       'archive_posts':len(data),'data_range_by_source':{src:{'first':min(p['display_time'] for p in data.values() if p['source']==src),'latest_post':max(p['display_time'] for p in data.values() if p['source']==src)} for src in ('facebook','threads')},
       'post_status_counts':dict(c),'remaining_not_started_groups':len(groups),'remaining_not_started_platform_posts':len(pending),
       'latest_attempted_or_reviewed_date':last_terminal,'all_posts_visited_before_first_unstarted':prefix[-1]['display_time'] if prefix else None,
       'successfully_completed_contiguous_prefix':success_prefix[-1]['display_time'] if success_prefix else None,
       'first_unstarted_date':first_pending,'latest_signal_date':latest_event,'pine':checks,
       'last_new_valid_response_date':max((r['display_time'] for r in new if r['status'] in ('completed_signal','completed_no_signal','pending_confirmation')),default=None),
       'new_stop_post_date':control.get('stopped_at'),
       'new_generation_attempts':sum(r['attempts'] for r in new),'new_http_responses':sum('http_status' in r for r in new),
       'new_status_counts':dict(Counter(r['status'] for r in new)), 'service_reported_usage':usage,
       'new_validated_responses':sum(bool(r.get('processed')) for r in new),
       'images_attached':sum(r.get('media_scope',{}).get('images_supplied',0) for r in new),
       'videos_unanalysed':sum(m.get('kind')=='video' for r in new for m in r.get('media_scope',{}).get('unanalysed_media',[])),
       'http_responses_without_usage':sum('http_status' in r and not isinstance(r.get('service_response',{}).get('usage'),dict) for r in new),
       'service_reported_cached_input_tokens':sum(((r.get('raw_response',{}).get('json',{}).get('usage') or {}).get('input_tokens_details') or {}).get('cached_tokens',0) or 0 for r in new),
       'apify_http_counts':control.get('apify_http_counts',{}),'apify_runs':[{k:r.get(k) for k in ('source','run_id','status','counts','reported_cost','http_status')} for r in control.get('runs',[])],
       'model_queries':0,'other_ai_provider_queries':0,'actual_points_deducted':None,'quota_headers':new[-1].get('remaining_headers',{}) if new else {},
       'stop_reason':control.get('stop_reason'),'service_quota_statement':control.get('service_quota_statement'),'all_history_fully_classified':control.get('acquisition_completed',False) and not any(c[x] for x in ('pending_confirmation','technical_failure','input_failure','unknown','not_started')),
       'rule_sha256':policy.fingerprint(),'provider_model_and_reasoning':'Service-reported gpt-5-mini / minimal, not independently verified',
       'usage_tracking_note':'ChatAnywhere request accounting is from durable ledgers; legacy usage.json ai_attempts is not the cumulative ChatAnywhere total.',
       'accounting_note':'Post counts include all prior tests, failures, reviews and cross-platform members; Pine counts are events, not posts. Tokens are service reports, not points or verified bills.'}
    h.s.write(ROOT/'data/history_completion_inventory.json',inventory);h.s.write(ROOT/'data/history_completion_summary.json',summary)
    text=['# 一次性歷史補齊執行紀錄','',
      '本次因實際阻塞停止，**尚未補齊全部歷史判讀**。' if control.get('stop_reason') else '請依下方剩餘及待確認清單判斷完成範圍。',
      '',f"資料抓取截止 UTC {control.get('cutoff_utc')}（Asia/Taipei 為 {summary['cutoff_taipei']}）；共 {len(data)} 篇。已走訪至 {summary['all_posts_visited_before_first_unstarted']}，其中待確認／失敗另列；本輪最後有效回應 {summary['last_new_valid_response_date']}，最新事件 {latest_event}。",
      '',f"完整 Pine {checks['total_events']} 事件 = 原歷史 {checks['historical_events']} + 累計新增 {checks['added_events']}；其中本輪新增 {sum(r['status']=='completed_signal' for r in new)}。",
      '',f"狀態依來源貼文計：有訊號 {c['completed_signal']}、無訊號 {c['completed_no_signal']}、待確認 {c['pending_confirmation']}、失敗 {c['technical_failure']+c['input_failure']}、狀態不明 {c['unknown']}、尚未處理 {c['not_started']}（去重後 {len(groups)} 組）。跨平台同組會對應多筆貼文，但只產生一個事件。",
      '',f"本輪生成 HTTP {summary['new_http_responses']} 次，成功固定格式回應 {summary['new_validated_responses']}；{summary['http_responses_without_usage']} 筆 HTTP 回應無 usage，不假定其零 tokens。已回報用量輸入 {usage['input_tokens']}／輸出 {usage['output_tokens']}／合計 {usage['total_tokens']} tokens。實際點數扣除未知；服務宣告共用 100 次免費請求的 24 小時視窗已耗盡，沒有提供確切重設時刻。",
      '', '原始程式曾未處理 429 的 usage=null，導致最後彙整步驟失敗；已修正並以全部已保存回應離線重建，不新增任何生成。供應商錯誤原含遮蔽後的金鑰識別片段，最新帳本已進一步去除該片段，保留清理前 JSON hash；完整金鑰未輸出。',
      '',json.dumps(summary,ensure_ascii=False,indent=2).join(['```json\n','\n```']),
      '', '原作者規則與 SHA256 未變。以前測試資料不是目前原作者標準的已完成結果；全部列入 inventory，未重送，也不自動沿用舊的額外門檻。舊帳本輸出矛盾的 technical_failure 僅在彙整清單標為待確認，原回應與原帳本不改。',
      '', '資料涵蓋截止時間請看 acquisition_completed、cutoff_utc 及 control 內各來源完成窗；latest_post 只代表最新抓到的貼文。latest_attempted_or_reviewed_date 包含以前測試樣本，不能當作連續處理進度。all_posts_visited_before_first_unstarted 包含待確認／失敗的已走訪資料，並非全部判讀成功；完整成功的前綴另列 successfully_completed_contiguous_prefix。最新訊號日期也不能代替資料處理完成日期。',
      '', '每篇來源、時間、狀態、原始帳本及原因見 data/history_completion_inventory.json。原文保留在 archive／增量資料，原始模型回應與 processed 分別保存於 history_progress。',
      '', '固定使用免費金鑰、.tech/v1、gpt-5-mini、minimal、嚴格格式；模型與推理僅供應商回報。圖片只有實際下載並附入者才標為讀取；影片未分析，圖片下載失敗及技術問題如實記錄。',
      '', '單篇矛盾保留待確認；單篇格式／媒體失敗隔離，不產生訊號或自動重試。連續三篇技術問題觸發共同故障停止（僅操作保護，不是情緒規則）；額度、認證、存取、服務端錯誤或已送出未保存的未知狀態立即保存停止。',
      '', '前後免費點數及實際扣點若未由服務回傳就是未知，不等同零，也不能由 tokens 換算。Apify 維持每 run 180 秒／512MB／maxItems 50／maxTotalChargeUsd 0.10、每月70次；run 回報費用不一定等同完整帳單，未儲值或提高上限。',
      '', '候選完整 Pine：candidates/8zz-history-latest.pine，保留所有原始歷史事件、作者署名及 MPL-2.0；待確認／技術失敗／unknown 無新增箭頭。使用者已確認前一候選可載入，這份新生成檔未在 TradingView 實際編譯。手動下載全文至 Pine Editor 完整取代、儲存並更新圖表，GitHub 不會自動同步。',
      '', '恢復方式：先核對 control 與各帳本；已完成、待確認、失敗、unknown 不自動重送。unknown 須人工查明原請求；quota／access 故障修復後，只續尚未送出項目，重新取得同一已保存 Apify dataset 不會重新啟動 Actor。新執行必須保留同一截止時間與 scope；不得重新抓整段歷史。',
      '', '本輪可接續的第一篇是 Threads 3956314846774104604，2026-08-04 21:18:23（Asia/Taipei）。額度重設時間未取得，不能假定台灣午夜恢復。恢復後保留現有資料 cutoff，不另啟動 Apify；若需要恢復新資料的私有媒體網址，只讀已保存 dataset。先將本次阻塞保留於 control 的歷史紀錄，明確解除 closed／stop_reason，再啟用這個一次性手動入口；只選 not_started，這次 429 失敗資料也不自動重送。',
      '', '本次 API 次數僅指 AI 生成及 Apify 啟動／讀取；GitHub 進度保存與圖片下載另計，沒有把上述數字宣稱為全部 HTTP 流量。data/usage.json 的 ai_attempts 為舊流程計數，不等於 ChatAnywhere 全部呼叫量，應以本次及既有帳本查核。',
      '', '只做一次性執行，不啟用持續排程、不發布 Pages、不合併 PR。']
    (ROOT/'docs/HISTORY_COMPLETION.md').write_text('\n'.join(text)+'\n')
    if remote:
        for path in ('data/history_completion_inventory.json','data/history_completion_summary.json'):
            remote.save(path,h.s.read(ROOT/path,{}))
        # Pine/docs aren't JSON: send as text via the same authenticated GitHub Contents endpoint.
        for path in ('candidates/8zz-history-latest.pine','candidates/8zz-history-latest.checks.json','docs/HISTORY_COMPLETION.md'):
            publish_text(remote,path,(ROOT/path).read_text())
    print(json.dumps({k:summary[k] for k in ('archive_posts','post_status_counts','new_generation_attempts','remaining_not_started_groups','stop_reason','latest_signal_date')},ensure_ascii=False),flush=True)
    return summary

def publish_text(remote,path,text):
    import base64
    if remote.token in text:raise ValueError('credential_in_output')
    store=h.GitHubStore(remote.token,path);d=store._request('GET',store.url+'?ref='+h.BRANCH)
    body={'message':'data: one-time history output [skip ci]','branch':h.BRANCH,'content':base64.b64encode(text.encode()).decode()}
    if d:body['sha']=d['sha']
    store._request('PUT',store.url,body)

def run():
    if os.getenv('AUTHORIZED_HISTORY_SCOPE')!=SCOPE or os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH or policy.fingerprint()!=RULE:raise SystemExit('Wrong one-time scope/branch/policy')
    key=os.environ.pop('CHATANYWHERE_API_KEY','');gh=os.environ.pop('GH_TOKEN','')
    if not key or not gh:raise SystemExit('Missing dedicated Secrets; no AI requests')
    remote=Remote(gh);control=remote.load(CONTROL,{})
    if control.get('closed') or control.get('stop_reason'):
        report(remote);return
    if not control.get('acquisition_completed'):raise SystemExit('Incremental acquisition not complete; no AI requests')
    data=archive();original=json.loads(subprocess.run(['git','show','51e27179cc4fa3447ce9e011c2e7d194ad5a9520:data/social_posts.json'],capture_output=True,check=True).stdout)
    raw=h.s.read(RAW,{})
    original.update(raw)
    number=1
    while True:
        excluded,_=exclusions(data);groups,_=select(data,excluded,25)
        if not groups:
            control.update(closed=True,stop_reason=None,all_unstarted_visited=True);remote.save(CONTROL,control);break
        plan=frozen_plan(groups,number);path='data/history_progress/'+plan['batch_id']+'.json'
        # A saved old chunk is immutable; its possibly-sent records are never replayed.
        if (ROOT/path).exists():number+=1;continue
        h.BATCH_ID=plan['batch_id'];h.LEDGER_PATH=path
        remote.save('data/history_plans/'+plan['batch_id']+'.json',plan)
        posts=[]
        for row in plan['posts']:
            p=copy.deepcopy(original.get(row['key']) or data[row['key']])
            if any(p[k]!=row[k] for k in ('text','source','post_id','published_at')):raise ValueError('post_identity_changed')
            posts.append(p)
        w=h.Worker(h.GitHubStore(gh,path),h.Provider(key),plan,prepare=prepare,secrets=(key,gh),local=ROOT/path,generation_limit=25,continue_isolated_failures=True)
        if control.get('consecutive_isolated_failures'):
            w.state['consecutive_isolated_failures']=control['consecutive_isolated_failures'];w.save()
        w.run(posts)
        control.update(last_chunk=plan['batch_id'],updated_at=h.now(),consecutive_isolated_failures=w.state.get('consecutive_isolated_failures',0))
        if w.state['stopped']:
            control.update(stop_reason=w.state.get('stop_reason'),stopped_at=next((r['display_time'] for r in reversed(w.state['records']) if r['status']!='not_started'),None))
        remote.save(CONTROL,control);report(remote)
        if w.state['stopped']:break
        number+=1
    report(remote)

if __name__=='__main__':
    if sys.argv[1:]==['report']:report()
    elif sys.argv[1:]==['publish-report']:
        gh=os.environ.pop('GH_TOKEN','')
        if not gh:raise SystemExit('Missing checkpoint credential')
        report(Remote(gh))
    else:
        try:run()
        except Exception as exc:
            # No raw tracebacks: urllib and payload errors can contain credentials/URLs.
            print(json.dumps({'fatal_error_type':type(exc).__name__,'reason':'Execution blocked; durable reservations retained; no automatic resend'}),flush=True)
            report();raise SystemExit(1)

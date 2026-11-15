"""Private Telegram setup and durable outbox. MPL-2.0 © hansai-art / Group.G.
Never log exception text, API URLs, credentials, updates or message bodies.
"""
import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

class TelegramError(Exception):
    def __init__(self, code, uncertain=False):
        self.code=code; self.uncertain=uncertain
        super().__init__(code)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class Telegram:
    def __init__(self, token):
        if not token:raise TelegramError('TELEGRAM_BOT_TOKEN 未設定')
        self.token=token
    def call(self, method, payload=None):
        req=urllib.request.Request('https://api.telegram.org/bot'+self.token+'/'+method,
            data=json.dumps(payload or {}).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.build_opener(NoRedirect()).open(req,timeout=25) as res:
                raw=res.read(2_000_001)
                if len(raw)>2_000_000:raise TelegramError('回應超過上限',method=='sendMessage')
                data=json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code==409:raise TelegramError('接收衝突：已有 webhook 或其他 getUpdates 接收程式；未變更任何設定') from None
            if e.code in (400,401,403,404,429):raise TelegramError('Telegram 拒絕請求 HTTP '+str(e.code)) from None
            raise TelegramError('Telegram HTTP 異常',method=='sendMessage') from None
        except TelegramError:raise
        except Exception:raise TelegramError('Telegram 傳輸或回應異常',method=='sendMessage') from None
        if not isinstance(data,dict) or data.get('ok') is not True:
            code=data.get('error_code') if isinstance(data,dict) else None
            if code==409:raise TelegramError('接收衝突：已有 webhook 或其他接收程式；未變更設定')
            raise TelegramError('Telegram 未確認成功',method=='sendMessage' and code not in (400,401,403,404,429))
        return data.get('result')
    def private(self, chat_id):
        if not re.fullmatch(r'[1-9][0-9]*',str(chat_id or '')):raise TelegramError('TELEGRAM_CHAT_ID 未設定或不是私人聊天室 ID')
        result=self.call('getChat',{'chat_id':str(chat_id)})
        if not isinstance(result,dict) or result.get('type')!='private' or str(result.get('id'))!=str(chat_id):
            raise TelegramError('指定目標不是確認的私人聊天室')
    def send(self,chat_id,text):
        result=self.call('sendMessage',{'chat_id':str(chat_id),'text':text,'link_preview_options':{'is_disabled':True}})
        if not isinstance(result,dict) or not isinstance(result.get('message_id'),int):raise TelegramError('發送回應缺少確認',True)
        return result['message_id']

def discover(client):
    webhook=client.call('getWebhookInfo')
    if not isinstance(webhook,dict):raise TelegramError('webhook 狀態無法確認')
    if webhook.get('url'):raise TelegramError('既有 webhook 已設定；不刪除或變更，請先確認接收方式')
    updates=client.call('getUpdates',{'timeout':0,'limit':100}) # No offset; do not acknowledge/consume others' updates.
    if not isinstance(updates,list):raise TelegramError('getUpdates 回應格式異常')
    ids=sorted({m['chat']['id'] for u in updates if isinstance(u,dict)
        for m in [u.get('message',{})] if isinstance(m,dict) and isinstance(m.get('chat'),dict)
        and m['chat'].get('type')=='private' and isinstance(m['chat'].get('id'),int) and m['chat']['id']>0})
    if not ids:return {'status':'未收到私人訊息，請回 @WS_8zz_Alert_bot 重新傳送文字後再執行','candidate_chat_ids':[]}
    return {'status':'請確認候選 ID，再手動存成 GitHub Secret TELEGRAM_CHAT_ID；不自動選取',
        'candidate_chat_ids':ids,'bounded_updates':len(updates)==100}

def message(e):
    def local(value):return datetime.fromisoformat(value).astimezone(ZoneInfo('Asia/Taipei')).isoformat() if value else '無歷史紀錄'
    direction={1:'偏多 ▲',-1:'偏空 ▼',0:'中性'}[e['direction']]
    return ('8zz '+('歷史補判讀' if e.get('historical') else '新文章訊號')+'｜'+('方向翻轉' if e['is_flip'] else '同向追加')+'\n'
        +'發文：'+local(e['time'])+'\n判讀完成：'+local(e.get('completed_at'))+'\n平台：'+e['platform']
        +'\n標的：'+e['target']+'\n原文情緒：'+e.get('sentiment','原判讀未另存情緒文字')[:700]
        +'\n反指標方向：'+direction+'\n強度：'+str(e['strength'])
        +'\n摘要：'+e['summary'][:1900]+'\n'+'\n'.join(e['urls'])[:800]
        +'\n媒體：'+e.get('media_note','原歷史媒體分析範圍無紀錄')[:400])[:4000]

def deliver(events,store,client,chat_id):
    """store.load/save must CAS/ACK persist. Reservation precedes send; no blind retries."""
    state=store.load() or {'records':{}}
    records=state['records']
    if not client or not chat_id:
        state['configuration']='未設定 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID';store.save(state);return state
    client.private(chat_id)
    state['configuration']='已設定（不表示本次已發送）'
    for e in events:
        if not e['direction']:continue
        r=records.get(e['event_key'])
        if r is None:
            # Existing snapshot is explicitly baseline; do not notify all 257 historical records on activation.
            r=records[e['event_key']]={'status':'baseline_suppressed' if e.get('baseline') else 'pending'}
        if r['status']!='pending':continue
        r.update(status='unknown',reserved_at=datetime.now(timezone.utc).isoformat(),recipient_sha256=hashlib.sha256(str(chat_id).encode()).hexdigest())
        store.save(state) # ACK before POST. Crash here retains unknown, even if POST never occurred.
        try:mid=client.send(chat_id,message(e))
        except TelegramError as exc:
            r.update(status='unknown' if exc.uncertain else 'failed',reason=exc.code)
            store.save(state);break # No service retry storm.
        r.update(status='sent',message_id=mid,sent_at=datetime.now(timezone.utc).isoformat())
        store.save(state)
    store.save(state)
    return state

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['discover','test']);a=p.parse_args()
    try:
        client=Telegram(os.environ.pop('TELEGRAM_BOT_TOKEN',''))
        if a.action=='discover':print(json.dumps(discover(client),ensure_ascii=False))
        else:
            chat=os.environ.pop('TELEGRAM_CHAT_ID','');client.private(chat)
            client.send(chat,'8zz 通知串接成功');print('已確認發送一次測試通知')
    except TelegramError as e:print(json.dumps({'error':e.code,'send_result_unknown':e.uncertain},ensure_ascii=False));raise SystemExit(1)
    except Exception:print('Telegram 設定流程異常；錯誤內容已遮蔽，請檢查設定');raise SystemExit(1)
if __name__=='__main__':main()

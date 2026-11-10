'use strict';
let D=window.DASHBOARD_DATA;const $=id=>document.getElementById(id);let mode='B',basis='published',page=0,asset='0050';const instrument=()=>asset==='TXF'?D.instruments.TXF:D;const market=()=>instrument().market;const assetName=()=>asset==='TXF'?'台指期貨 TXFR1':'0050.TW';const model=()=>basis==='available'?instrument().available_modes[mode]:instrument().modes[mode];const size=window.innerWidth<600?8:20;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=t=>t?new Date(t).toLocaleString('sv-SE',{timeZone:'Asia/Taipei',hour12:false}).slice(0,16):'—';
const pct=x=>x==null?'—':`${x>=0?'+':''}${x.toFixed(2)}%`;
const link=u=>/^https:\/\/(www\.)?(facebook\.com|threads\.(com|net))\//.test(u)?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">原文 ↗</a>`:'';
function chart(data){if(!data.length){$('chart').innerHTML='<p style="padding:65px 10px;text-align:center">缺少可核對的進場行情，暫不繪製策略曲線。<br><small>未將缺資料畫成零報酬，也不以日線替代 30 分鐘線。</small></p>';$('chart-range').innerHTML='';return}
 const W=Math.max(300,$('chart').clientWidth),H=window.innerWidth<600?230:280,p=32,values=data.flatMap(d=>[d.equity,d.benchmark]),lo=Math.min(100,...values)*.96,hi=Math.max(100,...values)*1.04;
 const x=t=>p+(t-data[0].time)/(data.at(-1).time-data[0].time||1)*(W-2*p),y=v=>H-p-(v-lo)/(hi-lo)*(H-2*p);
 let svg='';for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;svg+=`<line x1="${p}" y1="${y(v)}" x2="${W-p}" y2="${y(v)}" stroke="#263241"/><text x="3" y="${y(v)+4}" fill="#96a6b8" font-size="10">${v.toFixed(0)}</text>`}
 for(const [key,color] of (asset==='TXF'?[['equity','#5ee6bf']]:[['benchmark','#8095b2'],['equity','#5ee6bf']]))svg+=`<polyline fill="none" stroke="${color}" stroke-width="2.5" points="${data.map(d=>`${x(d.time)},${y(d[key])}`).join(' ')}"/>`;
 svg+=`<text x="${W-p}" y="18" text-anchor="end" fill="#5ee6bf" font-size="11">策略 ${data.at(-1).equity.toFixed(2)} ${asset==='TXF'?'':'/ 買入持有 '+data.at(-1).benchmark.toFixed(2)}</text>`;
 $('chart').innerHTML=`<svg role="img" aria-label="所選標的策略資金曲線" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${svg}</svg>`;$('chart-range').innerHTML=`<span>${date(data[0].time)}</span><span>${date(data.at(-1).time)} 台北</span>`;
}
function render(){const M=model(),s=M.stats;$('asset-description').textContent=asset==='TXF'?D.instruments.TXF.disclosure:'0050 等額本金代理，非原文個股績效。30分鐘行情來自永豐，排除未完整時段；日線以永豐收盤優先，經價格一致性核對後以既有Yahoo日線補缺。';$('chart-subtitle').textContent=assetName()+' 代理帳戶 · 單一部位 · 100%名目本金，無槓桿';$('benchmark-legend').hidden=asset==='TXF';document.querySelectorAll('[data-basis]').forEach(b=>b.classList.toggle('active',b.dataset.basis===basis));document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));$('mode-note').textContent=mode==='B'?'Mode B：所選標的日線代理，反向訊號後第一個完成收盤出場。原標的績效不在此混算。':`Mode A：${D.hold_bars} 根 30 分鐘固定持有；無完整對應週期行情的事件明列缺資料，不套用日線或小時線。`;$('mode-note').textContent+=(basis==='available'?' 判讀完成後可成交參考：缺完成時間者不納入交易；不回填已錯過收盤。':' 歷史發文參考：不代表當時已取得判讀。');$('mode-note').textContent+=' 本模式行情／績效截止：'+(market().series[mode==='A'?'30m':'1d'].length?date(market().series[mode==='A'?'30m':'1d'].at(-1).time):'缺資料')+'（台北）；重算時間：'+date(D.built_at)+'。';
 const metrics=[['已結算',s.settled,'僅已完成進出場'],['勝 / 敗 / 平手',`${s.wins} / ${s.losses} / ${s.ties}`,'多空虧損都計敗'],['已結算勝率',s.win_rate==null?'—':s.win_rate.toFixed(1)+'%','未平倉不計入分母'],['平均交易報酬',pct(s.average),'已結算交易算術平均'],['未平倉',s.open,M.trades.filter(t=>!t.exit).map(t=>'浮動 '+pct(t.floating)).join(' / ')||'無未平倉交易'],['缺行情',s.missing,'獨立列出，不計勝率']];$('metrics').innerHTML=metrics.map(([a,b,c])=>`<div class="metric"><b>${a}</b><strong>${b}</strong><small>${c}</small></div>`).join('');chart(M.curve);renderRows();
 $('gap-summary').textContent=`本模式 ${s.missing} 個事件缺行情或判讀時間。${historyText()} 未平倉 ${s.open} 筆。這些狀態不互相替代。`+(market().errors.length?' 行情取得錯誤：'+market().errors.map(e=>e.interval+' '+e.error).join('；'):'');
 $('missing-list').innerHTML=D.events.filter(e=>M.rows[e.id].missing).map(e=>`<p>#${e.id} · ${date(e.unix_ms)} · ${esc(M.rows[e.id].status)} · ${esc(e.target)}</p>`).join('')||'<p>無缺行情事件</p>';
}
function renderRows(){const M=model();let ev=D.events.filter(e=>{const day=new Date(e.unix_ms+8*3600000).toISOString().slice(0,10);return (!$('from').value||day>=$('from').value)&&(!$('to').value||day<=$('to').value)&&(!$('platform').value||e.platform.includes($('platform').value))&&(!$('direction').value||String(e.direction)===$('direction').value)&&(!$('strength').value||String(e.strength)===$('strength').value)&&(! $('keyword').value||[e.summary,e.target,...e.urls].join(' ').toLowerCase().includes($('keyword').value.toLowerCase()))}).reverse();
 const sr=ev.map(e=>M.rows[e.id]),done=sr.filter(r=>r.status==='已結算');$('filter-count').textContent=`符合 ${ev.length} / ${D.events.length} 個事件 · 構成交易 ${sr.filter(r=>r.trade).length} 筆 · 已結算 ${done.length} 筆 · 勝 ${done.filter(r=>r.result==='勝').length} / 敗 ${done.filter(r=>r.result==='敗').length} / 平 ${done.filter(r=>r.result==='平手').length} · 未平倉 ${sr.filter(r=>r.status==='未平倉').length}`;
 page=Math.min(page,Math.max(0,Math.ceil(ev.length/size)-1));$('event-rows').innerHTML=ev.slice(page*size,(page+1)*size).map(e=>{const r=M.rows[e.id],v=r.pnl??r.floating;return `<tr><td>#${e.id} · ${date(e.unix_ms)}<small>${esc(e.platform)}</small></td><td class="${e.direction===1?'bull':'bear'}">${e.direction===1?'▲ 偏多':e.direction===-1?'▼ 偏空':'中性'}<small>${'★'.repeat(e.strength)+'☆'.repeat(3-e.strength)}</small></td><td>${esc(e.target)}<small>→ ${assetName()}（代理）</small></td><td class="summary-cell"><details><summary>${esc(e.summary.split('\n').slice(0,3).join(' / '))}</summary><pre>${esc(e.summary)}
原文情緒：${esc(e.sentiment)}
媒體：${esc(e.media_note)}
抓取：${date(e.fetched_at)}
${e.historical?'歷史補判讀／歷史基準':'新文章'} · ${e.is_flip?'方向翻轉':'同向追加'}</pre></details><small>判讀完成：${date(e.completed_at)}${e.completed_at?'':'（未保存，不推估）'}</small>${e.urls.map(link).join(' · ')||'<small>原文網址缺失（歷史資料）</small>'}</td><td><span class="pill">${r.trade?'是':'否'}</span><small>${esc(r.status)}</small></td><td>${r.entry?date(r.entry.time)+'<small>@ '+r.entry.price.toFixed(4)+'</small>':'—'}${r.exit?'<small>出 '+date(r.exit.time)+' @ '+r.exit.price.toFixed(4)+'</small>':r.mark?'<small>估 '+date(r.mark.time)+' @ '+r.mark.price.toFixed(4)+'</small>':''}</td><td class="${v>=0?'bull':'bear'}">${pct(v)}<small>${r.floating!=null?'浮動，未計勝率':r.result||'—'}</small></td></tr>`}).join('')||'<tr><td colspan="7">沒有符合的事件。</td></tr>';document.querySelectorAll('#event-rows tr').forEach(tr=>Array.from(tr.children).forEach((td,i)=>td.dataset.label=['發文時間／平台','方向／強度','原標的／成交標的','原文與來源','是否交易／狀態','進出場時間','交易報酬'][i]));
 $('page').textContent=`${page+1} / ${Math.max(1,Math.ceil(ev.length/size))}`;$('prev').disabled=page===0;$('next').disabled=(page+1)*size>=ev.length;
}
function pending(){const labels={not_started:'待判讀',pending_confirmation:'待確認',technical_failure:'技術失敗',input_failure:'媒體前檢失敗',unknown:'請求狀態不明'};const rows=D.inventory.filter(p=>labels[p.status]&&(!$('pending-status').value||p.status===$('pending-status').value));$('pending-list').innerHTML=rows.map(p=>`<p>${esc(date(p.display_time))} · ${labels[p.status]} · ${link(p.url)}<br>${esc(p.reason||'尚未送出判讀')}</p>`).join('')}
function historyText(){const c=D.history.post_status_counts;return `歷史判讀：有訊號 ${c.completed_signal}、無訊號 ${c.completed_no_signal}、待確認 ${c.pending_confirmation}、技術失敗 ${c.technical_failure}、媒體前檢失敗 ${c.input_failure}、狀態不明 ${c.unknown}、未處理 ${c.not_started}（${D.history.remaining_not_started_groups} 篇待判讀）。`}
function freshness(){$('publication-note').textContent='發布範圍：發文與績效行情限於 '+D.publication.label+' 以前。十月、十一月文章不列入；截至九月底的判讀仍未完成。';document.querySelector('header .tag').textContent=D.live_status.enabled?'排程程式閘門已設定 · 狀態以 Actions 為準':'正式排程停用 · 保存資料預覽';const h=D.history,c=h.post_status_counts,marketTimes=Object.values(market().series).flat().map(b=>b.time);
$('freshness').innerHTML=[['Facebook 公開涵蓋截止',date(D.platform_cutoffs.facebook),'來源已抓取範圍，依發布上限截斷'],['Threads 公開涵蓋截止',date(D.platform_cutoffs.threads),'僅公開九月底以前的保存文章'],['已保存文章判讀進度',`${c.completed_signal+c.completed_no_signal} / ${h.archive_posts} 篇完成`,`待確認 ${c.pending_confirmation} · 失敗 ${c.technical_failure+c.input_failure} · 未處理 ${c.not_started}`],['最新訊號時間',date(h.latest_signal_date),'非判讀完整截止時間'],['Telegram 設定',D.live_status.notifications,'事件保存不受通知設定影響'],['新文章判讀',D.live_status.ai_stop?'暫停（待安全續接）':'僅處理未送出資料','依使用者要求更新；不自動抓取'],['行情最後成功取得',date(market().fetched_at),market().errors.length?'本次行情取得失敗，保留可用行情':'非網站資料重建時間'],['績效行情截止',marketTimes.length?date(Math.max(...marketTimes)):'缺資料','行情未前進時，不代表績效已更新'],['網站資料版本',(D.version||'舊快照').slice(0,12),'資料重建 '+date(D.built_at)]].map(([a,b,c])=>`<div><b>${esc(a)}</b><strong>${esc(b)}</strong><small>${esc(c)}</small></div>`).join('');}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;page=0;render()});document.querySelectorAll('.filters input,.filters select').forEach(el=>el.oninput=()=>{page=0;renderRows()});document.querySelector('.filters').onreset=()=>setTimeout(()=>{page=0;renderRows()},0);$('prev').onclick=()=>{page--;renderRows()};$('next').onclick=()=>{page++;renderRows()};$('pending-status').onchange=pending;
$('export').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(D,null,2)],{type:'application/json'}));a.download='8zz-audited-dashboard.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};freshness();pending();render();

document.querySelectorAll('[data-basis]').forEach(b=>b.onclick=()=>{basis=b.dataset.basis;page=0;render()});
let refreshing=false;
function validSnapshot(n){
 if(!n.instruments?.TXF?.market||!n.instruments.TXF.modes||!n.instruments.TXF.available_modes)throw Error('invalid_instruments');
 if(!n||!Array.isArray(n.events)||!Array.isArray(n.inventory)||!n.history?.post_status_counts||!n.platform_cutoffs||!n.live_status||!n.market?.series||!Array.isArray(n.market.errors)||!Number.isFinite(Date.parse(n.built_at)))throw Error('invalid_snapshot');
 for(const record of [n,n.instruments.TXF]){
 for(const interval of ['1d','30m'])if(!Array.isArray(record.market.series[interval])||record.market.series[interval].some(b=>!Number.isFinite(b.time)||!Number.isFinite(b.price)||b.price<=0))throw Error('invalid_market');
 for(const modes of [record.modes,record.available_modes])for(const key of ['A','B']){
  const m=modes?.[key];if(!m?.stats||!m.rows||!Array.isArray(m.curve)||!Array.isArray(m.trades))throw Error('invalid_modes');
  if(m.curve.some(p=>!['time','equity','benchmark'].every(k=>Number.isFinite(p[k]))))throw Error('invalid_curve');
  for(const e of n.events)if(!m.rows[e.id]||![-1,0,1].includes(e.direction)||![1,2,3].includes(e.strength)||!Array.isArray(e.urls)||typeof e.summary!=='string')throw Error('invalid_event');
 }
 }
 return n;
}
async function readPublic(url){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
 try{const r=await fetch(url,{cache:'no-store',signal:controller.signal});if(!r.ok)throw Error('http');return await r.json()}finally{clearTimeout(timer)}
}
async function refreshSavedData(){
 if(location.protocol==='file:'||window.INLINE_PREVIEW){$('refresh-status').textContent='離線保存預覽；不連外更新。正式排程停用。';return}
 if(refreshing)return;refreshing=true;
 try{
  const v=await readPublic('data-version.json?t='+Date.now());
  if(v.schema!==1||!/^[a-f0-9]{64}$/.test(v.version)||v.url!=='snapshots/'+v.version+'.json')throw Error('invalid_version');
  if(v.version!==D.version){
   const next=validSnapshot(await readPublic(v.url+'?v='+v.version));if(next.version!==v.version)throw Error('version_mismatch');
   if(Date.parse(next.built_at)<Date.parse(D.built_at))throw Error('stale_snapshot');
   const previous=D;
   try{D=next;freshness();pending();render()}catch(error){D=previous;freshness();pending();render();throw error}
  }
  $('refresh-status').textContent='已檢查保存資料 '+date(Date.now())+'（台北）；每 60 秒檢查版本，有更新才載入。網站資料更新不代表行情已更新。';
 }catch{$('refresh-status').textContent='資料更新失敗，保留最後成功資料（版本 '+(D.version||'舊快照').slice(0,12)+'）。60 秒後重試。'}finally{refreshing=false}
}
setInterval(refreshSavedData,60000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshSavedData()});refreshSavedData();

$('asset').onchange=()=>{asset=$('asset').value;page=0;freshness();render()};

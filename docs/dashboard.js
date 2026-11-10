'use strict';
let D=window.DASHBOARD_DATA;const $=id=>document.getElementById(id);let mode='B',basis='published',page=0,asset='0050';const instrument=()=>asset==='TXF'?D.instruments.TXF:D;const market=()=>instrument().market;const assetName=()=>asset==='TXF'?'台指期貨 TXFR1':'0050.TW';const model=()=>basis==='available'?instrument().available_modes[mode]:instrument().modes[mode];const size=Number.MAX_SAFE_INTEGER;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=t=>t?new Date(t).toLocaleString('sv-SE',{timeZone:'Asia/Taipei',hour12:false}).slice(0,16):'—';
const pct=x=>x==null?'—':`${x>=0?'+':''}${x.toFixed(2)}%`;
const link=u=>/^https:\/\/(www\.)?(facebook\.com|threads\.(com|net))\//.test(u)?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">原文 ↗</a>`:'';
function svgChart(data){if(!data.length){$('chart').innerHTML='<p style="padding:65px 10px;text-align:center">缺少可核對的進場行情，暫不繪製策略曲線。<br><small>未將缺資料畫成零報酬，也不以日線替代 30 分鐘線。</small></p>';$('chart-range').innerHTML='';return}
 const W=Math.max(300,$('chart').clientWidth),H=window.innerWidth<600?230:280,p=32,values=data.flatMap(d=>[d.equity,d.benchmark]),lo=Math.min(100,...values)*.96,hi=Math.max(100,...values)*1.04;
 const x=t=>p+(t-data[0].time)/(data.at(-1).time-data[0].time||1)*(W-2*p),y=v=>H-p-(v-lo)/(hi-lo)*(H-2*p);
 let svg='';for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;svg+=`<line x1="${p}" y1="${y(v)}" x2="${W-p}" y2="${y(v)}" stroke="#263241"/><text x="3" y="${y(v)+4}" fill="#96a6b8" font-size="10">${v.toFixed(0)}</text>`}
 for(const [key,color] of (asset==='TXF'?[['equity','#5ee6bf']]:[['benchmark','#8095b2'],['equity','#5ee6bf']]))svg+=`<polyline fill="none" stroke="${color}" stroke-width="2.5" points="${data.map(d=>`${x(d.time)},${y(d[key])}`).join(' ')}"/>`;
 svg+=`<text x="${W-p}" y="18" text-anchor="end" fill="#5ee6bf" font-size="11">策略 ${data.at(-1).equity.toFixed(2)} ${asset==='TXF'?'':'/ 買入持有 '+data.at(-1).benchmark.toFixed(2)}</text>`;
 $('chart').innerHTML=`<svg role="img" aria-label="所選標的策略資金曲線" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${svg}</svg>`;$('chart-range').innerHTML=`<span>${date(data[0].time)}</span><span>${date(data.at(-1).time)} 台北</span>`;
}
let equityChartObj=null;
function chart(data){
 const models=basis==='available'?instrument().available_modes:instrument().modes;
 $('equity-chart-title').textContent=`資產增長曲線（起始 100）｜反指標 Mode ${mode}${mode==='A'?'（固定 '+D.hold_bars+' 棒）':''}${asset==='0050'?' vs 買入持有 0050':'・台指期貨日盤'}`;
 if(!window.Chart){svgChart(data);return}
 if(equityChartObj){equityChartObj.destroy();equityChartObj=null}
 if(!models.A.curve.length&&!models.B.curve.length){svgChart([]);return}
 $('chart').innerHTML='<canvas id="equityChart" role="img" aria-label="Mode A、Mode B與代理標的資產增長曲線"></canvas>';
 const datasets=[['B','#00e676'],['A','#58a6ff']].map(([key,color])=>({label:key==='B'?'Mode B（翻轉出場）':`Mode A（固定 ${D.hold_bars} 棒）`,data:models[key].curve.map(p=>({x:p.time,y:p.equity})),borderColor:mode===key?color:color+'55',backgroundColor:'transparent',tension:0,pointRadius:models[key].curve.length<=30?4:1,borderWidth:2}));
 if(asset==='0050')datasets.push({label:'0050 買入持有',data:(models.B.curve.length?models.B.curve:models.A.curve).map(p=>({x:p.time,y:p.benchmark})),borderColor:'rgba(139,148,158,0.6)',backgroundColor:'transparent',borderDash:[6,4],pointRadius:0,borderWidth:1.5});
 equityChartObj=new window.Chart($('equityChart'),{type:'line',data:{datasets},options:{animation:false,maintainAspectRatio:false,interaction:{mode:'nearest',intersect:false},plugins:{legend:{labels:{color:'#8b949e',boxWidth:16}},tooltip:{callbacks:{title:items=>items.length?date(items[0].parsed.x)+'（台北）':'',label:ctx=>ctx.dataset.label+': '+ctx.parsed.y.toFixed(2)}}},scales:{x:{type:'time',time:{unit:'month',tooltipFormat:'yyyy-MM-dd HH:mm'},ticks:{color:'#8b949e',maxTicksLimit:8,callback:v=>date(v).slice(0,10)},grid:{color:'#30363d'}},y:{ticks:{color:'#8b949e',callback:v=>Number(v).toFixed(0)},grid:{color:'#30363d'}}}}});
 const times=[...models.A.curve,...models.B.curve].map(p=>p.time);$('chart-range').innerHTML=`<span>${date(Math.min(...times))}</span><span>${date(Math.max(...times))} 台北</span>`;
}
function render(){const M=model(),s=M.stats;$('asset-description').textContent=asset==='TXF'?D.instruments.TXF.disclosure:'0050 等額本金代理，非原文個股績效。30分鐘行情來自永豐，排除未完整時段；A、B均使用30分鐘行情計算，日線僅保留供來源核對，不參與績效。';$('chart-subtitle').textContent=assetName()+' 代理帳戶 · 單一部位 · 100%名目本金，無槓桿';$('benchmark-legend').hidden=asset==='TXF';document.querySelectorAll('[data-basis]').forEach(b=>b.classList.toggle('active',b.dataset.basis===basis));document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));$('mode-note').textContent=mode==='B'?'Mode B：與Mode A使用相同的30分鐘棒進場時點；反向訊號後於第一根有效30分鐘棒收盤出場，可於同價反向。':`Mode A：進場規則同Mode B，固定持有 ${D.hold_bars} 根30分鐘棒出場；持倉期間不重疊進場。`;$('mode-note').textContent+=(basis==='available'?' 判讀完成後可成交參考：缺完成時間者不納入交易；不回填已錯過收盤。':' 歷史發文參考：不代表當時已取得判讀。');$('mode-note').textContent+=' 本模式行情／績效截止：'+(market().series['30m'].length?date(market().series['30m'].at(-1).time):'缺資料')+'（台北）；重算時間：'+date(D.built_at)+'。';
 const metrics=[['勝率',s.win_rate==null?'—':s.win_rate.toFixed(1)+'%','僅已結算交易，平手計入分母','var(--green)'],['勝',s.wins,'平手 '+s.ties,'var(--green)'],['敗',s.losses,'已結算 '+s.settled,'var(--red)'],['進行中',s.open,'浮動損益未計入勝率','var(--yellow)'],['平均報酬率',pct(s.average),'已結算交易算術平均',s.average==null?'var(--muted)':s.average>=0?'var(--green)':'var(--red)'],['總事件數',D.events.length,'不等於交易筆數','var(--muted)'],['缺資料',s.missing,'行情／判讀／轉倉排除','var(--muted)']];
 $('metrics').innerHTML=metrics.map(([label,value,note,color],i)=>`<div class="stat-card${i===6?' stat-card-secondary':''}" title="${esc(note)}"><div class="val" style="color:${color}">${value}</div><div class="lbl">${label}</div></div>`).join('');
 $('parameter-wrap').hidden=mode!=='A';const a=(basis==='available'?instrument().available_modes:instrument().modes).A.stats;
 $('parameter-row').innerHTML=`<tr><td style="font-weight:700;color:var(--blue)">${D.hold_bars}</td><td>${a.win_rate==null?'—':a.win_rate.toFixed(1)+'%'}</td><td>${pct(a.average)}</td><td>${a.wins}</td><td>${a.losses}</td><td>${a.settled}</td></tr>`;
 $('exit-heading').textContent=`出場日(${mode})`;$('pnl-heading').textContent=`報酬(${mode})`;$('result-heading').textContent=`結果(${mode})`;
 chart(M.curve);renderRows();
 $('gap-summary').textContent=`本模式 ${s.missing} 個事件缺行情或判讀時間。${historyText()} 未平倉 ${s.open} 筆。這些狀態不互相替代。`+(market().errors.length?' 行情取得錯誤：'+market().errors.map(e=>e.interval+' '+e.error).join('；'):'');
 $('missing-list').innerHTML=D.events.filter(e=>M.rows[e.id].missing).map(e=>`<p>#${e.id} · ${date(e.unix_ms)} · ${esc(M.rows[e.id].status)} · ${esc(e.target)}</p>`).join('')||'<p>無缺行情事件</p>';
}
function renderRows(){const M=model();let ev=D.events.filter(e=>{const day=new Date(e.unix_ms+8*3600000).toISOString().slice(0,10),r=M.rows[e.id];return (!$('from').value||day>=$('from').value)&&(!$('to').value||day<=$('to').value)&&(!$('platform').value||e.platform.includes($('platform').value))&&(!$('direction').value||String(e.direction)===$('direction').value)&&(!$('traded').value||Boolean(r.trade)===($('traded').value==='yes'))&&(!$('strength').value||String(e.strength)===$('strength').value)&&(!$('flip').value||e.is_flip)&&(!$('outcome').value||($('outcome').value==='missing'?r.missing:$('outcome').value==='未平倉'?r.status==='未平倉':r.result===$('outcome').value))&&(!$('keyword').value||[e.summary,e.target,...e.urls].join(' ').toLowerCase().includes($('keyword').value.toLowerCase()))}).reverse();
 const sr=ev.map(e=>M.rows[e.id]),done=sr.filter(r=>r.status==='已結算');$('filter-count').textContent=`符合 ${ev.length} / ${D.events.length} 個事件 · 構成交易 ${sr.filter(r=>r.trade).length} 筆 · 已結算 ${done.length} 筆 · 勝 ${done.filter(r=>r.result==='勝').length} / 敗 ${done.filter(r=>r.result==='敗').length} / 平 ${done.filter(r=>r.result==='平手').length} · 未平倉 ${sr.filter(r=>r.status==='未平倉').length}`;
 $('event-rows').innerHTML=ev.map(e=>{const r=M.rows[e.id],v=r.pnl??r.floating,result=r.status==='未平倉'?'進行中':r.result||(r.missing?'缺資料':'—'),badge=result==='勝'?'green':result==='敗'?'red':result==='進行中'?'yellow':'muted';return `<tr><td class="hide-mobile" style="color:var(--muted)">${e.id}</td><td style="white-space:nowrap">${date(e.unix_ms)}<small>${esc(e.platform)}</small></td><td class="${e.direction===1?'dir-bull':'dir-bear'}">${e.direction===1?'偏多 ▲':e.direction===-1?'偏空 ▼':'中性'}</td><td style="white-space:nowrap">${'★'.repeat(e.strength)+'☆'.repeat(3-e.strength)}</td><td class="ticker-cell">${esc(assetName())}<small>原標的：${esc(e.target)}</small></td><td class="summary-cell hide-mobile"><details><summary>${esc(e.summary)}</summary><pre>${esc(e.summary)}
原文情緒：${esc(e.sentiment)}
媒體：${esc(e.media_note)}
抓取：${date(e.fetched_at)}
判讀完成：${date(e.completed_at)}${e.completed_at?'':'（未保存，不推估）'}
${e.historical?'歷史補判讀／歷史基準':'新文章'}</pre></details>${e.urls.map(link).join(' · ')||'<small>原文網址缺失</small>'}</td><td style="text-align:center">${e.is_flip?'🔄':''}</td><td><span class="badge badge-muted">${r.trade?'是':'否'}</span><small>${esc(r.status)}</small></td><td style="white-space:nowrap">${r.entry?date(r.entry.time)+'<small>@ '+r.entry.price.toFixed(4)+'</small>':'—'}</td><td style="white-space:nowrap">${r.exit?date(r.exit.time)+'<small>@ '+r.exit.price.toFixed(4)+'</small>':r.mark?'未平倉<small>估 '+date(r.mark.time)+' @ '+r.mark.price.toFixed(4)+'</small>':'—'}</td><td class="${v==null?'':v>=0?'pnl-pos':'pnl-neg'}" style="white-space:nowrap">${pct(v)}${r.floating!=null?'<small>浮動，未計勝率</small>':''}</td><td><span class="badge badge-${badge}">${esc(result)}</span></td></tr>`}).join('')||'<tr><td colspan="12">沒有符合的事件。</td></tr>';
}
function pending(){const labels={not_started:'待判讀',pending_confirmation:'待確認',technical_failure:'技術失敗',input_failure:'媒體前檢失敗',unknown:'請求狀態不明'};const rows=D.inventory.filter(p=>labels[p.status]&&(!$('pending-status').value||p.status===$('pending-status').value));$('pending-list').innerHTML=rows.map(p=>`<p>${esc(date(p.display_time))} · ${labels[p.status]} · ${link(p.url)}<br>${esc(p.reason||'尚未送出判讀')}</p>`).join('')}
function historyText(){const c=D.history.post_status_counts;return `歷史判讀：有訊號 ${c.completed_signal}、無訊號 ${c.completed_no_signal}、待確認 ${c.pending_confirmation}、技術失敗 ${c.technical_failure}、媒體前檢失敗 ${c.input_failure}、狀態不明 ${c.unknown}、未處理 ${c.not_started}（${D.history.remaining_not_started_groups} 篇待判讀）。`}
function freshness(){$('generated-at').textContent='資料產生：'+date(D.built_at)+' · 最新事件：'+date(D.history.latest_signal_date);$('publication-note').textContent='發布範圍：發文與績效行情限於 '+D.publication.label+' 以前。十月、十一月文章不列入；截至九月底的判讀仍未完成。';document.querySelector('header .tag').textContent=D.live_status.enabled?'排程程式閘門已設定 · 狀態以 Actions 為準':'正式排程停用 · 保存資料預覽';const h=D.history,c=h.post_status_counts,marketTimes=Object.values(market().series).flat().map(b=>b.time);
$('freshness').innerHTML=[['Facebook 公開涵蓋截止',date(D.platform_cutoffs.facebook),'來源已抓取範圍，依發布上限截斷'],['Threads 公開涵蓋截止',date(D.platform_cutoffs.threads),'僅公開九月底以前的保存文章'],['已保存文章判讀進度',`${c.completed_signal+c.completed_no_signal} / ${h.archive_posts} 篇完成`,`待確認 ${c.pending_confirmation} · 失敗 ${c.technical_failure+c.input_failure} · 未處理 ${c.not_started}`],['最新訊號時間',date(h.latest_signal_date),'非判讀完整截止時間'],['Telegram 設定',D.live_status.notifications,'事件保存不受通知設定影響'],['新文章判讀',D.live_status.ai_stop?'暫停（待安全續接）':'僅處理未送出資料','依使用者要求更新；不自動抓取'],['行情最後成功取得',date(market().fetched_at),market().errors.length?'本次行情取得失敗，保留可用行情':'非網站資料重建時間'],['績效行情截止',marketTimes.length?date(Math.max(...marketTimes)):'缺資料','行情未前進時，不代表績效已更新'],['網站資料版本',(D.version||'舊快照').slice(0,12),'資料重建 '+date(D.built_at)]].map(([a,b,c])=>`<div><b>${esc(a)}</b><strong>${esc(b)}</strong><small>${esc(c)}</small></div>`).join('');}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;page=0;render()});document.querySelectorAll('.filters input,.filters select').forEach(el=>el.oninput=()=>{page=0;renderRows()});document.querySelector('.filters').onreset=()=>setTimeout(()=>{page=0;renderRows()},0);$('pending-status').onchange=pending;
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
  document.querySelector('header .tag').classList.toggle('badge-red',false);document.querySelector('header .tag').textContent=D.live_status.enabled?'排程程式閘門已設定・狀態以Actions為準':'正式排程停用・保存資料預覽';
  $('refresh-status').textContent='已檢查保存資料 '+date(Date.now())+'（台北）；每 60 秒檢查版本，有更新才載入。網站資料更新不代表行情已更新。';
 }catch{document.querySelector('header .tag').classList.toggle('badge-red',true);document.querySelector('header .tag').textContent='資料更新失敗・保留最後成功資料';$('refresh-status').textContent='資料更新失敗，保留最後成功資料（版本 '+(D.version||'舊快照').slice(0,12)+'）。60 秒後重試。'}finally{refreshing=false}
}
setInterval(refreshSavedData,60000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshSavedData()});refreshSavedData();

$('asset').onchange=()=>{asset=$('asset').value;page=0;freshness();render()};

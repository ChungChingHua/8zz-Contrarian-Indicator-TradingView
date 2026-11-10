// DOM contract test, not a visual browser test.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const fixture=JSON.parse(fs.readFileSync('docs/dashboard-data.json','utf8'));
(async()=>{const results=[];for(const width of [1440,390])for(const chartReady of [false,true]){
 const nodes=new Map();const el=id=>{if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',textContent:'',clientWidth:width-80,hidden:false,classList:{toggle(){}},children:[]});return nodes.get(id)};
 const charts=[];class ChartStub{constructor(canvas,config){this.config=config;charts.push(this)}destroy(){this.destroyed=true}}
 const requests=[];let calls=0,current=structuredClone(fixture),interval;
 const context={window:{DASHBOARD_DATA:structuredClone(fixture),innerWidth:width,Chart:chartReady?ChartStub:undefined},document:{getElementById:el,querySelector:el,querySelectorAll:()=>[],addEventListener(){}},location:{protocol:'https:'},setTimeout:()=>1,clearTimeout(){},setInterval(fn,ms){interval=fn;assert.equal(ms,60000)},AbortController,fetch:async url=>{requests.push(url);return{ok:true,json:async()=>url.startsWith('data-version')?{schema:1,version:current.version,url:'snapshots/'+current.version+'.json'}:current}}};
 vm.createContext(context);vm.runInContext(fs.readFileSync('docs/dashboard.js','utf8'),context);await new Promise(r=>setImmediate(r));
 for(const selected of ['0050','TXF'])for(const mode of ['A','B'])for(const basis of ['published','available']){
  vm.runInContext(`asset='${selected}';mode='${mode}';basis='${basis}';page=0`,context);
  for(const value of ['', 'yes','no']){
   el('traded').value=value;vm.runInContext('render()',context);
   const rows=(selected==='TXF'?fixture.instruments.TXF:fixture)[basis==='available'?'available_modes':'modes'][mode].rows;
   const expected=fixture.events.filter(e=>!value||Boolean(rows[e.id].trade)===(value==='yes'));
   assert.match(el('filter-count').textContent,new RegExp('符合 '+expected.length+' /'));
   if(expected.length)assert.equal((el('event-rows').innerHTML.match(/<tr>/g)||[]).length,expected.length);
   else assert.match(el('event-rows').innerHTML,/沒有符合/);
  }
 }
 vm.runInContext("asset='0050';mode='B';basis='published';page=0",context);el('traded').value='yes';
 el('traded').value='';
 for(const result of ['勝','敗','平手','未平倉','missing']){
  el('outcome').value=result;el('flip').value='yes';vm.runInContext('renderRows()',context);
  const rows=fixture.modes.B.rows;
  const expected=fixture.events.filter(e=>e.is_flip&&(result==='missing'?rows[e.id].missing:result==='未平倉'?rows[e.id].status==='未平倉':rows[e.id].result===result));
  assert.match(el('filter-count').textContent,new RegExp('符合 '+expected.length+' /'));
 }
 el('outcome').value='';el('flip').value='';el('traded').value='yes';
 el('keyword').value='台';el('asset').value='TXF';el('asset').onchange();
 assert.match(el('asset-description').textContent,/TXFR1/);assert.equal(el('benchmark-legend').hidden,true);assert.match(el('chart').innerHTML,chartReady?/<canvas/:/<svg/);
 if(chartReady){const last=charts.at(-1);assert.equal(last.config.data.datasets.length,2);assert.equal(last.config.data.datasets[0].label,'Mode B（翻轉出場）');assert.match(last.config.data.datasets[1].label,/Mode A/);assert.equal(last.config.options.scales.x.type,'time')}
 assert.match(el('event-rows').innerHTML,/TXFR1/);
 current=structuredClone(fixture);current.version='a'.repeat(64);current.built_at=new Date(Date.parse(fixture.built_at)+1000).toISOString();current.instruments.TXF.modes.B.stats.settled=777;
 await interval();assert.equal(el('asset').value,'TXF');assert.equal(el('keyword').value,'台');assert.equal(el('traded').value,'yes');assert.match(el('metrics').innerHTML,/777/);
 const count=requests.filter(u=>u.startsWith('snapshots')).length;await interval();assert.equal(requests.filter(u=>u.startsWith('snapshots')).length,count);
 current=structuredClone(current);current.version='b'.repeat(64);current.instruments.TXF.modes=null;await interval();assert.match(el('refresh-status').textContent,/失敗/);assert.match(el('metrics').innerHTML,/777/);
 el('asset').value='0050';el('asset').onchange();assert.equal(el('benchmark-legend').hidden,false);assert.match(el('event-rows').innerHTML,/0050.TW/);
 results.push({width,chart_ready:chartReady,author_comparison_chart:true,result_and_flip_filters:true,asset_switch:true,trade_filter_all_assets_modes_bases:true,rows_stats_curve:true,poll_preserves_asset_and_filters:true,invalid_futures_snapshot_retained:true,unchanged_version_no_snapshot:true});
 }fs.writeFileSync('docs/previews/asset-ui-validation.json',JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify(results));})().catch(e=>{console.error(e);process.exitCode=1});

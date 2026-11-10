// DOM contract test, not a visual browser test.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const fixture=JSON.parse(fs.readFileSync('docs/dashboard-data.json','utf8'));
(async()=>{const results=[];for(const width of [1440,390]){
 const nodes=new Map();const el=id=>{if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',textContent:'',clientWidth:width-80,hidden:false,classList:{toggle(){}},children:[]});return nodes.get(id)};
 const requests=[];let calls=0,current=structuredClone(fixture),interval;
 const context={window:{DASHBOARD_DATA:structuredClone(fixture),innerWidth:width},document:{getElementById:el,querySelector:el,querySelectorAll:()=>[],addEventListener(){}},location:{protocol:'https:'},setTimeout:()=>1,clearTimeout(){},setInterval(fn,ms){interval=fn;assert.equal(ms,60000)},AbortController,fetch:async url=>{requests.push(url);return{ok:true,json:async()=>url.startsWith('data-version')?{schema:1,version:current.version,url:'snapshots/'+current.version+'.json'}:current}}};
 vm.createContext(context);vm.runInContext(fs.readFileSync('docs/dashboard.js','utf8'),context);await new Promise(r=>setImmediate(r));
 el('keyword').value='台';el('asset').value='TXF';el('asset').onchange();
 assert.match(el('asset-description').textContent,/TXFR1/);assert.equal(el('benchmark-legend').hidden,true);assert.match(el('chart').innerHTML,/<svg/);
 assert.match(el('event-rows').innerHTML,/TXFR1/);
 current=structuredClone(fixture);current.version='a'.repeat(64);current.built_at=new Date(Date.parse(fixture.built_at)+1000).toISOString();current.instruments.TXF.modes.B.stats.settled=777;
 await interval();assert.equal(el('asset').value,'TXF');assert.equal(el('keyword').value,'台');assert.match(el('metrics').innerHTML,/777/);
 const count=requests.filter(u=>u.startsWith('snapshots')).length;await interval();assert.equal(requests.filter(u=>u.startsWith('snapshots')).length,count);
 current=structuredClone(current);current.version='b'.repeat(64);current.instruments.TXF.modes=null;await interval();assert.match(el('refresh-status').textContent,/失敗/);assert.match(el('metrics').innerHTML,/777/);
 el('asset').value='0050';el('asset').onchange();assert.equal(el('benchmark-legend').hidden,false);assert.match(el('event-rows').innerHTML,/0050.TW/);
 results.push({width,asset_switch:true,rows_stats_curve:true,poll_preserves_asset_and_filters:true,invalid_futures_snapshot_retained:true,unchanged_version_no_snapshot:true});
 }fs.writeFileSync('docs/previews/asset-ui-validation.json',JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify(results));})().catch(e=>{console.error(e);process.exitCode=1});

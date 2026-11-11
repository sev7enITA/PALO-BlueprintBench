/* Optional UI regression check; static evidence only, no model calls. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const origin = process.env.PALO_SITE_URL || 'http://127.0.0.1:58195';
const output = process.env.PALO_SCREENSHOT_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'palo-ranking-'));
(async () => {
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true,reducedMotion:'reduce'});
  const errors=[]; page.on('pageerror',error=>(errors.push(error.message),console.error('PAGE ERROR',error.message)));
  const data = await (await page.request.get(origin+'/downloads/blueprintbench/leaderboard-data.json')).json();
  const origins = await (await page.request.get(origin+'/downloads/blueprintbench/model-origins.json')).json();
  const url=origin+'/PALO_BlueprintBench_Leaderboard.html';
  const rows=()=>page.locator('#model-table tbody tr').evaluateAll(items=>items.map(r=>({id:r.dataset.model,rank:r.dataset.rank?Number(r.dataset.rank):null})));
  async function jsonExport() {
    // Capture repeated export payloads without triggering Chromium's bulk-download limiter.
    await page.evaluate(()=>{window.__originalObjectURL=URL.createObjectURL;window.__originalAnchorClick=HTMLAnchorElement.prototype.click;URL.createObjectURL=blob=>{window.__exportBlob=blob;return window.__originalObjectURL(blob);};HTMLAnchorElement.prototype.click=function(){if(!this.href.startsWith('blob:'))return window.__originalAnchorClick.call(this);};});
    await page.click('#download-json');
    const text=await page.evaluate(async()=>{const text=await window.__exportBlob.text();URL.createObjectURL=window.__originalObjectURL;HTMLAnchorElement.prototype.click=window.__originalAnchorClick;return text;});
    return JSON.parse(text);
  }
  await page.goto(url+'?time_metric=agreement',{waitUntil:'networkidle'});
  await page.waitForSelector('#model-table');
  const initial=await rows();assert.equal(initial.length,data.internal.models.length);
  const expected=data.internal.models.filter(m=>data.internal.records.some(r=>r.model===m.id&&r.track==='verification'&&r.state!=='not_run')).sort((a,b)=>b.verification_correct-a.verification_correct);
  for(const row of initial){const index=expected.findIndex(m=>m.id===row.id);assert.equal(row.rank,index<0?null:expected.findIndex(m=>m.verification_correct===expected[index].verification_correct)+1);}
  assert.equal(initial.find(r=>r.id==='sakana/fugu-max').rank,null);
  assert(initial.some((r,i)=>r.rank&&initial.some((other,j)=>j!==i&&other.rank===r.rank)),'Real data must exercise ties');
  const firstDownload=page.waitForEvent('download');await page.click('#download-json');const file=await firstDownload;assert.equal(JSON.parse(fs.readFileSync(await file.path(),'utf8')).qualified,false);
  const exported=await jsonExport();assert.equal(exported.qualified,false);assert.equal(exported.origin_metadata_version,origins.version);assert.deepEqual(exported.models.map(m=>m.model),initial.map(r=>r.id));
  assert(exported.models.every(m=>m.qualified===false));
  assert.equal(exported.models.find(m=>m.model==='sakana/fugu-max').ranking_value,null);
  assert(exported.models.find(m=>m.model.startsWith('openai/')).country_sources.length>0);
  await page.selectOption('#country-filter','US');
  const filtered=await rows();assert(filtered.length>0&&filtered.length<initial.length);
  for(const r of filtered)assert.equal(r.rank,initial.find(x=>x.id===r.id).rank);
  const filteredExport=await jsonExport();assert.equal(filteredExport.filters.country,'US');assert(filteredExport.models.every(m=>m.developer_countries.some(c=>c.code==='US')));
  assert.equal(new URL(page.url()).searchParams.get('time_metric'),'agreement');
  await page.reload({waitUntil:'networkidle'});assert.equal(await page.inputValue('#country-filter'),'US');
  await page.selectOption('#country-filter','unknown');
  assert.deepEqual((await rows()).map(r=>r.id),data.internal.models.filter(m=>!origins.makers.find(o=>o.id===m.id.split('/')[0]&&o.status==='verified'&&o.countries.length)).map(m=>m.id));
  await page.click('#reset-filters');
  for(const direction of ['asc','desc']){
    await page.goto(url+'?sort=country&direction='+direction,{waitUntil:'networkidle'});
    const values=(await jsonExport()).models.map(m=>m.developer_countries.map(c=>c.name).join(' / '));
    let missing=false,previous;
    for(const value of values){if(!value){missing=true;continue;}assert(!missing,'Unknown countries stay last');if(previous)assert(direction==='asc'?previous.localeCompare(value)<=0:previous.localeCompare(value)>=0);previous=value;}
  }
  for(const rankMetric of ['matches','coverage','calls','missing','disagreements','cost','time','costpercall']){
    await page.selectOption('#rank-metric',rankMetric);
    const result=await jsonExport();assert.equal(result.filters.rankMetric,rankMetric);
    assert.equal(result.models.find(m=>m.model==='sakana/fugu-max').rank,null);
    const eligible=result.models.filter(m=>m.rank!==null);
    for(let i=1;i<eligible.length;i++)assert(eligible[i-1].rank<=eligible[i].rank);
    if(rankMetric==='disagreements')assert(eligible.every(m=>m.missing===0));
    if(['cost','time','costpercall'].includes(rankMetric))assert(eligible.every(m=>m.complete_calls===m.assigned_calls));
    if(['cost','costpercall'].includes(rankMetric))assert(eligible.every(m=>m.accounting_complete));
  }
  await page.selectOption('#kpi-columns','all');
  for(const metric of ['coverage','input','output','costpercall']){
    for(const direction of ['asc','desc']){
      await page.locator(`[data-sort="${metric}"]`).click();
      const items=(await jsonExport()).models;
      const key={coverage:'classification_coverage',input:'input_tokens',output:'completion_tokens_including_reasoning',costpercall:'cost_per_complete_call_usd'}[metric];
      let missing=false,previous=null;
      for(const m of items){const value=m[key];if(value===null){missing=true;continue;}assert(!missing,metric+' unknown last');if(previous!==null)assert(direction==='asc'?previous<=value:previous>=value,metric+' '+direction);previous=value;}
    }
  }
  const waiting=page.waitForEvent('download');await page.click('#download-csv');
  const csv=fs.readFileSync(await (await waiting).path(),'utf8');
  for(const field of ['metric_rank','developer_countries','country_sources','rank_eligible','country_filter','rank_metric','country_basis','origin_metadata_version','rank_scope','rank_case','rank_dimension','rank_lens'])assert(csv.includes('"'+field+'"'),field+' CSV');
  await page.click('#reset-filters');await page.selectOption('#dimension-filter','threshold');
  const scoped=await jsonExport();assert(scoped.models.every(m=>m.assigned<324));
  await page.selectOption('#label-lens','sensitivity');const sensitivity=await jsonExport();assert(sensitivity.models[0].assigned<scoped.models[0].assigned);
  await page.click('[data-view="operations"]');assert(await page.locator('#rank-controls').isHidden());
  assert((await jsonExport()).records.length>0);
  await page.click('[data-cohort="historical"]');assert(await page.locator('#rank-controls').isHidden());assert((await jsonExport()).models.every(m=>m.rank===null));
  await page.click('[data-cohort="all"]');assert.equal((await jsonExport()).models.length,data.internal.models.length+data.historical.models.length);
  await page.click('[data-cohort="qualified"]');assert(await page.locator('#download-json').isDisabled());
  await page.goto(url,{waitUntil:'networkidle'});await page.locator('#workspace').evaluate(el=>el.scrollIntoView({block:'start'}));
  await page.screenshot({path:path.join(output,'ranking-desktop.png')});
  for(const width of [320,375,768,1440]){
    await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'page overflow '+width);
    if(width===375){await page.locator('#workspace').evaluate(el=>el.scrollIntoView({block:'start'}));await page.screenshot({path:path.join(output,'ranking-mobile.png')});}
  }
  await page.route('**/model-origins.json',route=>route.abort());
  await page.goto(url,{waitUntil:'networkidle'});await page.waitForSelector('#model-table');assert.equal((await rows()).length,data.internal.models.length);
  assert((await page.locator('#model-table').innerText()).includes('Unavailable'));
  assert.deepEqual(errors,[]);
  const report={status:'passed',origin,models:data.internal.models.length,checks:['competition ties and blocked rank','country provenance','filter-stable rank','country sort both directions','unknown last','all 8 ranking metrics','4 new KPI sorts both directions','CSV and JSON','semantic scope and sensitivity','operations and cohort separation','metadata outage','320/375/768/1440 responsive','temporal URL preserved'],screenshots:['ranking-desktop.png','ranking-mobile.png']};
  fs.writeFileSync(path.join(output,'ranking-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});

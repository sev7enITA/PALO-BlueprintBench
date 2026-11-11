/* Descriptive dashboard regression; legacy filename retained for CI callers. No inference. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const origin = process.env.PALO_SITE_URL || 'http://127.0.0.1:58194';
const output = process.env.PALO_SCREENSHOT_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'palo-descriptive-'));
(async () => {
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true,reducedMotion:'reduce'});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const data=await (await page.request.get(origin+'/downloads/blueprintbench/leaderboard-data.json')).json();
  const url=origin+'/PALO_BlueprintBench_Leaderboard.html';
  const rows=()=>page.locator('#model-table tbody tr').evaluateAll(items=>items.map(r=>r.dataset.model));
  async function exportJSON() {
    await page.evaluate(()=>{window.__originalObjectURL=URL.createObjectURL;window.__originalAnchorClick=HTMLAnchorElement.prototype.click;URL.createObjectURL=blob=>{window.__exportBlob=blob;return window.__originalObjectURL(blob);};HTMLAnchorElement.prototype.click=function(){if(!this.href.startsWith('blob:'))return window.__originalAnchorClick.call(this);};});
    await page.click('#download-json');
    return JSON.parse(await page.evaluate(async()=>{const text=await window.__exportBlob.text();URL.createObjectURL=window.__originalObjectURL;HTMLAnchorElement.prototype.click=window.__originalAnchorClick;return text;}));
  }
  await page.goto(url+'?sort=rank&rankMetric=cost&time_metric=agreement',{waitUntil:'networkidle'});
  await page.waitForSelector('#model-table');
  assert.equal(await page.locator('#rank-metric, [data-sort="rank"], [data-rank], .rank-number, #calibration, #adversarial-review').count(),0);
  assert.equal(await page.locator('.brand-resources').count(),0);
  assert.equal(await page.inputValue('#sort-select'),'name');
  assert.equal((await rows()).length,18);
  assert((await page.locator('h1').innerText()).includes('Internal test'));
  const initial=await exportJSON();
  assert.equal(initial.publication_revision,'2026-11-11.3');
  assert.equal(initial.dataset_version,'2026-11-11.2');
  assert.equal(initial.qualified,false);
  assert(initial.models.every(m=>!Object.keys(m).some(k=>k.includes('rank'))));
  const names=initial.models.map(m=>m.name);assert.deepEqual(names,[...names].sort((a,b)=>a.localeCompare(b)));
  for(const m of initial.models){
    assert.equal(m.label_matches+m.disagreements+m.missing,m.assigned);
    assert.equal(m.classified+m.missing,m.assigned);
    assert.equal(m.conditional_label_agreement,m.classified?m.label_matches/m.classified:null);
    assert.equal(m.classification_coverage,m.classified/m.assigned);
  }
  assert((await page.locator('#model-table tr[data-model="google/gemini-4-argon"]').innerText()).includes('HTTP 503'));
  assert((await page.locator('#model-table tr[data-model="prism-ml/ternary-bonsai-2-27b"]').innerText()).includes('HTTP 429'));
  const gemini=initial.models.find(m=>m.model.startsWith('google/'));
  assert.equal(gemini.conditional_label_agreement,1);assert.equal(gemini.missing,36);assert(gemini.classification_coverage<1);
  const blocked=initial.models.find(m=>m.model==='sakana/fugu-max');assert.equal(blocked.conditional_label_agreement,null);assert.equal(blocked.missing,324);
  await page.selectOption('#country-filter','US');
  const filtered=await exportJSON();assert(filtered.models.length<18);assert(filtered.models.every(m=>m.developer_countries.some(c=>c.code==='US')));
  assert.equal(new URL(page.url()).searchParams.get('time_metric'),'agreement');
  await page.reload({waitUntil:'networkidle'});assert.equal(await page.inputValue('#country-filter'),'US');
  await page.click('#reset-filters');await page.selectOption('#kpi-columns','all');
  const metrics={agreement:'conditional_label_agreement',coverage:'classification_coverage',input:'input_tokens',output:'completion_tokens_including_reasoning',costpercall:'cost_per_complete_call_usd'};
  for(const [metric,key] of Object.entries(metrics)){
    for(const direction of ['asc','desc']){
      await page.locator(`[data-sort="${metric}"]`).click();const items=(await exportJSON()).models;
      let missing=false,previous=null;
      for(const m of items){const value=m[key];if(value===null){missing=true;continue;}assert(!missing,metric+' unknown last');if(previous!==null)assert(direction==='asc'?previous<=value:previous>=value,metric+' '+direction);previous=value;}
    }
  }
  const waiting=page.waitForEvent('download');await page.click('#download-csv');const csv=fs.readFileSync(await (await waiting).path(),'utf8');
  for(const field of ['conditional_label_agreement','classification_coverage','classified','assigned','missing','publication_revision','developer_countries','sort_by','view_url'])assert(csv.includes('"'+field+'"'),field);
  for(const field of ['metric_rank','rank_eligible','rank_metric','rank_scope'])assert(!csv.includes('"'+field+'"'),field+' removed');
  await page.click('#reset-filters');await page.locator('[data-compare]').first().check();await page.check('#selected-only');assert.equal((await rows()).length,1);assert(await page.locator('#comparison').isVisible());
  await page.click('#clear-comparison');await page.selectOption('#dimension-filter','threshold');const scoped=await exportJSON();assert(scoped.models.every(m=>m.assigned<324));
  await page.selectOption('#label-lens','sensitivity');assert((await exportJSON()).models[0].assigned<scoped.models[0].assigned);
  await page.click('[data-view="operations"]');assert(await page.locator('#kpi-controls').isHidden());assert((await exportJSON()).records.length>0);
  await page.click('[data-cohort="historical"]');assert.equal((await exportJSON()).models.length,10);
  await page.click('[data-cohort="all"]');assert.equal((await exportJSON()).models.length,28);
  await page.click('[data-cohort="qualified"]');assert(await page.locator('#download-json').isDisabled());
  await page.goto(url,{waitUntil:'networkidle'});await page.locator('#workspace').evaluate(el=>el.scrollIntoView({block:'start'}));await page.screenshot({path:path.join(output,'descriptive-desktop.png')});
  for(const width of [320,375,768,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'page overflow '+width);if(width===375){await page.locator('#workspace').evaluate(el=>el.scrollIntoView({block:'start'}));await page.screenshot({path:path.join(output,'descriptive-mobile.png')});}}
  await page.route('**/model-origins.json',route=>route.abort());await page.goto(url,{waitUntil:'networkidle'});await page.waitForSelector('#model-table');assert.equal((await rows()).length,18);
  await page.selectOption('#kpi-columns','all');assert((await page.locator('#model-table').innerText()).includes('Unavailable'));
  assert.deepEqual(errors,[]);
  const report={status:'passed',origin,models:18,checks:['numeric ranks absent in UI and exports','alphabetical default and stale rank URL handling','fixed denominator and conditional agreement','missing classifications separate','country filters and provenance','five KPI sorts both directions','CSV and JSON','semantic filters and sensitivity','comparison selection','operations and cohort separation','reviewer panels and badge absent','metadata outage','320/375/768/1440 responsive'],screenshots:['descriptive-desktop.png','descriptive-mobile.png']};
  fs.writeFileSync(path.join(output,'descriptive-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));await browser.close();
})().catch(error=>{console.error(error);process.exit(1)});

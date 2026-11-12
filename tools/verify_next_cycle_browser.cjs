/* Local browser regression check; no model calls or publication. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../web');
const output = process.env.PALO_SCREENSHOT_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'palo-next-cycle-ui-'));
const data = JSON.parse(fs.readFileSync(path.join(root, 'downloads/blueprintbench/next-cycle-results.json'), 'utf8'));
const server = http.createServer((req, res) => {
  const name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const target = path.resolve(root, '.' + name);
  if (!target.startsWith(root + path.sep) || !fs.existsSync(target) || !fs.statSync(target).isFile()) { res.writeHead(404).end(); return; }
  const types = {'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.png':'image/png','.webp':'image/webp'};
  res.setHeader('Content-Type', types[path.extname(target)] || 'application/octet-stream');
  res.end(fs.readFileSync(target));
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = process.env.PALO_SITE_URL || `http://127.0.0.1:${server.address().port}`;
  const url = origin + '/PALO_BlueprintBench_NextCycle.html';
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
  const errors = [];
  page.on('pageerror', e=>errors.push(e.message));
  try {
    await page.goto(url,{waitUntil:'networkidle'});
    await page.waitForSelector('.source-case');
    assert.equal(await page.locator('.source-case').count(),6);
    assert.equal(await page.locator('.probe').count(),48);
    assert.equal(await page.locator('#integrity code').first().textContent(),data.case_bank_sha256);
    const graph = await page.locator('#next-cycle-schema').evaluate(el=>JSON.parse(el.textContent));
    assert.deepEqual(graph['@graph'].map(x=>x['@type']),['WebPage','Dataset']);
    assert.equal(graph['@graph'][0].version,'2026-11-11.6');
    assert.equal(graph['@graph'][1].version,data.revision);
    for(const node of graph['@graph']) {assert(!('aggregateRating' in node));assert(!('review' in node));assert(!('ratingValue' in node));}
    assert.equal(graph['@graph'][1].distribution[0].contentUrl,'https://paloframework.org/downloads/blueprintbench/next-cycle-results.json');
    assert((await page.locator('body').innerText()).includes('independent semantic accuracy'));
    assert(!(await page.locator('body').innerText()).includes('\u2014'));
    assert.deepEqual(data.legacy_identity_map.items,[{review_item:'ITEM-A',original_probe_id:'P002'},{review_item:'ITEM-B',original_probe_id:'P013'},{review_item:'ITEM-C',original_probe_id:'P036'}]);
    assert(!JSON.stringify(data.legacy_identity_map).includes('expected_label'));
    if(data.postrun_semantic_observations) {
      assert.equal(await page.locator('.semantic-note[data-probe="bank-change-P07"]').count(),1);
      const note=await page.locator('.semantic-note[data-probe="bank-change-P07"]').innerText();
      assert(note.includes('Both a specification reading and a descriptive reading are defensible'));
      assert(note.includes('No retroactive scoring exclusion'));
      assert((await page.locator('#review-timing').innerText()).includes('Before inference: policy-transition-P05'));
      assert((await page.locator('#review-timing').innerText()).includes('After observing a response: bank-change-P07'));
    }
    if(data.counterfactual_advisory) {
      const note=await page.locator('#metamorphic-advisory').innerText();
      assert(note.includes('15 of 18 proposed relation pairs'));assert(note.includes('3 deviations remain counted'));
      assert(note.includes('not adjudicated model errors'));assert(note.includes('not a strict single-variable full-prompt experiment'));
      assert(note.includes('no majority vote supplies gold'));
    }
    const a = data.analysis;
    if (a) {
      assert.equal(await page.locator('#request-table tbody tr').count(),a.assigned_requests);
      assert.equal(await page.locator('#campaign-summary .stat strong').first().innerText(),String(a.assigned_requests));
      assert.equal(await page.locator('.case-bar').count(),6);
      const first = a.attempts.find(r=>r.track==='verification') || a.attempts[0];
      await page.selectOption('#case-filter',first.case_id);
      await page.selectOption('#model-filter',first.model);
      await page.selectOption('#track-filter',first.track);
      const selected = a.attempts.filter(r=>r.case_id===first.case_id&&r.model===first.model&&r.track===first.track);
      assert.equal(await page.locator('#request-table tbody tr').count(),selected.length);
      await page.locator('[data-inspect]').first().click();
      assert(await page.locator('#request-detail').isVisible());
      assert((await page.locator('#request-detail').innerText()).includes(first.model));
      assert.equal(await page.locator('#request-detail pre').count(),1);
      for(const key of ['prompt_tokens','completion_tokens','total_tokens','reasoning_tokens','cached_tokens','cache_write_tokens']) {assert.equal(await page.locator(`[data-usage="${key}"]`).innerText(),Number.isFinite(first[key])?first[key].toLocaleString('en-GB'):'Not recorded');}
      assert((await page.locator('#request-detail').innerText()).includes('not observed usage or tested context capacity'));
      if(first.returned_provider) assert((await page.locator('#request-detail').innerText()).includes(first.returned_provider));
      await page.locator('#close-detail').click();
      const wait = page.waitForEvent('download');await page.click('#export-json');
      const downloaded = await wait;
      const exported = JSON.parse(fs.readFileSync(await downloaded.path(),'utf8'));
      assert.equal(exported.qualified,false);assert.equal(exported.filters.model,first.model);assert.equal(exported.attempts.length,selected.length);
      const csvWait = page.waitForEvent('download');await page.click('#export-csv');
      const csv = fs.readFileSync(await (await csvWait).path(),'utf8');
      assert(csv.startsWith('revision,status,qualified,model,'));assert(csv.includes('cost_status'));assert(csv.includes('prompt_tokens,completion_tokens,total_tokens,reasoning_tokens,cached_tokens,cache_write_tokens,usage_status'));
      const measured=graph['@graph'][1].variableMeasured.map(x=>x.propertyID);
      for(const key of ['prompt_tokens','completion_tokens','total_tokens','reasoning_tokens','cached_tokens','cache_write_tokens']) {assert.equal(measured.includes(key),a.attempts.some(row=>row[key]!==null&&row[key]!==undefined));}
      await page.click('#reset');
      await page.selectOption('#track-filter','legacy');
      assert.equal(await page.locator('#request-table tbody tr').count(),a.attempts.filter(r=>r.track==='legacy').length);
      assert.equal(await page.locator('#legacy-results tbody tr').count(),a.attempts.filter(r=>r.track==='legacy').length);
      assert((await page.locator('#request-table').innerText()).includes('Not scored'));
      for(const row of a.attempts.filter(r=>r.track==='legacy'&&r.judgments?.length)) {
        for(const judgment of row.judgments) {const item=data.legacy_identity_map.items.find(x=>x.review_item===judgment.id);assert((await page.locator('#legacy-results').innerText()).includes(`${item.review_item} → ${item.original_probe_id}`));}
      }
      assert.equal(data.protocol.reasoning_effort,'high');assert.equal(data.protocol.max_output_tokens,32768);
      await page.click('#reset');
    } else {
      assert(await page.locator('#export-json').isDisabled());
      assert((await page.locator('#load-state').innerText()).includes('No execution outcomes'));
      assert.equal(await page.locator('#campaign-summary .stat').count(),0);
    }
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(output,'next-cycle-desktop.png')});
    await page.locator('#workspace').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(output,'next-cycle-explorer.png')});
    if(data.counterfactual_advisory) {await page.locator('#metamorphic-advisory').screenshot({path:path.join(output,'next-cycle-counterfactual-advisory.png')});}
    if(data.analysis) {await page.locator('#legacy').screenshot({path:path.join(output,'next-cycle-legacy-advisory.png')});}
    for(const width of [320,375,768,1440]) {
      await page.setViewportSize({width,height:900});
      const size = await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));
      assert(size.scroll<=size.client+1,`Page overflows at ${width}: ${JSON.stringify(size)}`);
    }
    await page.setViewportSize({width:375,height:900});await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(output,'next-cycle-mobile.png')});
    // A rendering-only malicious-text fixture never enters the campaign/export build.
    const fixture = structuredClone(data);
    fixture.case_bank.cases[0].title='<img src=x onerror="window.injected=true">';
    fixture.analysis=null;fixture.budget=null;
    await page.route('**/downloads/blueprintbench/next-cycle-results.json',route=>route.fulfill({json:fixture}));
    await page.reload({waitUntil:'networkidle'});
    assert.equal(await page.evaluate(()=>window.injected),undefined);
    assert.equal(await page.locator('.source-case img').count(),0);
    assert(await page.locator('#export-json').isDisabled());
    await page.unroute('**/downloads/blueprintbench/next-cycle-results.json');
    await page.route('**/downloads/blueprintbench/next-cycle-results.json',route=>route.fulfill({status:503,body:'Unavailable'}));
    await page.reload({waitUntil:'networkidle'});
    assert((await page.locator('#load-state').innerText()).includes('No counts or costs are inferred'));
    assert.equal(errors.length,0,errors.join('\n'));
    const result={status:'passed',revision:data.revision,observed_snapshot:!!data.analysis,assigned_requests:data.analysis?.assigned_requests??null,checks:['source scope','JSON-LD boundary and revision','hash display','filters and exports when observed','exact input inspection when observed','legacy unscored','320/375/768/1440 layouts','pending state','unavailable state','untrusted text escaping'],screenshots:output};
    fs.writeFileSync(path.join(output,'verification.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result));
  } finally {await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});

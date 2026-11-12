/* Real-document publication UI check; no provider calls or evidence mutations. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http'),os=require('node:os');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'../web'),output=process.env.PALO_SCREENSHOT_DIR||fs.mkdtempSync(path.join(os.tmpdir(),'blueprintbench-generation-'));
const filename='PALO_BlueprintBench_Generation.html';
const snapshot=JSON.parse(fs.readFileSync(path.join(root,'downloads/blueprintbench/generation-results.json'),'utf8'));
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}const mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.png':'image/png','.webp':'image/webp'};res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const origin=process.env.PALO_SITE_URL||`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch();const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});const errors=[];page.on('pageerror',e=>errors.push(e.message));fs.mkdirSync(output,{recursive:true});
 try{
  // Pin the exact retained data snapshot for the duration of this UI regression.
  await page.route('**/downloads/blueprintbench/generation-results.json',route=>route.fulfill({json:snapshot}));
  await page.goto(origin+'/'+filename,{waitUntil:'networkidle'});await page.waitForSelector('#run-table tr');
  assert.deepEqual(await page.locator('.bench-site-header nav a').allTextContents(),['Overview','3-text synthetic test','6-process synthetic test','Real-document generation','Corpus','Method']);
  assert.equal(await page.locator('#run-table tr').count(),snapshot.analysis.summary.assigned_calls);assert.equal(await page.locator('#document-cards article').count(),3);assert.equal(await page.locator('#configuration-cards article').count(),snapshot.models.length);
  assert.equal(await page.locator('.gen-chart-row').count(),snapshot.models.length);
  const chartBefore=await page.locator('#generation-chart').innerHTML();
  const first=snapshot.analysis.rows.find(r=>r.state==='completed')||snapshot.analysis.rows[0];
  await page.selectOption('#document-filter',first.task_id);assert.equal(await page.locator('#run-table tr').count(),snapshot.models.length*3);
  await page.selectOption('#model-filter',first.configuration_id||first.model);assert.equal(await page.locator('#run-table tr').count(),3);
  await page.selectOption('#repetition-filter',String(first.repetition));assert.equal(await page.locator('#run-table tr').count(),1);
  assert.equal(await page.locator('#generation-chart').innerHTML(),chartBefore,'Chart must retain full-study denominator');
  const jsonWait=page.waitForEvent('download');await page.click('#export-json');const json=JSON.parse(fs.readFileSync(await(await jsonWait).path(),'utf8'));assert.equal(json.rows.length,1);assert.equal(json.rows[0].id,first.id);assert.equal(json.filters.document,first.task_id);assert(json.evidence_status.includes('no independent validation'));assert.equal(json.fixed_study_summary.assigned_calls,snapshot.analysis.summary.assigned_calls);
  const csvWait=page.waitForEvent('download');await page.click('#export-csv');const csv=fs.readFileSync(await(await csvWait).path(),'utf8');assert(csv.includes('"cost_status"'));assert(csv.includes('"upstream_statuses","collection_failure","cost_zero_reason","native_usage_available"'));assert(csv.includes('"revision","evidence_status","qualified","selected_document","selected_model","selected_repetition","selected_order"'));assert(csv.includes(snapshot.evidence_status));assert(csv.includes(first.id));assert(csv.includes('"OpenRouter MCP"'));
  await page.locator('[data-run]').click();assert((await page.locator('#run-detail').innerText()).includes('Serving provider'));assert((await page.locator('#run-detail').innerText()).includes(first.returned_model||'not observed'));
  if(first.blueprint){const wait=page.waitForEvent('download');await page.click('#export-blueprint');const artifact=JSON.parse(fs.readFileSync(await(await wait).path(),'utf8'));assert.deepEqual(artifact,first.blueprint);assert.equal(artifact.qualified,false);assert.equal(artifact.business_approved,false);assert.equal(artifact.business_approval_required,true);await page.locator('#run-detail details summary').first().click();assert((await page.locator('#run-detail pre').first().innerText()).includes('requirements'));}
  if(first.raw_output!==null&&first.raw_output!==undefined){assert.equal(await page.locator('#raw-model-answer').textContent(),first.raw_output);assert.equal(await page.locator('.gen-raw-response').getAttribute('open'),null);}
  await page.locator('#run-detail').screenshot({path:path.join(output,'generation-inspector.png')});
  for(const id of ['document-filter','model-filter','repetition-filter'])await page.selectOption('#'+id,'all');
  assert.equal(await page.locator('#run-detail').innerText(),'');
  const googleConfigs=snapshot.models.filter(m=>m.model_id?.startsWith('google/'));
  for(const config of googleConfigs){await page.selectOption('#model-filter',config.id);assert.equal(await page.locator('#run-table tr').count(),9);const wait=page.waitForEvent('download');await page.click('#export-json');const selected=JSON.parse(fs.readFileSync(await(await wait).path(),'utf8'));assert(selected.rows.every(r=>r.configuration_id===config.id));assert.equal(selected.rows.length,9);}
  await page.selectOption('#model-filter','all');
  const incomplete=snapshot.analysis.rows.find(r=>!r.structural_valid&&typeof r.raw_output==='string');
  if(incomplete){await page.locator(`[data-run="${incomplete.id}"]`).click();assert.equal(await page.locator('#raw-model-answer').textContent(),incomplete.raw_output);assert((await page.locator('#run-detail').textContent()).includes('No repair'));}
  for(const order of ['cost','duration','matches','identity']){await page.selectOption('#order-filter',order);assert.equal(await page.locator('#run-table tr').count(),snapshot.analysis.summary.assigned_calls);}
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(output,'generation-desktop.png')});
  const layout=[];
  for(const width of [320,375,768,1440]){await page.setViewportSize({width,height:1000});const result=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('main *')].filter(el=>{const r=el.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&!el.closest('.table-scroll')}).slice(0,12).map(el=>({tag:el.tagName,id:el.id,class:el.className,right:el.getBoundingClientRect().right}))}));layout.push(result);}
  fs.writeFileSync(path.join(output,'layout.json'),JSON.stringify(layout,null,2)+'\n');
  await page.setViewportSize({width:375,height:1000});await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(output,'generation-mobile.png')});
  // Rendering fixture only: no published record or exported evidence is rewritten.
  const malicious=structuredClone(snapshot);malicious.models[0].name='<img src=x onerror="window.injected=true">';malicious.sources[0].title='<svg onload="window.injected=true">';
  const row=malicious.analysis.rows.find(r=>r.blueprint);if(row){row.blueprint.content.review_probe='<img src=x onerror="window.injected=true">';row.raw_output='<img src=x onerror="window.injected=true"><script>window.injected=true</script>';}
  await page.unroute('**/downloads/blueprintbench/generation-results.json');await page.route('**/downloads/blueprintbench/generation-results.json',route=>route.fulfill({json:malicious}));await page.reload({waitUntil:'networkidle'});
  assert.equal(await page.evaluate(()=>window.injected),undefined);assert.equal(await page.locator('#run-table img,#document-cards svg,#configuration-cards img').count(),0);
  if(row){await page.locator(`[data-run="${row.id}"]`).click();assert.equal(await page.locator('#run-detail img').count(),0);assert.equal(await page.locator('#raw-model-answer').textContent(),row.raw_output);assert.equal(await page.evaluate(()=>window.injected),undefined);}
  // Explicit upstream-failure rendering fixture; no retained analysis is modified.
  const failure=structuredClone(snapshot),failed=failure.analysis.rows.find(r=>r.state==='incomplete')||failure.analysis.rows[0];
  Object.assign(failed,{collection_failure:'Upstream error 502; incomplete capture',upstream_statuses:[502],native_usage_available:false,cost_usd:0,cost_zero_reason:'Provider accounting reports a zero charge for the upstream error; this is not a successful zero-cost generation.',usage:{native_prompt_tokens:0,native_completion_tokens:0,native_reasoning_tokens:0,native_cached_tokens:0},issues:['JSON parse failed for incomplete capture']});
  await page.unroute('**/downloads/blueprintbench/generation-results.json');await page.route('**/downloads/blueprintbench/generation-results.json',route=>route.fulfill({json:failure}));await page.reload({waitUntil:'networkidle'});
  const failedRow=page.locator(`[data-run="${failed.id}"]`).locator('..').locator('..');assert((await failedRow.innerText()).includes('Upstream error 502; incomplete capture'));assert((await failedRow.innerText()).includes('N/A / N/A'));assert((await failedRow.innerText()).includes('zero charge'));
  await page.locator(`[data-run="${failed.id}"]`).click();assert((await page.locator('#run-detail').innerText()).includes('cannot establish a model error'));assert((await page.locator('#run-detail').innerText()).includes('Native provider prompt / completion: N/A / N/A'));assert((await page.locator('#run-detail').textContent()).includes('Capture processing diagnostics'));assert(!(await page.locator('#run-detail').innerText()).includes('Contract or provenance issues'));
  await page.unroute('**/downloads/blueprintbench/generation-results.json');await page.route('**/downloads/blueprintbench/generation-results.json',route=>route.fulfill({status:503,body:'Unavailable'}));await page.reload({waitUntil:'networkidle'});assert((await page.locator('#selection-summary').innerText()).includes('Results could not be loaded'));assert((await page.locator('#generation-chart').innerText()).includes('no values have been substituted'));assert.equal(await page.locator('#run-table tr').count(),0);assert(await page.locator('#export-json').isDisabled());assert(await page.locator('#export-csv').isDisabled());
  assert.deepEqual(errors,[]);
  const receipt={status:layout.some(x=>x.scroll>x.width+1)?'failed_responsive_layout':'passed',assigned_calls:snapshot.analysis.summary.assigned_calls,serving_configurations:snapshot.models.length,completed_in_snapshot:snapshot.analysis.summary.completed_calls,filters_exports_blueprint:'passed',xss_text_fixture:'passed',unavailable_state:'passed',layout,screenshots:output,js_errors:errors};fs.writeFileSync(path.join(output,'verification.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));assert.equal(receipt.status,'passed');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});

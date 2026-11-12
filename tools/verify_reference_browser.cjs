const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const origin=process.env.PALO_SITE_URL||'http://127.0.0.1:53836';
const output=process.env.PALO_SCREENSHOT_DIR||'/tmp/palo-reference-check';
fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch();
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.goto(origin+'/PALO_BlueprintBench_Method.html',{waitUntil:'networkidle'});
 const data=await(await page.request.get(origin+'/downloads/blueprintbench/benchmark-references.json')).json();
 assert.equal(data.entries.length,35);
 assert.equal(data.entries.filter(r=>r.review_group==='visibility-expansion-20261111').length,15);
 const section=page.locator('#references');
 assert.equal(await section.locator('[data-reference]').count(),35);
 await section.locator('summary').filter({hasText:'Explore 15'}).click();
 assert.equal(await section.locator('[data-reference]:visible').count(),15);
 for(const row of data.entries.filter(r=>r.review_group==='visibility-expansion-20261111')){
  const element=section.locator('[data-reference="'+row.id+'"]');
  assert((await element.innerText()).includes(row.version_scope));
  assert((await element.innerText()).includes(row.palo_transfer));
 }
 const graph=JSON.parse(await page.locator('script[type="application/ld+json"]').textContent())['@graph'];
 const ref=graph.find(n=>n['@id'].endsWith('#benchmark-reference-review'));
 assert.equal(ref.citation.length,35);assert(ref.description.includes('35 methodological references'));
 const csv=await(await page.request.get(origin+'/downloads/blueprintbench/benchmark-references.csv')).text();
 assert.equal(csv.trim().split('\n').length,36);assert(csv.includes('visibility_sources'));
 assert.equal(await page.locator('a[href$=".md"]:not([href*="github.com"])').count(),0);
 for(const width of [375,768,1440]){
  await page.setViewportSize({width,height:1000});await section.locator('table').first().evaluate(el=>el.scrollIntoView({block:'start'}));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'document overflow '+width);
  await page.screenshot({path:output+'/references-'+width+'.png'});
 }
 assert.deepEqual(errors,[]);await browser.close();
 const receipt={status:'passed',origin,references:35,added:15,schema_citations:35,csv_records:35,widths:[375,768,1440],no_direct_markdown_links:true,js_errors:errors};
 fs.writeFileSync(output+'/reference-browser-verification.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
})().catch(error=>{console.error(error);process.exit(1)});

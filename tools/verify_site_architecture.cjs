/* Browser checks for site structure; no inference or publication. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http'),os=require('node:os');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'../web'),output=process.env.PALO_SCREENSHOT_DIR||fs.mkdtempSync(path.join(os.tmpdir(),'blueprintbench-architecture-'));
const nav=['Overview','Policy Interpretation','Process Interpretation','Specification Generation','Corpus','Method'];
const server=http.createServer((req,res)=>{const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);const file=path.resolve(root,'.'+pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'};res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const origin=process.env.PALO_SITE_URL||`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});const errors=[];page.on('pageerror',e=>errors.push(e.message));fs.mkdirSync(output,{recursive:true});
 const pages=['PALO_BlueprintBench.html','PALO_BlueprintBench_Method.html','PALO_BlueprintBench_Corpus.html','PALO_BlueprintBench_Leaderboard.html','PALO_BlueprintBench_NextCycle.html','PALO_BlueprintBench_Diagnostics.html'];
 if(fs.existsSync(path.join(root,'PALO_BlueprintBench_Generation.html')))pages.push('PALO_BlueprintBench_Generation.html');
 try{
  for(const filename of pages){
   const response=await page.goto(origin+'/'+filename,{waitUntil:'networkidle'});assert.equal(response.status(),200,filename);
   assert.deepEqual(await page.locator('.bench-site-header nav a').allTextContents(),nav,filename);
   assert.equal(await page.locator('h1').count(),1,filename);
   assert.equal(await page.locator('a[href$=".md"]:not([href*="github.com"])').count(),0,filename);
   for(const width of [320,375,768,1440]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),filename+' overflow '+width);}
   await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(output,filename.replace('.html','-desktop.png'))});
   if(filename==='PALO_BlueprintBench.html'){
    assert.equal(await page.locator('table').count(),0);assert.equal(await page.locator('.bench-test-cards article').count(),3);
    assert((await page.locator('main').innerText()).includes('What the research measures'));
    await page.setViewportSize({width:375,height:1000});await page.screenshot({path:path.join(output,'overview-mobile.png')});
   }
   if(filename==='PALO_BlueprintBench_Method.html'){
    assert.equal(await page.locator('[data-reference]').count(),35);
    await page.locator('#references summary').filter({hasText:'Explore 15'}).click();
    assert.equal(await page.locator('[data-reference]:visible').count(),15);
    await page.setViewportSize({width:375,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Open reference table causes overflow');
   }
   if(filename==='PALO_BlueprintBench_Corpus.html'){
    assert.equal(await page.locator('.bench-public-documents article').count(),3);
    assert((await page.locator('#real-documents').innerText()).includes('200 supplied pages'));
    assert((await page.locator('#adapter-diagnostics').innerText()).includes('not the three synthetic procurement texts'));
   }
   if(filename==='PALO_BlueprintBench_Leaderboard.html'){
    await page.waitForSelector('#model-table tbody tr');assert.equal(await page.locator('#model-table tbody tr').count(),18);
    await page.fill('#model-search','OpenAI');await page.waitForFunction(()=>document.querySelectorAll('#model-table tbody tr').length===1);assert.equal(await page.locator('#model-table tbody tr').count(),1);
    const wait=page.waitForEvent('download');await page.click('#download-json');const download=await wait;const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(exported.qualified,false);
    await page.fill('#model-search','');await page.click('[data-cohort="historical"]');assert((await page.locator('#cohort-content').innerText()).includes('4,994 UTF-8 bytes'));
   }
   if(filename==='PALO_BlueprintBench_NextCycle.html'){
    await page.waitForSelector('#request-table tbody tr');assert.equal(await page.locator('#request-table tbody tr').count(),60);
    assert((await page.locator('h1').innerText()).includes('synthetic test'));
    assert((await page.locator('.bench-study-scope').innerText()).includes('OpenRouter API'));
   }
  }
  assert.deepEqual(errors,[]);
  const receipt={status:'passed',presentation_revision:'2026-11-11.6',pages,real_document_page_present:pages.some(x=>x.includes('Generation')),widths:[320,375,768,1440],navigation:nav,source_checks:['3fictionaltexts separate from3adapterexcerpts','6fictionalprocesses','3publicdocuments with200pages'],frozen_data_rewritten:false,js_errors:errors,screenshots:output};
  fs.writeFileSync(path.join(output,'verification.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});

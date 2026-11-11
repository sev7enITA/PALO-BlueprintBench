/* Optional browser regression check. Requires Playwright; no inference calls. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const origin = process.env.PALO_SITE_URL || 'http://127.0.0.1:58192';
const output = process.env.PALO_SCREENSHOT_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'palo-ui-'));

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const data = await (await page.request.get(origin + '/downloads/blueprintbench/leaderboard-data.json')).json();
  const count = data.internal.models.length + data.historical.models.length;
  const ids = new Set([...data.internal.models.map(m => m.id), ...data.historical.models.map(m => m.model)]);
  assert(ids.size >= 15);
  const url = origin + '/PALO_BlueprintBench_Leaderboard.html';
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForSelector('#model-table');
  assert.equal(await page.locator('#model-table tbody tr').count(), data.internal.models.length);
  await page.screenshot({ path: path.join(output, 'leaderboard-internal-desktop.png') });
  await page.click('[data-cohort="all"]');
  await page.waitForSelector('#catalogue-table');
  assert.equal(await page.locator('#catalogue-table tbody tr').count(), count);
  assert.equal(await page.locator('#stat-models').innerText(), String(ids.size));
  assert.equal(await page.locator('#stat-configurations').innerText(), String(count));
  assert.equal(await page.evaluate(() => getComputedStyle(document.body).backgroundColor), 'rgb(8, 15, 28)');
  assert.equal(await page.locator('.hero .research-status').count(), 0);
  assert.equal(await page.locator('#limitations .research-status').count(), 1);
  const firstRow = await page.locator('#catalogue-table tbody tr').first().boundingBox();
  assert(firstRow.y > 0, 'Model table must be rendered');
  await page.locator('#workspace').scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(output, 'leaderboard-desktop.png') });
  for (const cohort of ['internal', 'historical']) {
    await page.locator(`[data-inspect="nex-agi/nex-n2.6"][data-inspect-cohort="${cohort}"]`).click();
    assert((await page.locator('#dialog-content').innerText()).includes(cohort === 'internal' ? 'Configuration details' : 'Historical configuration'));
    await page.keyboard.press('Escape');
  }
  await page.click('[data-cohort="internal"]');
  const metric = (id, key) => {
    const m = data.internal.models.find(x => x.id === id);
    if (key === 'matches') return m.verification_correct;
    if (key === 'disagreements') return m.verification_classified - m.verification_correct;
    if (key === 'missing') return m.verification_missing;
    if (key === 'calls') return m.completed_calls;
    if (key === 'cost') return m.unknown_cost_calls || m.not_run ? null : m.provider_reported_cost_usd;
    if (key === 'time') return m.latency_median_seconds;
  };
  for (const key of ['matches', 'disagreements', 'missing', 'calls', 'cost', 'time']) {
    for (const direction of ['asc', 'desc']) {
      await page.locator(`[data-sort="${key}"]`).click();
      const state = await page.locator(`[data-sort="${key}"]`).locator('..').getAttribute('aria-sort');
      assert.equal(state, direction === 'asc' ? 'ascending' : 'descending');
      const order = await page.locator('#model-table tbody tr').evaluateAll(rows => rows.map(r => r.dataset.model));
      const values = order.map(id => metric(id, key));
      let unavailable = false, previous = null;
      for (const value of values) {
        if (value == null) { unavailable = true; continue; }
        assert(!unavailable, `${key}: unavailable observations must remain last`);
        if (previous != null) assert(direction === 'asc' ? previous <= value : previous >= value, key);
        previous = value;
      }
    }
  }
  await page.check('#missing-only');
  const expectedMissing = data.internal.models.filter(m => m.verification_missing > 0 || m.completed_calls < m.assigned_calls).length;
  assert.equal(await page.locator('#model-table tbody tr').count(), expectedMissing);
  await page.click('#reset-filters');
  await page.selectOption('#minimum-matches', '100');
  assert.equal(await page.locator('#model-table tbody tr').count(), data.internal.models.filter(m => m.verification_correct === 324).length);
  await page.reload({ waitUntil: 'networkidle' });
  assert.equal(await page.inputValue('#minimum-matches'), '100');
  await page.click('#reset-filters');
  await page.locator('[data-compare]').first().check();
  await page.check('#selected-only');
  assert.equal(await page.locator('#model-table tbody tr').count(), 1);
  await page.click('#clear-comparison');
  assert.equal(await page.locator('#model-table tbody tr').count(), data.internal.models.length);
  await page.goto(url + '?cohort=internal&q=inference-net%2Fschematron-v2-turbo', { waitUntil: 'networkidle' });
  await page.locator('.model-button').click();
  assert((await page.locator('#dialog-content').innerText()).includes('8,192 tokens'));
  const challenge = new URL(await page.locator('.challenge-section a').getAttribute('href'));
  assert.equal(challenge.pathname, '/sev7enITA/PALO-BlueprintBench/issues/new');
  assert(challenge.searchParams.get('body').includes('inference-net/schematron-v2-turbo'));
  assert(challenge.searchParams.get('body').includes('Evidence cohort: internal'));
  assert(challenge.searchParams.get('body').includes('independent validation'));
  assert((await page.locator('#dialog-content').innerText()).includes('omitted; no reasoning control sent'));
  await page.keyboard.press('Escape');
  await page.goto(url + '?cohort=internal&q=sakana%2Ffugu-max', { waitUntil: 'networkidle' });
  assert((await page.locator('#model-table').innerText()).includes('Pre-call blocked'));
  assert((await page.locator('#model-table').innerText()).includes('N/A'));
  await page.goto(url + '?cohort=internal&sort=cost&direction=desc', { waitUntil: 'networkidle' });
  const downloading = page.waitForEvent('download');
  await page.click('#download-csv');
  const download = await downloading;
  const csv = fs.readFileSync(await download.path(), 'utf8');
  assert(csv.includes('"sort_by"') && csv.includes('"sort_direction"'));
  assert(csv.includes('"cost","desc"'));
  assert(csv.includes('"false"'));
  await page.click('[data-cohort="qualified"]');
  assert.equal(await page.locator('.gates li').count(), 4);
  assert.equal(await page.locator('#model-table').count(), 0);
  await page.goto(url, { waitUntil: 'networkidle' });
  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Leaderboard overflow ${width}`);
    if (width === 390) await page.screenshot({ path: path.join(output, 'leaderboard-mobile.png') });
  }
  await page.goto(origin + '/PALO_BlueprintBench.html', { waitUntil: 'networkidle' });
  await page.waitForSelector('#shared-models tr');
  assert.equal(await page.locator('#shared-models tr').count(), count);
  assert.equal(await page.locator('#internal-cards tbody tr').count(), data.internal.models.length);
  assert.equal(await page.locator('#overview-model-count').innerText(), String(ids.size));
  assert.equal(await page.locator('#overview-complete-count').innerText(), String(data.internal.completed_calls));
  await page.screenshot({path:path.join(output,'overview-desktop.png')});
  assert.equal(await page.locator('a[href*="presentation"]').count(),0);
  assert.equal(await page.locator('a[href$=".md"]:not([href*="github.com"])').count(),0);
  await page.selectOption('#catalogue-cohort', 'historical');
  assert.equal(await page.locator('#shared-models tr').count(), data.historical.models.length);
  await page.fill('#catalogue-search', 'Sakana');
  assert.equal(await page.locator('#shared-models tr').count(), 1);
  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Overview overflow ${width}`);
    if(width===390) await page.screenshot({path:path.join(output,'overview-mobile.png')});
  }
  assert.deepEqual(errors, []);
  const result = { status: 'passed', origin, distinct_models: ids.size, configuration_rows: count, checks: ['same catalogue across pages', 'dark PALO palette', 'limitations relocation', 'model visibility', 'cohort-specific dialogs', 'six metric sorts both directions', 'unknown values last', 'numeric and status filters', 'selection', 'URL restore', 'CSV sort and qualification', 'actual output cap', 'pre-call compatibility disclosure', 'empty qualified layer', 'responsive widths'], screenshots: ['leaderboard-desktop.png', 'leaderboard-mobile.png'] };
  fs.writeFileSync(path.join(output, 'browser-verification.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result));
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });

/**
 * Playwright probe script
 * - Navigates to a URL, captures title and screenshot
 * - Samples up to 100 links and performs HEAD checks
 *
 * Usage (Linux/macOS):
 *   npm init -y
 *   npm install playwright
 *   npx playwright install
 *   TARGET_URL=https://example.com node .github/hooks/playwright_probe.js
 *
 * Usage (Windows PowerShell):
 *   npm init -y
 *   npm install playwright
 *   npx playwright install
 *   $env:TARGET_URL='https://example.com'; node .github/hooks/playwright_probe.js
 */

const { chromium } = require('playwright');

const TARGET_URL = process.argv[2] || process.env.TARGET_URL;
if (!TARGET_URL) {
  console.error('Usage: node .github/hooks/playwright_probe.js <URL>');
  process.exit(2);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`Navigating to ${TARGET_URL} ...`);
    await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 30000 });

    const title = await page.title();
    console.log('Title:', title);

    const screenshotPath = 'playwright_probe_screenshot.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('Saved screenshot:', screenshotPath);

    const hrefs = await page.$$eval('a[href]', (els) => Array.from(els.map(e => e.href)).filter(Boolean));
    console.log('Found links:', hrefs.length);

    const limit = 100;
    const sample = hrefs.slice(0, limit);
    const results = [];

    for (const href of sample) {
      try {
        const res = await context.request.head(href, { timeout: 10000 });
        results.push({ url: href, status: res.status() });
      } catch (err) {
        results.push({ url: href, error: String(err) });
      }
    }

    console.log(`Link check (first ${sample.length} links):`);
    results.forEach(r => console.log(JSON.stringify(r)));
  } catch (err) {
    console.error('Probe error:', err && err.message ? err.message : err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();

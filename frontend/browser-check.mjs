import { chromium, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const output = path.resolve('../artifacts');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge', headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
page.on('console', (message) => { if (message.type() === 'error') console.log('Browser console:', message.text()); });
try {
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /Every landscape/ })).toBeVisible();
  await expect(page.getByText('Local service connected', { exact: true })).toBeVisible();
  await page.screenshot({ path: path.join(output, 'national-overview.png'), fullPage: true });
  await page.getByRole('button', { name: 'New assessment', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Let’s understand your land.' })).toBeVisible();
  await page.getByText('Use latitude & longitude', { exact: true }).click();
  await page.getByRole('textbox', { name: 'Latitude', exact: true }).fill('-26.22');
  await page.getByRole('textbox', { name: 'Longitude', exact: true }).fill('28.02');
  await page.getByRole('button', { name: 'Go to coordinates' }).click();
  await expect(page.getByRole('button', { name: 'Use 1 km² at map centre' })).toBeVisible({ timeout: 30000 });
  const canvasHeight = await page.locator('.map-canvas').evaluate((element) => element.clientHeight);
  if (canvasHeight < 300) throw new Error(`Map has collapsed: ${canvasHeight}px high`);
  await page.waitForTimeout(1200);
  await page.getByRole('button', { name: 'Use 1 km² at map centre' }).click();
  await page.getByRole('textbox', { name: 'Assessment name' }).fill('Browser workflow verification');
  await page.getByRole('button', { name: 'Start assessment' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'The assessment has not started yet' })).toBeVisible();
  await page.getByRole('checkbox', { name: /I have checked the map/ }).check();
  await expect(page.getByRole('button', { name: 'Start assessment' })).toBeEnabled();
  await page.getByRole('button', { name: 'Select a small plot on the map' }).click();
  await page.locator('.map-canvas').evaluate((element) => element.__assessmentMap.fire('click', { lngLat: { lat: -26.22, lng: 28.02 } }));
  await expect(page.getByRole('checkbox', { name: /I have checked the map/ })).not.toBeChecked();
  await page.getByRole('button', { name: 'Start assessment' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'The assessment has not started yet' })).toBeVisible();
  await page.getByRole('checkbox', { name: /I have checked the map/ }).check();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);
  await expect.poll(() => page.locator('.map-canvas').evaluate((element) =>
    element.__assessmentMap?.queryRenderedFeatures({layers:['boundary-line']}).length || 0),
    {timeout:15000, message:'The selected land must have a rendered dotted boundary'}).toBeGreaterThan(0);
  await page.screenshot({ path: path.join(output, 'national-assessment.png'), fullPage: true, animations: 'disabled' });
  // Changing location must invalidate the previous boundary and confirmation.
  await page.getByRole('textbox', { name: 'Latitude', exact: true }).fill('-33.9');
  await page.getByRole('textbox', { name: 'Longitude', exact: true }).fill('18.6');
  await page.getByRole('button', { name: 'Go to coordinates' }).click();
  await expect(page.getByRole('checkbox', { name: /I have checked the map/ })).toBeDisabled();
  await page.getByRole('button', { name: 'Start assessment' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'The assessment has not started yet' })).toBeVisible();
  await page.getByRole('button', { name: 'Assessment library', exact: true }).click();
  const records = await (await page.request.get('http://127.0.0.1:5173/api/assessments')).json();
  const ready = records.assessments.find((r) => ['complete', 'partial'].includes(r.status));
  if (ready) {
    const saved = await (await page.request.get(`http://127.0.0.1:5173/api/assessments/${ready.id}`)).json();
    await page.locator(`[data-assessment-id="${ready.id}"]`).click();
    await expect(page.getByRole('heading', { name: ready.name, exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Water, vegetation and the ground' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'What to investigate, and why' })).toBeVisible();
    if (saved.result?.overlay) await expect.poll(() => page.locator('.map-canvas').evaluate((element) => {
      const map=element.__assessmentMap;
      return map?.getLayer('boundary-line') ? map.queryRenderedFeatures({layers:['boundary-line']}).length : 0;
    }), {timeout:30000,message:'Saved report must render the confirmed site boundary'}).toBeGreaterThan(0);
    await expect.poll(() => page.locator('.map-canvas').evaluate((element) => {
      const map=element.__assessmentMap;
      return Boolean(map?.getSource('ndvi') && map.isSourceLoaded('ndvi'));
    }), {timeout:30000,message:'Dated satellite overlay must load on the saved report'}).toBe(true);
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(output, 'national-report.png'), fullPage: true });
    for (const name of ['History & change', 'Future outlook', 'Evidence & gaps']) {
      await page.getByRole('tab', { name, exact: true }).click();
      await expect(page.getByRole('tab', { name, exact: true })).toHaveAttribute('aria-selected', 'true');
      if (name === 'History & change') {
        await expect(page.getByRole('heading', { name: 'Current and previous owners' })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Places and stories around the site' })).toBeVisible();
      }
    }
    await expect(page.getByRole('heading', { name: 'What this assessment used' })).toBeVisible();
    const download = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Export evidence' }).click();
    const file = await download;
    if (!file.suggestedFilename().endsWith('.json')) throw new Error('Report download did not produce JSON');
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Every landscape/ })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  if (overflow) throw new Error('Mobile layout overflows horizontally');
  await page.screenshot({ path: path.join(output, 'national-mobile.png'), fullPage: true, animations: 'disabled' });
  if (errors.length) throw new Error(`Browser runtime errors: ${errors.join('; ')}`);
  console.log('PASS: desktop overview, map initialization, coordinates, boundary selection, confirmation invalidation, report tabs, JSON export, mobile navigation and no horizontal overflow.');
  console.log(`Screenshots: ${output}`);
} catch (error) {
  console.log('Runtime errors:', errors);
  console.log('Visible body:', (await page.locator('body').innerText()).slice(0, 3000));
  await page.screenshot({ path: path.join(output, 'browser-failure.png'), fullPage: true });
  throw error;
} finally {
  await browser.close();
}

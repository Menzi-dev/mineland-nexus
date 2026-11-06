import { chromium, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

// Documentation captures use an empty library or a labelled public engineering extent.
// They never display user-uploaded photographs or personal assessment records.
const output = path.resolve('../docs/images');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge', headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
try {
  await page.route('**/api/assessments', (route) => route.fulfill({json:{assessments:[]}}));
  await page.goto('http://127.0.0.1:5173/', {waitUntil:'networkidle'});
  await expect(page.getByRole('heading', {name:/Every landscape/})).toBeVisible();
  await page.screenshot({path:path.join(output,'overview.png')});
  await page.unroute('**/api/assessments');
  await page.reload({waitUntil:'networkidle'});
  const response = await page.request.get('http://127.0.0.1:8000/api/assessments');
  const source = (await response.json()).assessments.find((r) => r.name === 'National workflow verification (Johannesburg)' && ['partial','complete'].includes(r.status));
  if (!source) throw new Error('Run backend/check_workflow.py to create the public engineering-verification extent first.');
  await page.getByRole('button',{name:'Assessment library',exact:true}).click();
  await page.locator(`[data-assessment-id="${source.id}"]`).click();
  await expect(page.getByRole('heading',{name:'Water, vegetation and the ground'})).toBeVisible();
  await page.screenshot({path:path.join(output,'report.png')});
  console.log('Saved documentation screenshots using an empty workspace and a public verification report.');
} finally { await browser.close(); }

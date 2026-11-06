import { chromium, expect } from '@playwright/test';
import path from 'node:path';

const browser = await chromium.launch({channel:'msedge',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page = await browser.newPage({viewport:{width:1280,height:900}});
try {
  await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});
  await page.getByRole('button',{name:'New assessment',exact:true}).click();
  const start = page.getByRole('button',{name:'Start assessment',exact:true});
  const feedback = page.getByRole('alert').filter({hasText:'The assessment has not started yet'});
  await start.click();
  await expect(feedback).toContainText('Enter an assessment name');
  await expect(feedback).toContainText('Select the land boundary');
  await expect(feedback).toBeInViewport();
  const tiny = {type:'Polygon',coordinates:[[[28.01,-26.23],[28.0101,-26.23],[28.0101,-26.2299],[28.01,-26.2299],[28.01,-26.23]]]};
  const input = page.locator('input[type="file"][accept=".geojson,.json,application/geo+json"]');
  await input.setInputFiles({name:'tiny.geojson',mimeType:'application/geo+json',buffer:Buffer.from(JSON.stringify(tiny))});
  await page.getByRole('textbox',{name:/Assessment name/}).fill('Start button recovery verification');
  await page.getByRole('checkbox',{name:/I have checked the map/}).check();
  const rejected = page.waitForResponse((r)=>r.url().endsWith('/api/assessments') && r.request().method()==='POST');
  await start.click();
  expect((await rejected).status()).toBe(422);
  await expect(feedback).toContainText('hectares');
  await expect(feedback).toBeInViewport();
  await page.screenshot({path:path.resolve('../artifacts/start-validation-visible.png')});
  const rows = await (await page.request.get('http://127.0.0.1:8000/api/assessments')).json();
  const source = rows.assessments.find((r)=>r.name==='National workflow verification (Johannesburg)' && ['complete','partial'].includes(r.status));
  await input.setInputFiles({name:'valid.geojson',mimeType:'application/geo+json',buffer:Buffer.from(JSON.stringify(source.site.geometry))});
  await page.getByLabel(/First year/).fill(String(source.options.start_year));
  await page.getByLabel(/Last complete year/).fill(String(source.options.end_year));
  await page.getByLabel(/Comparable season/).selectOption(String(source.options.season_month));
  await page.getByRole('checkbox',{name:/I have checked the map/}).check();
  const accepted = page.waitForResponse((r)=>r.url().endsWith('/api/assessments') && r.request().method()==='POST');
  await start.click();
  expect((await accepted).status()).toBe(202);
  await expect(page.getByRole('heading',{name:'Start button recovery verification',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Water, vegetation and the ground'})).toBeVisible({timeout:180000});
  console.log('PASS: incomplete form gives visible guidance; real API boundary rejection is visible beside Start; correcting it starts a real assessment and reaches its report.');
} finally { await browser.close(); }

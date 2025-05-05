import { test, expect } from '@playwright/test';

test('Script Generator Theme Input Stage', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  await expect(page.getByRole('heading', { name: 'スクリプト生成' })).toBeVisible();
  
  await page.getByPlaceholder('スクリプトのテーマを入力...').fill('AIで英語学習');
  
  await page.getByPlaceholder('{"age":"18-24","interest":"study"}').fill('{"age":"18-24","interest":"study"}');
  
  await page.locator('#useSavedSettings').click();
  await page.locator('#useSavedSettings').click();
  
  await page.getByRole('button', { name: 'スクリプト生成' }).click();
  
  await expect(page.getByRole('heading', { level: 1 }).filter({ hasText: '選択' })).toBeVisible({ timeout: 60000 });
});

test('Loading State Test', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  await page.getByPlaceholder('スクリプトのテーマを入力...').fill('AIで英語学習');
  
  const api = page.waitForResponse(r => r.url().includes('/script') && r.ok());
  await page.getByRole('button', { name: 'スクリプト生成' }).click();
  await api;                           // wait for backend to respond

  await expect(page.getByRole('status').first()).toBeVisible({ timeout: 10000 });

  await expect(
    page.getByRole('heading', { level: 1 }).filter({ hasText: '選択' })
  ).toBeVisible({ timeout: 30000 });
});

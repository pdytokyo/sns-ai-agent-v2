import { test, expect } from '@playwright/test';

test('Script Generator Workflow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  await expect(page.getByRole('heading', { name: 'スクリプト生成' })).toBeVisible();
  
  await page.getByPlaceholder('スクリプトのテーマを入力...').fill('AIで英語学習');
  
  await page.getByPlaceholder('{"age":"18-24","interest":"study"}').fill('{"age":"18-24","interest":"study"}');
  
  await page.locator('#useSavedSettings').click();
  await page.locator('#useSavedSettings').click();
  
  await page.getByRole('button', { name: 'スクリプト生成' }).click();
  
  await expect(page.getByRole('heading', { level: 1 }).filter({ hasText: '選択' })).toBeVisible({ timeout: 20000 });
  
  await expect(page.getByText('一致リール数:', { exact: false })).toBeVisible();
  
  await page.getByRole('button', { name: /問題解決型|日常紹介型|ハウツー型|比較型|ストーリー型/ }).first().click();
  
  await expect(page.getByRole('heading', { level: 1 }).filter({ hasText: '編集・保存' })).toBeVisible();
  
  const textarea = page.locator('textarea').first();
  await textarea.click();
  await textarea.fill('これはテスト用に編集したスクリプトです。AIで英語学習するための効果的な方法について説明します。');
  
  await page.getByRole('button', { name: '保存する' }).click();
  
  await expect(page.getByText('保存しました！', { exact: true })).toBeVisible({ timeout: 10000 });
});

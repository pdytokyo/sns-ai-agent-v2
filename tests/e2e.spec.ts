import { test, expect } from '@playwright/test';

test('Script Generator Workflow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  await expect(page.getByText('テーマ入力')).toBeVisible();
  
  await page.getByPlaceholder('スクリプトのテーマを入力...').fill('AIで英語学習');
  
  await page.getByPlaceholder('ターゲット設定 (JSON)').fill('{"age":"18-24","interest":"study"}');
  
  await page.getByRole('switch', { name: '保存設定を使う' }).click();
  await page.getByRole('switch', { name: '保存設定を使う' }).click();
  
  await page.getByRole('button', { name: 'スクリプト生成' }).click();
  
  await expect(page.getByText('データ収集中...')).toBeVisible();
  
  await expect(page.getByText('オプション選択')).toBeVisible({ timeout: 10000 });
  
  await expect(page.getByText('一致リール数:')).toBeVisible();
  
  await page.getByRole('button', { name: /問題解決型|日常紹介型|ハウツー型|比較型|ストーリー型/ }).first().click();
  
  await expect(page.getByText('編集・保存')).toBeVisible();
  
  const textarea = page.locator('textarea').first();
  await textarea.click();
  await textarea.fill('これはテスト用に編集したスクリプトです。AIで英語学習するための効果的な方法について説明します。');
  
  await page.getByRole('button', { name: '保存' }).click();
  
  await expect(page.getByText('保存しました！')).toBeVisible();
});

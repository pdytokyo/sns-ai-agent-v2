import { test, expect } from '@playwright/test';

test('Account Analysis Settings Flow', async ({ page }) => {
  await page.route('**/api/analysis/verify_token', async (route) => {
    console.log('Mocking API response for /api/analysis/verify_token');
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        valid: true,
        username: 'test_user',
        account_id: '12345678'
      })
    });
  });
  
  await page.goto('http://localhost:3000/settings');
  
  await expect(page.getByRole('heading', { name: '設定' })).toBeVisible();
  
  await page.getByPlaceholder('Instagram Graph API アクセストークンを入力...').fill('mock_access_token');
  
  await page.getByRole('button', { name: 'アカウント分析を有効化' }).click();
  
  await expect(page.locator('[data-testid="toast-analysis-success"]')).toBeAttached();
  
  await expect(page.getByText('アカウント連携済み: @test_user')).toBeVisible();
  
  await expect(page.getByText('有効')).toBeVisible();
  
  await page.getByRole('button', { name: '連携を解除' }).click();
  
  await expect(page.getByPlaceholder('Instagram Graph API アクセストークンを入力...')).toBeVisible();
  
  await expect(page.getByText('無効')).toBeVisible();
});

test('Navigation between Home and Settings', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  await page.getByRole('button', { name: '設定' }).click();
  
  await expect(page.getByRole('heading', { name: '設定' })).toBeVisible();
  
  await page.getByRole('button', { name: 'ホームに戻る' }).click();
  
  await expect(page.getByRole('heading', { name: 'スクリプト生成' })).toBeVisible();
});

import { test, expect, Page } from '@playwright/test';

test.describe('Analysis Features', () => {
  test.beforeEach(() => {
    test.skip(process.env.ENABLE_ANALYSIS !== 'true', 'Analysis features are disabled');
    console.log(`Analysis tests running with ENABLE_ANALYSIS=${process.env.ENABLE_ANALYSIS}`);
  });
  
  test('Account Analysis Settings Flow', async ({ page }: { page: Page }) => {
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
    
    await expect(page.locator('label[for="analysis-enabled"]')).toHaveText('有効');
    
    await page.getByRole('button', { name: '連携を解除' }).click();
    
    await expect(page.getByPlaceholder('Instagram Graph API アクセストークンを入力...')).toBeVisible();
    
    await expect(page.locator('label[for="analysis-enabled"]')).toHaveText('無効');
  });
});

test('Navigation between Home and Settings', async ({ page }: { page: Page }) => {
  await page.goto('http://localhost:3000');
  
  await page.getByRole('button', { name: '設定' }).click();
  
  await expect(page.getByRole('heading', { name: '設定' })).toBeVisible();
  
  await page.getByRole('button', { name: 'ホームに戻る' }).click();
  
  await expect(page.getByRole('heading', { name: 'スクリプト生成' })).toBeVisible();
});

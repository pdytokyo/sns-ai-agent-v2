import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.on('console', msg => console.log(`Browser console: ${msg.text()}`));
});

test('Script Generator End-to-End Flow', async ({ page }) => {
  await page.route('**/api/script', async (route) => {
    console.log('Mocking API response for /api/script');
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        script: 'モックスクリプト1',
        alt: 'モックスクリプト2',
        matching_reels_count: 5
      })
    });
  });
  
  console.log('Navigating to application');
  await page.goto('http://localhost:3000');
  
  console.log('Verifying initial page load');
  await expect(page.getByRole('heading', { name: 'スクリプト生成' })).toBeVisible();
  
  console.log('Filling theme input');
  await page.getByPlaceholder('スクリプトのテーマを入力...').fill('AIで英語学習');
  
  console.log('Clicking generate button');
  await page.getByRole('button', { name: 'スクリプト生成' }).click();
  
  console.log('Waiting for toast success notification');
  await expect(page.locator('[data-testid="toast-success"]').first()).toBeAttached();
  
  console.log('Waiting for options to appear');
  await expect(page.getByRole('heading', { name: '選択' })).toBeVisible({ timeout: 60000 });
  
  console.log('Verifying option buttons');
  const optionButtons = page.getByRole('button', { name: /オプション/ });
  await expect(optionButtons).toHaveCount(2);
  
  console.log('Checking for hit count or error toast');
  const hitCountText = await page.getByText(/オプション 1 \(\d+件\)/).isVisible();
  if (!hitCountText) {
    console.log('Hit count not found, checking for error toast');
    const errorToast = await page.locator('[data-testid="error-toast"]').isVisible();
    console.log(`Error toast visible: ${errorToast}`);
  }
  
  console.log('Selecting first option');
  await optionButtons.first().click();
  
  console.log('Verifying edit stage');
  await expect(page.getByRole('heading', { name: '編集 & 保存' })).toBeVisible();
  
  console.log('Editing script');
  const textarea = page.getByRole('textbox').nth(0);
  await textarea.fill('AIで英語学習のカスタムスクリプト');
  
  console.log('Saving script');
  await page.getByRole('button', { name: 'スクリプトを保存' }).click();
  
  console.log('Verifying toast success notification for save');
  await expect(page.locator('[data-testid="toast-success"]').getByText('保存しました！')).toBeAttached();
  
  console.log('Verifying we remain on edit page after save');
  await expect(page.getByRole('heading', { name: '編集 & 保存' })).toBeVisible();
  
  console.log('Test completed successfully');
});

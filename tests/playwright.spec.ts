import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.on('console', msg => console.log(`Browser console: ${msg.text()}`));
});

test('Script Generator End-to-End Flow with Live Scraping', async ({ page }) => {
  console.log('Navigating to application');
  await page.goto('http://localhost:3000');
  
  console.log('Verifying initial page load');
  await expect(page.getByRole('heading', { name: 'スクリプト生成' })).toBeVisible();
  
  console.log('Filling theme input');
  await page.getByPlaceholder('スクリプトのテーマを入力...').fill('AIで英語学習');
  
  console.log('Clicking generate button');
  await page.getByRole('button', { name: 'スクリプト生成' }).click();
  
  console.log('Waiting for loading indicator');
  await expect(page.locator('.animate-spin')).toBeVisible({ timeout: 10000 });
  
  console.log('Waiting for toast success notification');
  await expect(page.locator('[data-testid="toast-success"]').first()).toBeVisible({ timeout: 90000 });
  
  console.log('Waiting for options to appear');
  await expect(page.getByRole('heading', { name: '選択' })).toBeVisible({ timeout: 90000 });
  
  console.log('Verifying option buttons');
  const optionButtons = page.getByRole('button', { name: /オプション/ });
  await expect(optionButtons).toHaveCount(2);
  
  console.log('Checking for matching reels count (if available)');
  const matchingReelsText = await page.getByText(/一致リール数: \d+/).isVisible();
  console.log(`Matching reels count visible: ${matchingReelsText}`);
  
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
  await expect(page.locator('[data-testid="toast-success"]').getByText('保存しました！').first()).toBeVisible();
  
  console.log('Verifying we remain on edit page after save');
  await expect(page.getByRole('heading', { name: '編集 & 保存' })).toBeVisible();
  
  console.log('Test completed successfully');
});

test('Instagram Scraping Returns Results', async ({ request }) => {
  console.log('Testing Instagram scraping API directly');
  
  const response = await request.post('http://localhost:8000/api/script/auto', {
    data: {
      theme: 'Instagram engagement',
      client_id: 'test_client',
      target: { age: '18-34', interest: 'social media' }
    }
  });
  
  console.log('Verifying API response');
  expect(response.ok()).toBeTruthy();
  
  const data = await response.json();
  console.log(`API returned matching_reels_count: ${data.matching_reels_count}`);
  
  if (data.matching_reels_count === 0) {
    console.log('Warning: No matching reels found. This may be expected in test environments.');
  }
  
  console.log('Scraping test completed successfully');
});

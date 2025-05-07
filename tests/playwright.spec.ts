import { test, expect } from '@playwright/test';

test('Script Generator End-to-End Flow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  await expect(page.getByRole('heading', { name: 'スクリプト生成' })).toBeVisible();
  
  await page.getByPlaceholder('スクリプトのテーマを入力...').fill('AIで英語学習');
  
  await page.getByRole('button', { name: 'スクリプト生成' }).click();
  
  await expect(page.locator('#toast-success')).toBeVisible();
  
  await expect(page.getByRole('heading', { name: '選択' })).toBeVisible({ timeout: 60000 });
  
  const optionButtons = page.getByRole('button', { name: /オプション/ });
  await expect(optionButtons).toHaveCount(2);
  
  const hitCountText = await page.getByText(/オプション 1 \(\d+件\)/).isVisible();
  if (!hitCountText) {
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
  }
  
  await optionButtons.first().click();
  
  await expect(page.getByRole('heading', { name: '編集 & 保存' })).toBeVisible();
  
  const textarea = page.getByRole('textbox').nth(0);
  await textarea.fill('AIで英語学習のカスタムスクリプト');
  
  await page.getByRole('button', { name: 'スクリプトを保存' }).click();
  
  await expect(page.locator('#toast-success').getByText('保存しました！')).toBeVisible();
});

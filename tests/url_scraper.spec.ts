import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.on('console', msg => console.log(`Browser console: ${msg.text()}`));
});

test('URL Scraper API Test', async ({ request }) => {
  console.log('Testing URL Scraper API directly');
  
  const response = await request.post('http://localhost:8000/api/url_scraper', {
    data: {
      keyword: '恋愛',
      platform: 'Instagram',
      count: 3
    }
  });
  
  console.log('Verifying API response');
  expect(response.ok()).toBeTruthy();
  
  const data = await response.json();
  console.log(`API returned ${data.urls.length} URLs`);
  
  expect(data.urls).toBeDefined();
  expect(Array.isArray(data.urls)).toBeTruthy();
  expect(data.urls.length).toBeGreaterThan(0);
  
  for (const url of data.urls) {
    expect(url).toHaveProperty('url');
    expect(url).toHaveProperty('platform');
    expect(url).toHaveProperty('summary');
    
    if (url.platform === 'Instagram') {
      expect(url.url).toMatch(/https?:\/\/(?:www\.)?instagram\.com\/(?:p|reel)\/[\w-]+\/?/);
    } else if (url.platform === 'TikTok') {
      expect(url.url).toMatch(/https?:\/\/(?:www\.)?tiktok\.com\/@[\w.]+\/video\/\d+/);
    } else if (url.platform === 'YouTube') {
      expect(url.url).toMatch(/https?:\/\/(?:www\.)?youtube\.com\/watch\?v=[\w-]+|https?:\/\/youtu\.be\/[\w-]+/);
    }
  }
  
  console.log('URL Scraper test completed successfully');
});

test('URL Scraper CLI Test', async ({ page }) => {
  if (process.env.CI === 'true') {
    console.log('Skipping CLI test in CI environment');
    test.skip();
    return;
  }
  
  console.log('Testing URL Scraper CLI');
  
  await page.goto('http://localhost:3000');
  
  await expect(page.getByRole('heading', { name: 'スクリプト生成' })).toBeVisible();
  
  console.log('URL Scraper CLI test completed successfully');
});

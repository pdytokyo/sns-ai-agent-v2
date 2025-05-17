"""
Instagram Reels Scraper

This script scrapes Instagram Reels from hashtag pages and filters them based on engagement metrics.
It uses Playwright for browser automation and saves the results to a JSON file.
"""

import json
import os
import sys
import time
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, quote

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

from login_instagram import load_cookies, is_logged_in, login_instagram

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scrape_reels')

def extract_number(text: str) -> int:
    """
    Extract number from text with K, M, B suffixes
    
    Args:
        text: Text containing a number (e.g., "1.5K", "2M")
        
    Returns:
        Extracted number as integer
    """
    if not text:
        return 0
    
    text = text.replace(',', '').replace(' ', '')
    
    match = re.search(r'([\d.]+)([KMB])?', text, re.IGNORECASE)
    if not match:
        return 0
    
    number, suffix = match.groups()
    number = float(number)
    
    if suffix:
        suffix = suffix.upper()
        if suffix == 'K':
            number *= 1_000
        elif suffix == 'M':
            number *= 1_000_000
        elif suffix == 'B':
            number *= 1_000_000_000
    
    return int(number)

def navigate_to_hashtag(page: Page, hashtag: str) -> bool:
    """
    Navigate to Instagram hashtag page
    
    Args:
        page: Playwright page
        hashtag: Hashtag to search for (without #)
        
    Returns:
        True if navigation successful, False otherwise
    """
    try:
        encoded_hashtag = quote(hashtag)
        url = f"https://www.instagram.com/explore/tags/{encoded_hashtag}/"
        
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        if "Page Not Found" in page.title():
            logger.error(f"Hashtag page not found: {hashtag}")
            return False
        
        logger.info(f"Successfully navigated to hashtag page: {hashtag}")
        return True
    
    except Exception as e:
        logger.error(f"Error navigating to hashtag page: {e}")
        return False

def get_reels_urls(page: Page, max_reels: int = 20) -> List[str]:
    """
    Get URLs of Reels from hashtag page
    
    Args:
        page: Playwright page
        max_reels: Maximum number of Reels to collect
        
    Returns:
        List of Reels URLs
    """
    urls = []
    
    try:
        logger.info("Waiting for Instagram feed to load...")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('main[role="main"]', timeout=60000)
        
        selectors = [
            'a[href*="/reel/"]',                  # Direct reel links
            'article a[href*="/p/"]',             # Post links (may contain reels)
            'div[role="presentation"] a',         # General post links
            'div[data-visualcompletion="media-vc-image"] a'  # Media container links
        ]
        
        found_selector = False
        for selector in selectors:
            try:
                logger.info(f"Trying selector: {selector}")
                if page.wait_for_selector(selector, timeout=20000, state='attached'):
                    logger.info(f"Found working selector: {selector}")
                    found_selector = True
                    
                    # Scroll a few times to load more content
                    for i in range(5):
                        logger.info(f"Scrolling page ({i+1}/5)...")
                        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        page.wait_for_timeout(3000)  # Wait longer for content to load
                    
                    links = page.query_selector_all(selector)
                    logger.info(f"Found {len(links)} potential links with selector: {selector}")
                    
                    for link in links[:max_reels * 2]:  # Get more links than needed as some might not be reels
                        href = link.get_attribute('href')
                        if href:
                            if '/reel/' in href or '/p/' in href:
                                full_url = f"https://www.instagram.com{href}" if href.startswith('/') else href
                                if full_url not in urls:
                                    urls.append(full_url)
                    
                    break  # Exit the loop if we found a working selector
            except PlaywrightTimeoutError:
                logger.warning(f"Selector {selector} timed out, trying next one...")
                continue
        
        if not found_selector:
            logger.warning("Could not find any working selector for Reels links")
            
            logger.info("Using fallback method to find links...")
            all_links = page.query_selector_all('a')
            
            for link in all_links:
                href = link.get_attribute('href')
                if href and ('/reel/' in href or '/p/' in href):
                    full_url = f"https://www.instagram.com{href}" if href.startswith('/') else href
                    if full_url not in urls:
                        urls.append(full_url)
        
        urls = list(dict.fromkeys(urls))[:max_reels]
        
        logger.info(f"Found {len(urls)} Reels URLs")
        return urls
    
    except Exception as e:
        logger.error(f"Error getting Reels URLs: {e}")
        return urls

def get_reel_metrics(page: Page, url: str) -> Dict[str, Any]:
    """
    Get metrics for a Reel
    
    Args:
        page: Playwright page
        url: Reel URL
        
    Returns:
        Dictionary with Reel metrics
    """
    metrics = {
        'url': url,
        'playsCount': 0,
        'ownerFollowersCount': 0
    }
    
    try:
        logger.info(f"Navigating to Reel URL: {url}")
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        # Wait for the page content to load
        logger.info("Waiting for Reel content to load...")
        
        video_selectors = [
            'video',
            'div[role="button"] video',
            'div[data-visualcompletion="media-vc-image"] video',
            'div[role="presentation"] video'
        ]
        
        video_found = False
        for selector in video_selectors:
            try:
                logger.info(f"Trying video selector: {selector}")
                if page.wait_for_selector(selector, timeout=20000, state='attached'):
                    logger.info(f"Found video with selector: {selector}")
                    video_found = True
                    break
            except PlaywrightTimeoutError:
                logger.warning(f"Video selector {selector} timed out, trying next one...")
                continue
        
        if not video_found:
            logger.warning("Could not find video element, trying to proceed anyway...")
        
        views_selectors = [
            'span:has-text("views")',
            'span:has-text("次視聴")',  # Japanese "views"
            'span:has-text("回再生")',  # Alternative Japanese "views"
            'div[role="button"] span:has-text("view")',
            'section span:has-text("view")'
        ]
        
        for selector in views_selectors:
            try:
                logger.info(f"Trying views selector: {selector}")
                views_element = page.query_selector(selector)
                if views_element:
                    try:
                        views_text = views_element.evaluate('el => el.previousSibling ? el.previousSibling.textContent : null')
                        if views_text:
                            metrics['playsCount'] = extract_number(views_text)
                            logger.info(f"Found plays count (method 1): {metrics['playsCount']}")
                            break
                    except Exception:
                        pass
                    
                    try:
                        views_text = views_element.evaluate('el => el.parentElement ? el.parentElement.textContent : null')
                        if views_text:
                            # Extract numbers from the text
                            numbers = re.findall(r'[\d,.]+[KMB]?', views_text)
                            if numbers:
                                metrics['playsCount'] = extract_number(numbers[0])
                                logger.info(f"Found plays count (method 2): {metrics['playsCount']}")
                                break
                    except Exception:
                        pass
                    
                    try:
                        views_text = views_element.inner_text()
                        numbers = re.findall(r'[\d,.]+[KMB]?', views_text)
                        if numbers:
                            metrics['playsCount'] = extract_number(numbers[0])
                            logger.info(f"Found plays count (method 3): {metrics['playsCount']}")
                            break
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Error with views selector {selector}: {e}")
        
        if metrics['playsCount'] == 0:
            logger.warning("Could not find plays count with any method")
        
        profile_selectors = [
            'header a',
            'a[role="link"][tabindex="0"]',
            'div[role="button"] a[role="link"]',
            'h2 a',
            'section a'
        ]
        
        profile_found = False
        for selector in profile_selectors:
            try:
                logger.info(f"Trying profile selector: {selector}")
                profile_link = page.query_selector(selector)
                if profile_link:
                    profile_url = profile_link.get_attribute('href')
                    if profile_url and ('/' in profile_url) and not ('/explore/' in profile_url) and not ('/reels/' in profile_url):
                        logger.info(f"Found profile URL: {profile_url}")
                        full_profile_url = f"https://www.instagram.com{profile_url}" if profile_url.startswith('/') else profile_url
                        
                        logger.info(f"Navigating to profile page: {full_profile_url}")
                        page.goto(full_profile_url)
                        page.wait_for_load_state('networkidle')
                        
                        logger.info("Waiting for profile page to load...")
                        page.wait_for_selector('main[role="main"]', timeout=60000)
                        
                        followers_selectors = [
                            'header section ul li',
                            'section ul li',
                            'span:has-text("followers")',
                            'span:has-text("フォロワー")'  # Japanese "followers"
                        ]
                        
                        for f_selector in followers_selectors:
                            try:
                                logger.info(f"Trying followers selector: {f_selector}")
                                if 'li' in f_selector:
                                    stats_elements = page.query_selector_all(f_selector)
                                    
                                    if len(stats_elements) >= 2:
                                        for i, element in enumerate(stats_elements):
                                            followers_text = element.inner_text().lower()
                                            if 'followers' in followers_text or 'フォロワー' in followers_text:
                                                numbers = re.findall(r'[\d,.]+[KMB]?', followers_text)
                                                if numbers:
                                                    metrics['ownerFollowersCount'] = extract_number(numbers[0])
                                                    logger.info(f"Found followers count (method 1): {metrics['ownerFollowersCount']}")
                                                    profile_found = True
                                                    break
                                else:
                                    followers_element = page.query_selector(f_selector)
                                    if followers_element:
                                        followers_text = followers_element.inner_text()
                                        if not followers_text:
                                            followers_text = followers_element.evaluate('el => el.parentElement ? el.parentElement.textContent : ""')
                                        
                                        numbers = re.findall(r'[\d,.]+[KMB]?', followers_text)
                                        if numbers:
                                            metrics['ownerFollowersCount'] = extract_number(numbers[0])
                                            logger.info(f"Found followers count (method 2): {metrics['ownerFollowersCount']}")
                                            profile_found = True
                                            break
                            except Exception as e:
                                logger.warning(f"Error with followers selector {f_selector}: {e}")
                            
                            if profile_found:
                                break
                        
                        if profile_found:
                            break
            except Exception as e:
                logger.warning(f"Error with profile selector {selector}: {e}")
        
        if metrics['ownerFollowersCount'] == 0:
            logger.warning("Could not find followers count with any method")
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error getting Reel metrics: {e}")
        return metrics

def filter_reels(reels: List[Dict[str, Any]], min_ratio: float = 5.0) -> List[Dict[str, Any]]:
    """
    Filter Reels based on plays/followers ratio
    
    Args:
        reels: List of Reels with metrics
        min_ratio: Minimum plays/followers ratio
        
    Returns:
        Filtered list of Reels
    """
    filtered = []
    
    for reel in reels:
        plays_count = reel.get('playsCount', 0)
        followers_count = reel.get('ownerFollowersCount', 0)
        
        if plays_count == 0 or followers_count == 0:
            logger.warning(f"Skipping {reel['url']}: Missing playsCount or ownerFollowersCount data")
            continue
        
        ratio = plays_count / followers_count if followers_count > 0 else 0
        
        reel['playsFollowersRatio'] = round(ratio, 2)
        
        if ratio >= min_ratio:
            logger.info(f"Reel {reel['url']} has engagement ratio: {ratio:.2f} (plays: {plays_count}, followers: {followers_count})")
            filtered.append(reel)
    
    logger.info(f"Found {len(filtered)} Reels with plays/followers ratio ≥ {min_ratio} out of {len(reels)} total Reels")
    return filtered

def save_to_json(data: List[Dict[str, Any]], output_file: str = 'output_reels.json') -> None:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        output_file: Output file path
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'reels': data}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving data to {output_file}: {e}")

def scrape_reels(
    hashtag: str,
    cookie_file: str = 'cookie.json',
    output_file: str = 'output_reels.json',
    max_reels: int = 20,
    min_ratio: float = 5.0,
    headless: bool = False
) -> None:
    """
    Scrape Instagram Reels from hashtag page
    
    Args:
        hashtag: Hashtag to search for (without #)
        cookie_file: Path to cookie file
        output_file: Output file path
        max_reels: Maximum number of Reels to collect
        min_ratio: Minimum plays/followers ratio
        headless: Run browser in headless mode
    """
    with sync_playwright() as p:
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        logger.info(f"Using real Chrome browser at: {chrome_path}")
        
        browser = p.chromium.launch(
            headless=headless,
            executable_path=chrome_path,
            args=[
                '--disable-blink-features=AutomationControlled',  # Avoid detection
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
            color_scheme='light',
            has_touch=True
        )
        
        page = context.new_page()
        
        # Apply stealth JavaScript to avoid bot detection
        page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
            configurable: true
        });
        
        // Hide automation-related properties
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' || 
            parameters.name === 'clipboard-read' || 
            parameters.name === 'clipboard-write' ?
            Promise.resolve({state: 'granted'}) :
            originalQuery(parameters)
        );
        """)
        
        page.add_init_script("""
        (() => {
            const originalMouseMove = window.MouseEvent.prototype.constructor;
            
            let lastTime = 0;
            let lastX = 0;
            let lastY = 0;
            
            window.MouseEvent.prototype.constructor = function(...args) {
                if (args[0] === 'mousemove') {
                    const now = Date.now();
                    const dt = now - lastTime;
                    
                    if (dt < 5) {
                        // Add slight randomness to consecutive mousemove events
                        const event = args[1] || {};
                        if (typeof event.clientX === 'number' && typeof event.clientY === 'number') {
                            const dx = event.clientX - lastX;
                            const dy = event.clientY - lastY;
                            
                            if (Math.abs(dx) < 10 && Math.abs(dy) < 10) {
                                event.clientX += (Math.random() - 0.5) * 2;
                                event.clientY += (Math.random() - 0.5) * 2;
                            }
                            
                            lastX = event.clientX;
                            lastY = event.clientY;
                        }
                    }
                    
                    lastTime = now;
                }
                
                return originalMouseMove.apply(this, args);
            };
        })();
        """)
        
        try:
            cookies_loaded = load_cookies(context, cookie_file)
            
            if not cookies_loaded or not is_logged_in(page):
                logger.error("Not logged in. Please run login_instagram.py first")
                browser.close()
                sys.exit(1)
            
            if not navigate_to_hashtag(page, hashtag):
                browser.close()
                sys.exit(1)
            
            urls = get_reels_urls(page, max_reels)
            
            if not urls:
                logger.warning(f"No Reels found for hashtag: {hashtag}")
                browser.close()
                sys.exit(0)
            
            reels = []
            for i, url in enumerate(urls):
                logger.info(f"Processing Reel {i+1}/{len(urls)}: {url}")
                metrics = get_reel_metrics(page, url)
                reels.append(metrics)
                
                time.sleep(2)
            
            filtered_reels = filter_reels(reels, min_ratio)
            
            save_to_json(filtered_reels, output_file)
            
        except Exception as e:
            logger.error(f"Error scraping Reels: {e}")
        
        finally:
            browser.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Reels Scraper')
    parser.add_argument('hashtag', help='Hashtag to search for (without #)')
    parser.add_argument('--cookie-file', '-c', default='cookie.json', help='Path to cookie file')
    parser.add_argument('--output-file', '-o', default='output_reels.json', help='Output file path')
    parser.add_argument('--max-reels', '-m', type=int, default=20, help='Maximum number of Reels to collect')
    parser.add_argument('--min-ratio', '-r', type=float, default=5.0, help='Minimum plays/followers ratio')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    
    args = parser.parse_args()
    
    scrape_reels(
        args.hashtag,
        args.cookie_file,
        args.output_file,
        args.max_reels,
        args.min_ratio,
        args.headless
    )

if __name__ == '__main__':
    main()

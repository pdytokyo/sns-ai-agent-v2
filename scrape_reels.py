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
        page.wait_for_selector('article a', timeout=10000)
        
        for _ in range(3):  # Scroll a few times to load more content
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(2000)  # Wait for content to load
        
        links = page.query_selector_all('article a')
        
        for link in links[:max_reels]:
            href = link.get_attribute('href')
            if href and '/reel/' in href:
                full_url = f"https://www.instagram.com{href}"
                if full_url not in urls:
                    urls.append(full_url)
        
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
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        page.wait_for_selector('video', timeout=10000)
        
        try:
            views_element = page.query_selector('span:has-text("views")')
            if views_element:
                views_text = views_element.evaluate('el => el.previousSibling.textContent')
                metrics['playsCount'] = extract_number(views_text)
                logger.info(f"Plays count: {metrics['playsCount']}")
        except Exception as e:
            logger.warning(f"Error getting plays count: {e}")
        
        profile_link = page.query_selector('header a')
        if profile_link:
            profile_url = profile_link.get_attribute('href')
            if profile_url:
                full_profile_url = f"https://www.instagram.com{profile_url}"
                page.goto(full_profile_url)
                page.wait_for_load_state('networkidle')
                
                try:
                    page.wait_for_selector('header section ul li', timeout=5000)
                    
                    stats_elements = page.query_selector_all('header section ul li')
                    
                    if len(stats_elements) >= 2:
                        followers_element = stats_elements[1]
                        followers_text = followers_element.inner_text()
                        
                        if 'followers' in followers_text.lower():
                            followers_count_text = followers_text.split('followers')[0].strip()
                            metrics['ownerFollowersCount'] = extract_number(followers_count_text)
                            logger.info(f"Followers count: {metrics['ownerFollowersCount']}")
                except Exception as e:
                    logger.warning(f"Error getting followers count: {e}")
        
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
        browser = p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']  # Avoid detection
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        )
        
        page = context.new_page()
        
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

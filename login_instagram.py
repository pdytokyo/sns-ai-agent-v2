"""
Instagram Login Script

This script handles Instagram login and saves cookies for session reuse.
It uses Playwright to automate the login process and saves the cookies to a JSON file.
"""

import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('login_instagram')

def save_cookies(context: BrowserContext, cookie_file: str = 'cookie.json') -> None:
    """
    Save browser cookies to a JSON file
    
    Args:
        context: Playwright browser context
        cookie_file: Path to save cookies
    """
    cookies = context.cookies()
    os.makedirs(os.path.dirname(cookie_file) if os.path.dirname(cookie_file) else '.', exist_ok=True)
    
    with open(cookie_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2)
    
    logger.info(f"Cookies saved to {cookie_file}")

def load_cookies(context: BrowserContext, cookie_file: str = 'cookie.json') -> bool:
    """
    Load cookies from a JSON file into the browser context
    
    Args:
        context: Playwright browser context
        cookie_file: Path to cookie file
        
    Returns:
        True if cookies were loaded successfully, False otherwise
    """
    if not os.path.exists(cookie_file):
        logger.warning(f"Cookie file {cookie_file} not found")
        return False
    
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        context.add_cookies(cookies)
        logger.info(f"Cookies loaded from {cookie_file}")
        return True
    except Exception as e:
        logger.error(f"Error loading cookies: {e}")
        return False

def is_logged_in(page: Page) -> bool:
    """
    Check if the user is logged in to Instagram
    
    Args:
        page: Playwright page
        
    Returns:
        True if logged in, False otherwise
    """
    page.goto('https://www.instagram.com/')
    
    page.wait_for_load_state('networkidle')
    
    try:
        logged_in = page.locator('svg[aria-label="Search"], a[href="/direct/inbox/"]').count() > 0
        
        if logged_in:
            logger.info("User is logged in to Instagram")
        else:
            logger.info("User is not logged in to Instagram")
        
        return logged_in
    except Exception as e:
        logger.error(f"Error checking login status: {e}")
        return False

def login_instagram(
    username: str, 
    password: str, 
    page: Page,
    cookie_file: str = 'cookie.json',
    save_cookies_after_login: bool = True
) -> bool:
    """
    Login to Instagram
    
    Args:
        username: Instagram username
        password: Instagram password
        page: Playwright page
        cookie_file: Path to save cookies
        save_cookies_after_login: Whether to save cookies after successful login
        
    Returns:
        True if login successful, False otherwise
    """
    try:
        page.goto('https://www.instagram.com/accounts/login/')
        
        page.wait_for_selector('input[name="username"]', timeout=10000)
        
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)
        
        page.click('button[type="submit"]')
        
        page.wait_for_load_state('networkidle')
        
        if page.url.startswith('https://www.instagram.com/accounts/onetap/'):
            logger.info("Login successful, on one-tap save login info page")
            if page.locator('button:has-text("Not Now")').count() > 0:
                page.click('button:has-text("Not Now")')
                page.wait_for_load_state('networkidle')
        
        if page.locator('button:has-text("Not Now")').count() > 0:
            page.click('button:has-text("Not Now")')
            page.wait_for_load_state('networkidle')
        
        if page.locator('button:has-text("Not Now")').count() > 0:
            page.click('button:has-text("Not Now")')
            page.wait_for_load_state('networkidle')
        
        login_success = is_logged_in(page)
        
        if login_success and save_cookies_after_login:
            save_cookies(page.context, cookie_file)
        
        return login_success
    
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return False

def wait_for_manual_login(page: Page, cookie_file: str = 'cookie.json', timeout: int = 300) -> bool:
    """
    Wait for user to manually login to Instagram
    
    Args:
        page: Playwright page
        cookie_file: Path to save cookies
        timeout: Maximum time to wait for login in seconds
        
    Returns:
        True if login successful, False otherwise
    """
    logger.info("Please login manually in the browser window")
    logger.info(f"Waiting up to {timeout} seconds for login...")
    
    page.goto('https://www.instagram.com/accounts/login/')
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_logged_in(page):
            logger.info("Manual login successful")
            
            handle_post_login_dialogs(page)
            
            # Save cookies
            save_cookies(page.context, cookie_file)
            return True
        
        time.sleep(5)
    
    logger.error(f"Timed out waiting for manual login after {timeout} seconds")
    return False

def handle_post_login_dialogs(page: Page) -> None:
    """
    Handle common Instagram dialogs that appear after login
    
    Args:
        page: Playwright page
    """
    dialog_buttons = [
        'button:has-text("Not Now")',
        'button:has-text("Cancel")',
        'button:has-text("Skip")',
        'button:has-text("Maybe Later")',
        'button:has-text("Close")'
    ]
    
    for button_selector in dialog_buttons:
        try:
            if page.locator(button_selector).count() > 0:
                logger.info(f"Dismissing dialog with {button_selector}")
                page.click(button_selector)
                page.wait_for_load_state('networkidle')
                time.sleep(1)  # Wait a bit for any animations
        except Exception as e:
            logger.debug(f"Error handling dialog {button_selector}: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Login Script')
    parser.add_argument('--cookie-file', '-c', default='cookie.json', help='Path to cookie file')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode (not recommended for manual login)')
    parser.add_argument('--timeout', '-t', type=int, default=300, help='Timeout for manual login in seconds')
    parser.add_argument('--auto-login', '-a', action='store_true', help='Use automated login instead of manual login')
    parser.add_argument('--username', '-u', help='Instagram username (only needed for auto-login)')
    parser.add_argument('--password', '-p', help='Instagram password (only needed for auto-login)')
    
    args = parser.parse_args()
    
    if args.auto_login:
        if not args.username or not args.password:
            username = os.environ.get('INSTAGRAM_USERNAME')
            password = os.environ.get('INSTAGRAM_PASSWORD')
            
            if not username or not password:
                logger.error("For auto-login, Instagram username and password must be provided")
                parser.print_help()
                sys.exit(1)
        else:
            username = args.username
            password = args.password
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=args.headless,  # Default is False from argparse
            args=['--disable-blink-features=AutomationControlled']  # Avoid detection
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        )
        
        page = context.new_page()
        
        cookies_loaded = load_cookies(context, args.cookie_file)
        
        if cookies_loaded and is_logged_in(page):
            logger.info("Already logged in with cookies")
            handle_post_login_dialogs(page)
        else:
            if args.auto_login:
                logger.info("Using automated login with username and password")
                login_success = login_instagram(
                    username, 
                    password, 
                    page,
                    args.cookie_file
                )
                
                if not login_success:
                    logger.error("Automated login failed")
                    browser.close()
                    sys.exit(1)
            else:
                login_success = wait_for_manual_login(page, args.cookie_file, args.timeout)
                
                if not login_success:
                    logger.error("Manual login failed or timed out")
                    browser.close()
                    sys.exit(1)
        
        logger.info("Login successful")
        
        time.sleep(3)
        
        browser.close()

if __name__ == '__main__':
    main()

"""
Instagram Login Script

This script handles Instagram login and saves cookies for session reuse.
It uses Playwright with stealth mode to avoid bot detection and automate the login process.
The cookies are saved to a JSON file for reuse in subsequent sessions.
"""

import json
import os
import sys
import time
import logging
import random
from pathlib import Path
from typing import Dict, Any, Optional, List

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('login_instagram')

MOBILE_USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 278.0.0.19.115 (iPhone14,3; iOS 16_3_1; en_US; en-US; scale=3.00; 1284x2778; 463736449)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 255.0.0.16.102 (iPhone13,4; iOS 15_6_1; en_US; en-US; scale=3.00; 1284x2778; 402788505)',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 Instagram 278.0.0.19.115 Android (31/12; 560dpi; 1440x3200; samsung; SM-G998U; p3q; qcom; en_US; 463736449)'
]

DEVICE_VIEWPORTS = [
    {'width': 390, 'height': 844},  # iPhone 13/14
    {'width': 428, 'height': 926},  # iPhone 13/14 Pro Max
    {'width': 360, 'height': 800},  # Common Android
    {'width': 412, 'height': 915},  # Pixel 7
    {'width': 360, 'height': 780},  # Samsung Galaxy S series
]

TIMEZONES = [
    'America/New_York',
    'America/Los_Angeles',
    'America/Chicago',
    'Europe/London',
    'Europe/Paris',
    'Asia/Tokyo',
    'Asia/Singapore',
    'Australia/Sydney',
]

LANGUAGES = [
    'en-US',
    'en-GB',
    'ja-JP',
    'ko-KR',
    'fr-FR',
    'de-DE',
    'es-ES',
    'it-IT',
]

def get_stealth_config() -> Dict[str, Any]:
    """
    Generate a realistic browser configuration to avoid bot detection
    
    Returns:
        Dictionary with stealth browser configuration
    """
    return {
        'viewport': random.choice(DEVICE_VIEWPORTS),
        'user_agent': random.choice(MOBILE_USER_AGENTS),
        'locale': random.choice(LANGUAGES),
        'timezone_id': random.choice(TIMEZONES),
        'geolocation': {
            'latitude': round(random.uniform(20, 60), 7),
            'longitude': round(random.uniform(-150, 150), 7),
            'accuracy': round(random.uniform(1, 100))
        },
        'color_scheme': 'dark' if random.random() > 0.5 else 'light',
        'reduced_motion': 'reduce' if random.random() > 0.8 else 'no-preference',
        'has_touch': True,
        'is_mobile': True,
        'device_scale_factor': random.choice([2, 2.5, 3, 3.5]),
    }

def apply_stealth_js(page: Page) -> None:
    """
    Apply stealth JavaScript to avoid bot detection
    
    Args:
        page: Playwright page
    """
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
    
    // Add missing plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {
                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "Chrome PDF Plugin"
            },
            {
                0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                description: "Portable Document Format",
                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                length: 1,
                name: "Chrome PDF Viewer"
            },
            {
                0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                description: "Native Client",
                filename: "internal-nacl-plugin",
                length: 2,
                name: "Native Client"
            }
        ],
        configurable: true
    });
    
    // Add language data
    Object.defineProperty(navigator, 'languages', {
        get: () => ['ja-JP', 'ja', 'en-US', 'en'],
        configurable: true
    });
    
    // Modify user agent data
    if (navigator.userAgentData) {
        Object.defineProperty(navigator.userAgentData, 'mobile', {
            get: () => true,
            configurable: true
        });
    }
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
    Wait for user to manually login to Instagram with enhanced stealth mode
    
    Args:
        page: Playwright page
        cookie_file: Path to save cookies
        timeout: Maximum time to wait for login in seconds
        
    Returns:
        True if login successful, False otherwise
    """
    logger.info("Please login manually in the browser window")
    logger.info(f"Waiting up to {timeout} seconds for login...")
    
    try:
        page.goto('https://www.instagram.com/accounts/login/', timeout=30000)
        
        if not page.locator('input[name="username"]').count() > 0:
            logger.warning("Login form not detected, trying alternative approach...")
            
            page.goto('https://www.instagram.com/', timeout=30000)
            page.wait_for_timeout(3000)  # Wait a bit before navigating to login
            
            if page.locator('a:has-text("Log in")').count() > 0:
                page.click('a:has-text("Log in")')
            else:
                page.goto('https://www.instagram.com/accounts/login/', timeout=30000)
        
        try:
            page.wait_for_selector('input[name="username"]', timeout=10000)
            logger.info("Login form detected successfully")
        except PlaywrightTimeoutError:
            logger.warning("Login form not visible, but continuing to wait for manual login")
    
    except Exception as e:
        logger.error(f"Error navigating to login page: {e}")
        logger.info("Continuing to wait for manual login regardless of errors")
    
    # Wait for user to complete login
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            if is_logged_in(page):
                logger.info("Manual login successful")
                
                handle_post_login_dialogs(page)
                
                # Save cookies
                save_cookies(page.context, cookie_file)
                return True
        except Exception as e:
            logger.warning(f"Error checking login status: {e}")
        
        # Check if we need to refresh the page due to potential bot detection
        try:
            if page.locator('text="Please wait a few minutes before you try again."').count() > 0:
                logger.warning("Bot detection message found, refreshing page...")
                page.reload(timeout=30000)
                page.wait_for_timeout(5000)  # Wait after reload
            
            if page.locator('text="Sorry, something went wrong."').count() > 0:
                logger.warning("Error message found, refreshing page...")
                page.reload(timeout=30000)
                page.wait_for_timeout(5000)  # Wait after reload
        except Exception as e:
            logger.debug(f"Error checking for bot detection: {e}")
        
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
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--disable-blink-features',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # Get stealth configuration
        stealth_config = get_stealth_config()
        
        context = browser.new_context(
            viewport=stealth_config['viewport'],
            user_agent=stealth_config['user_agent'],
            locale=stealth_config['locale'],
            timezone_id=stealth_config['timezone_id'],
            geolocation=stealth_config['geolocation'],
            color_scheme=stealth_config['color_scheme'],
            reduced_motion=stealth_config['reduced_motion'],
            has_touch=stealth_config['has_touch'],
            is_mobile=stealth_config['is_mobile'],
            device_scale_factor=stealth_config['device_scale_factor']
        )
        
        page = context.new_page()
        
        # Apply stealth JavaScript to avoid bot detection
        apply_stealth_js(page)
        
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

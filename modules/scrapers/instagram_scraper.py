"""
Instagram scraper module for SNS video script generation pipeline.
Uses Playwright to scrape Instagram Reels without using the official API.
"""

import os
import re
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, TimeoutError

from .base_scraper import BaseScraper

class InstagramScraper(BaseScraper):
    """Scraper for Instagram Reels."""
    
    def __init__(
        self, 
        output_dir: str = "projects/default", 
        max_videos: int = 20,
        min_engagement: float = 2.0,
        cookie_path: str = "cookie.json",
        user_data_dir: str = "~/.insta-profile"
    ):
        """
        Initialize the Instagram scraper.
        
        Args:
            output_dir: Directory to save output files
            max_videos: Maximum number of videos to scrape
            min_engagement: Minimum engagement ratio (views/followers)
            cookie_path: Path to cookie.json file for authentication
            user_data_dir: Path to Chrome user data directory
        """
        super().__init__(output_dir, max_videos)
        self.min_engagement = min_engagement
        self.cookie_path = cookie_path
        self.user_data_dir = os.path.expanduser(user_data_dir)
        self.browser = None
        self.page = None
    
    async def _init_browser(self) -> None:
        """Initialize browser with cookies for authentication."""
        self.logger.info("Initializing browser")
        
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        playwright = await async_playwright().start()
        
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if not os.path.exists(chrome_path):
            chrome_path = None
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for production
            slow_mo=100,
            executable_path=chrome_path,
            args=[f"--user-data-dir={self.user_data_dir}"]
        )
        
        self.page = await self.browser.new_page()
        
        if os.path.exists(self.cookie_path):
            self.logger.info(f"Loading cookies from {self.cookie_path}")
            with open(self.cookie_path, 'r') as f:
                cookies = json.load(f)
                await self.page.context.add_cookies(cookies)
    
    async def _close_browser(self) -> None:
        """Close browser."""
        if self.browser:
            self.logger.info("Closing browser")
            await self.browser.close()
            self.browser = None
            self.page = None
    
    async def search(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for Instagram Reels based on keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of video metadata dictionaries
        """
        self.logger.info(f"Searching Instagram for '{keyword}'")
        
        try:
            if not self.browser or not self.page:
                await self._init_browser()
            
            await self.page.goto("https://www.instagram.com/")
            
            await self.page.wait_for_selector("input[placeholder='Search']", timeout=10000)
            
            search_input = await self.page.query_selector("input[placeholder='Search']")
            await search_input.click()
            await search_input.fill(keyword)
            
            await self.page.wait_for_timeout(2000)
            
            hashtag_selector = f"a[href*='/explore/tags/{keyword.replace(' ', '')}']"
            try:
                await self.page.wait_for_selector(hashtag_selector, timeout=5000)
                await self.page.click(hashtag_selector)
            except TimeoutError:
                self.logger.warning(f"Hashtag '{keyword}' not found, trying explore page")
                await self.page.goto("https://www.instagram.com/explore/")
            
            await self.page.wait_for_timeout(3000)
            
            for _ in range(5):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                await self.page.wait_for_timeout(1000)
            
            self.results = await self._extract_videos()
            
            self.logger.info(f"Found {len(self.results)} Instagram Reels")
            return self.results
            
        except Exception as e:
            self.logger.error(f"Error searching Instagram: {e}")
            raise
        finally:
            await self._close_browser()
    
    async def _extract_videos(self) -> List[Dict[str, Any]]:
        """
        Extract video URLs and metadata from current page.
        
        Returns:
            List of video metadata dictionaries
        """
        videos = []
        
        video_elements = await self.page.query_selector_all("article a")
        
        for i, element in enumerate(video_elements):
            if i >= self.max_videos:
                break
                
            try:
                href = await element.get_attribute("href")
                if not href or "/reel/" not in href and "/p/" not in href:
                    continue
                
                video_url = f"https://www.instagram.com{href}"
                
                video_page = await self.browser.new_page()
                await video_page.goto(video_url)
                await video_page.wait_for_timeout(2000)
                
                html = await video_page.content()
                
                view_count = 0
                view_match = re.search(r'"play_count":(\d+)', html)
                if view_match:
                    view_count = int(view_match.group(1))
                
                like_count = 0
                like_match = re.search(r'"like_count":(\d+)', html)
                if like_match:
                    like_count = int(like_match.group(1))
                
                username = ""
                username_match = re.search(r'"username":"([^"]+)"', html)
                if username_match:
                    username = username_match.group(1)
                
                follower_count = 0
                follower_match = re.search(r'"edge_followed_by":{"count":(\d+)}', html)
                if follower_match:
                    follower_count = int(follower_match.group(1))
                
                engagement_ratio = 0
                if follower_count > 0:
                    engagement_ratio = view_count / follower_count
                
                video_id = ""
                id_match = re.search(r'/(?:reel|p)/([^/]+)', video_url)
                if id_match:
                    video_id = id_match.group(1)
                
                if engagement_ratio >= self.min_engagement:
                    videos.append({
                        "platform": "Instagram",
                        "url": video_url,
                        "video_id": video_id,
                        "username": username,
                        "view_count": view_count,
                        "like_count": like_count,
                        "follower_count": follower_count,
                        "engagement_ratio": engagement_ratio,
                        "scraped_at": datetime.now().isoformat()
                    })
                
                await video_page.close()
                
            except Exception as e:
                self.logger.error(f"Error extracting video metadata: {e}")
        
        videos.sort(key=lambda x: x.get("engagement_ratio", 0), reverse=True)
        
        return videos[:self.max_videos]

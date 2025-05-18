"""
YouTube scraper module for SNS video script generation pipeline.
Uses Playwright to scrape YouTube Shorts without using the official API.
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

class YouTubeScraper(BaseScraper):
    """Scraper for YouTube Shorts."""
    
    def __init__(
        self, 
        output_dir: str = "projects/default", 
        max_videos: int = 20,
        min_engagement: float = 2.0,
        cookie_path: str = "cookie.json",
        user_data_dir: str = "~/.youtube-profile"
    ):
        """
        Initialize the YouTube scraper.
        
        Args:
            output_dir: Directory to save output files
            max_videos: Maximum number of videos to scrape
            min_engagement: Minimum engagement ratio (views/subscribers)
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
        Search for YouTube Shorts based on keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of video metadata dictionaries
        """
        self.logger.info(f"Searching YouTube for '{keyword}'")
        
        try:
            if not self.browser or not self.page:
                await self._init_browser()
            
            search_url = f"https://www.youtube.com/results?search_query={keyword.replace(' ', '+')}&sp=EgIYAQ%253D%253D"  # EgIYAQ%253D%253D is the filter for Shorts
            await self.page.goto(search_url)
            
            await self.page.wait_for_timeout(3000)
            
            for _ in range(5):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                await self.page.wait_for_timeout(1000)
            
            self.results = await self._extract_videos()
            
            self.logger.info(f"Found {len(self.results)} YouTube Shorts")
            return self.results
            
        except Exception as e:
            self.logger.error(f"Error searching YouTube: {e}")
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
        
        video_elements = await self.page.query_selector_all("a#video-title-link, a.ytd-video-renderer")
        
        for i, element in enumerate(video_elements):
            if i >= self.max_videos:
                break
                
            try:
                href = await element.get_attribute("href")
                if not href or "/shorts/" not in href:
                    continue
                
                video_url = f"https://www.youtube.com{href}"
                
                video_page = await self.browser.new_page()
                await video_page.goto(video_url)
                await video_page.wait_for_timeout(2000)
                
                html = await video_page.content()
                
                view_count = 0
                view_match = re.search(r'"viewCount":"([^"]+)"', html) or re.search(r'"viewCount":\s*"([^"]+)"', html)
                if view_match:
                    view_count_str = view_match.group(1).replace(',', '')
                    view_count = int(re.sub(r'\D', '', view_count_str))
                
                like_count = 0
                like_match = re.search(r'"likeCount":"([^"]+)"', html) or re.search(r'"likeCount":\s*"([^"]+)"', html)
                if like_match:
                    like_count_str = like_match.group(1).replace(',', '')
                    like_count = int(re.sub(r'\D', '', like_count_str))
                
                channel_name = ""
                channel_match = re.search(r'"ownerChannelName":"([^"]+)"', html)
                if channel_match:
                    channel_name = channel_match.group(1)
                
                subscriber_count = 0
                subscriber_match = re.search(r'"subscriberCountText":\s*{"simpleText":"([^"]+)"', html)
                if subscriber_match:
                    subscriber_str = subscriber_match.group(1).replace(' subscribers', '').replace(',', '')
                    if 'K' in subscriber_str:
                        subscriber_count = int(float(subscriber_str.replace('K', '')) * 1000)
                    elif 'M' in subscriber_str:
                        subscriber_count = int(float(subscriber_str.replace('M', '')) * 1000000)
                    else:
                        subscriber_count = int(re.sub(r'\D', '', subscriber_str))
                
                engagement_ratio = 0
                if subscriber_count > 0:
                    engagement_ratio = view_count / subscriber_count
                
                video_id = ""
                id_match = re.search(r'/shorts/([^/?&]+)', video_url)
                if id_match:
                    video_id = id_match.group(1)
                
                if engagement_ratio >= self.min_engagement:
                    videos.append({
                        "platform": "YouTube",
                        "url": video_url,
                        "video_id": video_id,
                        "channel_name": channel_name,
                        "view_count": view_count,
                        "like_count": like_count,
                        "subscriber_count": subscriber_count,
                        "engagement_ratio": engagement_ratio,
                        "scraped_at": datetime.now().isoformat()
                    })
                
                await video_page.close()
                
            except Exception as e:
                self.logger.error(f"Error extracting video metadata: {e}")
        
        videos.sort(key=lambda x: x.get("engagement_ratio", 0), reverse=True)
        
        return videos[:self.max_videos]

"""
Video downloader module for SNS video script generation pipeline.
Uses yt-dlp to download videos from Instagram, TikTok, and YouTube.
"""

import os
import json
import logging
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path

class VideoDownloader:
    """Video downloader for social media platforms."""
    
    def __init__(
        self, 
        output_dir: str = "projects/default/downloads",
        cookie_path: str = "cookie.json",
        cookie_txt_path: str = "cookie.txt"
    ):
        """
        Initialize the video downloader.
        
        Args:
            output_dir: Directory to save downloaded videos
            cookie_path: Path to cookie.json file for authentication
            cookie_txt_path: Path to cookie.txt file for yt-dlp
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = output_dir
        self.cookie_path = cookie_path
        self.cookie_txt_path = cookie_txt_path
        
        os.makedirs(output_dir, exist_ok=True)
        
        self._convert_cookies_if_needed()
    
    def _convert_cookies_if_needed(self) -> None:
        """Convert cookie.json to cookie.txt format for yt-dlp."""
        if not os.path.exists(self.cookie_path):
            self.logger.warning(f"Cookie file not found: {self.cookie_path}")
            return
            
        if os.path.exists(self.cookie_txt_path):
            if os.path.getmtime(self.cookie_txt_path) > os.path.getmtime(self.cookie_path):
                self.logger.info(f"Using existing cookie.txt file: {self.cookie_txt_path}")
                return
        
        try:
            self.logger.info(f"Converting {self.cookie_path} to {self.cookie_txt_path}")
            
            with open(self.cookie_path, 'r') as f:
                cookies = json.load(f)
            
            with open(self.cookie_txt_path, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                
                for cookie in cookies:
                    domain = cookie.get('domain', '')
                    flag = 'TRUE'
                    path = cookie.get('path', '/')
                    secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                    expiry = str(int(cookie.get('expires', 0)))
                    name = cookie.get('name', '')
                    value = cookie.get('value', '')
                    
                    if name and value and domain:
                        f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
            
            self.logger.info(f"Successfully converted cookies to {self.cookie_txt_path}")
            
        except Exception as e:
            self.logger.error(f"Error converting cookies: {e}")
    
    def download(self, video_data: Dict[str, Any]) -> Optional[str]:
        """
        Download video from URL.
        
        Args:
            video_data: Video metadata dictionary with URL
            
        Returns:
            Path to downloaded video file or None if download failed
        """
        if 'url' not in video_data:
            self.logger.error("Missing URL in video data")
            return None
        
        url = video_data['url']
        platform = video_data.get('platform', self._detect_platform(url))
        video_id = video_data.get('video_id', self._extract_video_id(url, platform))
        
        if not video_id:
            self.logger.error(f"Could not extract video ID from URL: {url}")
            return None
        
        output_filename = f"{platform.lower()}_{video_id}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        if os.path.exists(output_path):
            self.logger.info(f"Video already exists: {output_path}")
            return output_path
        
        user_agent = self._get_user_agent(platform)
        
        cmd = [
            "yt-dlp",
            url,
            "--cookies", self.cookie_txt_path,
            "--user-agent", user_agent,
            "-o", output_path,
            "--no-warnings",
            "--no-progress",
            "--quiet"
        ]
        
        if platform == "Instagram":
            cmd.extend(["--add-header", "Accept-Language: en-US,en;q=0.9"])
        elif platform == "TikTok":
            cmd.extend(["--add-header", "Referer: https://www.tiktok.com/"])
        
        try:
            self.logger.info(f"Downloading {platform} video: {url}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error downloading video: {result.stderr}")
                return None
            
            if not os.path.exists(output_path):
                self.logger.error(f"Download completed but file not found: {output_path}")
                return None
            
            self.logger.info(f"Successfully downloaded video to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error downloading video: {e}")
            return None
    
    def batch_download(self, videos_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Download multiple videos.
        
        Args:
            videos_data: List of video metadata dictionaries
            
        Returns:
            Dictionary mapping video URLs to local file paths
        """
        results = {}
        
        for video_data in videos_data:
            url = video_data.get('url')
            if not url:
                continue
                
            output_path = self.download(video_data)
            if output_path:
                results[url] = output_path
        
        self.logger.info(f"Downloaded {len(results)}/{len(videos_data)} videos")
        return results
    
    def _detect_platform(self, url: str) -> str:
        """
        Detect platform from URL.
        
        Args:
            url: Video URL
            
        Returns:
            Platform name (Instagram, TikTok, YouTube)
        """
        if "instagram.com" in url:
            return "Instagram"
        elif "tiktok.com" in url:
            return "TikTok"
        elif "youtube.com" in url or "youtu.be" in url:
            return "YouTube"
        else:
            return "Unknown"
    
    def _extract_video_id(self, url: str, platform: str) -> Optional[str]:
        """
        Extract video ID from URL.
        
        Args:
            url: Video URL
            platform: Platform name
            
        Returns:
            Video ID or None if extraction failed
        """
        import re
        
        if platform == "Instagram":
            match = re.search(r'/(?:reel|p)/([^/]+)', url)
            if match:
                return match.group(1)
        elif platform == "TikTok":
            match = re.search(r'/video/(\d+)', url)
            if match:
                return match.group(1)
        elif platform == "YouTube":
            match = re.search(r'(?:v=|shorts/|youtu\.be/)([^&?/]+)', url)
            if match:
                return match.group(1)
        
        return None
    
    def _get_user_agent(self, platform: str) -> str:
        """
        Get user agent for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            User agent string
        """
        if platform == "Instagram" or platform == "TikTok":
            return "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        else:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

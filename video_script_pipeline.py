"""
API-less video script generation pipeline.
Collects trending videos from social media platforms, downloads them,
transcribes the audio, and generates scripts based on the transcripts.
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("video_script_pipeline")

try:
    from modules.scrapers.instagram_scraper import InstagramScraper
    from modules.scrapers.tiktok_scraper import TikTokScraper
    from modules.scrapers.youtube_scraper import YouTubeScraper
    from modules.downloaders.video_downloader import VideoDownloader
    from modules.transcribers.whisper_transcriber import WhisperTranscriber
    from modules.generators.script_generator import ScriptGenerator
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    logger.error("Make sure all required modules are installed.")
    sys.exit(1)

class VideoScriptPipeline:
    """API-less video script generation pipeline."""
    
    def __init__(
        self,
        project_id: str = "default",
        platforms: List[str] = ["Instagram", "TikTok", "YouTube"],
        max_videos: int = 10,
        min_engagement: float = 2.0,
        cookie_path: str = "cookie.json",
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the video script pipeline.
        
        Args:
            project_id: Project ID for output directory
            platforms: List of platforms to scrape
            max_videos: Maximum number of videos to process per platform
            min_engagement: Minimum engagement ratio for videos
            cookie_path: Path to cookie.json file for authentication
            openai_api_key: OpenAI API key (if None, uses environment variable)
        """
        self.project_id = project_id
        self.platforms = platforms
        self.max_videos = max_videos
        self.min_engagement = min_engagement
        self.cookie_path = cookie_path
        self.openai_api_key = openai_api_key
        
        self.project_dir = f"projects/{project_id}"
        self.downloads_dir = f"{self.project_dir}/downloads"
        self.transcripts_dir = f"{self.project_dir}/transcripts"
        self.scripts_dir = f"{self.project_dir}/scripts"
        
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.transcripts_dir, exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        self.scrapers = {
            "Instagram": InstagramScraper(
                output_dir=self.project_dir,
                max_videos=max_videos,
                min_engagement=min_engagement,
                cookie_path=cookie_path
            ),
            "TikTok": TikTokScraper(
                output_dir=self.project_dir,
                max_videos=max_videos,
                min_engagement=min_engagement,
                cookie_path=cookie_path
            ),
            "YouTube": YouTubeScraper(
                output_dir=self.project_dir,
                max_videos=max_videos,
                min_engagement=min_engagement,
                cookie_path=cookie_path
            )
        }
        
        self.downloader = VideoDownloader(
            output_dir=self.downloads_dir,
            cookie_path=cookie_path
        )
        
        self.transcriber = WhisperTranscriber(
            output_dir=self.transcripts_dir,
            api_key=openai_api_key
        )
        
        self.generator = ScriptGenerator(
            output_dir=self.scripts_dir,
            api_key=openai_api_key
        )
        
        self.results = {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "platforms": platforms,
            "videos": [],
            "scripts": []
        }
    
    async def run(self, keyword: str, target_audience: str = "20-35歳の女性") -> Dict[str, Any]:
        """
        Run the complete pipeline.
        
        Args:
            keyword: Search keyword
            target_audience: Target audience description
            
        Returns:
            Dictionary with pipeline results
        """
        logger.info(f"Starting video script pipeline for keyword: {keyword}")
        start_time = time.time()
        
        videos_data = await self._collect_videos(keyword)
        
        video_paths = self._download_videos(videos_data)
        
        transcripts = self._transcribe_videos(video_paths)
        
        scripts = self._generate_scripts(transcripts, target_audience)
        
        self._save_results()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")
        
        return self.results
    
    async def _collect_videos(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Collect video URLs from platforms.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of video metadata dictionaries
        """
        logger.info(f"Collecting videos for keyword: {keyword}")
        videos_data = []
        
        for platform in self.platforms:
            if platform not in self.scrapers:
                logger.warning(f"Scraper not found for platform: {platform}")
                continue
            
            try:
                logger.info(f"Searching {platform} for '{keyword}'")
                scraper = self.scrapers[platform]
                platform_videos = await scraper.search(keyword)
                
                if platform_videos:
                    videos_data.extend(platform_videos)
                    logger.info(f"Found {len(platform_videos)} videos on {platform}")
                else:
                    logger.warning(f"No videos found on {platform}")
                
            except Exception as e:
                logger.error(f"Error collecting videos from {platform}: {e}")
        
        videos_data.sort(key=lambda x: x.get("engagement_ratio", 0), reverse=True)
        
        videos_data = videos_data[:self.max_videos]
        
        self.results["videos"] = videos_data
        
        logger.info(f"Collected {len(videos_data)} videos in total")
        return videos_data
    
    def _download_videos(self, videos_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Download videos.
        
        Args:
            videos_data: List of video metadata dictionaries
            
        Returns:
            Dictionary mapping video URLs to local file paths
        """
        logger.info(f"Downloading {len(videos_data)} videos")
        
        video_paths = self.downloader.batch_download(videos_data)
        
        for video in self.results["videos"]:
            if video.get("url") in video_paths:
                video["local_path"] = video_paths[video["url"]]
        
        logger.info(f"Downloaded {len(video_paths)} videos")
        return video_paths
    
    def _transcribe_videos(self, video_paths: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Transcribe videos.
        
        Args:
            video_paths: Dictionary mapping video URLs to local file paths
            
        Returns:
            Dictionary mapping video URLs to transcription results
        """
        logger.info(f"Transcribing {len(video_paths)} videos")
        
        transcripts = self.transcriber.batch_transcribe(video_paths)
        
        for video in self.results["videos"]:
            if video.get("url") in transcripts:
                video["transcript"] = transcripts[video["url"]].get("text", "")
                video["transcript_path"] = os.path.join(
                    self.transcripts_dir,
                    f"{self._extract_video_id(video['url'])}.json"
                )
        
        logger.info(f"Transcribed {len(transcripts)} videos")
        return transcripts
    
    def _generate_scripts(
        self,
        transcripts: Dict[str, Dict[str, Any]],
        target_audience: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate scripts based on transcripts.
        
        Args:
            transcripts: Dictionary mapping video URLs to transcription results
            target_audience: Target audience description
            
        Returns:
            Dictionary mapping video URLs to lists of generated scripts
        """
        logger.info(f"Generating scripts for {len(transcripts)} videos")
        
        scripts = self.generator.batch_generate(
            transcripts=transcripts,
            target_audience=target_audience,
            num_options=2
        )
        
        script_list = []
        for url, options in scripts.items():
            for option in options:
                script_entry = {
                    "url": url,
                    "option_id": option.get("option_id", 1),
                    "title": option.get("title", ""),
                    "platform": option.get("platform", ""),
                    "style": option.get("style", ""),
                    "target_audience": option.get("target_audience", ""),
                    "script_path": os.path.join(
                        self.scripts_dir,
                        f"{self._extract_video_id(url)}_option{option.get('option_id', 1)}_script.json"
                    )
                }
                script_list.append(script_entry)
        
        self.results["scripts"] = script_list
        
        logger.info(f"Generated scripts for {len(scripts)} videos")
        return scripts
    
    def _save_results(self) -> str:
        """
        Save pipeline results to JSON file.
        
        Returns:
            Path to results file
        """
        results_path = os.path.join(self.project_dir, "pipeline_results.json")
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved pipeline results to {results_path}")
        return results_path
    
    def _extract_video_id(self, url: str) -> str:
        """
        Extract video ID from URL.
        
        Args:
            url: Video URL
            
        Returns:
            Video ID
        """
        import re
        
        if "instagram.com" in url:
            match = re.search(r'/(?:reel|p)/([^/]+)', url)
            if match:
                return f"instagram_{match.group(1)}"
        elif "tiktok.com" in url:
            match = re.search(r'/video/(\d+)', url)
            if match:
                return f"tiktok_{match.group(1)}"
        elif "youtube.com" in url or "youtu.be" in url:
            match = re.search(r'(?:v=|shorts/|youtu\.be/)([^&?/]+)', url)
            if match:
                return f"youtube_{match.group(1)}"
        
        return f"video_{int(time.time())}"

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="API-less video script generation pipeline")
    parser.add_argument("keyword", help="Search keyword")
    parser.add_argument("--project-id", default=f"project_{int(time.time())}", help="Project ID")
    parser.add_argument("--platforms", default="Instagram,TikTok,YouTube", help="Comma-separated list of platforms")
    parser.add_argument("--max-videos", type=int, default=10, help="Maximum number of videos to process per platform")
    parser.add_argument("--min-engagement", type=float, default=2.0, help="Minimum engagement ratio for videos")
    parser.add_argument("--cookie-path", default="cookie.json", help="Path to cookie.json file")
    parser.add_argument("--target-audience", default="20-35歳の女性", help="Target audience description")
    
    args = parser.parse_args()
    
    platforms = args.platforms.split(",")
    
    pipeline = VideoScriptPipeline(
        project_id=args.project_id,
        platforms=platforms,
        max_videos=args.max_videos,
        min_engagement=args.min_engagement,
        cookie_path=args.cookie_path
    )
    
    results = await pipeline.run(args.keyword, args.target_audience)
    
    print(f"\nPipeline completed for project: {args.project_id}")
    print(f"Videos collected: {len(results['videos'])}")
    print(f"Scripts generated: {len(results['scripts'])}")
    print(f"Results saved to: projects/{args.project_id}/pipeline_results.json")

if __name__ == "__main__":
    asyncio.run(main())

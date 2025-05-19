"""
Base scraper module for SNS video script generation pipeline.
Provides common functionality for all platform-specific scrapers.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseScraper(ABC):
    """Base class for all platform-specific scrapers."""
    
    def __init__(
        self, 
        output_dir: str = "projects/default", 
        max_videos: int = 20,
        max_retries: int = 3
    ):
        """
        Initialize the base scraper.
        
        Args:
            output_dir: Directory to save output files
            max_videos: Maximum number of videos to scrape
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = output_dir
        self.max_videos = max_videos
        self.max_retries = max_retries
        self.results = []
        self.failed_urls = []
        
        os.makedirs(output_dir, exist_ok=True)
    
    @abstractmethod
    async def search(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for videos based on keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of video metadata dictionaries
        """
        pass
    
    def save_results(self, filename: str = "output_urls.json") -> str:
        """
        Save scraping results to JSON file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = os.path.join(self.output_dir, filename)
        
        for result in self.results:
            if "scraped_at" not in result:
                result["scraped_at"] = datetime.now().isoformat()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved {len(self.results)} results to {output_path}")
        return output_path
    
    def load_results(self, filename: str = "output_urls.json") -> List[Dict[str, Any]]:
        """
        Load previously saved results.
        
        Args:
            filename: Input filename
            
        Returns:
            List of video metadata dictionaries
        """
        input_path = os.path.join(self.output_dir, filename)
        
        if not os.path.exists(input_path):
            self.logger.warning(f"File not found: {input_path}")
            return []
        
        with open(input_path, 'r', encoding='utf-8') as f:
            self.results = json.load(f)
        
        self.logger.info(f"Loaded {len(self.results)} results from {input_path}")
        return self.results
    
    def filter_results(self, min_engagement: float = 0.0) -> List[Dict[str, Any]]:
        """
        Filter results based on engagement metrics.
        
        Args:
            min_engagement: Minimum engagement ratio
            
        Returns:
            Filtered list of video metadata dictionaries
        """
        filtered = []
        
        for result in self.results:
            if "engagement_ratio" not in result:
                continue
                
            if result["engagement_ratio"] >= min_engagement:
                filtered.append(result)
        
        self.logger.info(f"Filtered {len(filtered)}/{len(self.results)} results with min_engagement={min_engagement}")
        return filtered
        
    def save_failed_urls(self, filename: str = "failed_urls.json") -> str:
        """
        Save failed URLs to JSON file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = os.path.join(self.output_dir, filename)
        
        existing_urls = []
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_urls = json.load(f)
                    if not isinstance(existing_urls, list):
                        existing_urls = []
            except Exception as e:
                self.logger.error(f"Error loading existing failed URLs: {e}")
                existing_urls = []
        
        all_failed_urls = existing_urls + self.failed_urls
        
        unique_failed_urls = []
        seen = set()
        for url in all_failed_urls:
            if url not in seen:
                seen.add(url)
                unique_failed_urls.append(url)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(unique_failed_urls, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved {len(unique_failed_urls)} failed URLs to {output_path}")
        return output_path

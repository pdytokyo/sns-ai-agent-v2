from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from modules.gpt_url_scraper import GPTUrlScraper

router = APIRouter()
logger = logging.getLogger("url_scraper_router")

class UrlScraperRequest(BaseModel):
    keyword: str
    platform: Optional[str] = "Instagram"
    count: Optional[int] = 5

class UrlScraperResponse(BaseModel):
    urls: List[Dict[str, str]]
    output_file: str

@router.post("/api/url_scraper", response_model=UrlScraperResponse)
async def scrape_urls(request: UrlScraperRequest, background_tasks: BackgroundTasks):
    """
    Scrape trending video URLs using GPT-4 with browsing capability.
    
    Args:
        request: The URL scraper request containing keyword, platform, and count.
        
    Returns:
        A response containing the scraped URLs and the path to the output JSON file.
    """
    if not request.keyword:
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    try:
        scraper = GPTUrlScraper()
        
        urls = await scraper.fetch_urls(request.keyword, request.platform, request.count)
        
        output_file = "output_urls.json"
        background_tasks.add_task(scraper.save_urls_to_json, urls, output_file)
        
        return UrlScraperResponse(
            urls=urls,
            output_file=output_file
        )
    
    except Exception as e:
        logger.error(f"Error scraping URLs: {e}")
        logger.exception("Full exception details:")
        raise HTTPException(status_code=500, detail=f"Error scraping URLs: {str(e)}")

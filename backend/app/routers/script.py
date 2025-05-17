from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import uuid
import os
import logging
from datetime import datetime, timedelta

from ..services.script_generator import ScriptGenerator
from ..database import (
    extract_and_save_keywords,
    get_reels_by_audience,
    save_script,
    save_user_feedback,
    get_client_settings
)

logger = logging.getLogger("script_router")

router = APIRouter()
script_generator = ScriptGenerator()

class ThemeRequest(BaseModel):
    theme: str
    client_id: Optional[str] = "default"
    target: Optional[Dict[str, str]] = None
    need_video: Optional[bool] = False

class ScriptSaveRequest(BaseModel):
    client_id: str
    option: int
    sections: List[Dict[str, str]]
    original_content: Optional[str] = None
    edited_content: Optional[str] = None

class ScriptResponse(BaseModel):
    script: str
    alt: str
    matching_reels_count: int = 0

class ScriptDetailResponse(BaseModel):
    id: str
    sections: List[Dict[str, str]]
    created_at: str

def format_script_to_string(script: Dict[str, Any]) -> str:
    """Format script sections into a single string"""
    if not script or 'sections' not in script:
        return ""
    
    sections = script.get('sections', [])
    content_parts = []
    
    for section in sections:
        if 'content' in section:
            content_parts.append(section['content'])
    
    return "\n\n".join(content_parts)

@router.post("/api/script", response_model=ScriptResponse)
async def generate_script(request: ThemeRequest, background_tasks: BackgroundTasks):
    """
    Generate script options based on theme and target audience
    
    Steps:
    1. Extract keywords from theme
    2. Find matching reels based on target audience
    3. Download media and transcribe if needed
    4. Generate two script options based on reel structure
    5. Return formatted scripts
    """
    if not request.theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    keywords = extract_and_save_keywords(request.theme, request.client_id)
    
    target = request.target or {"age": "18-34", "interest": "general"}
    matching_reels = get_reels_by_audience(target)
    matching_count = len(matching_reels)
    
    trace_script, high_eng_script = script_generator.generate_scripts(
        request.client_id, request.theme, target
    )
    
    script_text = format_script_to_string(trace_script)
    alt_text = format_script_to_string(high_eng_script)
    
    background_tasks.add_task(save_script, trace_script)
    background_tasks.add_task(save_script, high_eng_script)
    
    return ScriptResponse(
        script=script_text,
        alt=alt_text,
        matching_reels_count=matching_count
    )

@router.post("/api/script/save", response_model=ScriptDetailResponse)
async def save_script_endpoint(request: ScriptSaveRequest):
    """
    Save a script and user feedback
    
    Steps:
    1. Format sections into a script object
    2. Save script to database
    3. If original and edited content provided, save user feedback
    4. Return saved script details
    """
    if not request.client_id:
        raise HTTPException(status_code=400, detail="Client ID is required")
    
    if not request.sections:
        raise HTTPException(status_code=400, detail="Script sections are required")
    
    script_id = f"script_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
    script_data = {
        "id": script_id,
        "client_id": request.client_id,
        "option": request.option,
        "sections": request.sections,
    }
    
    saved_id = save_script(script_data)
    
    if not saved_id:
        raise HTTPException(status_code=500, detail="Failed to save script")
    
    if request.original_content and request.edited_content:
        save_user_feedback(saved_id, request.original_content, request.edited_content)
    
    return ScriptDetailResponse(
        id=saved_id,
        sections=request.sections,
        created_at=datetime.now().isoformat()
    )

@router.post("/api/script/auto", response_model=ScriptResponse)
async def auto_generate_script(request: ThemeRequest, background_tasks: BackgroundTasks):
    """
    Automatically generate scripts with full 7-step pipeline
    
    Steps:
    1. Extract keywords from theme and store in SQLite
    2. Scrape SNS content (3 months, high-ER, target-match)
    3. Download media and create Whisper transcriptions
    4. Model content structure/length based on source videos
    5. Generate two script options (trace / high-eng alt) with client data
    6. Return formatted scripts for UI workflow
    7. Store edits and embed for future reference (handled by save endpoint)
    """
    import concurrent.futures
    from ig_scraper import InstagramScraper
    
    if not request.theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    keywords = extract_and_save_keywords(request.theme, request.client_id)
    
    # Get client settings and target audience
    client_settings = get_client_settings(request.client_id)
    if not client_settings:
        client_settings = {
            'client_id': request.client_id,
            'default_target': request.target or {'age': '18-34', 'interest': 'general'},
            'tone_rules': {},
            'length_limit': 500
        }
    
    target = request.target or client_settings.get('default_target', {})
    
    # Step 2: Scrape SNS content based on keywords and target
    matching_reels = []
    top_reels = []
    
    def run_instagram_scraper():
        try:
            ig_cookie = os.getenv('IG_COOKIE')
            mock_mode = False
            if not ig_cookie:
                logger.warning("IG_COOKIE not found in .env file. Using MOCK mode for Instagram scraping.")
                mock_mode = True
            
            result_reels = []
            result_matching = []
            
            with InstagramScraper(headless=True, mock_mode=mock_mode) as scraper:
                logger.info("InstagramScraper instance created")
                main_keyword = keywords[0] if keywords else request.theme
                logger.info("Calling search_reels_by_keyword")
                result_reels = scraper.search_reels_by_keyword(
                    main_keyword, 
                    top_count=10, 
                    min_engagement=0.5
                )
                logger.info(f"Top reels fetched: {len(result_reels)}")
                
                three_months_ago = datetime.now() - timedelta(days=90)
                recent_reels = [
                    reel for reel in result_reels 
                    if 'scraped_at' in reel and datetime.fromisoformat(reel['scraped_at']) > three_months_ago
                ]
                
                for reel in recent_reels[:3]:  # Process top 3 reels
                    if 'reel_id' in reel:
                        audience_data = scraper.analyze_audience(reel['reel_id'])
                        
                        match_score = 0
                        for key, value in target.items():
                            if key in audience_data and audience_data[key] == value:
                                match_score += 1
                        
                        if match_score > 0:
                            # Download and transcribe
                            media_result = scraper.download_and_transcribe(
                                reel['reel_id'], 
                                need_video=request.need_video
                            )
                            
                            if media_result.get('transcript'):
                                reel['transcript'] = media_result['transcript']
                                result_matching.append(reel)
                
                logger.info(f"Found {len(result_matching)} matching reels for target audience")
            
            return result_reels, result_matching
        except Exception as e:
            logger.error(f"Error in scraping/transcription: {e}")
            return [], []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_instagram_scraper)
        top_reels, matching_reels = future.result()
    
    if matching_reels:
        best_reel = matching_reels[0]
        
        trace_script, high_eng_script = script_generator.generate_scripts(
            request.client_id, request.theme, target
        )
    else:
        trace_script, high_eng_script = script_generator.generate_scripts(
            request.client_id, request.theme, target
        )
    
    script_text = format_script_to_string(trace_script)
    alt_text = format_script_to_string(high_eng_script)
    
    background_tasks.add_task(save_script, trace_script)
    background_tasks.add_task(save_script, high_eng_script)
    
    return ScriptResponse(
        script=script_text,
        alt=alt_text,
        matching_reels_count=len(matching_reels)
    )

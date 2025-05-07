from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import uuid
import os
from datetime import datetime
import httpx
from dotenv import load_dotenv

from ..database import save_account_analysis, get_account_analysis

load_dotenv()

router = APIRouter()

class AnalysisRequest(BaseModel):
    client_id: str
    access_token: Optional[str] = None

class AccountAnalysisResponse(BaseModel):
    account_id: str
    username: str
    followers_count: int
    media_count: int
    engagement_rate: float
    top_hashtags: List[str]
    analyzed_at: str

@router.post("/api/analysis/account", response_model=AccountAnalysisResponse)
async def analyze_account(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze Instagram account using Graph API (requires OAuth token)
    
    Steps:
    1. Validate access token
    2. Fetch account data from Instagram Graph API
    3. Calculate engagement metrics
    4. Store analysis results
    5. Return analysis summary
    """
    if not request.access_token:
        access_token = os.getenv("IG_ACCESS_TOKEN")
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail="Instagram access token is required for account analysis"
            )
    else:
        access_token = request.access_token
    
    try:
        async with httpx.AsyncClient() as client:
            account_response = await client.get(
                f"https://graph.instagram.com/me",
                params={"fields": "id,username,media_count", "access_token": access_token}
            )
            
            if account_response.status_code != 200:
                raise HTTPException(
                    status_code=account_response.status_code,
                    detail=f"Instagram API error: {account_response.text}"
                )
            
            account_data = account_response.json()
            
            media_response = await client.get(
                f"https://graph.instagram.com/me/media",
                params={
                    "fields": "id,media_type,like_count,comments_count,caption,timestamp,children{media_url}",
                    "access_token": access_token
                }
            )
            
            if media_response.status_code != 200:
                raise HTTPException(
                    status_code=media_response.status_code,
                    detail=f"Instagram API error: {media_response.text}"
                )
            
            media_data = media_response.json()
        
        total_likes = 0
        total_comments = 0
        hashtags = {}
        
        for media in media_data.get("data", []):
            total_likes += media.get("like_count", 0)
            total_comments += media.get("comments_count", 0)
            
            caption = media.get("caption", "")
            if caption:
                for word in caption.split():
                    if word.startswith("#"):
                        hashtag = word.strip("#")
                        hashtags[hashtag] = hashtags.get(hashtag, 0) + 1
        
        media_count = account_data.get("media_count", 0)
        followers_count = account_data.get("followers_count", 0)
        
        engagement_rate = 0
        if followers_count > 0 and media_count > 0:
            engagement_rate = ((total_likes + total_comments) / media_count) / followers_count * 100
        
        top_hashtags = sorted(hashtags.items(), key=lambda x: x[1], reverse=True)[:10]
        top_hashtags_list = [tag for tag, count in top_hashtags]
        
        analysis_result = {
            "account_id": account_data.get("id"),
            "username": account_data.get("username"),
            "followers_count": followers_count,
            "media_count": media_count,
            "engagement_rate": engagement_rate,
            "top_hashtags": top_hashtags_list,
            "analyzed_at": datetime.now().isoformat()
        }
        
        background_tasks.add_task(save_account_analysis, request.client_id, analysis_result)
        
        return AccountAnalysisResponse(**analysis_result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/api/analysis/account/{client_id}", response_model=AccountAnalysisResponse)
async def get_account_analysis_endpoint(client_id: str):
    """
    Get the latest account analysis for a client
    """
    analysis = get_account_analysis(client_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this client")
    
    return AccountAnalysisResponse(**analysis)

@router.post("/api/analysis/verify_token")
async def verify_token(request: AnalysisRequest):
    """
    Verify if the Instagram access token is valid
    """
    if not request.access_token:
        access_token = os.getenv("IG_ACCESS_TOKEN")
        if not access_token:
            return {"valid": False, "message": "No access token provided"}
    else:
        access_token = request.access_token
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.instagram.com/me",
                params={"fields": "id,username", "access_token": access_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "valid": True, 
                    "username": data.get("username"),
                    "account_id": data.get("id")
                }
            else:
                return {"valid": False, "message": f"Invalid token: {response.text}"}
    
    except Exception as e:
        return {"valid": False, "message": f"Error verifying token: {str(e)}"}

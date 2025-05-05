import os
import uuid
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .database import (
    init_db, insert_reel, get_reel, get_reels_by_audience,
    save_client_settings, get_client_settings,
    save_script, get_script, get_scripts_by_client
)

from .script_generator import generate_scripts_from_reels

app = FastAPI(title="Instagram Reels Script Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TargetModel(BaseModel):
    age: Optional[str] = None
    gender: Optional[str] = None
    interest: Optional[str] = None

class ScriptAutoRequest(BaseModel):
    client_id: str
    theme: str
    target: Optional[TargetModel] = None
    need_video: bool = False

class ScriptSection(BaseModel):
    type: str  # "intro", "main", "hook", "cta" など
    content: str
    duration: Optional[int] = None  # 秒単位の推奨尺

class ScriptModel(BaseModel):
    id: str
    title: str
    style: str
    sections: List[ScriptSection]
    original_reel_id: str
    engagement_stats: Dict[str, Any]

class ScriptAutoResponse(BaseModel):
    scripts: List[ScriptModel]
    matching_reels_count: int

class ScriptSaveRequest(BaseModel):
    client_id: str
    script_id: str
    option: int
    sections: List[Dict[str, Any]]

class ScriptSaveResponse(BaseModel):
    success: bool
    script_id: str

init_db()

@app.get("/")
async def root():
    """APIルートエンドポイント"""
    return {"message": "Instagram Reels Script Generator API"}

@app.post("/script/auto", response_model=ScriptAutoResponse)
async def generate_auto_script(request: ScriptAutoRequest):
    """テーマとターゲットに基づいて自動的にスクリプトを生成"""
    client_id = request.client_id
    theme = request.theme
    target = request.target
    need_video = request.need_video
    
    client_settings = get_client_settings(client_id)
    
    if not target and client_settings and client_settings.get("default_target"):
        target_dict = client_settings["default_target"]
        target = TargetModel(**target_dict)
    
    target_dict = target.dict() if target else {}
    target_dict = {k: v for k, v in target_dict.items() if v is not None}
    
    matching_reels = get_reels_by_audience(target_dict)
    matching_reels_count = len(matching_reels)
    
    if not matching_reels:
        raise HTTPException(
            status_code=404,
            detail=f"指定されたターゲット {target_dict} に一致するReelsが見つかりませんでした"
        )
    
    scripts = generate_scripts_from_reels(matching_reels, theme, target_dict, client_settings)
    
    response = ScriptAutoResponse(
        scripts=scripts,
        matching_reels_count=matching_reels_count
    )
    
    return response

@app.post("/script/save", response_model=ScriptSaveResponse)
async def save_script_endpoint(request: ScriptSaveRequest):
    """選択されたスクリプトを保存"""
    client_id = request.client_id
    script_id = request.script_id
    option = request.option
    sections = request.sections
    
    original_reel_id = sections[0].get("original_reel_id", "unknown")
    
    success = save_script(
        script_id=script_id,
        client_id=client_id,
        original_reel_id=original_reel_id,
        option=option,
        sections=sections
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="スクリプトの保存に失敗しました"
        )
    
    return ScriptSaveResponse(
        success=True,
        script_id=script_id
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

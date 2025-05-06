from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ThemeRequest(BaseModel):
    theme: str

class ScriptResponse(BaseModel):
    script: str
    alt: str

@router.post("/api/script", response_model=ScriptResponse)
async def generate_script(request: ThemeRequest):
    """
    Generate two script options based on the provided theme.
    """
    if not request.theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    script = f"# {request.theme}に関するスクリプト\n\nこんにちは、今日は{request.theme}について話します。\n\n{request.theme}は現代社会において非常に重要なトピックです。多くの人々が日々この問題に直面しています。\n\nまず、{request.theme}の基本的な概念を理解することが大切です。次に、実践的なアプローチを考えていきましょう。\n\n最後に、{request.theme}を日常生活に取り入れる方法をご紹介します。"
    alt = f"# 別の{request.theme}スクリプト\n\n皆さん、{request.theme}について考えたことはありますか？\n\n今日は{request.theme}の魅力と可能性について探っていきます。\n\n{request.theme}は私たちの生活を豊かにする可能性を秘めています。具体的な例を見ていきましょう。\n\n1. {request.theme}の歴史\n2. 現代における{request.theme}の役割\n3. 未来の{request.theme}の展望\n\nぜひコメントで皆さんの{request.theme}体験を教えてください！"
    
    return ScriptResponse(script=script, alt=alt)

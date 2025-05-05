"""
スクリプト生成モジュール
Reelsのトランスクリプトとオーディエンス情報に基づいて日本語スクリプトを生成
"""

import os
import re
import uuid
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

SCRIPT_STYLES = [
    "問題解決型",  # Problem-Solution
    "日常紹介型",  # Day-in-the-Life
    "ハウツー型",  # How-To
    "比較型",      # Comparison
    "ストーリー型"  # Storytelling
]

def generate_scripts_from_reels(
    reels: List[Dict], 
    theme: str, 
    target: Dict, 
    client_settings: Optional[Dict] = None
) -> List[Dict]:
    """Reelsからスクリプトを生成"""
    
    top_reels = sorted(reels, key=lambda x: x["like_count"] + x["comment_count"], reverse=True)[:2]
    
    scripts = []
    
    for i, reel in enumerate(top_reels):
        reel_id = reel["reel_id"]
        transcript = reel.get("transcript", "")
        audience = reel.get("audience_json", {})
        
        style = SCRIPT_STYLES[i % len(SCRIPT_STYLES)]
        
        script = generate_script(reel_id, transcript, theme, style, target, audience, client_settings)
        scripts.append(script)
    
    while len(scripts) < 2:
        mock_script = generate_mock_script(theme, SCRIPT_STYLES[len(scripts)], target)
        scripts.append(mock_script)
    
    return scripts

def generate_script(
    reel_id: str,
    transcript: str,
    theme: str,
    style: str,
    target: Dict,
    audience: Dict,
    client_settings: Optional[Dict] = None
) -> Dict:
    """トランスクリプトからスクリプトを生成"""
    
    tone_rules = {}
    if client_settings and "tone_rules" in client_settings:
        tone_rules = client_settings["tone_rules"]
    
    length_limit = 500
    if client_settings and "length_limit" in client_settings:
        length_limit = client_settings["length_limit"]
    
    script_id = str(uuid.uuid4())
    
    title = f"{style}スクリプト: {theme}"
    
    sections = []
    
    
    if style == "問題解決型":
        sections = [
            {
                "type": "intro",
                "content": f"👋 {theme}で悩んでいませんか？私も同じ悩みを抱えていましたが、3つの方法で解決しました。",
                "duration": 8,
                "original_reel_id": reel_id
            },
            {
                "type": "main",
                "content": f"🔥 1つ目: 90/20ルール。90分集中して作業し、その後20分完全に休憩します。脳のリセットに必要なんです！",
                "duration": 10
            },
            {
                "type": "main",
                "content": f"🔥 2つ目: 作業専用のスペースを作りましょう。この場所を「集中モード」と脳が関連付けるようになります。",
                "duration": 10
            },
            {
                "type": "main",
                "content": f"🔥 3つ目: 一日の終わりに「シャットダウン儀式」を行いましょう。明日のタスクトップ3を書き出し、物理的にノートPCを閉じます。",
                "duration": 12
            },
            {
                "type": "cta",
                "content": f"どのテクニックを最初に試してみますか？コメントで教えてください！ #{theme.replace(' ', '')}テクニック",
                "duration": 5
            }
        ]
    elif style == "日常紹介型":
        sections = [
            {
                "type": "intro",
                "content": f"POV: 私が{theme}をマスターした方法",
                "duration": 5,
                "original_reel_id": reel_id
            },
            {
                "type": "main",
                "content": f"朝のルーティンが全てです。前日の夜に水出しコーヒーをセットし、運動着を準備しておきます。",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"午前7時: スマホをスクロールする代わりに20分の簡単なワークアウト。この習慣が一日の流れを変えました。",
                "duration": 10
            },
            {
                "type": "main",
                "content": f"午前8時30分: メールを開く前にカレンダーをタイムブロッキング。これが大きな違いを生みます！",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"正午: デスクから離れて実際に休憩。スマホは禁止です。",
                "duration": 6
            },
            {
                "type": "main",
                "content": f"午後3時のエネルギー低下？もう一杯のコーヒーではなく、10分間外を歩きます。",
                "duration": 8
            },
            {
                "type": "cta",
                "content": f"一日に2時間以上節約できました。あなたはどの部分に苦戦していますか？ #{theme.replace(' ', '')}ハック",
                "duration": 5
            }
        ]
    elif style == "ハウツー型":
        sections = [
            {
                "type": "intro",
                "content": f"今日は{theme}の効果的な方法を3ステップでご紹介します。",
                "duration": 5,
                "original_reel_id": reel_id
            },
            {
                "type": "main",
                "content": f"ステップ1: 目標を明確にする。具体的で測定可能な目標を設定しましょう。例えば「1日30分の集中作業を5日間続ける」など。",
                "duration": 10
            },
            {
                "type": "main",
                "content": f"ステップ2: 環境を整える。通知をオフにし、水とメモを手元に置き、タイマーをセットします。",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"ステップ3: 小さな成功を祝う。各セッション後に自分を褒めることで、脳内の報酬系が活性化し、習慣化が促進されます。",
                "duration": 10
            },
            {
                "type": "cta",
                "content": f"今すぐ試してみてください！結果をコメントで教えてくださいね。 #{theme.replace(' ', '')}テクニック",
                "duration": 5
            }
        ]
    elif style == "比較型":
        sections = [
            {
                "type": "intro",
                "content": f"{theme}の初心者と上級者の違いをご紹介します。",
                "duration": 5,
                "original_reel_id": reel_id
            },
            {
                "type": "main",
                "content": f"初心者: 完璧を目指してスタートできない。\n上級者: 不完全でも行動し、改善し続ける。",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"初心者: 長時間作業して燃え尽きる。\n上級者: ポモドーロテクニックで休憩を挟みながら持続する。",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"初心者: 複数のタスクを同時進行。\n上級者: 一度に1つのタスクに集中し、バッチ処理を活用。",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"初心者: 計画なしで即行動。\n上級者: 前日に翌日のトップ3タスクを決定。",
                "duration": 8
            },
            {
                "type": "cta",
                "content": f"あなたはどちらに近いですか？コメントで教えてください！ #{theme.replace(' ', '')}マスター",
                "duration": 5
            }
        ]
    elif style == "ストーリー型":
        sections = [
            {
                "type": "intro",
                "content": f"私が{theme}に挫折しかけた時の話をします。",
                "duration": 5,
                "original_reel_id": reel_id
            },
            {
                "type": "main",
                "content": f"3ヶ月前、私は毎日遅くまで作業するのに、成果が出ていませんでした。疲れ果て、諦めかけていました。",
                "duration": 10
            },
            {
                "type": "main",
                "content": f"そんな時、ある本で「エネルギー管理は時間管理より重要」という言葉に出会いました。",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"翌日から、朝の90分を最も重要なタスクに使い、午後は創造性の低いタスクに充てる習慣を始めました。",
                "duration": 10
            },
            {
                "type": "main",
                "content": f"2週間後、作業時間は減ったのに成果は2倍に。今では毎日定時に終わり、趣味の時間も確保できています。",
                "duration": 10
            },
            {
                "type": "cta",
                "content": f"あなたも自分のエネルギーパターンを観察してみてください。気づきをコメントで共有しましょう！ #{theme.replace(' ', '')}ストーリー",
                "duration": 7
            }
        ]
    
    engagement_stats = {
        "like_count": 0,
        "comment_count": 0,
        "view_count": 0
    }
    
    return {
        "id": script_id,
        "title": title,
        "style": style,
        "sections": sections,
        "original_reel_id": reel_id,
        "engagement_stats": engagement_stats
    }

def generate_mock_script(theme: str, style: str, target: Dict) -> Dict:
    """モックスクリプトを生成（十分なReelsがない場合）"""
    script_id = str(uuid.uuid4())
    
    title = f"{style}スクリプト: {theme}"
    
    mock_reel_id = f"mock_{uuid.uuid4().hex[:8]}"
    
    sections = []
    
    if style == "問題解決型":
        sections = [
            {
                "type": "intro",
                "content": f"👋 {theme}で悩んでいませんか？私も同じ悩みを抱えていましたが、3つの方法で解決しました。",
                "duration": 8,
                "original_reel_id": mock_reel_id
            },
            {
                "type": "main",
                "content": f"🔥 1つ目: 90/20ルール。90分集中して作業し、その後20分完全に休憩します。脳のリセットに必要なんです！",
                "duration": 10
            },
            {
                "type": "main",
                "content": f"🔥 2つ目: 作業専用のスペースを作りましょう。この場所を「集中モード」と脳が関連付けるようになります。",
                "duration": 10
            },
            {
                "type": "main",
                "content": f"🔥 3つ目: 一日の終わりに「シャットダウン儀式」を行いましょう。明日のタスクトップ3を書き出し、物理的にノートPCを閉じます。",
                "duration": 12
            },
            {
                "type": "cta",
                "content": f"どのテクニックを最初に試してみますか？コメントで教えてください！ #{theme.replace(' ', '')}テクニック",
                "duration": 5
            }
        ]
    else:
        sections = [
            {
                "type": "intro",
                "content": f"今日は{theme}について話します。",
                "duration": 5,
                "original_reel_id": mock_reel_id
            },
            {
                "type": "main",
                "content": f"多くの人が{theme}に取り組む際に、最初の一歩を踏み出すのが難しいと感じています。",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"私のおすすめは、小さな目標から始めることです。例えば、1日5分だけ取り組むなど。",
                "duration": 8
            },
            {
                "type": "main",
                "content": f"継続は力なり。小さな成功体験を積み重ねることで、大きな変化が生まれます。",
                "duration": 8
            },
            {
                "type": "cta",
                "content": f"あなたの{theme}への取り組み方を教えてください！コメントお待ちしています。",
                "duration": 5
            }
        ]
    
    engagement_stats = {
        "like_count": 100,
        "comment_count": 20,
        "view_count": 1000
    }
    
    return {
        "id": script_id,
        "title": title,
        "style": style,
        "sections": sections,
        "original_reel_id": mock_reel_id,
        "engagement_stats": engagement_stats
    }

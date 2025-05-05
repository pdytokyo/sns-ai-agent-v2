import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")

def get_db_connection():
    """SQLiteデータベース接続を取得"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """データベーススキーマの初期化"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reels(
        reel_id TEXT PRIMARY KEY,
        permalink TEXT, 
        like_count INT, 
        comment_count INT,
        audio_url TEXT, 
        local_video TEXT, 
        transcript TEXT,
        audience_json TEXT, 
        scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS client_settings(
        client_id TEXT PRIMARY KEY,
        default_target TEXT,
        tone_rules TEXT,
        length_limit INT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scripts(
        id TEXT PRIMARY KEY,
        client_id TEXT, 
        original_reel_id TEXT,
        option INT, 
        sections TEXT, 
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (original_reel_id) REFERENCES reels(reel_id),
        FOREIGN KEY (client_id) REFERENCES client_settings(client_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def insert_reel(
    reel_id: str, 
    permalink: str, 
    like_count: int, 
    comment_count: int, 
    audio_url: Optional[str] = None, 
    local_video: Optional[str] = None, 
    transcript: Optional[str] = None, 
    audience_json: Optional[Dict] = None
) -> bool:
    """Reelデータをデータベースに挿入または更新"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM reels WHERE reel_id = ?", (reel_id,))
    existing = cursor.fetchone()
    
    audience_json_str = json.dumps(audience_json) if audience_json else None
    
    if existing:
        cursor.execute('''
        UPDATE reels 
        SET permalink = ?, 
            like_count = ?, 
            comment_count = ?, 
            audio_url = COALESCE(?, audio_url), 
            local_video = COALESCE(?, local_video), 
            transcript = COALESCE(?, transcript), 
            audience_json = COALESCE(?, audience_json),
            scraped_at = CURRENT_TIMESTAMP
        WHERE reel_id = ?
        ''', (
            permalink, 
            like_count, 
            comment_count, 
            audio_url, 
            local_video, 
            transcript, 
            audience_json_str,
            reel_id
        ))
    else:
        cursor.execute('''
        INSERT INTO reels (
            reel_id, permalink, like_count, comment_count, 
            audio_url, local_video, transcript, audience_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            reel_id, 
            permalink, 
            like_count, 
            comment_count, 
            audio_url, 
            local_video, 
            transcript, 
            audience_json_str
        ))
    
    conn.commit()
    conn.close()
    return True

def get_reel(reel_id: str) -> Optional[Dict]:
    """指定されたreel_idのReelデータを取得"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM reels WHERE reel_id = ?", (reel_id,))
    reel = cursor.fetchone()
    
    conn.close()
    
    if reel:
        reel_dict = dict(reel)
        if reel_dict['audience_json']:
            reel_dict['audience_json'] = json.loads(reel_dict['audience_json'])
        return reel_dict
    
    return None

def get_reels_by_audience(target: Dict[str, str], limit: int = 10) -> List[Dict]:
    """ターゲットオーディエンスに基づいてReelを取得"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT * FROM reels 
    WHERE transcript IS NOT NULL 
    AND audience_json IS NOT NULL 
    ORDER BY (like_count + comment_count) DESC
    LIMIT ?
    """, (limit,))
    
    reels = cursor.fetchall()
    conn.close()
    
    filtered_reels = []
    for reel in reels:
        reel_dict = dict(reel)
        if reel_dict['audience_json']:
            audience = json.loads(reel_dict['audience_json'])
            
            match = True
            for key, value in target.items():
                if key in audience and audience[key] != value:
                    match = False
                    break
            
            if match:
                reel_dict['audience_json'] = audience
                filtered_reels.append(reel_dict)
    
    return filtered_reels

def save_client_settings(
    client_id: str, 
    default_target: Dict[str, str], 
    tone_rules: Dict[str, Any], 
    length_limit: int
) -> bool:
    """クライアント設定を保存"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    default_target_json = json.dumps(default_target)
    tone_rules_json = json.dumps(tone_rules)
    
    cursor.execute("SELECT * FROM client_settings WHERE client_id = ?", (client_id,))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
        UPDATE client_settings 
        SET default_target = ?, 
            tone_rules = ?, 
            length_limit = ?
        WHERE client_id = ?
        ''', (default_target_json, tone_rules_json, length_limit, client_id))
    else:
        cursor.execute('''
        INSERT INTO client_settings (
            client_id, default_target, tone_rules, length_limit
        ) VALUES (?, ?, ?, ?)
        ''', (client_id, default_target_json, tone_rules_json, length_limit))
    
    conn.commit()
    conn.close()
    return True

def get_client_settings(client_id: str) -> Optional[Dict]:
    """クライアント設定を取得"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM client_settings WHERE client_id = ?", (client_id,))
    settings = cursor.fetchone()
    
    conn.close()
    
    if settings:
        settings_dict = dict(settings)
        if settings_dict['default_target']:
            settings_dict['default_target'] = json.loads(settings_dict['default_target'])
        if settings_dict['tone_rules']:
            settings_dict['tone_rules'] = json.loads(settings_dict['tone_rules'])
        return settings_dict
    
    return None

def save_script(
    script_id: str,
    client_id: str,
    original_reel_id: str,
    option: int,
    sections: List[Dict]
) -> bool:
    """生成されたスクリプトを保存"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sections_json = json.dumps(sections)
    
    cursor.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
        UPDATE scripts 
        SET client_id = ?, 
            original_reel_id = ?, 
            option = ?, 
            sections = ?,
            created_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (client_id, original_reel_id, option, sections_json, script_id))
    else:
        cursor.execute('''
        INSERT INTO scripts (
            id, client_id, original_reel_id, option, sections
        ) VALUES (?, ?, ?, ?, ?)
        ''', (script_id, client_id, original_reel_id, option, sections_json))
    
    conn.commit()
    conn.close()
    return True

def get_script(script_id: str) -> Optional[Dict]:
    """指定されたIDのスクリプトを取得"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
    script = cursor.fetchone()
    
    conn.close()
    
    if script:
        script_dict = dict(script)
        if script_dict['sections']:
            script_dict['sections'] = json.loads(script_dict['sections'])
        return script_dict
    
    return None

def get_scripts_by_client(client_id: str) -> List[Dict]:
    """クライアントIDに基づいてスクリプトを取得"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM scripts WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
    scripts = cursor.fetchall()
    
    conn.close()
    
    result = []
    for script in scripts:
        script_dict = dict(script)
        if script_dict['sections']:
            script_dict['sections'] = json.loads(script_dict['sections'])
        result.append(script_dict)
    
    return result

if __name__ == "__main__":
    init_db()

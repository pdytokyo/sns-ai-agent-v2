import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

os.makedirs(os.path.dirname(os.path.abspath(__file__)) + "/../data", exist_ok=True)
DB_PATH = os.path.dirname(os.path.abspath(__file__)) + "/../data/sns_ai_agent.db"

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
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
        default_target JSON,
        tone_rules JSON,
        length_limit INT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scripts(
        id TEXT PRIMARY KEY,
        client_id TEXT,
        original_reel_id TEXT,
        option INT,
        sections JSON,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES client_settings(client_id),
        FOREIGN KEY (original_reel_id) REFERENCES reels(reel_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keywords(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        client_id TEXT,
        frequency INTEGER DEFAULT 1,
        last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES client_settings(client_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id TEXT NOT NULL,
        original_content TEXT,
        edited_content TEXT,
        edit_distance INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (script_id) REFERENCES scripts(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def validate_schema():
    """Validate database schema and add missing columns/tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = {
        "reels": [
            "reel_id TEXT PRIMARY KEY",
            "permalink TEXT", 
            "like_count INT", 
            "comment_count INT",
            "audio_url TEXT", 
            "local_video TEXT", 
            "transcript TEXT",
            "audience_json TEXT", 
            "scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ],
        "client_settings": [
            "client_id TEXT PRIMARY KEY",
            "default_target JSON",
            "tone_rules JSON",
            "length_limit INT"
        ],
        "scripts": [
            "id TEXT PRIMARY KEY",
            "client_id TEXT",
            "original_reel_id TEXT",
            "option INT",
            "sections JSON",
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ],
        "keywords": [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "keyword TEXT NOT NULL",
            "client_id TEXT",
            "frequency INTEGER DEFAULT 1",
            "last_used DATETIME DEFAULT CURRENT_TIMESTAMP"
        ],
        "user_feedback": [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "script_id TEXT NOT NULL",
            "original_content TEXT",
            "edited_content TEXT",
            "edit_distance INTEGER",
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ]
    }
    
    for table_name, columns in tables.items():
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            column_defs = ", ".join(columns)
            cursor.execute(f"CREATE TABLE {table_name} ({column_defs})")
            print(f"Created missing table: {table_name}")
        else:
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row['name']: row for row in cursor.fetchall()}
            
            for column_def in columns:
                column_parts = column_def.split()
                column_name = column_parts[0]
                
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
                    print(f"Added missing column {column_def} to {table_name}")
    
    conn.commit()
    conn.close()

def insert_reel(reel_data: Dict[str, Any]) -> bool:
    """Insert or update a reel in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if isinstance(reel_data.get('audience_json'), dict):
        reel_data['audience_json'] = json.dumps(reel_data['audience_json'])
    
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO reels (
            reel_id, permalink, like_count, comment_count, 
            audio_url, local_video, transcript, audience_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            reel_data.get('reel_id'),
            reel_data.get('permalink'),
            reel_data.get('like_count'),
            reel_data.get('comment_count'),
            reel_data.get('audio_url'),
            reel_data.get('local_video'),
            reel_data.get('transcript'),
            reel_data.get('audience_json')
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting reel: {e}")
        return False
    finally:
        conn.close()

def get_reels_by_audience(target: Dict[str, str], limit: int = 10) -> List[Dict[str, Any]]:
    """Get reels that match the target audience criteria"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM reels 
    WHERE audience_json IS NOT NULL 
    ORDER BY scraped_at DESC
    ''')
    
    reels = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    matched_reels = []
    for reel in reels:
        try:
            audience = json.loads(reel['audience_json'])
            match_score = 0
            
            for key, value in target.items():
                if key in audience and audience[key] == value:
                    match_score += 1
            
            if match_score > 0:
                reel['match_score'] = match_score
                matched_reels.append(reel)
        except:
            continue
    
    matched_reels.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    return matched_reels[:limit]

def get_client_settings(client_id: str) -> Optional[Dict[str, Any]]:
    """Get client settings by client_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM client_settings WHERE client_id = ?', (client_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        settings = dict(row)
        if settings.get('default_target'):
            settings['default_target'] = json.loads(settings['default_target'])
        if settings.get('tone_rules'):
            settings['tone_rules'] = json.loads(settings['tone_rules'])
        return settings
    
    return None

def save_client_settings(settings: Dict[str, Any]) -> bool:
    """Save client settings to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if isinstance(settings.get('default_target'), dict):
        settings['default_target'] = json.dumps(settings['default_target'])
    if isinstance(settings.get('tone_rules'), dict):
        settings['tone_rules'] = json.dumps(settings['tone_rules'])
    
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO client_settings (
            client_id, default_target, tone_rules, length_limit
        ) VALUES (?, ?, ?, ?)
        ''', (
            settings.get('client_id'),
            settings.get('default_target'),
            settings.get('tone_rules'),
            settings.get('length_limit')
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving client settings: {e}")
        return False
    finally:
        conn.close()

def save_script(script_data: Dict[str, Any]) -> str:
    """Save a generated script to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not script_data.get('id'):
        script_data['id'] = f"script_{int(datetime.now().timestamp())}"
    
    if isinstance(script_data.get('sections'), (dict, list)):
        script_data['sections'] = json.dumps(script_data.get('sections'))
    
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO scripts (
            id, client_id, original_reel_id, option, sections
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
            script_data.get('id'),
            script_data.get('client_id'),
            script_data.get('original_reel_id'),
            script_data.get('option'),
            script_data.get('sections')
        ))
        conn.commit()
        return script_data['id']
    except Exception as e:
        print(f"Error saving script: {e}")
        return ""
    finally:
        conn.close()

def get_script(script_id: str) -> Optional[Dict[str, Any]]:
    """Get a script by its ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM scripts WHERE id = ?', (script_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        script = dict(row)
        if script.get('sections'):
            script['sections'] = json.loads(script['sections'])
        return script
    
    return None

def extract_and_save_keywords(text: str, client_id: str) -> List[str]:
    """Extract keywords from text and save to database"""
    import re
    from collections import Counter
    
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    words = text.split()
    word_counts = Counter(words)
    
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'like'}
    keywords = [word for word, count in word_counts.items() 
                if len(word) > 3 and word not in stop_words and count > 1]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for keyword in keywords:
        cursor.execute('''
        SELECT id, frequency FROM keywords 
        WHERE keyword = ? AND client_id = ?
        ''', (keyword, client_id))
        
        row = cursor.fetchone()
        if row:
            cursor.execute('''
            UPDATE keywords 
            SET frequency = ?, last_used = CURRENT_TIMESTAMP 
            WHERE id = ?
            ''', (row['frequency'] + 1, row['id']))
        else:
            cursor.execute('''
            INSERT INTO keywords (keyword, client_id) 
            VALUES (?, ?)
            ''', (keyword, client_id))
    
    conn.commit()
    conn.close()
    
    return keywords

def get_top_keywords(client_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top keywords for a client by frequency"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT keyword, frequency, last_used 
    FROM keywords 
    WHERE client_id = ? 
    ORDER BY frequency DESC 
    LIMIT ?
    ''', (client_id, limit))
    
    keywords = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return keywords

def save_user_feedback(script_id: str, original: str, edited: str) -> bool:
    """Save user feedback (edited script) to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    edit_distance = sum(1 for a, b in zip(original, edited) if a != b)
    edit_distance += abs(len(original) - len(edited))
    
    try:
        cursor.execute('''
        INSERT INTO user_feedback (
            script_id, original_content, edited_content, edit_distance
        ) VALUES (?, ?, ?, ?)
        ''', (script_id, original, edited, edit_distance))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving user feedback: {e}")
        return False
    finally:
        conn.close()

def save_account_analysis(client_id: str, analysis_data: Dict[str, Any]) -> bool:
    """Save Instagram account analysis data to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS account_analysis(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        account_id TEXT NOT NULL,
        username TEXT NOT NULL,
        followers_count INTEGER,
        media_count INTEGER,
        engagement_rate REAL,
        top_hashtags TEXT,
        analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        analysis_data JSON,
        FOREIGN KEY (client_id) REFERENCES client_settings(client_id)
    )
    ''')
    
    if isinstance(analysis_data.get('top_hashtags'), list):
        top_hashtags = ','.join(analysis_data.get('top_hashtags', []))
    else:
        top_hashtags = analysis_data.get('top_hashtags', '')
    
    analysis_json = json.dumps(analysis_data)
    
    try:
        cursor.execute('''
        INSERT INTO account_analysis (
            client_id, account_id, username, followers_count, 
            media_count, engagement_rate, top_hashtags, analyzed_at, analysis_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_id,
            analysis_data.get('account_id'),
            analysis_data.get('username'),
            analysis_data.get('followers_count', 0),
            analysis_data.get('media_count', 0),
            analysis_data.get('engagement_rate', 0.0),
            top_hashtags,
            analysis_data.get('analyzed_at', datetime.now().isoformat()),
            analysis_json
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving account analysis: {e}")
        return False
    finally:
        conn.close()

def get_account_analysis(client_id: str) -> Optional[Dict[str, Any]]:
    """Get the latest account analysis for a client"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='account_analysis'
        ''')
        if not cursor.fetchone():
            return None
        
        cursor.execute('''
        SELECT * FROM account_analysis 
        WHERE client_id = ? 
        ORDER BY analyzed_at DESC 
        LIMIT 1
        ''', (client_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        analysis = dict(row)
        
        if analysis.get('top_hashtags'):
            analysis['top_hashtags'] = analysis['top_hashtags'].split(',')
        else:
            analysis['top_hashtags'] = []
        
        if analysis.get('analysis_data'):
            try:
                full_data = json.loads(analysis['analysis_data'])
                analysis.update(full_data)
            except:
                pass
        
        return analysis
    except Exception as e:
        print(f"Error getting account analysis: {e}")
        return None
    finally:
        conn.close()

init_db()
validate_schema()

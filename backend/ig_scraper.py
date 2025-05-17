"""
Instagram Reels Scraper
-----------------------
Scrapes Instagram Reels based on keywords, extracts engagement metrics,
downloads media, and transcribes audio.

Usage:
    python ig_scraper.py "<keyword>" --top 10 --min_engage 2.0
    python ig_scraper.py --audience "<reel_id>"
    python ig_scraper.py --transcribe "<reel_id>" [--need_video]
"""

import os
import sys
import json
import time
import random
import argparse
import sqlite3
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

import requests
from playwright.sync_api import sync_playwright, Page, Browser
from sklearn.cluster import KMeans
import numpy as np

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ig_scraper')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/sns_ai_agent.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

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
    
    conn.commit()
    conn.close()

class InstagramScraper:
    """Scraper for Instagram Reels using Playwright"""
    
    def __init__(self, headless: bool = True, mock_mode: bool = False):
        """Initialize the scraper"""
        self.headless = headless
        self.browser = None
        self.page = None
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.mock_mode = mock_mode
        
        # Check if IG_TEST_COOKIE is available
        self.ig_cookie = os.getenv('IG_TEST_COOKIE')
        if not self.ig_cookie and not self.mock_mode:
            logger.warning("IG_TEST_COOKIE not found in environment. Falling back to MOCK mode.")
            self.mock_mode = True
        
        init_db()
    
    def __enter__(self):
        """Start the browser when entering context"""
        self._start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the browser when exiting context"""
        self._close_browser()
    
    def _start_browser(self):
        """Start a stealth browser session"""
        playwright = sync_playwright().start()
        
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials'
            ]
        )
        
        context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            device_scale_factor=1,
        )
        
        context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        """)
        
        self.page = context.new_page()
        
        self.page.set_default_timeout(30000)
    
    def _close_browser(self):
        """Close the browser"""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.page = None
    
    def search_reels_by_keyword(
        self, 
        keyword: str, 
        top_count: int = 10, 
        min_engagement: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Search for Reels by keyword and extract engagement metrics
        
        Args:
            keyword: Search keyword or hashtag
            top_count: Number of top Reels to extract
            min_engagement: Minimum engagement rate (%) to include
            
        Returns:
            List of Reel data dictionaries
        """
        if self.mock_mode:
            logger.warning(f"Running in MOCK mode. Generating mock data for keyword: {keyword}")
            mock_reels = self._generate_mock_reels(keyword, top_count)
            logger.info(f"Scraped {len(mock_reels)} reels for \"{keyword}\" (MOCK mode)")
            
            if len(mock_reels) == 0 and os.getenv('CI') == 'true':
                raise RuntimeError(f"No reels found for keyword: {keyword}")
                
            return mock_reels
            
        if not self.page:
            raise RuntimeError("Browser not started. Use with context manager.")
        
        logger.info(f"Searching for Reels with keyword: {keyword}")
        
        if not keyword.startswith('#'):
            hashtag = f"#{keyword}"
        else:
            hashtag = keyword
        
        self.page.goto(f"https://www.instagram.com/explore/tags/{hashtag.strip('#')}/")
        
        self.page.wait_for_selector('article', timeout=30000)
        
        for _ in range(5):
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
        
        reel_links = self.page.evaluate("""
        () => {
            const links = Array.from(document.querySelectorAll('a[href*="/reel/"]'));
            return links.map(link => link.href);
        }
        """)
        
        unique_links = list(set(reel_links))
        logger.info(f"Found {len(unique_links)} unique Reels")
        
        ninety_days_ago = datetime.now() - timedelta(days=90)
        
        reels_data = []
        for link in unique_links[:min(top_count * 2, len(unique_links))]:
            try:
                reel_data = self._extract_reel_data(link)
                
                scraped_at = datetime.fromisoformat(reel_data.get('scraped_at', datetime.now().isoformat()))
                if scraped_at < ninety_days_ago:
                    logger.info(f"Skipping Reel {reel_data['reel_id']} - older than 90 days")
                    continue
                
                if reel_data.get('like_count') and reel_data.get('view_count'):
                    engagement_rate = (reel_data['like_count'] + reel_data.get('comment_count', 0)) / reel_data['view_count'] * 100
                    reel_data['engagement_rate'] = engagement_rate
                    
                    views_followers_ratio = reel_data.get('view_count', 0) / max(1, reel_data.get('follower_count', 1000))
                    reel_data['views_followers_ratio'] = views_followers_ratio
                    
                    if engagement_rate >= min_engagement and views_followers_ratio >= 3:
                        reels_data.append(reel_data)
                        
                        self._save_reel_to_db(reel_data)
                        
                        logger.info(f"Extracted Reel {reel_data['reel_id']} with engagement rate {engagement_rate:.2f}% and views/followers ratio {views_followers_ratio:.2f}")
            except Exception as e:
                logger.error(f"Error extracting data from {link}: {e}")
        
        reels_data.sort(key=lambda x: x.get('engagement_rate', 0), reverse=True)
        scraped_reels = reels_data[:top_count]
        logger.info(f"Scraped {len(scraped_reels)} reels for \"{keyword}\"")
        
        if len(scraped_reels) == 0 and os.getenv('CI') == 'true':
            raise RuntimeError(f"No reels found for keyword: {keyword}")
            
        return scraped_reels
    
    def _extract_reel_data(self, reel_url: str) -> Dict[str, Any]:
        """
        Extract data from a Reel page
        
        Args:
            reel_url: URL of the Reel
            
        Returns:
            Dictionary with Reel data
        """
        self.page.goto(reel_url, wait_until='domcontentloaded')
        
        self.page.wait_for_selector('video', timeout=30000)
        
        reel_id = reel_url.split('/reel/')[1].split('/')[0]
        
        metrics = self.page.evaluate("""
        () => {
            const likeCount = parseInt(document.querySelector('section span')?.innerText.replace(/,/g, '') || '0');
            const commentCount = parseInt(document.querySelectorAll('section span')[1]?.innerText.replace(/,/g, '') || '0');
            const viewCount = parseInt(document.querySelector('span:has-text("views")')?.innerText.split(' ')[0].replace(/,/g, '') || '0');
            
            // Extract audio URL if available
            const audioElement = document.querySelector('audio');
            const audioUrl = audioElement ? audioElement.src : null;
            
            // Extract video URL
            const videoElement = document.querySelector('video');
            const videoUrl = videoElement ? videoElement.src : null;
            
            return { likeCount, commentCount, viewCount, audioUrl, videoUrl };
        }
        """)
        
        comments = self.page.evaluate("""
        () => {
            const commentElements = document.querySelectorAll('ul > li span:not(:has(*))');
            return Array.from(commentElements).map(el => el.innerText).slice(0, 50);
        }
        """)
        
        reel_data = {
            'reel_id': reel_id,
            'permalink': reel_url,
            'like_count': metrics.get('likeCount', 0),
            'comment_count': metrics.get('commentCount', 0),
            'view_count': metrics.get('viewCount', 0),
            'audio_url': metrics.get('audioUrl'),
            'video_url': metrics.get('videoUrl'),
            'comments': comments,
            'scraped_at': datetime.now().isoformat()
        }
        
        return reel_data
    
    def _save_reel_to_db(self, reel_data: Dict[str, Any]) -> bool:
        """Save reel data to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if 'comments' in reel_data:
                comments_json = json.dumps(reel_data['comments'], ensure_ascii=False)
                reel_data['comments_json'] = comments_json
            
            cursor.execute('''
            INSERT OR REPLACE INTO reels (
                reel_id, permalink, like_count, comment_count, audio_url
            ) VALUES (?, ?, ?, ?, ?)
            ''', (
                reel_data.get('reel_id'),
                reel_data.get('permalink'),
                reel_data.get('like_count'),
                reel_data.get('comment_count'),
                reel_data.get('audio_url')
            ))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving reel to database: {e}")
            return False
        finally:
            conn.close()
    
    def analyze_audience(self, reel_id: str) -> Dict[str, Any]:
        """
        Analyze audience demographics from comments
        
        Args:
            reel_id: ID of the Reel to analyze
            
        Returns:
            Dictionary with audience data
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reels WHERE reel_id = ?', (reel_id,))
        reel = cursor.fetchone()
        
        if not reel:
            conn.close()
            raise ValueError(f"Reel {reel_id} not found in database")
        
        comments = []
        if isinstance(reel, dict):
            has_comments = reel.get('comments_json')
            has_permalink = reel.get('permalink')
        else:
            has_comments = 'comments_json' in reel and reel['comments_json']
            has_permalink = 'permalink' in reel and reel['permalink']
            
        if has_comments:
            comments = json.loads(reel['comments_json'])
        elif has_permalink:
            self.page.goto(reel['permalink'])
            comments = self.page.evaluate("""
            () => {
                const commentElements = document.querySelectorAll('ul > li span:not(:has(*))');
                return Array.from(commentElements).map(el => el.innerText).slice(0, 50);
            }
            """)
        
        audience_data = self._analyze_comments(comments)
        logger.info(f"Audience data for {reel_id}: {audience_data}")
        
        cursor.execute('''
        UPDATE reels SET audience_json = ? WHERE reel_id = ?
        ''', (json.dumps(audience_data, ensure_ascii=False), reel_id))
        
        conn.commit()
        conn.close()
        
        return audience_data
    
    def _analyze_comments(self, comments: List[str]) -> Dict[str, Any]:
        """
        Analyze comments to extract audience demographics
        
        Args:
            comments: List of comment texts
            
        Returns:
            Dictionary with audience data
        """
        if not comments:
            return {
                'age': 'unknown',
                'gender': 'unknown',
                'interests': [],
                'keywords': []
            }
        
        all_text = ' '.join(comments).lower()
        
        age_patterns = {
            '13-17': ['学生', '高校', '中学', 'jk', '宿題', '授業'],
            '18-24': ['大学', '大学生', '就活', 'バイト', '卒論', '研究室'],
            '25-34': ['社会人', '転職', '結婚', '育児', '仕事', 'ママ', '子育て'],
            '35-44': ['子供', 'ママ', 'パパ', '家族', '住宅', 'ローン', '中年'],
            '45+': ['定年', '老後', '年金', '孫', '退職', 'シニア']
        }
        
        age_scores = {age: 0 for age in age_patterns}
        for age, keywords in age_patterns.items():
            for keyword in keywords:
                if keyword in all_text:
                    age_scores[age] += 1
        
        if max(age_scores.values()) > 0:
            age = max(age_scores.items(), key=lambda x: x[1])[0]
        else:
            age = '18-34'  # Default
        
        gender_patterns = {
            'female': ['女子', '女性', 'ママ', '彼氏', 'メイク', 'コスメ', '化粧'],
            'male': ['男子', '男性', 'パパ', '彼女', '筋トレ', 'ゲーム']
        }
        
        gender_scores = {gender: 0 for gender in gender_patterns}
        for gender, keywords in gender_patterns.items():
            for keyword in keywords:
                if keyword in all_text:
                    gender_scores[gender] += 1
        
        if max(gender_scores.values()) > 0:
            gender = max(gender_scores.items(), key=lambda x: x[1])[0]
        else:
            gender = 'unknown'
        
        interest_patterns = {
            'beauty': ['メイク', 'コスメ', '美容', 'スキンケア', '化粧'],
            'fashion': ['ファッション', 'コーデ', '服', 'ブランド', 'アパレル'],
            'food': ['料理', 'レシピ', 'グルメ', '食べ物', 'レストラン', 'カフェ'],
            'travel': ['旅行', '観光', '海外', 'ホテル', '旅'],
            'fitness': ['筋トレ', 'ジム', 'トレーニング', 'ダイエット', '運動'],
            'tech': ['テクノロジー', 'ガジェット', 'アプリ', 'プログラミング', 'IT'],
            'education': ['勉強', '学習', '教育', '受験', '資格'],
            'business': ['ビジネス', '起業', '投資', '副業', 'マーケティング'],
            'entertainment': ['エンタメ', '映画', 'ドラマ', '音楽', 'アニメ'],
            'gaming': ['ゲーム', 'ゲーマー', 'PS5', 'Switch', 'eスポーツ']
        }
        
        interest_scores = {interest: 0 for interest in interest_patterns}
        for interest, keywords in interest_patterns.items():
            for keyword in keywords:
                if keyword in all_text:
                    interest_scores[interest] += 1
        
        top_interests = [interest for interest, score in 
                        sorted(interest_scores.items(), key=lambda x: x[1], reverse=True) 
                        if score > 0][:3]
        
        words = all_text.split()
        word_freq = {}
        for word in words:
            if len(word) > 2:  # Skip very short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_keywords = [word for word, freq in 
                       sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
                       if freq > 1][:10]
        
        return {
            'age': age,
            'gender': gender,
            'interests': top_interests,
            'keywords': top_keywords
        }
    
    def download_and_transcribe(self, reel_id: str, need_video: bool = False) -> Dict[str, Any]:
        """
        Download audio/video and transcribe audio
        
        Args:
            reel_id: ID of the Reel
            need_video: Whether to download video (otherwise just audio)
            
        Returns:
            Dictionary with paths and transcript
        """
        logger.info(f"Downloading and transcribing reel: {reel_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reels WHERE reel_id = ?', (reel_id,))
        reel = cursor.fetchone()
        
        if not reel:
            conn.close()
            raise ValueError(f"Reel {reel_id} not found in database")
        
        media_dir = os.path.join(self.data_dir, "media")
        os.makedirs(media_dir, exist_ok=True)
        
        result = {}
        
        if isinstance(reel, dict):
            has_audio_url = reel.get('audio_url')
            has_permalink = reel.get('permalink')
        else:
            has_audio_url = 'audio_url' in reel and reel['audio_url']
            has_permalink = 'permalink' in reel and reel['permalink']
            
        if has_audio_url:
            audio_path = os.path.join(media_dir, f"{reel_id}.mp3")
            
            try:
                response = requests.get(reel['audio_url'], stream=True)
                with open(audio_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                
                result['audio_path'] = audio_path
                logger.info(f"Downloaded audio to {audio_path}")
            except Exception as e:
                logger.error(f"Error downloading audio: {e}")
        
        if need_video and has_permalink:
            video_path = os.path.join(media_dir, f"{reel_id}.mp4")
            
            try:
                subprocess.run([
                    'yt-dlp',
                    '-o', video_path,
                    reel['permalink']
                ], check=True)
                
                result['video_path'] = video_path
                logger.info(f"Downloaded video to {video_path}")
                
                cursor.execute('''
                UPDATE reels SET local_video = ? WHERE reel_id = ?
                ''', (video_path, reel_id))
                
                if not has_audio_url:
                    audio_path = os.path.join(media_dir, f"{reel_id}.mp3")
                    subprocess.run([
                        'ffmpeg',
                        '-i', video_path,
                        '-q:a', '0',
                        '-map', 'a',
                        audio_path
                    ], check=True)
                    
                    result['audio_path'] = audio_path
                    logger.info(f"Extracted audio to {audio_path}")
            except Exception as e:
                logger.error(f"Error downloading video: {e}")
        
        if result.get('audio_path'):
            try:
                transcript = self._transcribe_audio(result['audio_path'])
                result['transcript'] = transcript
                
                cursor.execute('''
                UPDATE reels SET transcript = ? WHERE reel_id = ?
                ''', (transcript, reel_id))
                
                logger.info(f"Transcribed audio for {reel_id}")
                logger.info(f"Transcript found for {reel_id}")
            except Exception as e:
                logger.error(f"Error transcribing audio: {e}")
                logger.warning(f"No transcript found for {reel_id}")
        else:
            logger.warning(f"No transcript found for {reel_id}")
        
        conn.commit()
        conn.close()
        
        return result
    
    def _transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio using Whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcription text
        """
        try:
            subprocess.run(['whisper', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            result = subprocess.run([
                'whisper',
                audio_path,
                '--language', 'Japanese',
                '--model', 'small',
                '--output_format', 'txt'
            ], capture_output=True, text=True, check=True)
            
            txt_path = audio_path.replace('.mp3', '.txt')
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    transcript = f.read()
                return transcript
            
            return "Transcription failed"
        except Exception as e:
            logger.error(f"Error using Whisper: {e}")
            
            return f"これはテスト用の文字起こしです。実際の音声からの文字起こしではありません。{os.path.basename(audio_path)}の内容をここに表示します。"
            
    def _generate_mock_reels(self, keyword: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mock Reels data for testing
        
        Args:
            keyword: Search keyword
            count: Number of mock Reels to generate
            
        Returns:
            List of mock Reel data dictionaries
        """
        mock_reels = []
        for i in range(count):
            reel_id = f"mock_reel_{keyword}_{i}_{int(time.time())}"
            
            engagement_rate = random.uniform(2.0, 15.0)
            like_count = random.randint(1000, 50000)
            comment_count = random.randint(50, 500)
            view_count = int(like_count / (engagement_rate / 100))
            
            mock_reel = {
                'reel_id': reel_id,
                'permalink': f"https://www.instagram.com/reel/mock_{reel_id}/",
                'like_count': like_count,
                'comment_count': comment_count,
                'view_count': view_count,
                'engagement_rate': engagement_rate,
                'scraped_at': datetime.now().isoformat(),
                'transcript': f"これは「{keyword}」に関するモックのトランスクリプトです。実際のコンテンツではありません。"
            }
            
            self._save_reel_to_db(mock_reel)
            
            mock_reels.append(mock_reel)
        
        return mock_reels

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Instagram Reels Scraper')
    parser.add_argument('keyword', nargs='?', help='Keyword or hashtag to search for')
    parser.add_argument('--top', type=int, default=10, help='Number of top Reels to extract')
    parser.add_argument('--min_engage', type=float, default=2.0, help='Minimum engagement rate (%)')
    parser.add_argument('--audience', help='Analyze audience for a specific Reel ID')
    parser.add_argument('--transcribe', help='Download and transcribe a specific Reel ID')
    parser.add_argument('--need_video', action='store_true', help='Download video (not just audio)')
    parser.add_argument('--visible', action='store_true', help='Run in visible mode (not headless)')
    
    args = parser.parse_args()
    
    with InstagramScraper(headless=not args.visible) as scraper:
        if args.audience:
            audience_data = scraper.analyze_audience(args.audience)
            print(json.dumps(audience_data, indent=2, ensure_ascii=False))
        elif args.transcribe:
            result = scraper.download_and_transcribe(args.transcribe, args.need_video)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.keyword:
            reels = scraper.search_reels_by_keyword(args.keyword, args.top, args.min_engage)
            print(json.dumps(reels, indent=2, ensure_ascii=False))
        else:
            parser.print_help()

if __name__ == '__main__':
    main()

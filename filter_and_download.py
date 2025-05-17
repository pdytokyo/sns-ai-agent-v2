"""
Filter and download Instagram Reels from results.json
- Filters posts containing "/reel/" and with likesCount >= 500
- Downloads mp4 files using yt-dlp to the downloads folder
"""

import json
import os
import subprocess
import logging
import shutil
from typing import List, Dict, Any
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('filter_and_download')

def load_results(file_path: str = 'results.json') -> List[Dict[str, Any]]:
    """
    Load results from JSON file
    
    Args:
        file_path: Path to the results JSON file
        
    Returns:
        List of result items
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'results' in data:
            return data['results']
        else:
            logger.error(f"Unexpected JSON structure in {file_path}")
            return []
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {file_path}")
        return []

def filter_reels(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter results to only include reels with likesCount >= 500
    
    Args:
        results: List of result items
        
    Returns:
        Filtered list of reels
    """
    filtered = []
    
    for item in results:
        url = item.get('url', '')
        likes_count = item.get('likesCount', 0)
        
        if '/reel/' in url and likes_count >= 500:
            filtered.append(item)
    
    logger.info(f"Found {len(filtered)} reels with 500+ likes out of {len(results)} total posts")
    return filtered

def check_yt_dlp_installed() -> bool:
    """
    Check if yt-dlp is installed
    
    Returns:
        True if installed, False otherwise
    """
    return shutil.which('yt-dlp') is not None

def download_reels(reels: List[Dict[str, Any]], output_dir: str = 'downloads') -> None:
    """
    Download reels using yt-dlp
    
    Args:
        reels: List of reel items to download
        output_dir: Directory to save downloads
    """
    if not check_yt_dlp_installed():
        logger.error("yt-dlp is not installed. Please install it with 'pip install yt-dlp'")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Saving downloads to: {output_dir}")
    
    ig_cookie = os.getenv('IG_TEST_COOKIE')
    cookie_args = []
    
    if ig_cookie:
        cookie_file = os.path.join(output_dir, '.cookies.txt')
        with open(cookie_file, 'w') as f:
            f.write(f"instagram.com\tTRUE\t/\tTRUE\t0\tcookie\t{ig_cookie}")
        
        cookie_args = ['--cookies', cookie_file]
        logger.info("Using Instagram cookie from IG_TEST_COOKIE environment variable")
    else:
        logger.warning("No IG_TEST_COOKIE environment variable found. Downloads may fail due to authentication issues.")
    
    for i, reel in enumerate(reels):
        url = reel.get('url', '')
        if not url:
            logger.warning(f"Skipping reel {i+1}/{len(reels)}: No URL found")
            continue
        
        reel_id = url.split('/reel/')[1].split('/')[0] if '/reel/' in url else f"reel_{i+1}"
        output_path = os.path.join(output_dir, f"{reel_id}.mp4")
        
        logger.info(f"Downloading reel {i+1}/{len(reels)}: {url}")
        
        try:
            cmd = [
                'yt-dlp',
                '-o', output_path,
                '--format', 'mp4',
            ]
            
            if cookie_args:
                cmd.extend(cookie_args)
            
            cmd.append(url)
            
            subprocess.run(cmd, check=True)
            
            logger.info(f"Successfully downloaded: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
    
    if ig_cookie and os.path.exists(cookie_file):
        try:
            os.remove(cookie_file)
        except Exception as e:
            logger.warning(f"Failed to remove temporary cookie file: {e}")

def main():
    """Main function"""
    # Load results from JSON
    results = load_results()
    
    if not results:
        logger.error("No results found. Exiting.")
        sys.exit(1)
    
    filtered_reels = filter_reels(results)
    
    if not filtered_reels:
        logger.warning("No reels matched the criteria (must contain '/reel/' and have 500+ likes)")
        sys.exit(0)
    
    download_reels(filtered_reels)
    
    logger.info("Download process complete")

if __name__ == '__main__':
    main()

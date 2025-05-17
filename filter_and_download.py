"""
Filter and download Instagram Reels from results.json
- Filters posts containing "/reel/" and with likesCount >= 500
- Downloads mp4 files using yt-dlp to the downloads folder
"""

import json
import os
import subprocess
import logging
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

def download_reels(reels: List[Dict[str, Any]], output_dir: str = 'downloads') -> None:
    """
    Download reels using yt-dlp
    
    Args:
        reels: List of reel items to download
        output_dir: Directory to save downloads
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Saving downloads to: {output_dir}")
    
    for i, reel in enumerate(reels):
        url = reel.get('url', '')
        if not url:
            logger.warning(f"Skipping reel {i+1}/{len(reels)}: No URL found")
            continue
        
        reel_id = url.split('/reel/')[1].split('/')[0] if '/reel/' in url else f"reel_{i+1}"
        output_path = os.path.join(output_dir, f"{reel_id}.mp4")
        
        logger.info(f"Downloading reel {i+1}/{len(reels)}: {url}")
        
        try:
            subprocess.run([
                'yt-dlp',
                '-o', output_path,
                '--format', 'mp4',
                url
            ], check=True)
            
            logger.info(f"Successfully downloaded: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")

def main():
    """Main function"""
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

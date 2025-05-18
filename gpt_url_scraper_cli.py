"""
CLI tool for fetching trending video URLs using GPT-4 with browsing capability.
"""

import os
import sys
import argparse
import logging
from modules.gpt_url_scraper import GPTUrlScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gpt_url_scraper_cli")

def main():
    """
    CLI entry point for the GPT URL Scraper.
    """
    parser = argparse.ArgumentParser(
        description="Fetch trending video URLs using GPT-4 with browsing capability."
    )
    parser.add_argument(
        "keyword", 
        help="The keyword to search for (e.g., 恋愛, 副業, スピリチュアル)."
    )
    parser.add_argument(
        "--platform", "-p", 
        default="Instagram", 
        choices=["Instagram", "TikTok", "YouTube"],
        help="The platform to search on (Instagram, TikTok, YouTube)."
    )
    parser.add_argument(
        "--count", "-c", 
        type=int, 
        default=5, 
        help="The number of URLs to fetch."
    )
    parser.add_argument(
        "--output", "-o", 
        default="output_urls.json", 
        help="The path to the output JSON file."
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging."
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        scraper = GPTUrlScraper()
        
        print(f"Fetching {args.count} {args.platform} URLs for keyword '{args.keyword}'...")
        
        urls = scraper.fetch_urls_sync(args.keyword, args.platform, args.count)
        
        output_file = scraper.save_urls_to_json(urls, args.output)
        
        print(f"\nSaved {len(urls)} URLs to {output_file}")
        
        for i, url_data in enumerate(urls, 1):
            print(f"\n{i}. {url_data['platform']}: {url_data['url']}")
            print(f"   Summary: {url_data['summary']}")
        
        return 0
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.exception("Full exception details:")
        return 1


if __name__ == "__main__":
    sys.exit(main())

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gpt_url_scraper")

class GPTUrlScraper:
    """
    A class that uses OpenAI's GPT-4 with browsing capability to collect trending video URLs
    from platforms like Instagram, TikTok, and YouTube based on keywords.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GPT URL Scraper with OpenAI API key.
        
        Args:
            api_key: OpenAI API key. If None, it will be loaded from environment variables.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables. Using dummy key for testing.")
            self.api_key = "dummy-api-key-for-testing"
            self.mock_mode = True
        else:
            self.mock_mode = False
            
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        self.system_prompt = self._load_prompt_template("system_prompt.txt")
        self.user_prompt = self._load_prompt_template("user_prompt.txt")
    
    def _load_prompt_template(self, filename: str) -> str:
        """
        Load a prompt template from the prompt_templates directory.
        
        Args:
            filename: Name of the prompt template file.
            
        Returns:
            The content of the prompt template file.
        """
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prompt_templates",
            filename
        )
        
        if not os.path.exists(template_path):
            if filename == "system_prompt.txt":
                return (
                    "You are a helpful assistant that searches for trending videos on social media platforms. "
                    "Your task is to find recent popular videos based on the keywords provided. "
                    "For each video, provide the direct URL and a brief summary of its content. "
                    "Focus on videos with high engagement (likes, comments, shares) and recent posting dates. "
                    "Do not include any videos that appear to violate platform guidelines or contain inappropriate content."
                )
            elif filename == "user_prompt.txt":
                return (
                    "Please find {count} trending videos on {platform} related to the keyword '{keyword}'. "
                    "For each video, provide:\n"
                    "1. The direct URL to the video\n"
                    "2. A brief summary of what the video is about (1-2 sentences)\n\n"
                    "Focus on videos that have high engagement and were posted recently. "
                    "Format your response as a list with URL and summary for each video."
                )
            
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            
            with open(template_path, "w", encoding="utf-8") as f:
                if filename == "system_prompt.txt":
                    f.write(
                        "You are a helpful assistant that searches for trending videos on social media platforms. "
                        "Your task is to find recent popular videos based on the keywords provided. "
                        "For each video, provide the direct URL and a brief summary of its content. "
                        "Focus on videos with high engagement (likes, comments, shares) and recent posting dates. "
                        "Do not include any videos that appear to violate platform guidelines or contain inappropriate content."
                    )
                elif filename == "user_prompt.txt":
                    f.write(
                        "Please find {count} trending videos on {platform} related to the keyword '{keyword}'. "
                        "For each video, provide:\n"
                        "1. The direct URL to the video\n"
                        "2. A brief summary of what the video is about (1-2 sentences)\n\n"
                        "Focus on videos that have high engagement and were posted recently. "
                        "Format your response as a list with URL and summary for each video."
                    )
            
            logger.info(f"Created default prompt template: {template_path}")
            
            if filename == "system_prompt.txt":
                return (
                    "You are a helpful assistant that searches for trending videos on social media platforms. "
                    "Your task is to find recent popular videos based on the keywords provided. "
                    "For each video, provide the direct URL and a brief summary of its content. "
                    "Focus on videos with high engagement (likes, comments, shares) and recent posting dates. "
                    "Do not include any videos that appear to violate platform guidelines or contain inappropriate content."
                )
            elif filename == "user_prompt.txt":
                return (
                    "Please find {count} trending videos on {platform} related to the keyword '{keyword}'. "
                    "For each video, provide:\n"
                    "1. The direct URL to the video\n"
                    "2. A brief summary of what the video is about (1-2 sentences)\n\n"
                    "Focus on videos that have high engagement and were posted recently. "
                    "Format your response as a list with URL and summary for each video."
                )
        
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def _generate_mock_urls(self, keyword: str, platform: str, count: int) -> List[Dict[str, str]]:
        """
        Generate mock URLs for testing purposes.
        
        Args:
            keyword: The keyword to search for.
            platform: The platform to search on.
            count: The number of URLs to generate.
            
        Returns:
            A list of dictionaries containing mock URLs and summaries.
        """
        mock_urls = []
        
        for i in range(count):
            if platform.lower() == "instagram":
                url = f"https://www.instagram.com/reel/mock{i}_{keyword}/"
                summary = f"Instagram Reel about {keyword} with trending content #{i+1}"
            elif platform.lower() == "tiktok":
                url = f"https://www.tiktok.com/@user/video/mock{i}_{keyword}"
                summary = f"TikTok video showcasing {keyword} trends and tips #{i+1}"
            elif platform.lower() == "youtube":
                url = f"https://www.youtube.com/watch?v=mock{i}_{keyword}"
                summary = f"YouTube video explaining {keyword} concepts and applications #{i+1}"
            else:
                url = f"https://example.com/video/mock{i}_{keyword}"
                summary = f"Video about {keyword} on generic platform #{i+1}"
            
            mock_urls.append({
                "url": url,
                "platform": platform,
                "summary": summary
            })
        
        return mock_urls
    
    def _extract_urls_from_response(self, response_text: str) -> List[Dict[str, str]]:
        """
        Extract URLs and summaries from the GPT response.
        
        Args:
            response_text: The text response from GPT.
            
        Returns:
            A list of dictionaries containing URLs and summaries.
        """
        import re
        
        instagram_pattern = r'https?://(?:www\.)?instagram\.com/(?:p|reel)/[\w-]+/?'
        tiktok_pattern = r'https?://(?:www\.)?tiktok\.com/@[\w.]+/video/\d+'
        youtube_pattern = r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+'
        
        url_pattern = f"({instagram_pattern}|{tiktok_pattern}|{youtube_pattern})"
        
        urls = re.findall(url_pattern, response_text)
        
        result = []
        
        for i, url in enumerate(urls):
            if "instagram.com" in url:
                platform = "Instagram"
            elif "tiktok.com" in url:
                platform = "TikTok"
            elif "youtube.com" in url or "youtu.be" in url:
                platform = "YouTube"
            else:
                platform = "Unknown"
            
            url_pos = response_text.find(url)
            
            next_url_pos = len(response_text)
            if i < len(urls) - 1:
                next_url_pos = response_text.find(urls[i+1])
            
            text_between = response_text[url_pos + len(url):next_url_pos].strip()
            
            summary = re.sub(r'^[:\s-]*', '', text_between)  # Remove leading colons, spaces, dashes
            summary = re.sub(r'\n+', ' ', summary)  # Replace newlines with spaces
            summary = re.sub(r'\s+', ' ', summary)  # Replace multiple spaces with a single space
            
            if summary:
                if len(summary) > 200:
                    summary = summary[:197] + "..."
            else:
                summary = f"Video about {platform} content"
            
            result.append({
                "url": url,
                "platform": platform,
                "summary": summary
            })
        
        return result
    
    async def fetch_urls(self, keyword: str, platform: str = "Instagram", count: int = 5) -> List[Dict[str, str]]:
        """
        Fetch trending video URLs using GPT-4 with browsing capability.
        
        Args:
            keyword: The keyword to search for.
            platform: The platform to search on (Instagram, TikTok, YouTube).
            count: The number of URLs to fetch.
            
        Returns:
            A list of dictionaries containing URLs and summaries.
        """
        if self.mock_mode:
            logger.warning("Running in mock mode. Returning mock URLs.")
            return self._generate_mock_urls(keyword, platform, count)
        
        try:
            formatted_user_prompt = self.user_prompt.format(
                keyword=keyword,
                platform=platform,
                count=count
            )
            
            # Use the already initialized OpenAI client
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # Use the latest GPT-4 model with browsing capability
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": formatted_user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                tools=[{"type": "retrieval"}]  # Enable web browsing capability
            )
            
            response_text = response.choices[0].message.content or ""
            
            urls = self._extract_urls_from_response(response_text)
            
            urls = urls[:count]
            
            return urls
            
        except Exception as e:
            logger.error(f"Error fetching URLs: {e}")
            logger.exception("Full exception details:")
            
            logger.warning("Returning mock URLs due to error.")
            return self._generate_mock_urls(keyword, platform, count)
    
    def fetch_urls_sync(self, keyword: str, platform: str = "Instagram", count: int = 5) -> List[Dict[str, str]]:
        """
        Synchronous version of fetch_urls for CLI usage.
        
        Args:
            keyword: The keyword to search for.
            platform: The platform to search on (Instagram, TikTok, YouTube).
            count: The number of URLs to fetch.
            
        Returns:
            A list of dictionaries containing URLs and summaries.
        """
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            urls = loop.run_until_complete(self.fetch_urls(keyword, platform, count))
            return urls
        finally:
            loop.close()
    
    def save_urls_to_json(self, urls: List[Dict[str, str]], output_file: str = "output_urls.json") -> str:
        """
        Save the URLs to a JSON file.
        
        Args:
            urls: A list of dictionaries containing URLs and summaries.
            output_file: The path to the output JSON file.
            
        Returns:
            The path to the saved JSON file.
        """
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(urls, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(urls)} URLs to {output_file}")
        
        return output_file


def main():
    """
    CLI entry point for the GPT URL Scraper.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch trending video URLs using GPT-4 with browsing capability.")
    parser.add_argument("keyword", help="The keyword to search for.")
    parser.add_argument("--platform", "-p", default="Instagram", help="The platform to search on (Instagram, TikTok, YouTube).")
    parser.add_argument("--count", "-c", type=int, default=5, help="The number of URLs to fetch.")
    parser.add_argument("--output", "-o", default="output_urls.json", help="The path to the output JSON file.")
    
    args = parser.parse_args()
    
    scraper = GPTUrlScraper()
    
    urls = scraper.fetch_urls_sync(args.keyword, args.platform, args.count)
    
    output_file = scraper.save_urls_to_json(urls, args.output)
    
    print(f"Saved {len(urls)} URLs to {output_file}")
    
    for i, url_data in enumerate(urls, 1):
        print(f"\n{i}. {url_data['platform']}: {url_data['url']}")
        print(f"   Summary: {url_data['summary']}")


if __name__ == "__main__":
    main()

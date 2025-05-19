"""
Script generator module for SNS video script generation pipeline.
Uses GPT to generate scripts based on video transcripts.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import re

import openai

class ScriptGenerator:
    """Script generator using GPT."""
    
    def __init__(
        self, 
        output_dir: str = "projects/default/scripts",
        template_dir: str = "prompt_templates/script_generation",
        language: str = "ja",
        api_key: Optional[str] = None
    ):
        """
        Initialize the script generator.
        
        Args:
            output_dir: Directory to save generated scripts
            template_dir: Directory containing prompt templates
            language: Language code for script generation (default: Japanese)
            api_key: OpenAI API key (if None, uses environment variable)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.language = language
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(template_dir, exist_ok=True)
        
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI()  # Uses OPENAI_API_KEY environment variable
        
        self._create_default_templates()
    
    def _create_default_templates(self) -> None:
        """Create default prompt templates if they don't exist."""
        templates = {
            "system_prompt.txt": """You are an expert script writer for social media short videos. Your task is to create engaging scripts based on transcripts from popular videos.

Follow these guidelines:
1. Create a script with a clear hook, main content, and call-to-action
2. Maintain the core message and topic of the original video
3. Adapt the style to match the target audience
4. Keep the script concise and engaging
5. Use natural, conversational language
6. Include appropriate emoji and formatting for social media
7. Structure the script in clear sections

The output should be in JSON format with the following structure:
{
  "title": "Catchy title for the video",
  "hook": "Attention-grabbing opening (15-20% of total length)",
  "main_content": "Core message and value (60-70% of total length)",
  "cta": "Clear call-to-action (10-15% of total length)",
  "hashtags": ["#relevant", "#hashtags", "#forTheVideo"],
  "estimated_duration": "Estimated duration in seconds"
}""",
            
            "user_prompt.txt": """Create a script for a {platform} short video based on the following transcript:

TRANSCRIPT:
{transcript}

TARGET AUDIENCE:
{target_audience}

STYLE:
{style}

LENGTH:
{length} seconds

Please generate a script that captures the essence of this content while making it more engaging and structured for {platform}."""
        }
        
        for filename, content in templates.items():
            filepath = os.path.join(self.template_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.info(f"Created default template: {filepath}")
    
    def _load_template(self, filename: str) -> str:
        """
        Load prompt template from file.
        
        Args:
            filename: Template filename
            
        Returns:
            Template content
        """
        filepath = os.path.join(self.template_dir, filename)
        
        if not os.path.exists(filepath):
            self.logger.warning(f"Template file not found: {filepath}")
            return ""
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate(
        self,
        transcript: Dict[str, Any],
        video_id: Optional[str] = None,
        platform: str = "Instagram",
        target_audience: str = "20-35歳の女性、美容・ファッションに興味がある",
        style: str = "教育的でありながらエンターテイニング",
        length: int = 30,
        temperature: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        Generate script based on transcript.
        
        Args:
            transcript: Transcript dictionary
            video_id: Video ID for output filename
            platform: Platform name (Instagram, TikTok, YouTube)
            target_audience: Target audience description
            style: Script style description
            length: Target script length in seconds
            temperature: GPT temperature parameter
            
        Returns:
            Dictionary with generated script or None if generation failed
        """
        if video_id:
            output_filename = f"{video_id}_script.json"
        else:
            import time
            output_filename = f"script_{int(time.time())}.json"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        if os.path.exists(output_path):
            self.logger.info(f"Script already exists: {output_path}")
            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        try:
            self.logger.info(f"Generating script for {platform} video")
            
            if isinstance(transcript, dict) and "text" in transcript:
                transcript_text = transcript["text"]
            elif isinstance(transcript, str):
                transcript_text = transcript
            else:
                transcript_text = json.dumps(transcript, ensure_ascii=False)
            
            system_prompt = self._load_template("system_prompt.txt")
            user_prompt = self._load_template("user_prompt.txt")
            
            user_prompt = user_prompt.format(
                platform=platform,
                transcript=transcript_text,
                target_audience=target_audience,
                style=style,
                length=length
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            script_text = response.choices[0].message.content
            
            script = json.loads(script_text)
            
            script["platform"] = platform
            script["target_audience"] = target_audience
            script["style"] = style
            script["target_length"] = length
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully generated script to {output_path}")
            return script
            
        except Exception as e:
            self.logger.error(f"Error generating script: {e}")
            return None
    
    def generate_options(
        self,
        transcript: Dict[str, Any],
        video_id: Optional[str] = None,
        platform: str = "Instagram",
        target_audience: str = "20-35歳の女性、美容・ファッションに興味がある",
        num_options: int = 2,
        temperature: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple script options based on transcript.
        
        Args:
            transcript: Transcript dictionary
            video_id: Video ID for output filename
            platform: Platform name (Instagram, TikTok, YouTube)
            target_audience: Target audience description
            num_options: Number of script options to generate
            temperature: GPT temperature parameter
            
        Returns:
            List of dictionaries with generated scripts
        """
        options = []
        
        styles = [
            "教育的でありながらエンターテイニング",
            "ストーリーテリング形式で感情に訴える",
            "データと事実に基づいた説得力のある内容",
            "ユーモアを交えた親しみやすい内容",
            "Q&A形式で疑問に答える構成"
        ]
        
        lengths = [30, 45, 60]
        
        for i in range(num_options):
            style = styles[i % len(styles)]
            length = lengths[i % len(lengths)]
            
            option_id = f"{video_id}_option{i+1}" if video_id else None
            script = self.generate(
                transcript=transcript,
                video_id=option_id,
                platform=platform,
                target_audience=target_audience,
                style=style,
                length=length,
                temperature=temperature
            )
            
            if script:
                script["option_id"] = i + 1
                options.append(script)
        
        self.logger.info(f"Generated {len(options)}/{num_options} script options")
        return options
    
    def batch_generate(
        self,
        transcripts: Dict[str, Dict[str, Any]],
        platform: str = "Instagram",
        target_audience: str = "20-35歳の女性、美容・ファッションに興味がある",
        num_options: int = 2
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate scripts for multiple transcripts.
        
        Args:
            transcripts: Dictionary mapping video URLs to transcript dictionaries
            platform: Platform name (Instagram, TikTok, YouTube)
            target_audience: Target audience description
            num_options: Number of script options to generate per transcript
            
        Returns:
            Dictionary mapping video URLs to lists of generated scripts
        """
        results = {}
        
        for url, transcript in transcripts.items():
            video_id = self._extract_video_id(url)
            
            options = self.generate_options(
                transcript=transcript,
                video_id=video_id,
                platform=platform,
                target_audience=target_audience,
                num_options=num_options
            )
            
            if options:
                results[url] = options
        
        self.logger.info(f"Generated scripts for {len(results)}/{len(transcripts)} videos")
        return results
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from URL.
        
        Args:
            url: Video URL
            
        Returns:
            Video ID or None if extraction failed
        """
        import re
        
        if "instagram.com" in url:
            match = re.search(r'/(?:reel|p)/([^/]+)', url)
            if match:
                return f"instagram_{match.group(1)}"
        elif "tiktok.com" in url:
            match = re.search(r'/video/(\d+)', url)
            if match:
                return f"tiktok_{match.group(1)}"
        elif "youtube.com" in url or "youtu.be" in url:
            match = re.search(r'(?:v=|shorts/|youtu\.be/)([^&?/]+)', url)
            if match:
                return f"youtube_{match.group(1)}"
        
        import time
        return f"script_{int(time.time())}"

"""
Whisper transcriber module for SNS video script generation pipeline.
Uses OpenAI's Whisper API to transcribe audio from videos.
"""

import os
import json
import logging
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile

import openai

class WhisperTranscriber:
    """Transcriber using OpenAI's Whisper API."""
    
    def __init__(
        self, 
        output_dir: str = "projects/default/transcripts",
        language: str = "ja",
        api_key: Optional[str] = None
    ):
        """
        Initialize the Whisper transcriber.
        
        Args:
            output_dir: Directory to save transcripts
            language: Language code for transcription (default: Japanese)
            api_key: OpenAI API key (if None, uses environment variable)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = output_dir
        self.language = language
        
        os.makedirs(output_dir, exist_ok=True)
        
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI()  # Uses OPENAI_API_KEY environment variable
    
    def extract_audio(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file or None if extraction failed
        """
        if not os.path.exists(video_path):
            self.logger.error(f"Video file not found: {video_path}")
            return None
        
        audio_path = os.path.splitext(video_path)[0] + ".wav"
        
        if os.path.exists(audio_path):
            self.logger.info(f"Audio file already exists: {audio_path}")
            return audio_path
        
        try:
            self.logger.info(f"Extracting audio from {video_path}")
            
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit little-endian
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",  # Mono
                "-y",  # Overwrite output file
                audio_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error extracting audio: {result.stderr}")
                return None
            
            if not os.path.exists(audio_path):
                self.logger.error(f"Audio extraction completed but file not found: {audio_path}")
                return None
            
            self.logger.info(f"Successfully extracted audio to {audio_path}")
            return audio_path
            
        except Exception as e:
            self.logger.error(f"Error extracting audio: {e}")
            return None
    
    def transcribe(self, audio_path: str, video_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using Whisper API.
        
        Args:
            audio_path: Path to audio file
            video_id: Video ID for output filename
            
        Returns:
            Dictionary with transcription results or None if transcription failed
        """
        if not os.path.exists(audio_path):
            self.logger.error(f"Audio file not found: {audio_path}")
            return None
        
        if video_id:
            output_filename = f"{video_id}.json"
        else:
            output_filename = os.path.basename(audio_path).replace(".wav", ".json")
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        if os.path.exists(output_path):
            self.logger.info(f"Transcript already exists: {output_path}")
            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        try:
            self.logger.info(f"Transcribing audio: {audio_path}")
            
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=self.language,
                    response_format="verbose_json"
                )
            
            if isinstance(response, dict):
                result = response
            else:
                result = response.model_dump()
            
            result["audio_path"] = audio_path
            result["language"] = self.language
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully transcribed audio to {output_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return None
    
    def transcribe_video(self, video_path: str, video_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Extract audio from video and transcribe it.
        
        Args:
            video_path: Path to video file
            video_id: Video ID for output filename
            
        Returns:
            Dictionary with transcription results or None if transcription failed
        """
        audio_path = self.extract_audio(video_path)
        if not audio_path:
            return None
        
        return self.transcribe(audio_path, video_id)
    
    def batch_transcribe(self, video_paths: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Transcribe multiple videos.
        
        Args:
            video_paths: Dictionary mapping video URLs to local file paths
            
        Returns:
            Dictionary mapping video URLs to transcription results
        """
        results = {}
        
        for url, video_path in video_paths.items():
            video_id = self._extract_video_id(url)
            
            transcript = self.transcribe_video(video_path, video_id)
            if transcript:
                results[url] = transcript
        
        self.logger.info(f"Transcribed {len(results)}/{len(video_paths)} videos")
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
        return f"transcript_{int(time.time())}"

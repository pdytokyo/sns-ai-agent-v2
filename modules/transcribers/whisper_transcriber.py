"""
Whisper transcriber module for SNS video script generation pipeline.
Supports both OpenAI's Whisper API and faster-whisper for local transcription.
"""

import os
import json
import logging
import subprocess
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import tempfile
from tqdm import tqdm

import openai

try:
    import torch
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

class WhisperTranscriber:
    """Transcriber using OpenAI's Whisper API or faster-whisper for local transcription."""
    
    def __init__(
        self, 
        output_dir: str = "projects/default/transcripts",
        language: str = "ja",
        api_key: Optional[str] = None,
        use_faster_whisper: bool = False,
        model_size: str = "base",
        device: Optional[str] = None
    ):
        """
        Initialize the Whisper transcriber.
        
        Args:
            output_dir: Directory to save transcripts
            language: Language code for transcription (default: Japanese)
            api_key: OpenAI API key (if None, uses environment variable)
            use_faster_whisper: Whether to use faster-whisper instead of OpenAI API
            model_size: Model size for faster-whisper (tiny, base, small, medium, large-v1, large-v2, large-v3)
            device: Device to use for faster-whisper (cpu, cuda, auto). If None, uses TRANSCRIBE_DEVICE env var or defaults to "cpu"
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = output_dir
        self.language = language
        self.use_faster_whisper = use_faster_whisper and FASTER_WHISPER_AVAILABLE
        self.model_size = model_size
        
        if device is None:
            self.device = os.environ.get("TRANSCRIBE_DEVICE", "cpu")
        else:
            self.device = device
            
        self.logger.info(f"Initializing WhisperTranscriber with device={self.device}, use_faster_whisper={self.use_faster_whisper}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize OpenAI client if not using faster-whisper
        if not self.use_faster_whisper:
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
            else:
                self.client = openai.OpenAI()  # Uses OPENAI_API_KEY environment variable
        # Initialize faster-whisper model if available
        elif FASTER_WHISPER_AVAILABLE:
            try:
                self.model = WhisperModel(self.model_size, device=self.device, compute_type="float16" if self.device == "cuda" else "int8")
                self.logger.info(f"Initialized faster-whisper model: {self.model_size} on {self.device}")
            except Exception as e:
                self.logger.error(f"Failed to initialize faster-whisper model: {e}")
                self.use_faster_whisper = False
                self.client = openai.OpenAI()  # Fallback to OpenAI API
        else:
            self.logger.warning("faster-whisper not available, falling back to OpenAI API")
            self.use_faster_whisper = False
            self.client = openai.OpenAI()  # Fallback to OpenAI API
    
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
    
    def transcribe_with_faster_whisper(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using faster-whisper.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with transcription results or None if transcription failed
        """
        if not FASTER_WHISPER_AVAILABLE:
            self.logger.error("faster-whisper is not available")
            return None
            
        try:
            self.logger.info(f"Transcribing audio with faster-whisper ({self.model_size} model on {self.device}): {audio_path}")
            
            # Transcribe with faster-whisper
            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
                task="transcribe",
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            segments_list = []
            full_text = ""
            
            is_ci = os.environ.get("CI", "false").lower() == "true"
            segment_iterator = segments if is_ci else tqdm(list(segments), desc="Processing segments")
            
            for segment in segment_iterator:
                segment_dict = {
                    "id": len(segments_list),
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "tokens": [],  # faster-whisper doesn't provide tokens
                    "temperature": 0.0,
                    "avg_logprob": segment.avg_logprob,
                    "compression_ratio": 1.0,
                    "no_speech_prob": segment.no_speech_prob
                }
                segments_list.append(segment_dict)
                full_text += segment.text + " "
            
            result = {
                "text": full_text.strip(),
                "segments": segments_list,
                "language": info.language,
                "audio_path": audio_path,
                "transcription_method": f"faster-whisper-{self.model_size}"
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error transcribing with faster-whisper: {e}")
            return None
    
    def transcribe(self, audio_path: str, video_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using Whisper API or faster-whisper.
        
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
            
            if self.use_faster_whisper:
                result = self.transcribe_with_faster_whisper(audio_path)
                if not result:
                    self.logger.warning("faster-whisper transcription failed, falling back to OpenAI API")
                    self.use_faster_whisper = False
                    # Fall through to OpenAI API
                else:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    self.logger.info(f"Successfully transcribed audio to {output_path} using faster-whisper")
                    return result
            
            # Use OpenAI API
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
            result["transcription_method"] = "openai-whisper-api"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully transcribed audio to {output_path} using OpenAI API")
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
        
        is_ci = os.environ.get("CI", "false").lower() == "true"
        
        items = list(video_paths.items())
        progress_iter = items if is_ci else tqdm(items, desc="Transcribing videos", unit="video")
        
        for url, video_path in progress_iter:
            video_id = self._extract_video_id(url)
            
            if not is_ci:
                if isinstance(progress_iter, tqdm):
                    progress_iter.set_description(f"Transcribing {os.path.basename(video_path)}")
            
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

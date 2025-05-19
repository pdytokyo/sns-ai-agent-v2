"""
Unit tests for script JSON validation.
Tests that script sections (hook, build, cta) have durations within specified ranges.
"""

import os
import json
import pytest
from pathlib import Path

EXPECTED_RANGES = {
    "hook": (3, 10),  # Hook should be 3-10 seconds
    "main_content": (15, 60),  # Main content should be 15-60 seconds
    "cta": (3, 15)  # CTA should be 3-15 seconds
}

def load_script_json(script_path):
    """Load script JSON from file."""
    with open(script_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_test_scripts():
    """Get list of script JSON files for testing."""
    script_files = []
    projects_dir = Path("projects")
    
    if not projects_dir.exists():
        return []
    
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            scripts_dir = project_dir / "scripts"
            if scripts_dir.exists():
                for script_file in scripts_dir.glob("*_script.json"):
                    script_files.append(script_file)
    
    return script_files

def estimate_section_duration(section_text, words_per_second=2.5):
    """
    Estimate section duration based on word count.
    
    Args:
        section_text: Text content of the section
        words_per_second: Average speaking rate (default: 2.5 words per second)
        
    Returns:
        Estimated duration in seconds
    """
    if not section_text:
        return 0
        
    word_count = len(section_text.split())
    
    duration = word_count / words_per_second
    
    return duration

class TestScriptValidation:
    """Test script JSON validation."""
    
    @pytest.mark.parametrize("script_path", get_test_scripts())
    def test_script_section_durations(self, script_path):
        """Test that script sections have durations within specified ranges."""
        if not script_path:
            pytest.skip("No script files found for testing")
        
        script = load_script_json(script_path)
        
        if "hook" in script:
            hook_duration = estimate_section_duration(script["hook"])
            min_duration, max_duration = EXPECTED_RANGES["hook"]
            assert min_duration <= hook_duration <= max_duration, \
                f"Hook duration ({hook_duration:.1f}s) outside expected range ({min_duration}-{max_duration}s)"
        
        if "main_content" in script:
            main_content_duration = estimate_section_duration(script["main_content"])
            min_duration, max_duration = EXPECTED_RANGES["main_content"]
            assert min_duration <= main_content_duration <= max_duration, \
                f"Main content duration ({main_content_duration:.1f}s) outside expected range ({min_duration}-{max_duration}s)"
        
        if "cta" in script:
            cta_duration = estimate_section_duration(script["cta"])
            min_duration, max_duration = EXPECTED_RANGES["cta"]
            assert min_duration <= cta_duration <= max_duration, \
                f"CTA duration ({cta_duration:.1f}s) outside expected range ({min_duration}-{max_duration}s)"

    def test_mock_script_validation(self):
        """Test script validation with mock data."""
        mock_script = {
            "title": "Test Script",
            "style": "Casual",
            "hook": "Hey there! Today we're going to talk about something amazing.",  # ~5 seconds
            "main_content": "This is the main content of our video. We'll cover several important points. " * 5,  # ~25 seconds
            "cta": "Thanks for watching! Don't forget to like and subscribe for more content.",  # ~5 seconds
            "hashtags": ["test", "video", "content"]
        }
        
        hook_duration = estimate_section_duration(mock_script["hook"])
        min_duration, max_duration = EXPECTED_RANGES["hook"]
        assert min_duration <= hook_duration <= max_duration, \
            f"Hook duration ({hook_duration:.1f}s) outside expected range ({min_duration}-{max_duration}s)"
        
        main_content_duration = estimate_section_duration(mock_script["main_content"])
        min_duration, max_duration = EXPECTED_RANGES["main_content"]
        assert min_duration <= main_content_duration <= max_duration, \
            f"Main content duration ({main_content_duration:.1f}s) outside expected range ({min_duration}-{max_duration}s)"
        
        cta_duration = estimate_section_duration(mock_script["cta"])
        min_duration, max_duration = EXPECTED_RANGES["cta"]
        assert min_duration <= cta_duration <= max_duration, \
            f"CTA duration ({cta_duration:.1f}s) outside expected range ({min_duration}-{max_duration}s)"

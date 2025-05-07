import os
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..database import (
    get_reels_by_audience,
    get_client_settings,
    save_script,
    extract_and_save_keywords,
    get_top_keywords
)

class ScriptGenerator:
    """Generate scripts based on reels data and client settings"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data")
        os.makedirs(self.data_dir, exist_ok=True)
    
    def generate_scripts(
        self, 
        client_id: str, 
        theme: str, 
        target: Optional[Dict[str, str]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate two script options based on theme and target audience
        
        Args:
            client_id: Client ID
            theme: Script theme
            target: Target audience (optional, will use client default if not provided)
            
        Returns:
            Tuple of two script dictionaries (trace script, high-engagement script)
        """
        keywords = extract_and_save_keywords(theme, client_id)
        
        client_settings = get_client_settings(client_id)
        if not client_settings:
            client_settings = {
                'client_id': client_id,
                'default_target': target or {'age': '18-34', 'interest': 'general'},
                'tone_rules': {},
                'length_limit': 500
            }
        
        target_audience = target or client_settings.get('default_target', {})
        
        matching_reels = get_reels_by_audience(target_audience, limit=5)
        
        if not matching_reels:
            return self._create_default_scripts(client_id, theme, target_audience)
        
        best_reel = matching_reels[0]
        
        trace_script = self._generate_trace_script(client_id, theme, best_reel)
        high_eng_script = self._generate_high_engagement_script(client_id, theme, best_reel, matching_reels)
        
        return trace_script, high_eng_script
    
    def _create_default_scripts(
        self, 
        client_id: str, 
        theme: str, 
        target: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Create default scripts when no matching reels are found"""
        top_keywords = get_top_keywords(client_id)
        keywords_text = ", ".join([k['keyword'] for k in top_keywords[:5]])
        
        timestamp = int(datetime.now().timestamp())
        
        trace_script = {
            'id': f"script_trace_{timestamp}",
            'client_id': client_id,
            'original_reel_id': None,
            'option': 1,
            'sections': [
                {
                    'type': 'intro',
                    'content': f"# {theme}に関するスクリプト\n\nこんにちは、今日は{theme}について話します。\n\n{theme}は現代社会において非常に重要なトピックです。多くの人々が日々この問題に直面しています。"
                },
                {
                    'type': 'main',
                    'content': f"まず、{theme}の基本的な概念を理解することが大切です。次に、実践的なアプローチを考えていきましょう。\n\n{keywords_text}などのキーワードが重要です。\n\n最後に、{theme}を日常生活に取り入れる方法をご紹介します。"
                },
                {
                    'type': 'conclusion',
                    'content': f"いかがでしたか？{theme}についての理解が深まったでしょうか。\n\nコメント欄で皆さんの{theme}に関する経験や質問をぜひシェアしてください。"
                }
            ]
        }
        
        high_eng_script = {
            'id': f"script_high_eng_{timestamp}",
            'client_id': client_id,
            'original_reel_id': None,
            'option': 2,
            'sections': [
                {
                    'type': 'hook',
                    'content': f"# 別の{theme}スクリプト\n\n皆さん、{theme}について考えたことはありますか？\n\n今日は{theme}の魅力と可能性について探っていきます。"
                },
                {
                    'type': 'content',
                    'content': f"{theme}は私たちの生活を豊かにする可能性を秘めています。具体的な例を見ていきましょう。\n\n1. {theme}の歴史\n2. 現代における{theme}の役割\n3. 未来の{theme}の展望\n\n{keywords_text}などのキーワードが重要です。"
                },
                {
                    'type': 'cta',
                    'content': f"ぜひコメントで皆さんの{theme}体験を教えてください！\n\nいいね、保存、シェアもお願いします！"
                }
            ]
        }
        
        return trace_script, high_eng_script
    
    def _generate_trace_script(
        self, 
        client_id: str, 
        theme: str, 
        reel: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a script that closely traces the structure of the source reel"""
        timestamp = int(datetime.now().timestamp())
        
        transcript = reel.get('transcript', '')
        if not transcript:
            return self._create_default_scripts(client_id, theme, {})[0]
        
        sections = self._analyze_transcript_structure(transcript)
        
        new_sections = []
        for i, section in enumerate(sections):
            if i == 0:
                new_content = f"# {theme}に関するスクリプト\n\n"
                new_content += f"こんにちは、今日は{theme}について話します。\n\n"
                new_content += f"{theme}は多くの人が興味を持つトピックです。"
                
                target_length = len(section)
                current_length = len(new_content)
                
                if current_length < target_length * 0.95:
                    new_content += f"\n\n{theme}について詳しく見ていきましょう。"
                
                new_sections.append({
                    'type': 'intro',
                    'content': new_content
                })
            elif i == len(sections) - 1:
                new_content = f"いかがでしたか？{theme}についての理解が深まったでしょうか。\n\n"
                new_content += f"コメント欄で皆さんの{theme}に関する経験や質問をぜひシェアしてください。\n\n"
                new_content += f"いいね、保存もお願いします！"
                
                target_length = len(section)
                current_length = len(new_content)
                
                if current_length < target_length * 0.95:
                    new_content += f"\n\n次回も{theme}に関連する内容をお届けします。お楽しみに！"
                
                new_sections.append({
                    'type': 'conclusion',
                    'content': new_content
                })
            else:
                new_content = f"{theme}について、いくつかの重要なポイントを紹介します。\n\n"
                
                points = min(3, max(1, len(section) // 100))  # Scale points based on section length
                for p in range(1, points + 1):
                    new_content += f"{p}. {theme}の{'重要性' if p == 1 else '活用方法' if p == 2 else '将来性'}\n"
                
                target_length = len(section)
                current_length = len(new_content)
                
                if current_length < target_length * 0.95:
                    new_content += f"\n\nこれらのポイントを押さえることで、{theme}をより効果的に活用できるでしょう。"
                    new_content += f"\n\n{theme}は日常生活でも役立つ知識です。ぜひ実践してみてください。"
                
                new_sections.append({
                    'type': 'main',
                    'content': new_content
                })
        
        script = {
            'id': f"script_trace_{timestamp}",
            'client_id': client_id,
            'original_reel_id': reel.get('reel_id'),
            'option': 1,
            'sections': new_sections
        }
        
        return script
    
    def _generate_high_engagement_script(
        self, 
        client_id: str, 
        theme: str, 
        primary_reel: Dict[str, Any],
        all_reels: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a high-engagement script based on multiple reels"""
        timestamp = int(datetime.now().timestamp())
        
        engagement_patterns = self._extract_engagement_patterns(all_reels)
        
        new_sections = []
        
        hook = f"# {theme}の秘密を公開します！\n\n"
        hook += f"多くの人が{theme}について誤解しています。今日はその真実をお伝えします。\n\n"
        
        if engagement_patterns.get('questions_in_hook', False):
            hook += f"{theme}について、あなたはどう思いますか？\n\n"
        
        if engagement_patterns.get('emojis', False):
            hook += f"👀 驚きの事実を知る準備はできていますか？ 👀\n\n"
        
        new_sections.append({
            'type': 'hook',
            'content': hook
        })
        
        main_content = f"{theme}に関する3つの重要なポイントを紹介します。\n\n"
        
        if engagement_patterns.get('numbered_lists', False):
            main_content += f"1️⃣ {theme}の基本\n"
            main_content += f"2️⃣ 知っておくべき{theme}のテクニック\n"
            main_content += f"3️⃣ {theme}を活用した成功事例\n\n"
        
        if engagement_patterns.get('personal_stories', False):
            main_content += f"私自身も{theme}に取り組む中で多くの失敗を経験しました。しかし、ある方法を見つけてから状況が一変したのです。\n\n"
        
        if engagement_patterns.get('contrasts', False):
            main_content += f"多くの人は{theme}を難しいと考えていますが、実は正しいアプローチさえ知っていれば誰でも簡単に習得できるのです。\n\n"
        
        new_sections.append({
            'type': 'content',
            'content': main_content
        })
        
        cta = f"この情報が役に立ったと思ったら、いいね・保存・シェアをお願いします！\n\n"
        
        if engagement_patterns.get('questions_in_cta', False):
            cta += f"あなたは{theme}についてどんな経験がありますか？コメントで教えてください！\n\n"
        
        if engagement_patterns.get('next_content_teaser', False):
            cta += f"次回は「{theme}の応用テクニック」について詳しく解説します。お楽しみに！\n\n"
        
        if engagement_patterns.get('emojis', False):
            cta += f"👍 いいね 🔖 保存 🚀 シェア"
        
        new_sections.append({
            'type': 'cta',
            'content': cta
        })
        
        script = {
            'id': f"script_high_eng_{timestamp}",
            'client_id': client_id,
            'original_reel_id': primary_reel.get('reel_id'),
            'option': 2,
            'sections': new_sections
        }
        
        return script
    
    def _analyze_transcript_structure(self, transcript: str) -> List[str]:
        """Analyze transcript structure and divide into sections"""
        if not transcript:
            return ["", "", ""]
        
        paragraphs = transcript.split('\n\n')
        
        if len(paragraphs) < 3:
            if len(paragraphs) == 1 and len(paragraphs[0]) > 200:
                text = paragraphs[0]
                third = len(text) // 3
                return [text[:third], text[third:2*third], text[2*third:]]
            
            while len(paragraphs) < 3:
                paragraphs.append("")
        
        if len(paragraphs) > 5:
            intro = paragraphs[0]
            main = '\n\n'.join(paragraphs[1:-1])
            conclusion = paragraphs[-1]
            return [intro, main, conclusion]
        
        return paragraphs
    
    def _extract_engagement_patterns(self, reels: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Extract engagement patterns from reels"""
        patterns = {
            'questions_in_hook': False,
            'questions_in_cta': False,
            'numbered_lists': False,
            'emojis': False,
            'personal_stories': False,
            'contrasts': False,
            'next_content_teaser': False
        }
        
        for reel in reels:
            transcript = reel.get('transcript', '')
            if not transcript:
                continue
            
            if '?' in transcript[:200]:
                patterns['questions_in_hook'] = True
            
            if '?' in transcript[-200:]:
                patterns['questions_in_cta'] = True
            
            if any(marker in transcript for marker in ['1.', '2.', '①', '②', '1️⃣', '2️⃣']):
                patterns['numbered_lists'] = True
            
            if any(ord(c) > 0x1F000 for c in transcript):
                patterns['emojis'] = True
            
            if any(marker in transcript.lower() for marker in ['私は', '私の', '私が', '私も', '自分の']):
                patterns['personal_stories'] = True
            
            if any(marker in transcript for marker in ['しかし', 'だが', 'けれども', '一方', 'VS']):
                patterns['contrasts'] = True
            
            if any(marker in transcript[-200:] for marker in ['次回', '次は', 'お楽しみに']):
                patterns['next_content_teaser'] = True
        
        return patterns
    
    def calculate_structure_match_score(self, original: str, generated: str) -> float:
        """
        Calculate structural similarity between original and generated scripts
        
        Args:
            original: Original script text
            generated: Generated script text
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not original or not generated:
            return 0.0
        
        char_ratio = min(len(generated) / len(original), len(original) / len(generated))
        
        orig_paragraphs = original.split('\n\n')
        gen_paragraphs = generated.split('\n\n')
        para_ratio = min(len(gen_paragraphs) / max(1, len(orig_paragraphs)), 
                         len(orig_paragraphs) / max(1, len(gen_paragraphs)))
        
        orig_sentences = len([s for s in original.split('。') if s.strip()])
        gen_sentences = len([s for s in generated.split('。') if s.strip()])
        sent_ratio = min(gen_sentences / max(1, orig_sentences),
                         orig_sentences / max(1, gen_sentences))
        
        score = (0.5 * char_ratio) + (0.3 * para_ratio) + (0.2 * sent_ratio)
        
        return min(1.0, score)

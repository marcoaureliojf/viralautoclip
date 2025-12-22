"""
Text Processing Utilities
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from ..core.shared_config import CHUNK_SIZE
except ImportError:
    import sys
    backend_path = Path(__file__).parent.parent
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    from core.shared_config import CHUNK_SIZE

import pysrt

logger = logging.getLogger(__name__)

class TextProcessor:
    """Utility class for text and subtitle processing"""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
        """
        Splits long text into chunks based on character count.
        Priority: Paragraphs > Sentences.
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
                current_chunk += paragraph + '\n'
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                if len(paragraph) > chunk_size:
                    sentences = re.split(r'[。！？.!?]', paragraph)
                    temp_chunk = ""
                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) + 1 <= chunk_size:
                            temp_chunk += sentence + " "
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = sentence + " "
                    current_chunk = temp_chunk
                else:
                    current_chunk = paragraph + '\n'
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk_srt_data(self, srt_data: List[Dict], interval_minutes: int = 10, max_chars: int = CHUNK_SIZE) -> List[Dict]:
        """
        Splits SRT data into chunks based on time intervals AND character limits.
        This prevents overloading LLM token limits (Fix for Groq 413 Error).

        Args:
            srt_data: List of SRT entries.
            interval_minutes: Target duration per chunk (Reduced to 10 min for safety).
            max_chars: Maximum characters allowed per chunk (from config).
        """
        if not srt_data:
            return []

        interval_seconds = interval_minutes * 60
        chunks = []
        current_entries = []
        current_text_len = 0
        chunk_index = 0
        
        # Determine start time of the first entry
        first_start = self.time_to_seconds(srt_data[0]['start_time'])
        last_cut_time = first_start

        for entry in srt_data:
            entry_start = self.time_to_seconds(entry['start_time'])
            entry_text_len = len(entry['text'])
            
            # Check if adding this entry violates time OR character limit
            time_limit_reached = (entry_start - last_cut_time) >= interval_seconds
            char_limit_reached = (current_text_len + entry_text_len) >= max_chars

            if (time_limit_reached or char_limit_reached) and current_entries:
                # Save current chunk
                chunks.append(self._create_chunk_payload(chunk_index, current_entries))
                # Reset for next chunk
                chunk_index += 1
                current_entries = []
                current_text_len = 0
                last_cut_time = entry_start

            current_entries.append(entry)
            current_text_len += entry_text_len

        # Add remaining entries
        if current_entries:
            chunks.append(self._create_chunk_payload(chunk_index, current_entries))
            
        return chunks

    def _create_chunk_payload(self, index: int, entries: List[Dict]) -> Dict:
        """Helper to format the chunk metadata"""
        return {
            "chunk_index": index,
            "text": " ".join([e['text'] for e in entries]),
            "start_time": entries[0]['start_time'],
            "end_time": entries[-1]['end_time'],
            "srt_entries": entries
        }

    @staticmethod
    def parse_srt(srt_path: Path) -> List[Dict]:
        """Parses SRT file into a list of dictionaries"""
        if not srt_path.exists() or srt_path.stat().st_size == 0:
            logger.error(f"SRT file missing or empty: {srt_path}")
            return []

        try:
            subs = pysrt.open(str(srt_path), encoding='utf-8')
        except UnicodeDecodeError:
            subs = pysrt.open(str(srt_path), encoding='utf-8-sig')

        return [{
            'start_time': str(sub.start),
            'end_time': str(sub.end),
            'text': sub.text.strip(),
            'index': sub.index
        } for sub in subs]
    
    @staticmethod
    def time_to_seconds(time_str: str) -> float:
        """Converts SRT timestamp (HH:MM:SS,mmm) to total seconds"""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s_full = parts
            return int(h) * 3600 + int(m) * 60 + float(s_full)
        raise ValueError(f"Invalid time format: {time_str}")

    @staticmethod
    def seconds_to_time(seconds: float) -> str:
        """Converts seconds to HH:MM:SS string"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
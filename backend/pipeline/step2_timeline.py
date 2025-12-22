"""
Step 2: Timeline Extraction - Extract precise time intervals for each topic in the outline
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict

# Import dependencies
from ..utils.llm_client import LLMClient
from ..utils.text_processor import TextProcessor
from ..core.shared_config import PROMPT_FILES, METADATA_DIR

logger = logging.getLogger(__name__)

class TimelineExtractor:
    """Extract precise time intervals for each topic in the outline from the outline and SRT subtitle"""
    
    def __init__(self, metadata_dir: Path = None, prompt_files: Dict = None):
        self.llm_client = LLMClient()
        self.text_processor = TextProcessor()
        
        # Use the provided metadata_dir or default value
        if metadata_dir is None:
            metadata_dir = METADATA_DIR
        self.metadata_dir = metadata_dir
        
        # Load prompts
        prompt_files_to_use = prompt_files if prompt_files is not None else PROMPT_FILES
        with open(prompt_files_to_use['timeline'], 'r', encoding='utf-8') as f:
            self.timeline_prompt = f.read()
            
        # SRT block directory
        self.srt_chunks_dir = self.metadata_dir / "step1_srt_chunks"
        self.timeline_chunks_dir = self.metadata_dir / "step2_timeline_chunks"
        self.llm_raw_output_dir = self.metadata_dir / "step2_llm_raw_output"

    def extract_timeline(self, outlines: List[Dict]) -> List[Dict]:
        """
        Extract time intervals for each topic in the outline from the outline and SRT subtitle.
        Features:
        - Based on pre-divided SRT blocks
        - Batch processing by block
        - Cache original LLM responses to avoid repeated calls
        - Save processing results for each block as intermediate files to enhance robustness
        """
        logger.info("Start extracting topic time intervals...")
        
        if not outlines:
            logger.warning("Outline data is empty, cannot extract timeline.")
            return []

        if not self.srt_chunks_dir.exists():
            logger.error(f"SRT block directory does not exist: {self.srt_chunks_dir}. Please run Step 1 first.")
            return []

        # 1. Create directories needed for this step
        self.timeline_chunks_dir.mkdir(parents=True, exist_ok=True)
        self.llm_raw_output_dir.mkdir(parents=True, exist_ok=True)

        # 2. Group all outlines by chunk_index
        outlines_by_chunk = defaultdict(list)
        for outline in outlines:
            chunk_index = outline.get('chunk_index')
            if chunk_index is not None:
                outlines_by_chunk[chunk_index].append(outline)
            else:
                logger.warning(f"Topic '{outline.get('title', 'Unknown')}' missing chunk_index, skipping.")

        all_timeline_data = []
        # 3. Iterate through each block, batch process, and save results as independent JSON files
        for chunk_index, chunk_outlines in outlines_by_chunk.items():
            logger.info(f"Processing chunk {chunk_index}, containing {len(chunk_outlines)} topics...")
            
            # Always reprocess, do not use cache
            chunk_output_path = self.timeline_chunks_dir / f"chunk_{chunk_index}.json"

            try:
                # Load corresponding SRT block file
                srt_chunk_path = self.srt_chunks_dir / f"chunk_{chunk_index}.json"
                if not srt_chunk_path.exists():
                    logger.warning(f"  > Cannot find corresponding SRT chunk file: {srt_chunk_path}, skipping entire chunk.")
                    continue
                
                with open(srt_chunk_path, 'r', encoding='utf-8') as f:
                    srt_chunk_data = json.load(f)

                if not srt_chunk_data:
                    logger.warning(f"SRT block file is empty: {srt_chunk_path}, skipping entire chunk.")
                    continue

                # Get time range information
                chunk_start_time = srt_chunk_data[0]['start_time']
                chunk_end_time = srt_chunk_data[-1]['end_time']

                raw_response = ""
                llm_cache_path = self.llm_raw_output_dir / f"chunk_{chunk_index}.txt"

                if llm_cache_path.exists():
                    logger.info(f"Found LLM raw response cache for chunk {chunk_index}, reading directly.")
                    with open(llm_cache_path, 'r', encoding='utf-8') as f:
                        raw_response = f.read()
                else:
                    logger.info(f"No LLM cache found, calling API...")
                    
                    # Build SRT text for LLM
                    srt_text_for_prompt = ""
                    for sub in srt_chunk_data:
                        srt_text_for_prompt += f"{sub['index']}\\n{sub['start_time']} --> {sub['end_time']}\\n{sub['text']}\\n\\n"
                    
                    # Prepare a "clean" input for LLM
                    llm_input_outlines = [
                        {"title": o.get("title"), "subtopics": o.get("subtopics")}
                        for o in chunk_outlines
                    ]

                    input_data = {
                        "outline": llm_input_outlines,
                        "srt_text": srt_text_for_prompt
                    }
                    
                    # Call LLM with retry mechanism
                    parsed_items = None
                    max_parse_retries = 2
                    
                    for retry_count in range(max_parse_retries + 1):
                        try:
                            raw_response = self.llm_client.call_with_retry(self.timeline_prompt, input_data)
                            
                            if not raw_response:
                                logger.warning(f"  > Block {chunk_index} LLM response is empty, skipping")
                                break
                            
                            # Save raw response to cache
                            cache_file = self.llm_raw_output_dir / f"chunk_{chunk_index}_attempt_{retry_count}.txt"
                            with open(cache_file, 'w', encoding='utf-8') as f:
                                f.write(raw_response)
                            
                            # Parse LLM's raw response
                            parsed_items = self._parse_and_validate_response(
                                raw_response, 
                                chunk_start_time, 
                                chunk_end_time,
                                chunk_index
                            )
                            
                            if parsed_items:
                                # Save parsed results
                                with open(chunk_output_path, 'w', encoding='utf-8') as f:
                                    json.dump(parsed_items, f, ensure_ascii=False, indent=2)
                                
                                logger.info(f"  > Block {chunk_index} successfully parsed {len(parsed_items)} time intervals")
                                break  # Success, exit retry loop
                            else:
                                if retry_count < max_parse_retries:
                                    logger.warning(f"  > Block {chunk_index} parsing failed, retrying ({retry_count + 1}/{max_parse_retries + 1})")
                                    # Reinforce prompt constraints
                                    input_data['additional_instruction'] = "\n\n【Important】Output requirements:\n1. Must start with [ and end with ]\n2. Use English double quotes\n3. String quotes must be escaped as \\\"\n4. No explanation text or code block markers\n5. Ensure complete JSON format"
                                else:
                                    logger.error(f"  > Block {chunk_index} failed after {max_parse_retries + 1} attempts")
                                    self._save_debug_response(raw_response, chunk_index, "final_parse_failure")
                                    
                        except Exception as parse_error:
                            logger.error(f"  > Block {chunk_index} attempt {retry_count + 1} parsing failed with exception: {parse_error}")
                            if retry_count == max_parse_retries:
                                self._save_debug_response(raw_response if 'raw_response' in locals() else "No response", chunk_index, "parse_exception")
                            continue
                    
                    if not parsed_items:
                         logger.warning(f"  > Block {chunk_index} final parsing failed, skipping")
                         continue

            except Exception as e:
                logger.error(f"  > Error processing block {chunk_index}: {str(e)}")
                continue
        
        # 4. Assemble final results from all intermediate files
        logger.info("All blocks processed, assembling final results from intermediate files...")
        all_timeline_data = []
        chunk_files = sorted(self.timeline_chunks_dir.glob("*.json"))
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
                all_timeline_data.extend(chunk_data)

        logger.info(f"Successfully loaded {len(all_timeline_data)} topics from {len(chunk_files)} chunk files.")
        
        # Final Sort: Sort by start time globally
        if all_timeline_data:
            logger.info("Performing final sort of all topics by start time...")
            try:
                all_timeline_data.sort(key=lambda x: self.text_processor.time_to_seconds(x['start_time']))
                logger.info("Sorting completed.")
                
                # Assign sequential IDs
                logger.info("Assigning fixed IDs to all segments...")
                for i, timeline_item in enumerate(all_timeline_data):
                    timeline_item['id'] = str(i + 1)
                logger.info(f"Assigned fixed IDs (1-{len(all_timeline_data)}) to {len(all_timeline_data)} segments.")
                
            except Exception as e:
                logger.error(f"Error during final sorting: {e}. Returning unsorted results.")

        return all_timeline_data
        
    def _parse_and_validate_response(self, response: str, chunk_start: str, chunk_end: str, chunk_index: int) -> List[Dict]:
        """Enhanced parsing of LLM batch response, validation and time adjustment"""
        validated_items = []
        
        # Save raw response for debugging
        self._save_debug_response(response, chunk_index, "original_response")
        
        try:
            # Attempt JSON parse
            parsed_response = self.llm_client.parse_json_response(response)
            
            # Validate structure
            if not self.llm_client._validate_json_structure(parsed_response):
                logger.error(f"  > Block {chunk_index} JSON structure validation failed")
                self._save_debug_response(str(parsed_response), chunk_index, "invalid_structure")
                return []
            
            if not isinstance(parsed_response, list):
                logger.warning(f"  > Block {chunk_index} LLM did not return a list")
                self._save_debug_response(f"Type: {type(parsed_response)}, Content: {parsed_response}", chunk_index, "not_list")
                return []
            
            for timeline_item in parsed_response:
                if 'outline' not in timeline_item or 'start_time' not in timeline_item or 'end_time' not in timeline_item:
                    logger.warning(f"  > Incorrect JSON object format from LLM: {timeline_item}")
                    continue
                
                # Re-attach chunk_index
                timeline_item['chunk_index'] = chunk_index
                
                # Validate and adjust time ranges
                try:
                    if not self._validate_time_format(timeline_item['start_time']):
                        logger.warning(f"  > Topic '{timeline_item['outline']}' start time format incorrect: {timeline_item['start_time']}")
                        continue
                    
                    if not self._validate_time_format(timeline_item['end_time']):
                        logger.warning(f"  > Topic '{timeline_item['outline']}' end time format incorrect: {timeline_item['end_time']}")
                        continue
                    
                    start_time = self._convert_time_format(timeline_item['start_time'])
                    end_time = self._convert_time_format(timeline_item['end_time'])
                    
                    start_sec = self.text_processor.time_to_seconds(start_time)
                    end_sec = self.text_processor.time_to_seconds(end_time)
                    chunk_start_sec = self.text_processor.time_to_seconds(chunk_start)
                    chunk_end_sec = self.text_processor.time_to_seconds(chunk_end)
                    
                    if start_sec < chunk_start_sec:
                        logger.warning(f"  > Adjusting topic '{timeline_item['outline']}' start time from {start_time} to {chunk_start}")
                        timeline_item['start_time'] = chunk_start
                    
                    if end_sec > chunk_end_sec:
                        logger.warning(f"  > Adjusting topic '{timeline_item['outline']}' end time from {end_time} to {chunk_end}")
                        timeline_item['end_time'] = chunk_end
                    
                    logger.info(f"  > Location successful: {timeline_item['outline']} ({timeline_item['start_time']} -> {timeline_item['end_time']})")
                    validated_items.append(timeline_item)
                except Exception as e:
                    logger.error(f"  > Error validating individual timestamp: {e} - Item: {timeline_item}")
                    continue
            
            return validated_items

        except Exception as e:
            logger.error(f"  > Block {chunk_index} error parsing LLM response: {e}")
            error_info = {
                "error": str(e),
                "error_type": type(e).__name__,
                "response_length": len(response),
                "response_preview": response[:200],
                "chunk_index": chunk_index,
                "chunk_start": chunk_start,
                "chunk_end": chunk_end
            }
            self._save_debug_response(json.dumps(error_info, indent=2, ensure_ascii=False), chunk_index, "parse_error")
            return []

    def _validate_time_format(self, time_str: str) -> bool:
        """Verify time format (HH:MM:SS,mmm)"""
        pattern = r'^\d{2}:\d{2}:\d{2},\d{3}$'
        return bool(re.match(pattern, time_str))
    
    def _convert_time_format(self, time_str: str) -> str:
        """Convert time format: SRT format -> FFmpeg format"""
        if not time_str or time_str == "end":
            return time_str
        return time_str.replace(',', '.')

    def _save_debug_response(self, response: str, chunk_index: int, error_type: str) -> None:
        """Save debug response to file"""
        try:
            debug_dir = self.metadata_dir / "debug_responses"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"chunk_{chunk_index}_{error_type}.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response)
            logger.info(f"Debug response saved to: {debug_file}")
        except Exception as e:
            logger.error(f"Failed to save debug response: {e}")

    def save_timeline(self, timeline_data: List[Dict], output_path: Optional[Path] = None) -> Path:
        """Save time interval data"""
        if output_path is None:
            output_path = METADATA_DIR / "step2_timeline.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timeline_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Time data saved to: {output_path}")
        return output_path

    def load_timeline(self, input_path: Path) -> List[Dict]:
        """Load time data from file"""
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)

def run_step2_timeline(outline_path: Path, metadata_dir: Path = None, output_path: Optional[Path] = None, prompt_files: Dict = None) -> List[Dict]:
    """Run Step 2: Timestamp Extraction"""
    if metadata_dir is None:
        metadata_dir = METADATA_DIR
        
    extractor = TimelineExtractor(metadata_dir, prompt_files)
    
    # Load outline
    with open(outline_path, 'r', encoding='utf-8') as f:
        outlines = json.load(f)
        
    timeline_data = extractor.extract_timeline(outlines)
    
    # Save results
    if output_path is None:
        output_path = metadata_dir / "step2_timeline.json"
        
    extractor.save_timeline(timeline_data, output_path)
    
    return timeline_data
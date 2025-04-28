import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

_log = logging.getLogger(__name__)

class ChunkMapper:
    """
    Maps chunks from BreadcrumbChunker to the standardized JSON format
    for database storage as specified in the requirements.
    """
    
    def __init__(self, creator_tool: str = "DoclingToJsonScript_V1.1"):
        self.creator_tool = creator_tool
        
    def map_chunks(self, chunks: List[Dict], doc_id: Optional[str] = None) -> List[Dict]:
        """
        Maps a list of chunks to the standardized output format.
        
        Args:
            chunks: List of chunks from BreadcrumbChunker
            doc_id: Optional document ID to associate with all chunks
            
        Returns:
            List of mapped chunks in the standardized format
        """
        mapped_chunks = []
        
        for i, chunk in enumerate(chunks, 1):
            # Convert chunk if it's a string (JSON)
            if isinstance(chunk, str):
                try:
                    chunk = json.loads(chunk)
                except json.JSONDecodeError:
                    _log.error(f"Failed to parse chunk {i} as JSON")
                    continue
            
            # Basic mapping of chunk to standardized format
            mapped_chunk = {
                "_id": None,
                "block_id": i,
                "doc_id": doc_id,
                "content_type": self._determine_content_type(chunk),
                "file_type": chunk.get("file_type", "application/pdf"),
                "master_index": chunk.get("page_no", 1),
                "master_index2": None,
                "coords_x": self._get_coordinate(chunk, "x"),
                "coords_y": self._get_coordinate(chunk, "y"),
                "coords_cx": self._get_coordinate(chunk, "width"),
                "coords_cy": self._get_coordinate(chunk, "height"),
                "author_or_speaker": None,
                "added_to_collection": None,
                "file_source": self._get_file_source(chunk),
                "table_block": self._format_table_data(chunk) if self._is_table(chunk) else None,
                "modified_date": None,
                "created_date": None,
                "creator_tool": self.creator_tool,
                "external_files": self._get_image_path(chunk) if self._is_image(chunk) else None,
                "text_block": self._format_text_block(chunk),
                "header_text": chunk.get("breadcrumb", ""),
                "text_search": self._get_search_text(chunk),
                "user_tags": None,
                "special_field1": json.dumps(self._create_metadata_object(chunk)),
                "special_field2": chunk.get("breadcrumb", ""),
                "special_field3": None,
                "graph_status": None,
                "dialog": None,
                "embedding_flags": None
            }
            
            mapped_chunks.append(mapped_chunk)
            
        return mapped_chunks
    
    def _determine_content_type(self, chunk: Dict) -> str:
        """Determines the content type (text, table, image) from the chunk."""
        if "element_type" in chunk:
            element_type = chunk["element_type"].lower()
            if "table" in element_type:
                return "table"
            elif "picture" in element_type or "image" in element_type:
                return "image"
        return "text"
    
    def _get_coordinate(self, chunk: Dict, coord_type: str) -> int:
        """Extracts and normalizes coordinate values from the chunk."""
        if "bbox" in chunk:
            bbox = chunk["bbox"]
            if coord_type == "x" and "l" in bbox:
                return int(bbox["l"])
            elif coord_type == "y" and "t" in bbox:
                return int(bbox["t"])
            elif coord_type == "width" and "l" in bbox and "r" in bbox:
                return int(bbox["r"] - bbox["l"])
            elif coord_type == "height" and "t" in bbox and "b" in bbox:
                return int(bbox["b"] - bbox["t"])
        return 0
    
    def _get_file_source(self, chunk: Dict) -> str:
        """Gets the file source from the chunk metadata."""
        if "source" in chunk:
            return chunk["source"]
        return ""
    
    def _is_table(self, chunk: Dict) -> bool:
        """Determines if the chunk represents a table."""
        return self._determine_content_type(chunk) == "table"
    
    def _is_image(self, chunk: Dict) -> bool:
        """Determines if the chunk represents an image."""
        return self._determine_content_type(chunk) == "image"
    
    def _format_table_data(self, chunk: Dict) -> Optional[str]:
        """Formats table data as a JSON string."""
        if "table_data" in chunk:
            return json.dumps(chunk["table_data"])
        return None
    
    def _get_image_path(self, chunk: Dict) -> Optional[str]:
        """Gets the path to the externally referenced image."""
        if "image_path" in chunk:
            return chunk["image_path"]
        return None
    
    def _format_text_block(self, chunk: Dict) -> str:
        """
        Formats the text block with breadcrumb and content.
        For images, includes preceding text, image text, and succeeding text.
        """
        breadcrumb = chunk.get("breadcrumb", "")
        content = chunk.get("content", "")
        
        if self._is_image(chunk):
            preceding_text = chunk.get("context_before", "")
            ocr_text = chunk.get("ocr_text", "")
            succeeding_text = chunk.get("context_after", "")
            
            return f"{breadcrumb}\n\n{preceding_text}\n\n[Image Text: {ocr_text}]\n\n{succeeding_text}"
        
        return f"{breadcrumb}\n\n{content}"
    
    def _get_search_text(self, chunk: Dict) -> str:
        """Gets the text for search indexing."""
        if self._is_image(chunk) and "caption" in chunk:
            return chunk["caption"] or ""
        return chunk.get("content", "")
    
    def _create_metadata_object(self, chunk: Dict) -> Dict:
        """Creates a complete metadata object from the chunk."""
        metadata = {
            "breadcrumb": chunk.get("breadcrumb", ""),
            "page_no": chunk.get("page_no", 1),
            "bbox_raw": chunk.get("bbox", {}),
            "docling_label": chunk.get("element_type", "text"),
            "docling_ref": chunk.get("self_ref", "")
        }
        
        # Add caption if available
        if "caption" in chunk:
            metadata["caption"] = chunk["caption"]
        
        # Add context before/after if available
        if "context_before" in chunk:
            metadata["context_before"] = chunk["context_before"]
        if "context_after" in chunk:
            metadata["context_after"] = chunk["context_after"]
        
        # Add image-specific metadata if relevant
        if self._is_image(chunk):
            metadata.update({
                "image_mimetype": chunk.get("mimetype", "image/png"),
                "image_width": chunk.get("width", 0),
                "image_height": chunk.get("height", 0),
                "image_ocr_text": chunk.get("ocr_text", "")
            })
            
        return metadata

def map_chunks_to_spec(input_data, output_file: str, doc_id: Optional[str] = None):
    """
    Converts chunks from BreadcrumbChunker to the standardized format and saves to file.
    
    Args:
        input_data: Path to file containing chunks or list of chunk dictionaries/JSON strings
        output_file: Path to save the mapped chunks
        doc_id: Optional document ID to associate with all chunks
    """
    chunks = []
    
    # Handle input data (file path or list of chunks)
    if isinstance(input_data, str) and os.path.exists(input_data):
        # Load chunks from file
        with open(input_data, 'r') as f:
            try:
                content = f.read()
                # Try parsing as JSON array
                if content.strip().startswith('['):
                    chunks = json.loads(content)
                # Try parsing as newline-delimited JSON
                else:
                    chunks = [json.loads(line) for line in content.strip().split('\n') if line.strip()]
            except json.JSONDecodeError as e:
                _log.error(f"Failed to parse input file as JSON: {e}")
                return
    elif isinstance(input_data, list):
        # Input is already a list of chunks
        chunks = input_data
    else:
        _log.error(f"Invalid input data: {input_data}")
        return
    
    # Map chunks to standardized format
    mapper = ChunkMapper()
    mapped_chunks = mapper.map_chunks(chunks, doc_id)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save mapped chunks to file
    with open(output_file, 'w') as f:
        json.dump({
            "chunks": mapped_chunks,
            "source_metadata": {
                "doc_id": doc_id,
                "filename": os.path.basename(input_data) if isinstance(input_data, str) else None,
                "processed_date": None,
                "chunk_count": len(mapped_chunks)
            }
        }, f, indent=2)
    
    _log.info(f"Successfully mapped {len(mapped_chunks)} chunks to {output_file}")
    return mapped_chunks

if __name__ == "__main__":
    import argparse
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(description="Map BreadcrumbChunker output to standardized JSON format")
    parser.add_argument("input_file", help="JSON file containing chunks from BreadcrumbChunker")
    parser.add_argument("output_file", help="File to save mapped chunks to")
    parser.add_argument("--doc_id", help="Document ID to associate with all chunks")
    
    args = parser.parse_args()
    
    map_chunks_to_spec(args.input_file, args.output_file, args.doc_id) 
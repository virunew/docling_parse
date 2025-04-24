"""
SQL Formatter for Docling Parser

This module provides functionality to convert the parsed Docling document data
into a standardized JSON format suitable for SQL database ingestion.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Import the logger configuration
from logger_config import logger

# Import standardized output formatter
from src.format_standardized_output import save_standardized_output

# Import SQL insert generator
from src.sql_insert_generator import SQLInsertGenerator


class SQLFormatter:
    """
    Formats document data into SQL-compatible JSON format and generates SQL INSERT statements.
    
    This class provides methods to convert Docling document data into a standardized
    format that maps to SQL database schemas and can generate SQL INSERT statements
    for direct database ingestion.
    """
    
    def __init__(self, dialect: str = "postgresql"):
        """
        Initialize the SQL formatter.
        
        Args:
            dialect (str): SQL dialect to use for INSERT statements
                          (postgresql, mysql, sqlite)
        """
        logger.info(f"Initializing SQL formatter with dialect: {dialect}")
        self.dialect = dialect
        
        # Initialize SQL insert generator
        self.insert_generator = SQLInsertGenerator(dialect)
    
    def format_as_sql(self, document_data: Dict[str, Any], doc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Format document data as SQL-compatible JSON.
        
        Args:
            document_data (Dict[str, Any]): The parsed Docling document data
            doc_id (Optional[str]): Optional document ID to use in the output
            
        Returns:
            Dict[str, Any]: A dictionary with the standardized output format containing
                          chunks, furniture, and source_metadata
        """
        logger.info("Formatting document as SQL-compatible JSON")
        try:
            return process_docling_json_to_sql_format(document_data, doc_id)
        except Exception as e:
            logger.error(f"Error formatting document as SQL: {e}", exc_info=True)
            # Return a minimal structure in case of failure
            return {
                "chunks": [],
                "furniture": [],
                "source_metadata": {
                    "filename": document_data.get("metadata", {}).get("filename", "unknown"),
                    "mimetype": "application/pdf",
                    "binary_hash": ""
                }
            }
    
    def generate_sql_inserts(self, document_data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Generate SQL INSERT statements from document data.
        
        Args:
            document_data (Dict[str, Any]): The document data to generate INSERT statements from
            doc_id (Optional[str]): Optional document ID to use in the output
            
        Returns:
            str: SQL INSERT statements as a string
        """
        logger.info("Generating SQL INSERT statements")
        try:
            # First, format the document data as SQL-compatible JSON
            formatted_data = self.format_as_sql(document_data, doc_id)
            
            # Then generate SQL INSERT statements
            return self.insert_generator.generate_sql_inserts(formatted_data)
        except Exception as e:
            logger.error(f"Error generating SQL INSERT statements: {e}", exc_info=True)
            return f"-- Error generating SQL INSERT statements: {e}"
    
    def save_formatted_output(self, document_data: Dict[str, Any], 
                              output_dir: Union[str, Path], 
                              doc_id: Optional[str] = None,
                              use_standardized_format: bool = False,
                              pdf_path: Optional[str] = None,
                              generate_inserts: bool = False) -> str:
        """
        Format document data as SQL-compatible JSON and save it to disk.
        
        Args:
            document_data (Dict[str, Any]): The parsed Docling document data
            output_dir (Union[str, Path]): Directory to save the output file
            doc_id (Optional[str]): Optional document ID to use in the output
            use_standardized_format (bool): Whether to use the standardized format
                from format_standardized_output instead of the default SQL format
            pdf_path (Optional[str]): Path to the original PDF file, required if
                use_standardized_format is True
            generate_inserts (bool): Whether to generate SQL INSERT statements
                instead of SQL-compatible JSON
            
        Returns:
            str: Path to the saved output file
        """
        logger.info(f"Saving SQL formatted output to directory: {output_dir}")
        
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # If generating INSERT statements
        if generate_inserts:
            logger.info("Generating SQL INSERT statements")
            # Use standardized format as basis for INSERT statements
            if use_standardized_format and pdf_path is not None:
                logger.info("Using standardized format for SQL INSERT statements")
                # Generate standardized format and then create INSERT statements
                standardized_output_file = save_standardized_output(document_data, output_path, pdf_path)
                
                # Load the standardized output
                with open(standardized_output_file, 'r', encoding='utf-8') as f:
                    standardized_data = json.load(f)
                
                # Generate and save SQL INSERT statements
                return self.insert_generator.save_sql_inserts(standardized_data, output_path)
            else:
                logger.info("Using default SQL format for SQL INSERT statements")
                # Use default SQL format as basis for INSERT statements
                sql_formatted_data = self.format_as_sql(document_data, doc_id)
                
                # Generate and save SQL INSERT statements
                return self.insert_generator.save_sql_inserts(sql_formatted_data, output_path)
        
        # Determine the output approach for non-INSERT formats
        if use_standardized_format:
            if pdf_path is None:
                logger.warning("PDF path is required for standardized format. Using default SQL format.")
                return self._save_default_sql_format(document_data, output_path, doc_id)
            
            # Use the standardized output format
            output_file = save_standardized_output(document_data, output_path, pdf_path)
            logger.info(f"SQL formatted output (standardized format) saved to: {output_file}")
            return output_file
        else:
            # Use the default SQL format
            return self._save_default_sql_format(document_data, output_path, doc_id)
    
    def _save_default_sql_format(self, document_data: Dict[str, Any], 
                                output_path: Path, 
                                doc_id: Optional[str] = None) -> str:
        """
        Save document data using the default SQL format.
        
        Args:
            document_data (Dict[str, Any]): The parsed Docling document data
            output_path (Path): Path to the output directory
            doc_id (Optional[str]): Optional document ID to use in the output
            
        Returns:
            str: Path to the saved SQL format file
        """
        # Format the document data
        sql_formatted_data = self.format_as_sql(document_data, doc_id)
        
        # Determine the output filename
        filename = document_data.get("name", "document")
        if "metadata" in document_data and "filename" in document_data["metadata"]:
            # Extract base filename from the PDF path if available
            pdf_filename = Path(document_data["metadata"]["filename"]).stem
            filename = pdf_filename
        
        # Create output file path
        output_file = output_path / f"{filename}_sql.json"
        
        # Save the formatted data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sql_formatted_data, f, indent=2)
        
        logger.info(f"SQL formatted output (default format) saved to: {output_file}")
        return str(output_file)


def process_docling_json_to_sql_format(document_data: Dict[str, Any], 
                                       doc_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process the Docling document data and convert it to a standardized SQL-compatible format.
    
    Args:
        document_data (Dict[str, Any]): The parsed Docling document data
        doc_id (Optional[str]): Optional document ID to use in the output
        
    Returns:
        Dict[str, Any]: A dictionary with the standardized output format containing
                        chunks, furniture, and source_metadata
    """
    logger.info("Processing document data into SQL-compatible format")
    
    try:
        # Initialize the output structure
        output = {
            "chunks": [],
            "furniture": [],
            "source_metadata": {
                "filename": document_data.get("metadata", {}).get("filename", ""),
                "mimetype": document_data.get("metadata", {}).get("mimetype", "application/pdf"),
                "binary_hash": document_data.get("metadata", {}).get("binary_hash", "")
            }
        }
        
        # Extract furniture elements
        if "furniture" in document_data:
            for furniture_item in document_data.get("furniture", []):
                if furniture_item.get("text"):
                    output["furniture"].append(furniture_item["text"])
        
        # Process content elements into chunks
        block_id = 1
        for element in document_data.get("body", []):
            content_type = _determine_content_type(element)
            
            # Create chunk with all required fields from the fusa_library schema
            chunk = {
                "_id": None,  # Generated by DB
                "block_id": block_id,
                "doc_id": doc_id,
                "content_type": content_type,
                "file_type": output["source_metadata"]["mimetype"],
                "master_index": _extract_page_number(element),
                "master_index2": None,
                "coords_x": _extract_coord(element, "l"),
                "coords_y": _extract_coord(element, "t"),
                "coords_cx": _extract_coord(element, "r") - _extract_coord(element, "l"),
                "coords_cy": _extract_coord(element, "b") - _extract_coord(element, "t"),
                "author_or_speaker": None,
                "added_to_collection": None,
                "file_source": output["source_metadata"]["filename"],
                "table_block": _format_table_content(element) if content_type == "table" else None,
                "modified_date": None,
                "created_date": None,
                "creator_tool": "DoclingToJsonScript_V1.1",
                "external_files": _get_external_file_path(element) if content_type == "image" else None,
                "text_block": _format_text_block(element, _get_breadcrumb(element)),
                "header_text": _get_breadcrumb(element),
                "text_search": _get_searchable_text(element),
                "user_tags": None,
                "special_field1": json.dumps(_build_metadata_object(element)),
                "special_field2": _get_breadcrumb(element),
                "special_field3": None,
                "graph_status": None,
                "dialog": None,
                "embedding_flags": None,
                "metadata": _build_metadata_object(element)
            }
            
            output["chunks"].append(chunk)
            block_id += 1
        
        logger.info(f"Successfully processed document data: {len(output['chunks'])} chunks, {len(output['furniture'])} furniture items")
        return output
    
    except Exception as e:
        logger.error(f"Error processing document data: {e}", exc_info=True)
        raise

def _determine_content_type(element: Dict[str, Any]) -> str:
    """Determine the content type (text, table, or image) of an element."""
    element_type = element.get("type", "")
    
    if element_type == "table":
        return "table"
    elif element_type == "picture":
        return "image"
    else:
        return "text"

def _extract_page_number(element: Dict[str, Any]) -> int:
    """Extract the page number from an element."""
    prov = element.get("prov", {})
    return prov.get("page_no", 1)

def _extract_coord(element: Dict[str, Any], coord_key: str) -> int:
    """Extract coordinate value from an element's bounding box."""
    prov = element.get("prov", {})
    bbox = prov.get("bbox", {})
    coord = bbox.get(coord_key, 0)
    return int(coord)

def _format_table_content(element: Dict[str, Any]) -> Optional[str]:
    """Format table content as a JSON string of the grid."""
    if not element.get("grid"):
        return None
    
    try:
        return json.dumps(element["grid"])
    except Exception as e:
        logger.warning(f"Error formatting table content: {e}")
        return None

def _get_external_file_path(element: Dict[str, Any]) -> Optional[str]:
    """Get the path to an externally stored image file."""
    if "external_path" in element:
        return element["external_path"]
    return None

def _get_breadcrumb(element: Dict[str, Any]) -> str:
    """Get the hierarchical breadcrumb for an element."""
    return element.get("breadcrumb", "")

def _format_text_block(element: Dict[str, Any], breadcrumb: str) -> str:
    """Format the text block with breadcrumb and content."""
    content = ""
    
    if _determine_content_type(element) == "text":
        content = element.get("text", "")
    elif _determine_content_type(element) == "image":
        # Format for images: preceding text, image text (OCR), and succeeding text
        preceding_text = element.get("context_before", "")
        image_ocr_text = element.get("ocr_text", "")
        succeeding_text = element.get("context_after", "")
        
        content = f"{preceding_text}\n\n[Image Text: {image_ocr_text}]\n\n{succeeding_text}"
    elif _determine_content_type(element) == "table":
        content = f"[Table: {element.get('caption', 'Table content')}]"
    
    return f"{breadcrumb}\n\n{content}" if breadcrumb else content

def _get_searchable_text(element: Dict[str, Any]) -> str:
    """Get text for search indexing."""
    if _determine_content_type(element) == "text":
        return element.get("text", "")
    elif _determine_content_type(element) == "image":
        return element.get("caption", "") or element.get("ocr_text", "")
    elif _determine_content_type(element) == "table":
        return element.get("caption", "")
    return ""

def _build_metadata_object(element: Dict[str, Any]) -> Dict[str, Any]:
    """Build a complete metadata object for an element."""
    content_type = _determine_content_type(element)
    prov = element.get("prov", {})
    bbox = prov.get("bbox", {})
    
    metadata = {
        "breadcrumb": _get_breadcrumb(element),
        "page_no": _extract_page_number(element),
        "bbox_raw": {
            "l": bbox.get("l", 0),
            "t": bbox.get("t", 0),
            "r": bbox.get("r", 0),
            "b": bbox.get("b", 0)
        },
        "caption": element.get("caption", ""),
        "context_before": element.get("context_before", ""),
        "context_after": element.get("context_after", ""),
        "docling_label": element.get("type", ""),
        "docling_ref": element.get("self_ref", "")
    }
    
    # Add image-specific metadata
    if content_type == "image":
        metadata.update({
            "image_mimetype": element.get("mimetype", "image/png"),
            "image_width": element.get("width", 0),
            "image_height": element.get("height", 0),
            "image_ocr_text": element.get("ocr_text", "")
        })
    
    return metadata 
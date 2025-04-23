"""
SQL Formatter Module

This module provides a formatter that transforms document data into a
structure compatible with SQL database insertion. It serializes the document
data into a JSON format that can be directly inserted into the fusa_library table.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class SQLFormatter:
    """
    Formats document data into a structure compatible with the fusa_library table schema.

    The formatter converts the document data into a JSON format with a specific structure
    including chunks of content, furniture text, and source metadata. This can be
    directly inserted into a SQL database table.
    """

    def __init__(self):
        """
        Initialize the SQL formatter with default configuration.

        Sets up the configuration options for SQL formatting, including options
        for including metadata, images, and captions.
        """
        logger.info("Initializing SQL formatter")
        # Configuration options
        self.include_metadata = True
        self.include_images = True
        self.include_captions = True
        self.chunk_size = 2000  # Characters per chunk

    def format_as_sql_json(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the document data into a SQL-compatible JSON structure.

        Args:
            document: The document data to format

        Returns:
            Dict[str, Any]: A dictionary in SQL-compatible format

        Raises:
            ValueError: If the document data is invalid or missing required fields
        """
        logger.info(f"Formatting document as SQL-compatible JSON")
        
        try:
            # Extract necessary data
            if not document:
                raise ValueError("Empty document data provided")

            # Extract metadata from the document
            source_metadata = self._extract_source_metadata(document)
            
            # Process elements into chunks
            chunks = self._process_elements_to_chunks(document.get("elements", []))
            
            # Extract furniture (title, abstract, etc.)
            furniture = self._extract_furniture(document)
            
            # Construct the SQL-compatible JSON structure
            sql_json = {
                "chunks": chunks,
                "furniture": furniture,
                "source": source_metadata
            }
            
            logger.info(f"Successfully formatted document as SQL-compatible JSON with {len(chunks)} chunks")
            return sql_json
            
        except Exception as e:
            logger.error(f"Error formatting document as SQL-compatible JSON: {e}", exc_info=True)
            raise

    def save_formatted_output(self, document: Dict[str, Any], output_dir: str) -> str:
        """
        Format the document and save the SQL-compatible output to a file.

        Args:
            document: The document data to format
            output_dir: Directory to save the formatted output

        Returns:
            str: Path to the saved output file

        Raises:
            ValueError: If the document data is invalid or the output directory is inaccessible
        """
        # Ensure output directory exists
        output_path = Path(output_dir)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            
        # Format the document
        sql_json = self.format_as_sql_json(document)
        
        # Determine output filename
        pdf_name = document.get("pdf_name", "document")
        if isinstance(pdf_name, list) and len(pdf_name) > 0:
            pdf_name = pdf_name[0]
        elif isinstance(pdf_name, str):
            pdf_name = Path(pdf_name).stem
        else:
            pdf_name = "document"
            
        output_file = output_path / f"{pdf_name}_sql.json"
        
        # Save to file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(sql_json, f, ensure_ascii=False, indent=2)
            logger.info(f"SQL-compatible output saved to {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Error saving SQL-compatible output: {e}", exc_info=True)
            raise

    def _extract_source_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract source metadata from the document.

        Args:
            document: The document data

        Returns:
            Dict[str, Any]: The source metadata
        """
        logger.debug("Extracting source metadata")
        metadata = {}
        
        # Extract basic document metadata
        if "pdf_name" in document:
            pdf_name = document["pdf_name"]
            if isinstance(pdf_name, list) and len(pdf_name) > 0:
                metadata["file_name"] = pdf_name[0]
            elif isinstance(pdf_name, str):
                metadata["file_name"] = pdf_name
                
        # Extract document information
        if "pdf_info" in document:
            pdf_info = document["pdf_info"]
            if isinstance(pdf_info, dict):
                metadata.update({
                    "title": pdf_info.get("Title", ""),
                    "author": pdf_info.get("Author", ""),
                    "subject": pdf_info.get("Subject", ""),
                    "producer": pdf_info.get("Producer", ""),
                    "creator": pdf_info.get("Creator", ""),
                    "creation_date": pdf_info.get("CreationDate", ""),
                    "mod_date": pdf_info.get("ModDate", ""),
                })
        
        # Add page count
        if "num_pages" in document:
            metadata["page_count"] = document["num_pages"]
        
        # Add document content type (default to "document")
        metadata["content_type"] = "document"
        
        return metadata

    def _extract_furniture(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract furniture text (title, headers, etc.) from the document.

        Args:
            document: The document data

        Returns:
            Dict[str, Any]: The furniture text
        """
        logger.debug("Extracting furniture text")
        furniture = {
            "title": "",
            "abstract": "",
            "headers": [],
            "footnotes": [],
            "tables": []
        }
        
        # Try to extract title from document metadata first
        if "pdf_info" in document and isinstance(document["pdf_info"], dict):
            pdf_info = document["pdf_info"]
            furniture["title"] = pdf_info.get("Title", "")
        
        # Extract other furniture from elements
        elements = document.get("elements", [])
        for elem in elements:
            # Extract headers (assume larger font elements near the beginning might be headers)
            if elem.get("type") == "text" and elem.get("font_size", 0) > 12:
                page_num = elem.get("page_num", 0)
                if page_num <= 2:  # First 2 pages might contain title and abstract
                    text = elem.get("text", "").strip()
                    if not furniture["title"] and len(text) < 200:
                        furniture["title"] = text
                    elif text and len(text) < 300:
                        furniture["headers"].append(text)
            
            # Extract tables
            elif elem.get("type") == "table":
                table_data = self._format_table_text(elem)
                if table_data:
                    furniture["tables"].append(table_data)
            
            # Extract footnotes (typically at bottom of page with smaller font)
            elif elem.get("type") == "text" and elem.get("font_size", 12) < 10:
                y_pos = elem.get("y", 0)
                height = elem.get("height", 0)
                page_height = elem.get("page_height", 1000)
                
                # If text is at bottom 20% of page, consider it a footnote
                if y_pos + height > page_height * 0.8:
                    footnote_text = elem.get("text", "").strip()
                    if footnote_text:
                        furniture["footnotes"].append(footnote_text)
        
        # If no title found yet, try to extract from first few text elements
        if not furniture["title"]:
            for elem in elements:
                if elem.get("type") == "text" and elem.get("page_num", 0) == 1:
                    text = elem.get("text", "").strip()
                    if text and len(text) < 200:
                        furniture["title"] = text
                        break
        
        # Try to construct an abstract from first page content
        abstract_text = ""
        for elem in elements:
            if (elem.get("type") == "text" and 
                elem.get("page_num", 0) == 1 and 
                elem.get("text", "").strip() != furniture["title"]):
                abstract_text += elem.get("text", "").strip() + " "
                if len(abstract_text) > 500:
                    break
        
        if abstract_text:
            furniture["abstract"] = abstract_text[:500].strip()  # Limit abstract length
        
        return furniture

    def _process_elements_to_chunks(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process elements into chunks for SQL storage.

        Args:
            elements: The document elements to process

        Returns:
            List[Dict[str, Any]]: The processed chunks
        """
        logger.debug(f"Processing {len(elements)} elements to chunks")
        chunks = []
        current_chunk = ""
        current_page = 1
        chunk_page_start = 1
        chunk_index = 0
        
        for elem in elements:
            elem_type = elem.get("type", "")
            page_num = elem.get("page_num", current_page)
            
            # Start a new chunk if we're on a new page and current chunk is not empty
            if page_num != current_page and current_chunk:
                # Save the current chunk
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": current_chunk.strip(),
                    "content_type": "text",
                    "page_range": f"{chunk_page_start}-{current_page}"
                })
                # Reset for new chunk
                chunk_index += 1
                current_chunk = ""
                chunk_page_start = page_num
            
            current_page = page_num
            
            # Process based on element type
            if elem_type == "text":
                text = elem.get("text", "").strip()
                if text:
                    # If adding this text would exceed chunk size, save current chunk and start new one
                    if len(current_chunk) + len(text) > self.chunk_size and current_chunk:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "content": current_chunk.strip(),
                            "content_type": "text",
                            "page_range": f"{chunk_page_start}-{current_page}"
                        })
                        chunk_index += 1
                        current_chunk = text + " "
                        chunk_page_start = page_num
                    else:
                        current_chunk += text + " "
            
            elif elem_type == "table":
                # Process table as a separate chunk
                table_text = self._format_table_text(elem)
                
                # First save any accumulated text as its own chunk
                if current_chunk:
                    chunks.append({
                        "chunk_index": chunk_index,
                        "content": current_chunk.strip(),
                        "content_type": "text",
                        "page_range": f"{chunk_page_start}-{current_page}"
                    })
                    chunk_index += 1
                
                # Then add the table as its own chunk
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": table_text,
                    "content_type": "table",
                    "page_range": f"{page_num}"
                })
                chunk_index += 1
                
                # Reset text accumulation
                current_chunk = ""
                chunk_page_start = page_num
            
            elif elem_type == "image" and self.include_images:
                # Process image as a separate chunk
                image_text = self._format_image_text(elem)
                
                # First save any accumulated text as its own chunk
                if current_chunk:
                    chunks.append({
                        "chunk_index": chunk_index,
                        "content": current_chunk.strip(),
                        "content_type": "text",
                        "page_range": f"{chunk_page_start}-{current_page}"
                    })
                    chunk_index += 1
                
                # Then add the image as its own chunk
                image_path = self._get_image_path(elem)
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": image_text,
                    "content_type": "image",
                    "page_range": f"{page_num}",
                    "image_path": image_path
                })
                chunk_index += 1
                
                # Reset text accumulation
                current_chunk = ""
                chunk_page_start = page_num
        
        # Add any remaining content as the final chunk
        if current_chunk:
            chunks.append({
                "chunk_index": chunk_index,
                "content": current_chunk.strip(),
                "content_type": "text",
                "page_range": f"{chunk_page_start}-{current_page}"
            })
        
        logger.debug(f"Created {len(chunks)} chunks from elements")
        return chunks

    def _map_element_type_to_content_type(self, elem_type: str) -> str:
        """
        Map element type to content type for SQL storage.

        Args:
            elem_type: The element type

        Returns:
            str: The content type
        """
        type_mapping = {
            "text": "text",
            "table": "table",
            "image": "image",
            "figure": "image",
            "chart": "image",
            "equation": "equation",
            "list": "list",
            "code": "code",
            "header": "header",
            "footer": "footer"
        }
        return type_mapping.get(elem_type, "text")

    def _format_table_text(self, table_elem: Dict[str, Any]) -> str:
        """
        Format table element for human-readable text representation.

        Args:
            table_elem: The table element data

        Returns:
            str: Formatted table text
        """
        if not table_elem or table_elem.get("type") != "table":
            return ""
        
        # First try with pre-processed table representation if available
        if "table_rep" in table_elem and table_elem["table_rep"]:
            return table_elem["table_rep"]
        
        # Otherwise, generate table blocks from data
        table_data = table_elem.get("data", [])
        if not table_data:
            return ""
        
        return self._generate_table_blocks(table_data)

    def _format_image_text(self, image_elem: Dict[str, Any]) -> str:
        """
        Format image element for text representation, including caption if available.

        Args:
            image_elem: The image element data

        Returns:
            str: Formatted image text
        """
        image_text = "[IMAGE]"
        
        # Add AI-generated description if available
        if self.include_captions and image_elem.get("ai_description"):
            image_text += f"\nDescription: {image_elem['ai_description']}"
        
        # Add OCR text if available
        if image_elem.get("ocr_text"):
            image_text += f"\nText content: {image_elem['ocr_text']}"
        
        # Add caption if available
        caption = image_elem.get("caption", "")
        if caption and self.include_captions:
            image_text += f"\nCaption: {caption}"
        
        return image_text

    def _generate_table_blocks(self, table_data: List[List[str]]) -> str:
        """
        Generate a text representation of a table.

        Args:
            table_data: 2D array of table cell content

        Returns:
            str: Text representation of the table
        """
        if not table_data or not isinstance(table_data, list):
            return ""
        
        # Calculate column widths for better formatting
        col_widths = []
        for row in table_data:
            if isinstance(row, list):
                for i, cell in enumerate(row):
                    cell_text = str(cell) if cell is not None else ""
                    width = len(cell_text)
                    if i >= len(col_widths):
                        col_widths.append(width)
                    else:
                        col_widths[i] = max(col_widths[i], width)
        
        # Generate table text with proper alignment
        table_lines = []
        
        # Add header row
        if table_data and len(table_data) > 0:
            header_row = table_data[0]
            if isinstance(header_row, list):
                header_cells = []
                for i, cell in enumerate(header_row):
                    cell_text = str(cell) if cell is not None else ""
                    if i < len(col_widths):
                        header_cells.append(cell_text.ljust(col_widths[i]))
                    else:
                        header_cells.append(cell_text)
                table_lines.append(" | ".join(header_cells))
                
                # Add separator line
                separator = []
                for width in col_widths:
                    separator.append("-" * width)
                table_lines.append(" | ".join(separator))
        
        # Add data rows
        for row_idx in range(1, len(table_data)):
            row = table_data[row_idx]
            if isinstance(row, list):
                row_cells = []
                for i, cell in enumerate(row):
                    cell_text = str(cell) if cell is not None else ""
                    if i < len(col_widths):
                        row_cells.append(cell_text.ljust(col_widths[i]))
                    else:
                        row_cells.append(cell_text)
                table_lines.append(" | ".join(row_cells))
        
        return "\n".join(table_lines)

    def _get_image_path(self, image_elem: Dict[str, Any]) -> str:
        """
        Get the path to the image file.

        Args:
            image_elem: The image element data

        Returns:
            str: Path to the image file
        """
        # Try to get the image path from the element
        if "image_path" in image_elem:
            return image_elem["image_path"]
        
        # Otherwise construct a path based on available metadata
        page_num = image_elem.get("page_num", 0)
        image_idx = image_elem.get("image_index", 0)
        return f"images/page_{page_num}_img_{image_idx}.png" 
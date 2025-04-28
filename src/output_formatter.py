"""
Output Formatter Module

This module provides functionality to convert the parsed document output into
different formats, including simplified JSON, Markdown, and HTML.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Union, Optional
import io
import csv
import uuid
from copy import deepcopy
from datetime import datetime

# Import the SQL formatter
from src.sql_formatter import process_docling_json_to_sql_format
from src.sql_insert_generator import SQLInsertGenerator

# Configure logging
logger = logging.getLogger(__name__)

class OutputFormatter:
    """
    A class for formatting document parsing output into different formats.
    
    This formatter takes the standard document JSON output from the parser
    and converts it to various formats for different use cases.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the OutputFormatter with configuration settings.
        
        Args:
            config: Configuration dictionary with options for formatting.
        """
        if config is None:
            config = {}

        # Set default configuration values
        self.config = {
            "include_metadata": True,
            "include_images": True,
            "image_base_url": '',
            "max_image_width": 800,
            "max_heading_depth": 3,
            "include_page_breaks": True,
            "include_captions": True,
            "table_formatting": "grid",  # 'grid', 'simple', or 'none'
            "doc_id": None,  # Document ID for SQL formatting
            "markdown_heading_style": 'atx',  # atx uses # style, setext uses underlines
            "include_section_numbers": False,
            "merge_consecutive_paragraphs": False,
            "simplified_structure": False,
            "output_indent": 2,
            "format": "simplified_json",
            "output_dir": None,
            "include_sql": False,
            "sql_dialect": "postgresql"
        }

        # Update with user-provided configuration
        self.config.update(config)
        
        logger.debug(f"Initialized OutputFormatter with config: {self.config}")
    
    def format_as_sql_json(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the document data as SQL-compatible JSON.
        
        This format is optimized for database ingestion with a specific schema.
        
        Args:
            document_data: Original document data dictionary
            
        Returns:
            Dictionary with SQL-compatible document structure
        """
        logger.info("Formatting document as SQL-compatible JSON")
        
        try:
            # Process document data using the SQL formatter
            sql_data = process_docling_json_to_sql_format(document_data, self.config.get('doc_id'))
            logger.info(f"Successfully formatted document as SQL-compatible JSON with {len(sql_data.get('chunks', []))} chunks")
            return sql_data
            
        except Exception as e:
            logger.error(f"Error formatting document as SQL-compatible JSON: {e}", exc_info=True)
            # Return minimal structure in case of error
            return {
                "error": str(e),
                "chunks": [],
                "furniture": [],
                "source_metadata": {}
            }
    
    def format_as_simplified_json(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format document data as simplified JSON.
        
        Args:
            document_data: Document data dictionary
            
        Returns:
            Simplified JSON object
        """
        try:
            logger.info("Formatting document as simplified JSON")
            
            # Handle string input (typically an error message)
            if isinstance(document_data, str):
                logger.error(f"Invalid document_data in format_as_simplified_json (received string): {document_data}")
                return {"error": document_data}
                
            # Initialize output structure
            output_json = {
                "type": "document",
                "metadata": self._extract_document_metadata(document_data),
                "content": []
            }

            # Process document content
            content_items = []
            
            # Process pages if available
            if "pages" in document_data:
                # Check if pages is a list
                if not isinstance(document_data["pages"], list):
                    logger.error(f"Invalid pages data in format_as_simplified_json (expected list, got {type(document_data['pages']).__name__})")
                    document_data["pages"] = []
                    
                pages = document_data["pages"]
                
                for page_idx, page in enumerate(pages):
                    # Skip if not a dictionary
                    if not isinstance(page, dict):
                        logger.error(f"Invalid page data in format_as_simplified_json (expected dict, got {type(page).__name__})")
                        continue
                    
                    # Process page content
                    page_content = self._process_page_content(page)
                    
                    # Add page break if configured
                    if self.config["include_page_breaks"] and page_idx < len(pages) - 1:
                        page_content.append({
                            "type": "page_break",
                            "page_number": page_idx + 1
                        })
                    
                    content_items.extend(page_content)
            
            # Process flattened_sequence if available
            if "flattened_sequence" in document_data:
                if isinstance(document_data["flattened_sequence"], list):
                    flattened_content = self._process_content_sequence(document_data["flattened_sequence"])
                    content_items.extend(flattened_content)
                else:
                    logger.error(f"Invalid flattened_sequence data (expected list, got {type(document_data['flattened_sequence']).__name__})")
            
            # Process images data if available
            if "images_data" in document_data:
                image_items = self._process_images_data(document_data["images_data"])
                content_items.extend(image_items)
            
            # Sort content by page number and position
            output_json["content"] = sorted(
                content_items,
                key=lambda x: (
                    x.get("metadata", {}).get("page_number", 999),
                    x.get("metadata", {}).get("position", 999)
                )
            )
            
            return output_json
        except Exception as e:
            error_msg = f"Error formatting document as simplified JSON: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def format_as_markdown(self, document_data: Dict[str, Any]) -> str:
        """
        Format the document data as Markdown text.
        
        Args:
            document_data: Original document data dictionary
            
        Returns:
            String with Markdown representation of the document
        """
        logger.info("Formatting document as Markdown")
        
        try:
            # First convert to simplified format
            simplified = self.format_as_simplified_json(document_data)
            
            # Convert simplified format to Markdown
            md_lines = []
            
            # Add document title
            title = simplified.get("metadata", {}).get("title", "Document")
            md_lines.append(f"# {title}")
            md_lines.append("")
            
            # Add document metadata (optional)
            if self.config["include_metadata"]:
                metadata = simplified.get("metadata", {})
                if metadata:
                    md_lines.append("## Document Information")
                    for key, value in metadata.items():
                        if key != "title" and value:  # Skip title as we already used it
                            md_lines.append(f"**{key.replace('_', ' ').title()}**: {value}")
                    md_lines.append("")
            
            # Process content items
            for item in simplified.get("content", []):
                item_type = item.get("type", "")
                
                if item_type == "heading":
                    level = min(item.get("level", 1), self.config["max_heading_depth"])
                    md_lines.append(f"{'#' * level} {item.get('text', '')}")
                    md_lines.append("")
                
                elif item_type == "paragraph":
                    md_lines.append(item.get("text", ""))
                    md_lines.append("")
                
                elif item_type == "table":
                    md_lines.extend(self._table_to_markdown(item))
                    md_lines.append("")
                
                elif item_type == "image":
                    caption = item.get("caption", "")
                    alt_text = item.get("alt_text", caption or "Image")
                    image_url = item.get("url", "")
                    
                    if image_url:
                        md_lines.append(f"![{alt_text}]({image_url})")
                        if caption and self.config["include_captions"]:
                            md_lines.append(f"*{caption}*")
                        md_lines.append("")
                
                elif item_type == "page_break" and self.config["include_page_breaks"]:
                    page_num = item.get("page_number", "")
                    md_lines.append(f"---\n*Page {page_num}*\n")
            
            return "\n".join(md_lines)
            
        except Exception as e:
            logger.error(f"Error formatting document as Markdown: {e}")
            return f"# Error\n\nFailed to format document: {e}"
    
    def format_as_html(self, document_data: Dict[str, Any]) -> str:
        """
        Format the document data as HTML.
        
        Args:
            document_data: Original document data dictionary
            
        Returns:
            String with HTML representation of the document
        """
        logger.info("Formatting document as HTML")
        
        try:
            # First convert to simplified format
            simplified = self.format_as_simplified_json(document_data)
            
            # Convert simplified format to HTML
            html_lines = []
            
            # HTML header
            html_lines.append("<!DOCTYPE html>")
            html_lines.append("<html>")
            html_lines.append("<head>")
            
            # Add document title
            title = simplified.get("metadata", {}).get("title", "Document")
            html_lines.append(f"  <title>{title}</title>")
            
            # Add basic styling
            html_lines.append("  <style>")
            html_lines.append("    body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }")
            html_lines.append("    img { max-width: 100%; height: auto; }")
            html_lines.append("    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }")
            html_lines.append("    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
            html_lines.append("    th { background-color: #f2f2f2; }")
            html_lines.append("    .caption { font-style: italic; margin-top: 5px; margin-bottom: 15px; }")
            html_lines.append("    .page-break { border-top: 1px dashed #ccc; margin: 20px 0; padding-top: 20px; color: #666; font-style: italic; }")
            html_lines.append("  </style>")
            html_lines.append("</head>")
            html_lines.append("<body>")
            
            # Add document title
            html_lines.append(f"  <h1>{title}</h1>")
            
            # Add document metadata (optional)
            if self.config["include_metadata"]:
                metadata = simplified.get("metadata", {})
                if metadata:
                    html_lines.append("  <div class='metadata'>")
                    html_lines.append("    <h2>Document Information</h2>")
                    html_lines.append("    <dl>")
                    for key, value in metadata.items():
                        if key != "title" and value:  # Skip title as we already used it
                            html_lines.append(f"      <dt>{key.replace('_', ' ').title()}</dt>")
                            html_lines.append(f"      <dd>{value}</dd>")
                    html_lines.append("    </dl>")
                    html_lines.append("  </div>")
            
            # Process content items
            for item in simplified.get("content", []):
                item_type = item.get("type", "")
                
                if item_type == "heading":
                    level = min(item.get("level", 1), self.config["max_heading_depth"])
                    html_lines.append(f"  <h{level}>{item.get('text', '')}</h{level}>")
                
                elif item_type == "paragraph":
                    html_lines.append(f"  <p>{item.get('text', '')}</p>")
                
                elif item_type == "table":
                    html_lines.extend(self._table_to_html(item))
                
                elif item_type == "image":
                    caption = item.get("caption", "")
                    alt_text = item.get("alt_text", caption or "Image")
                    image_url = item.get("url", "")
                    
                    if image_url:
                        html_lines.append(f"  <figure>")
                        html_lines.append(f"    <img src='{image_url}' alt='{alt_text}' />")
                        if caption and self.config["include_captions"]:
                            html_lines.append(f"    <figcaption class='caption'>{caption}</figcaption>")
                        html_lines.append(f"  </figure>")
                
                elif item_type == "page_break" and self.config["include_page_breaks"]:
                    page_num = item.get("page_number", "")
                    html_lines.append(f"  <div class='page-break'>Page {page_num}</div>")
            
            # HTML footer
            html_lines.append("</body>")
            html_lines.append("</html>")
            
            return "\n".join(html_lines)
            
        except Exception as e:
            logger.error(f"Error formatting document as HTML: {e}")
            return f"<!DOCTYPE html><html><body><h1>Error</h1><p>Failed to format document: {e}</p></body></html>"
    
    def format_as_csv(self, document_data: Dict[str, Any]) -> str:
        """
        Format the document data as CSV.
        
        This format extracts text content from paragraphs and headings
        and formats it as comma-separated values, with one row per content item.
        Tables are flattened with each cell represented as a separate row.
        
        Uses the csv module to properly handle escaping of special characters,
        particularly quotes and commas, ensuring compliance with RFC 4180.
        
        Args:
            document_data: Original document data dictionary
            
        Returns:
            String with CSV representation of the document
        """
        logger.info("Formatting document as CSV")
        
        try:
            # Use StringIO to build CSV in memory
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
            
            # Add header row
            header = ["content_type", "page_number", "content", "level", "metadata"]
            writer.writerow(header)
            
            content_count = 0  # Track whether we've added any content rows
            
            # Check if document_data is a string (error message)
            if isinstance(document_data, str):
                logger.error(f"Invalid document data in format_as_csv (received string): {document_data}")
                writer.writerow(["error", "0", f"Invalid document data: {document_data}", "", ""])
                return output.getvalue()
            
            # First try to convert to simplified format
            simplified = {}
            try:
                simplified = self.format_as_simplified_json(document_data)
            except Exception as e:
                logger.error(f"Error in format_as_csv while generating simplified JSON: {e}")
                # Continue without simplified format - we'll try to process directly
            
            # Process content items if available in simplified format
            if simplified and "content" in simplified and simplified["content"]:
                for item in simplified.get("content", []):
                    item_type = item.get("type", "")
                    page_number = str(item.get("metadata", {}).get("page_number", ""))
                    
                    if item_type == "heading":
                        level = str(item.get("level", 1))
                        text = item.get("text", "").replace("\n", " ")
                        writer.writerow([
                            "heading", 
                            page_number, 
                            text, 
                            level, 
                            ""
                        ])
                        content_count += 1
                    
                    elif item_type == "paragraph":
                        text = item.get("text", "").replace("\n", " ")
                        writer.writerow([
                            "paragraph", 
                            page_number, 
                            text, 
                            "", 
                            ""
                        ])
                        content_count += 1
                    
                    elif item_type == "table":
                        # Process table (grid or data format)
                        self._process_table_for_csv(writer, item, page_number, content_count)
                        content_count += 1  # At least for the table header row
                    
                    elif item_type == "image":
                        caption = item.get("caption", "").replace("\n", " ")
                        url = item.get("url", "")
                        writer.writerow([
                            "image", 
                            page_number, 
                            caption, 
                            "", 
                            url
                        ])
                        content_count += 1
                    
                    elif item_type == "page_break":
                        writer.writerow([
                            "page_break", 
                            page_number, 
                            "", 
                            "", 
                            ""
                        ])
                        content_count += 1
            
            # If simplified format didn't have content, try to process directly from the document
            elif "texts" in document_data:
                # Process text elements
                for i, text in enumerate(document_data.get("texts", [])):
                    if "content_layer" in text and text.get("content_layer") == "furniture":
                        continue  # Skip furniture elements
                    
                    # Extract text content and metadata
                    content_text = text.get("text", "").replace("\n", " ")
                    page_number = ""
                    if "prov" in text and "page_no" in text["prov"]:
                        page_number = str(text["prov"].get("page_no", ""))
                    
                    # Determine content type
                    content_type = "paragraph"
                    level = ""
                    if "label" in text:
                        label = text.get("label", "")
                        if "section_header" in label or "title" in label:
                            content_type = "heading"
                            # Try to determine heading level
                            if "h1" in label:
                                level = "1"
                            elif "h2" in label:
                                level = "2"
                            elif "h3" in label:
                                level = "3"
                            else:
                                level = "1"  # Default
                    
                    # Write row
                    writer.writerow([
                        content_type,
                        page_number,
                        content_text,
                        level,
                        f"text_index:{i}"
                    ])
                    content_count += 1
                
                # Process tables if available
                for i, table in enumerate(document_data.get("tables", [])):
                    if "content_layer" in table and table.get("content_layer") == "furniture":
                        continue  # Skip furniture tables
                    
                    # Get page number
                    page_number = ""
                    if "prov" in table and "page_no" in table["prov"]:
                        page_number = str(table["prov"].get("page_no", ""))
                    
                    # Add table header row
                    writer.writerow([
                        "table",
                        page_number,
                        f"Table {i+1}",
                        "",
                        f"table_index:{i}"
                    ])
                    content_count += 1
                    
                    # Process cells
                    for cell in table.get("cells", []):
                        row = cell.get("row", 0)
                        col = cell.get("col", 0)
                        cell_text = cell.get("text", "").replace("\n", " ")
                        metadata = f"row:{row};col:{col}"
                        
                        writer.writerow([
                            "table_cell",
                            page_number,
                            cell_text,
                            "",
                            metadata
                        ])
                        content_count += 1
            
            # Process images if available
            for i, image in enumerate(document_data.get("pictures", [])):
                if "content_layer" in image and image.get("content_layer") == "furniture":
                    continue  # Skip furniture images
                
                # Get page number
                page_number = ""
                if "prov" in image and "page_no" in image["prov"]:
                    page_number = str(image["prov"].get("page_no", ""))
                
                # Add image row
                caption = image.get("caption", "") or f"Image {i+1}"
                writer.writerow([
                    "image",
                    page_number,
                    caption,
                    "",
                    f"image_index:{i}"
                ])
                content_count += 1
            
            # Make sure we have at least one content row in the output
            if content_count == 0:
                # Empty content, add a dummy row to avoid blank CSV
                writer.writerow([
                    "info", 
                    "0", 
                    "No content found in document", 
                    "", 
                    ""
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error formatting document as CSV: {e}")
            # Return minimal CSV with error info
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["content_type", "page_number", "content", "level", "metadata"])
            writer.writerow(["error", "0", f"Failed to format document: {str(e)}", "", ""])
            return output.getvalue()
    
    def _process_table_for_csv(self, writer, table_item, page_number, content_count):
        """
        Helper method to process a table item for CSV output.
        
        Args:
            writer: CSV writer object
            table_item: Table item dictionary
            page_number: Page number string
            content_count: Current content count (passed by reference)
            
        Returns:
            None (modifies writer and content_count directly)
        """
        # Add table info row
        caption = table_item.get("caption", "").replace("\n", " ")
        writer.writerow([
            "table", 
            page_number, 
            caption, 
            "", 
            ""
        ])
        
        # Process table cells
        # Check for grid format (from _process_table)
        if "grid" in table_item:
            grid = table_item.get("grid", [])
            for row_idx, row in enumerate(grid):
                for col_idx, cell in enumerate(row):
                    if cell is not None:  # Skip empty cells
                        cell_text = str(cell.get("text", "")).replace("\n", " ")
                        metadata = f"row:{row_idx};col:{col_idx}"
                        writer.writerow([
                            "table_cell", 
                            page_number, 
                            cell_text, 
                            "", 
                            metadata
                        ])
                        content_count += 1
        
        # Check for data format (simpler table representation)
        elif "data" in table_item:
            rows = table_item.get("data", [])
            for row_idx, row in enumerate(rows):
                for col_idx, cell in enumerate(row):
                    cell_text = str(cell).replace("\n", " ")
                    metadata = f"row:{row_idx};col:{col_idx}"
                    writer.writerow([
                        "table_cell", 
                        page_number, 
                        cell_text, 
                        "", 
                        metadata
                    ])
                    content_count += 1
        
        # Handle raw cells format (input format)
        elif "cells" in table_item:
            cells = table_item.get("cells", [])
            for cell in cells:
                row = cell.get("row", 0)
                col = cell.get("col", 0)
                cell_text = cell.get("text", "").replace("\n", " ")
                metadata = f"row:{row};col:{col}"
                writer.writerow([
                    "table_cell", 
                    page_number, 
                    cell_text, 
                    "", 
                    metadata
                ])
                content_count += 1
    
    def save_formatted_output(
        self, 
        document_data: Dict[str, Any], 
        output_path: Union[str, Path], 
        format_type: str = "json"
    ) -> str:
        """
        Format and save document data to a file in the specified format.
        
        Args:
            document_data: Document data dictionary
            output_path: Directory to save the output
            format_type: Format to save as (json, md, html, csv, sql)
            
        Returns:
            Path to the saved file
        """
        logger.info(f"Saving formatted output in {format_type} format to {output_path}")
        
        # Ensure output_path is a Path object
        if isinstance(output_path, str):
            output_path = Path(output_path)
            
        # Create output directory if it doesn't exist
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
        
        # Get document name for output filename
        doc_name = document_data.get("metadata", {}).get("filename", "document")
        if isinstance(doc_name, str):
            doc_name = Path(doc_name).stem
        
        # Format the document based on the requested format
        if format_type.lower() == "json":
            # Format the document data first, then save
            formatted_data = self.format_as_simplified_json(document_data)
            output_file = output_path / f"document_simplified.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        elif format_type.lower() == "sql":
            # Format the document data first, then save
            formatted_data = self.format_as_sql_json(document_data)
            output_file = output_path / f"document_sql.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)
                
        elif format_type.lower() == "md":
            # Format the document data first, then save
            formatted_data = self.format_as_markdown(document_data)
            output_file = output_path / f"document.md"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_data)
                
        elif format_type.lower() == "html":
            # Format the document data first, then save
            formatted_data = self.format_as_html(document_data)
            output_file = output_path / f"document.html"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_data)
                
        elif format_type.lower() == "csv":
            # Format the document data first, then save
            formatted_data = self.format_as_csv(document_data)
            output_file = output_path / f"document.csv"
            
            with open(output_file, "w", encoding="utf-8", newline="") as f:
                f.write(formatted_data)
                
        else:
            logger.warning(f"Unsupported format type: {format_type}, defaulting to JSON")
            # Format the document data first, then save
            formatted_data = self.format_as_simplified_json(document_data)
            output_file = output_path / f"document_simplified.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved formatted output to {output_file}")
        return str(output_file)
    
    def _extract_document_metadata(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract document metadata from the original document data.
        
        Args:
            document_data: Original document data dictionary
            
        Returns:
            Dictionary with document metadata
        """
        metadata = {}
        
        # Check if document_data is a string (error message from previous step)
        if isinstance(document_data, str):
            logger.error(f"Invalid document data in _extract_document_metadata (received string): {document_data}")
            metadata["name"] = "error"
            metadata["error"] = document_data
            return metadata
        
        # Extract document name
        metadata["name"] = document_data.get("name", "")
        
        # Extract document title if available
        if "metadata" in document_data and isinstance(document_data["metadata"], dict):
            doc_metadata = document_data["metadata"]
            
            # Common metadata fields
            metadata_fields = [
                "title", "author", "creator", "producer", "subject", 
                "keywords", "created", "modified", "page_count"
            ]
            
            for field in metadata_fields:
                if field in doc_metadata:
                    metadata[field] = doc_metadata[field]
        
        # Get page count if available
        if "pages" in document_data and isinstance(document_data["pages"], list):
            metadata["page_count"] = len(document_data["pages"])
        
        return metadata
    
    def _process_content_sequence(self, flattened_sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process the flattened content sequence into a simplified format.
        
        Args:
            flattened_sequence: List of elements in reading order
            
        Returns:
            List of simplified content items
        """
        content = []
        current_page = None
        
        for element in flattened_sequence:
            element_type = element.get("metadata", {}).get("type", "")
            
            # Add page break if needed and configured
            page_number = element.get("metadata", {}).get("page_number")
            if (self.config["include_page_breaks"] and 
                page_number is not None and 
                page_number != current_page):
                
                current_page = page_number
                if content:  # Don't add page break before first content
                    content.append({
                        "type": "page_break",
                        "page_number": page_number
                    })
            
            # Process the element based on its type
            if element_type == "heading" or element_type.startswith("h"):
                content.append(self._process_heading(element))
                
            elif element_type == "paragraph" or element_type == "text":
                content.append(self._process_paragraph(element))
                
            elif element_type == "table":
                content.append(self._process_table(element))
                
            elif element_type in ["image", "picture"]:
                content.append(self._process_image(element))
        
        return content
    
    def _process_page_content(self, page: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process content from a page.
        
        Args:
            page: Page data dictionary
            
        Returns:
            List of simplified content items
        """
        content = []
        
        # Process paragraphs/segments
        segments = page.get("segments", [])
        for segment in segments:
            content.append({
                "type": "paragraph",
                "text": segment.get("text", ""),
                "metadata": {
                    "page_number": page.get("page_number", 0)
                }
            })
        
        # Process tables
        tables = page.get("tables", [])
        for table in tables:
            content.append(self._process_table(table))
        
        # Process images
        pictures = page.get("pictures", [])
        for picture in pictures:
            content.append(self._process_image(picture))
        
        return content
    
    def _process_heading(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a heading element.
        
        Args:
            element: Heading element dictionary
            
        Returns:
            Simplified heading item
        """
        # Determine heading level (h1, h2, etc.)
        heading_type = element.get("metadata", {}).get("type", "")
        level = 1  # Default level
        
        if heading_type.startswith("h") and len(heading_type) > 1:
            try:
                level = int(heading_type[1])
            except ValueError:
                pass
        
        return {
            "type": "heading",
            "level": level,
            "text": element.get("text", ""),
            "metadata": {
                "page_number": element.get("metadata", {}).get("page_number")
            }
        }
    
    def _process_paragraph(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a paragraph element.
        
        Args:
            element: Paragraph element dictionary
            
        Returns:
            Simplified paragraph item
        """
        return {
            "type": "paragraph",
            "text": element.get("text", ""),
            "metadata": {
                "page_number": element.get("metadata", {}).get("page_number")
            }
        }
    
    def _process_table(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a table element.
        
        Args:
            element: Table element dictionary
            
        Returns:
            Simplified table item
        """
        cells = element.get("cells", [])
        
        # Determine table dimensions
        max_row = 0
        max_col = 0
        for cell in cells:
            row = cell.get("row", 0)
            col = cell.get("col", 0)
            rowspan = cell.get("rowspan", 1)
            colspan = cell.get("colspan", 1)
            max_row = max(max_row, row + rowspan)
            max_col = max(max_col, col + colspan)
        
        # Create empty table grid
        grid = []
        for i in range(max_row):
            grid.append([None] * max_col)
        
        # Fill the grid with cell contents
        for cell in cells:
            row = cell.get("row", 0)
            col = cell.get("col", 0)
            rowspan = cell.get("rowspan", 1)
            colspan = cell.get("colspan", 1)
            text = cell.get("text", "")
            
            # Skip invalid cells
            if row < 0 or col < 0 or row >= max_row or col >= max_col:
                continue
            
            # Store cell in grid
            grid[row][col] = {
                "text": text,
                "rowspan": rowspan,
                "colspan": colspan
            }
        
        return {
            "type": "table",
            "caption": element.get("metadata", {}).get("caption", ""),
            "grid": grid,
            "metadata": {
                "page_number": element.get("metadata", {}).get("page_number")
            }
        }
    
    def _process_image(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an image element.
        
        Args:
            element: Image element dictionary
            
        Returns:
            Simplified image item
        """
        # Get image path
        image_path = element.get("image_path", "")
        
        # If a base URL is configured, create a full URL
        image_url = image_path
        if self.config["image_base_url"] and image_path:
            image_url = self.config["image_base_url"] + "/" + image_path.split("/")[-1]
        
        return {
            "type": "image",
            "url": image_url,
            "caption": element.get("metadata", {}).get("caption", ""),
            "alt_text": element.get("metadata", {}).get("alt_text", ""),
            "metadata": {
                "page_number": element.get("metadata", {}).get("page_number"),
                "width": element.get("metadata", {}).get("width"),
                "height": element.get("metadata", {}).get("height")
            }
        }
    
    def _process_images_data(self, images_data: Any) -> List[Dict[str, Any]]:
        """
        Process images data from document and convert to content items.
        
        Args:
            images_data: Images data from document
            
        Returns:
            List of image content items
        """
        try:
            logger.debug("Processing images data")
            
            # Handle non-dictionary input
            if not isinstance(images_data, dict):
                logger.error(f"Invalid images_data in _process_images_data (expected dict, got {type(images_data).__name__}): {images_data}")
                return []
                
            result = []
            
            # Process each image
            for img_id, img_data in images_data.items():
                # Skip if not a dictionary
                if not isinstance(img_data, dict):
                    logger.error(f"Invalid image data for {img_id} (expected dict, got {type(img_data).__name__})")
                    continue
                
                # Extract image metadata
                metadata = {}
                if "page_number" in img_data:
                    metadata["page_number"] = img_data["page_number"]
                if "position" in img_data:
                    metadata["position"] = img_data["position"]
                if "bbox" in img_data:
                    metadata["bbox"] = img_data["bbox"]
                    
                # Create image content item
                image_item = {
                    "type": "image",
                    "id": img_id,
                    "metadata": metadata
                }
                
                # Add caption if available and configured
                if self.config["include_captions"] and "caption" in img_data:
                    image_item["caption"] = img_data["caption"]
                
                # Add image path if available
                if "path" in img_data:
                    image_item["path"] = img_data["path"]
                    
                result.append(image_item)
                
            return result
        except Exception as e:
            logger.error(f"Error processing images data: {str(e)}")
            return []
    
    def _table_to_markdown(self, table: Dict[str, Any]) -> List[str]:
        """
        Convert a table item to Markdown format.
        
        Args:
            table: Table item dictionary
            
        Returns:
            List of Markdown lines for the table
        """
        md_lines = []
        grid = table.get("grid", [])
        
        if not grid:
            return md_lines
        
        # Add caption if available and configured
        caption = table.get("caption", "")
        if caption and self.config["include_captions"]:
            md_lines.append(f"**{caption}**")
        
        # Create the table header row
        header_row = grid[0] if grid else []
        header_cells = []
        
        for cell in header_row:
            if cell is None:
                header_cells.append("")
            else:
                header_cells.append(cell.get("text", ""))
        
        md_lines.append("| " + " | ".join(header_cells) + " |")
        
        # Create the separator row
        md_lines.append("| " + " | ".join(["---"] * len(header_row)) + " |")
        
        # Create data rows
        for row in grid[1:]:
            row_cells = []
            
            for cell in row:
                if cell is None:
                    row_cells.append("")
                else:
                    row_cells.append(cell.get("text", ""))
            
            md_lines.append("| " + " | ".join(row_cells) + " |")
        
        return md_lines
    
    def _table_to_html(self, table: Dict[str, Any]) -> List[str]:
        """
        Convert a table item to HTML format.
        
        Args:
            table: Table item dictionary
            
        Returns:
            List of HTML lines for the table
        """
        html_lines = []
        grid = table.get("grid", [])
        
        if not grid:
            return html_lines
        
        # Start table
        html_lines.append("  <table>")
        
        # Add caption if available and configured
        caption = table.get("caption", "")
        if caption and self.config["include_captions"]:
            html_lines.append(f"    <caption>{caption}</caption>")
        
        # Add header row
        if grid:
            html_lines.append("    <thead>")
            html_lines.append("      <tr>")
            
            for cell in grid[0]:
                if cell is None:
                    html_lines.append("        <th></th>")
                else:
                    colspan = cell.get("colspan", 1)
                    rowspan = cell.get("rowspan", 1)
                    
                    if colspan > 1 or rowspan > 1:
                        html_lines.append(f"        <th colspan='{colspan}' rowspan='{rowspan}'>{cell.get('text', '')}</th>")
                    else:
                        html_lines.append(f"        <th>{cell.get('text', '')}</th>")
            
            html_lines.append("      </tr>")
            html_lines.append("    </thead>")
        
        # Add body rows
        if len(grid) > 1:
            html_lines.append("    <tbody>")
            
            for row in grid[1:]:
                html_lines.append("      <tr>")
                
                for cell in row:
                    if cell is None:
                        html_lines.append("        <td></td>")
                    else:
                        colspan = cell.get("colspan", 1)
                        rowspan = cell.get("rowspan", 1)
                        
                        if colspan > 1 or rowspan > 1:
                            html_lines.append(f"        <td colspan='{colspan}' rowspan='{rowspan}'>{cell.get('text', '')}</td>")
                        else:
                            html_lines.append(f"        <td>{cell.get('text', '')}</td>")
                
                html_lines.append("      </tr>")
            
            html_lines.append("    </tbody>")
        
        # End table
        html_lines.append("  </table>")
        
        return html_lines

    def format_as_sql(self, document_data: Dict[str, Any], save_to_file: bool = False) -> str:
        """
        Format document data as SQL INSERT statements.

        Args:
            document_data: The parsed document data.
            save_to_file: Whether to save the SQL to a file.

        Returns:
            SQL INSERT statements as a string.
        """
        try:
            dialect = self.config.get("sql_dialect", "postgresql")
            self.logger.info(f"Generating SQL INSERT statements using {dialect} dialect")
            
            sql_generator = SQLInsertGenerator(dialect=dialect)
            sql_inserts = sql_generator.generate_sql_inserts(document_data)
            
            if save_to_file and self.config.get("output_dir"):
                output_path = sql_generator.save_sql_inserts(
                    document_data,
                    self.config["output_dir"]
                )
                self.logger.info(f"Saved SQL INSERT statements to {output_path}")
            
            return sql_inserts
        except Exception as e:
            error_msg = f"Error generating SQL INSERT statements: {str(e)}"
            self.logger.error(error_msg)
            return f"-- {error_msg}"
    
    def format_document(self, document_data: Dict[str, Any], save_to_file: bool = True) -> Dict[str, Any]:
        """
        Format the document data according to the specified format.

        Args:
            document_data: The parsed document data.
            save_to_file: Whether to save the formatted output to a file.

        Returns:
            The formatted document data.
        """
        format_type = self.config.get("format", "simplified_json").lower()
        logger.info(f"Formatting document as {format_type}")

        # Check if document_data is a string (error message from previous step)
        if isinstance(document_data, str):
            logger.error(f"Invalid document data in format_document (received string): {document_data}")
            # Return basic error structure
            return {
                "error": f"Invalid document data: {document_data}"
            }

        result = {}

        try:
            if format_type == "json":
                result["json"] = document_data
                if save_to_file:
                    self.save_formatted_output(document_data, self.config["output_dir"], format_type)

            elif format_type == "simplified_json":
                result["simplified_json"] = self.format_as_simplified_json(document_data)
                if save_to_file:
                    self.save_formatted_output(document_data, self.config["output_dir"], format_type)

            elif format_type == "markdown":
                result["markdown"] = self.format_as_markdown(document_data)
                if save_to_file:
                    self.save_formatted_output(document_data, self.config["output_dir"], format_type)

            elif format_type == "html":
                result["html"] = self.format_as_html(document_data)
                if save_to_file:
                    self.save_formatted_output(document_data, self.config["output_dir"], format_type)

            elif format_type == "csv":
                result["csv"] = self.format_as_csv(document_data)
                if save_to_file:
                    self.save_formatted_output(document_data, self.config["output_dir"], format_type)

            # Generate SQL JSON if requested
            if self.config.get("include_sql_json", False):
                result["sql_json"] = self.format_as_sql_json(document_data)
                if save_to_file:
                    self.save_formatted_output(document_data, self.config["output_dir"], "sql")
            
            # Generate SQL INSERT statements if requested
            if self.config.get("include_sql", False):
                result["sql"] = self.format_as_sql(document_data, save_to_file=save_to_file)

        except Exception as e:
            logger.error(f"Error formatting document: {e}")
            result["error"] = str(e)

        return result

    def _process_document_content(self, doc_content: Any) -> List[Dict[str, Any]]:
        """
        Process document content into a list of content items.
        
        Args:
            doc_content: Document content to process
            
        Returns:
            List of processed content items
        """
        try:
            logger.debug("Processing document content")
            result = []
            
            # Handle non-dictionary input
            if not isinstance(doc_content, dict):
                logger.error(f"Invalid doc_content in _process_document_content (expected dict, got {type(doc_content).__name__}): {doc_content}")
                return []
            
            # Process pages if available
            pages = doc_content.get("pages", [])
            if not isinstance(pages, list):
                logger.error(f"Invalid pages data (expected list, got {type(pages).__name__})")
                return []
                
            for page in pages:
                # Skip if not a dictionary
                if not isinstance(page, dict):
                    logger.error(f"Invalid page data (expected dict, got {type(page).__name__})")
                    continue
                    
                page_number = page.get("page_number", 0)
                blocks = page.get("blocks", [])
                
                # Skip if blocks is not a list
                if not isinstance(blocks, list):
                    logger.error(f"Invalid blocks data for page {page_number} (expected list, got {type(blocks).__name__})")
                    continue
                
                for block in blocks:
                    # Skip if not a dictionary
                    if not isinstance(block, dict):
                        logger.error(f"Invalid block data in page {page_number} (expected dict, got {type(block).__name__})")
                        continue
                    
                    # Create content item
                    content_item = {
                        "type": "text",
                        "text": block.get("text", ""),
                        "metadata": {
                            "page_number": page_number,
                            "position": block.get("position", 0)
                        }
                    }
                    
                    # Add block type if available
                    if "block_type" in block:
                        content_item["metadata"]["block_type"] = block["block_type"]
                    
                    # Add bbox if available
                    if "bbox" in block:
                        content_item["metadata"]["bbox"] = block["bbox"]
                    
                    result.append(content_item)
            
            # Process flattened if available and no pages processed
            if len(result) == 0 and "flattened" in doc_content:
                flattened = doc_content.get("flattened", [])
                
                # Skip if flattened is not a list
                if not isinstance(flattened, list):
                    logger.error(f"Invalid flattened data (expected list, got {type(flattened).__name__})")
                    return []
                
                for item in flattened:
                    # Skip if not a dictionary
                    if not isinstance(item, dict):
                        logger.error(f"Invalid flattened item (expected dict, got {type(item).__name__})")
                        continue
                    
                    # Create content item
                    content_item = {
                        "type": "text",
                        "text": item.get("text", ""),
                        "metadata": {
                            "page_number": item.get("page_number", 0),
                            "position": item.get("position", 0)
                        }
                    }
                    
                    # Add block type if available
                    if "block_type" in item:
                        content_item["metadata"]["block_type"] = item["block_type"]
                    
                    # Add bbox if available
                    if "bbox" in item:
                        content_item["metadata"]["bbox"] = item["bbox"]
                    
                    result.append(content_item)
            
            return result
        except Exception as e:
            logger.error(f"Error processing document content: {str(e)}")
            return []


# Example usage (when running as standalone module)
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python output_formatter.py input_file.json output_format")
        print("Output formats: json, md, html")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_format = sys.argv[2]
    
    # Load document data
    with open(input_file, 'r', encoding='utf-8') as f:
        document_data = json.load(f)
    
    # Create formatter with default configuration
    formatter = OutputFormatter()
    
    # Generate output path from input file
    input_path = Path(input_file)
    output_dir = input_path.parent
    
    # Save formatted output
    output_file = formatter.save_formatted_output(
        document_data, 
        output_dir,
        output_format
    )
    
    print(f"Formatted output saved to {output_file}") 
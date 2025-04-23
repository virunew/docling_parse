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

# Configure logging
logger = logging.getLogger(__name__)

class OutputFormatter:
    """
    A class for formatting document parsing output into different formats.
    
    This formatter takes the standard document JSON output from the parser
    and converts it to various formats for different use cases.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the OutputFormatter with configuration settings.
        
        Args:
            config: Dictionary with configuration settings
        """
        self.config = config or {}
        
        # Default configuration
        self.default_config = {
            'include_metadata': True,
            'include_images': True,
            'image_base_url': '',
            'max_image_width': 800,
            'max_heading_depth': 3,
            'include_page_breaks': True,
            'include_captions': True,
            'table_formatting': 'grid'  # 'grid', 'simple', or 'none'
        }
        
        # Apply default config for any missing values
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
                
        logger.debug(f"Initialized OutputFormatter with config: {self.config}")
    
    def format_as_simplified_json(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the document data as simplified JSON.
        
        This format is optimized for readability and easier consumption by client applications.
        
        Args:
            document_data: Original document data dictionary
            
        Returns:
            Dictionary with simplified document structure
        """
        logger.info("Formatting document as simplified JSON")
        
        try:
            # Check if document_data is a string (error message from previous step)
            if isinstance(document_data, str):
                logger.error(f"Invalid document data (received string instead of dict): {document_data}")
                return {
                    "metadata": {"name": "error", "error": document_data},
                    "content": []
                }
                
            # Initialize output structure
            output = {
                "metadata": self._extract_document_metadata(document_data),
                "content": []
            }
            
            # Process document content
            if "flattened_sequence" in document_data:
                output["content"] = self._process_content_sequence(document_data["flattened_sequence"])
            elif "pages" in document_data:
                # Process pages if available
                pages = document_data.get("pages", [])
                content = []
                
                for page in pages:
                    # Add page break marker if configured
                    if self.config["include_page_breaks"] and content:
                        content.append({
                            "type": "page_break",
                            "page_number": page.get("page_number")
                        })
                    
                    # Process page content
                    page_content = self._process_page_content(page)
                    content.extend(page_content)
                
                output["content"] = content
            
            # Add images data if available and configured
            if self.config["include_images"] and "images_data" in document_data:
                output["images"] = self._process_images_data(document_data["images_data"])
            
            logger.info("Successfully formatted document as simplified JSON")
            return output
            
        except Exception as e:
            logger.error(f"Error formatting document as simplified JSON: {e}")
            # Return minimal structure in case of error
            return {
                "metadata": {"name": document_data.get("name", "") if isinstance(document_data, dict) else "", "error": str(e)},
                "content": []
            }
    
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
    ) -> Path:
        """
        Save the formatted document to a file.
        
        Args:
            document_data: Original document data dictionary
            output_path: Directory to save the formatted file
            format_type: Output format type ('json', 'md', 'html', or 'csv')
            
        Returns:
            Path object to the saved file
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get the document name, ensuring we handle various cases
        doc_name = "document"  # Default fallback name
        
        if isinstance(document_data, dict):
            # First check if name is directly in the dictionary
            if "name" in document_data:
                doc_name = document_data.get("name", "document")
            # Then check metadata
            elif "metadata" in document_data and isinstance(document_data["metadata"], dict):
                doc_name = document_data["metadata"].get("name", "document")
            # Finally check origin
            elif "origin" in document_data and isinstance(document_data["origin"], dict):
                # Try to get filename without extension from origin
                filename = document_data["origin"].get("filename", "")
                if filename:
                    # Strip extension if present
                    doc_name = Path(filename).stem
        
        # Sanitize doc_name to be safe for file names
        doc_name = doc_name.replace('/', '_').replace('\\', '_').replace(':', '_')
        
        # Format the output based on the requested format type
        if format_type.lower() == "json":
            formatted_data = self.format_as_simplified_json(document_data)
            output_file = output_path / f"{doc_name}_simplified.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, indent=2)
                
        elif format_type.lower() == "md":
            formatted_data = self.format_as_markdown(document_data)
            output_file = output_path / f"{doc_name}.md"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_data)
                
        elif format_type.lower() == "html":
            formatted_data = self.format_as_html(document_data)
            output_file = output_path / f"{doc_name}.html"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_data)
                
        elif format_type.lower() == "csv":
            formatted_data = self.format_as_csv(document_data)
            output_file = output_path / f"{doc_name}.csv"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_data)
                
        else:
            logger.warning(f"Unsupported format type: {format_type}, defaulting to JSON")
            formatted_data = self.format_as_simplified_json(document_data)
            output_file = output_path / f"{doc_name}_simplified.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, indent=2)
        
        logger.info(f"Saved formatted output to {output_file}")
        return output_file
    
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
    
    def _process_images_data(self, images_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process images data into a simplified list.
        
        Args:
            images_data: Images data dictionary
            
        Returns:
            List of simplified image items
        """
        images = []
        
        # Extract images list if available
        image_list = images_data.get("images", [])
        
        for img in image_list:
            image_path = img.get("path", "")
            
            # If a base URL is configured, create a full URL
            image_url = image_path
            if self.config["image_base_url"] and image_path:
                image_url = self.config["image_base_url"] + "/" + image_path.split("/")[-1]
            
            # Create simplified image entry
            image_item = {
                "type": "image",
                "url": image_url,
                "caption": img.get("caption", ""),
                "alt_text": img.get("alt_text", ""),
                "metadata": {
                    "page_number": img.get("page_number"),
                    "width": img.get("width"),
                    "height": img.get("height")
                }
            }
            
            images.append(image_item)
        
        return images
    
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
#!/usr/bin/env python3
"""
PDF Document Parser Main Program

This module serves as the entry point for the PDF document parsing application.
It processes PDF documents using the docling library, extracts text and images,
and generates a structured dictionary of elements for use by other application
components.

Environment variables can be set in a .env file:
- DOCLING_PDF_PATH: Path to input PDF file
- DOCLING_OUTPUT_DIR: Directory for output files
- DOCLING_LOG_LEVEL: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- DOCLING_CONFIG_FILE: Optional path to a configuration file
- DOCLING_OUTPUT_FORMAT: Output format (json, md, html)
- DOCLING_IMAGE_BASE_URL: Base URL for image links in output
"""
import docling_fix

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Standard library imports
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Import the logger configuration
from logger_config import logger, setup_logging

# Import the helper functions
from parse_helper import process_pdf_document, save_output

# Import the output formatter
from output_formatter import OutputFormatter

# Import docling library components
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from element_map_builder import build_element_map
    # Import the content extractor module
    from content_extractor import (
        extract_text_content, 
        extract_table_content, 
        extract_image_content, 
        is_furniture, 
        find_sibling_text_in_sequence, 
        get_captions
    )
    # Import the metadata extractor module
    from metadata_extractor import (
        convert_bbox,
        extract_page_number,
        extract_image_metadata,
        build_metadata_object,
        extract_full_metadata
    )
    # Import the PDFImageExtractor class
    from pdf_image_extractor import PDFImageExtractor, ImageContentRelationship
except ImportError as e:
    logging.error(f"Error importing local modules: {e}")
    sys.exit(1)

# Fix docling imports
import docling_fix

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Standard library imports
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Import the logger configuration
from logger_config import logger, setup_logging

# Import the helper functions
from parse_helper import process_pdf_document, save_output

# Import the output formatter
from output_formatter import OutputFormatter

try:
    from element_map_builder import build_element_map
    # Import the content extractor module
    from content_extractor import (
        extract_text_content, 
        extract_table_content, 
        extract_image_content, 
        is_furniture, 
        find_sibling_text_in_sequence, 
        get_captions
    )
    # Import the metadata extractor module
    from metadata_extractor import (
        convert_bbox,
        extract_page_number,
        extract_image_metadata,
        build_metadata_object,
        extract_full_metadata
    )
    # Import the PDFImageExtractor class
    from pdf_image_extractor import PDFImageExtractor, ImageContentRelationship
except ImportError as e:
    logging.error(f"Error importing local modules: {e}")
    sys.exit(1)


class Configuration:
    """
    Manages configuration settings with proper precedence:
    1. Environment variables
    2. Command-line arguments
    3. Default values
    """
    
    def __init__(self):
        """Initialize with default values."""
        # Default configuration values
        self.pdf_path = None
        self.output_dir = "output"
        self.log_level = "INFO"
        self.config_file = None
        self.output_format = "json"
        self.image_base_url = ""
        self.include_metadata = True
        self.include_page_breaks = True
        self.include_captions = True
        
        # Load environment variables
        self._load_from_env()
        
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Load variables from .env file if present
        load_dotenv()
        
        # Override with environment variables if they exist
        if os.environ.get("DOCLING_PDF_PATH"):
            self.pdf_path = os.environ.get("DOCLING_PDF_PATH")
            
        if os.environ.get("DOCLING_OUTPUT_DIR"):
            self.output_dir = os.environ.get("DOCLING_OUTPUT_DIR")
            
        if os.environ.get("DOCLING_LOG_LEVEL"):
            self.log_level = os.environ.get("DOCLING_LOG_LEVEL")
            
        if os.environ.get("DOCLING_CONFIG_FILE"):
            self.config_file = os.environ.get("DOCLING_CONFIG_FILE")
            
        if os.environ.get("DOCLING_OUTPUT_FORMAT"):
            self.output_format = os.environ.get("DOCLING_OUTPUT_FORMAT").lower()
            
        if os.environ.get("DOCLING_IMAGE_BASE_URL"):
            self.image_base_url = os.environ.get("DOCLING_IMAGE_BASE_URL")
            
        if os.environ.get("DOCLING_INCLUDE_METADATA"):
            self.include_metadata = os.environ.get("DOCLING_INCLUDE_METADATA").lower() in ("true", "yes", "1")
            
        if os.environ.get("DOCLING_INCLUDE_PAGE_BREAKS"):
            self.include_page_breaks = os.environ.get("DOCLING_INCLUDE_PAGE_BREAKS").lower() in ("true", "yes", "1")
            
        if os.environ.get("DOCLING_INCLUDE_CAPTIONS"):
            self.include_captions = os.environ.get("DOCLING_INCLUDE_CAPTIONS").lower() in ("true", "yes", "1")
    
    def update_from_args(self, args):
        """
        Update configuration from command-line arguments.
        Only updates values that were explicitly provided.
        """
        if args.pdf_path is not None:
            self.pdf_path = args.pdf_path
            
        if args.output_dir is not None:
            self.output_dir = args.output_dir
            
        if args.log_level is not None:
            self.log_level = args.log_level
            
        if args.config_file is not None:
            self.config_file = args.config_file
            
        if args.output_format is not None:
            self.output_format = args.output_format.lower()
            
        if args.image_base_url is not None:
            self.image_base_url = args.image_base_url
            
        if args.include_metadata is not None:
            self.include_metadata = args.include_metadata
            
        if args.include_page_breaks is not None:
            self.include_page_breaks = args.include_page_breaks
            
        if args.include_captions is not None:
            self.include_captions = args.include_captions
    
    def validate(self):
        """
        Validate the configuration settings.
        Returns a list of error messages, empty if all is valid.
        """
        errors = []
        
        # Required: PDF path must be provided and exist
        if not self.pdf_path:
            errors.append("PDF file path is required but not provided.")
        elif not Path(self.pdf_path).exists():
            errors.append(f"PDF file not found: {self.pdf_path}")
        
        # Output directory doesn't need to exist, we can create it
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")
        
        # If config file is provided, it must exist
        if self.config_file and not Path(self.config_file).exists():
            errors.append(f"Config file not found: {self.config_file}")
            
        # Validate output format
        valid_formats = ["json", "md", "html", "csv"]
        if self.output_format.lower() not in valid_formats:
            errors.append(f"Invalid output format: {self.output_format}. Must be one of {valid_formats}")
        
        return errors

    def get_formatter_config(self):
        """
        Get configuration for the OutputFormatter.
        
        Returns:
            dict: Configuration settings for OutputFormatter
        """
        return {
            'include_metadata': self.include_metadata,
            'include_images': True,  # Always include images in the output
            'image_base_url': self.image_base_url,
            'include_page_breaks': self.include_page_breaks,
            'include_captions': self.include_captions
        }


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Parse PDF documents using the docling library."
    )
    
    parser.add_argument(
        "--pdf_path", "-p",
        help="Path to the input PDF file"
    )
    
    parser.add_argument(
        "--output_dir", "-o",
        help="Directory for output files (default: 'output')"
    )
    
    parser.add_argument(
        "--log_level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity level (default: INFO)"
    )
    
    parser.add_argument(
        "--config_file", "-c",
        help="Path to additional configuration file"
    )
    
    parser.add_argument(
        "--output_format", "-f",
        choices=["json", "md", "html", "csv"],
        help="Output format (default: json)"
    )
    
    parser.add_argument(
        "--image_base_url", "-i",
        help="Base URL for image links in output"
    )
    
    parser.add_argument(
        "--include_metadata",
        action="store_true",
        help="Include metadata in output (default: True)"
    )
    
    parser.add_argument(
        "--no_metadata",
        action="store_false",
        dest="include_metadata",
        help="Exclude metadata from output"
    )
    
    parser.add_argument(
        "--include_page_breaks",
        action="store_true",
        help="Include page break markers in output (default: True)"
    )
    
    parser.add_argument(
        "--no_page_breaks",
        action="store_false",
        dest="include_page_breaks",
        help="Exclude page break markers from output"
    )
    
    parser.add_argument(
        "--include_captions",
        action="store_true",
        help="Include captions for tables and images (default: True)"
    )
    
    parser.add_argument(
        "--no_captions",
        action="store_false",
        dest="include_captions",
        help="Exclude captions from tables and images"
    )
    
    # Set default values to None to distinguish between
    # not provided and explicitly set to False
    parser.set_defaults(
        include_metadata=None,
        include_page_breaks=None,
        include_captions=None
    )
    
    return parser.parse_args()


def main():
    """
    Main function - entry point for the application
    
    Processes a PDF document using the docling library and saves the 
    extracted document structure as a JSON file.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # Parse command line arguments
        args = parse_arguments()
        
        # Create a configuration object
        config = Configuration()
        config.update_from_args(args)
        
        # Validate configuration
        errors = config.validate()
        if errors:
            for error in errors:
                logging.error(error)
            return 1
        
        # Set up logging
        global logger
        logger = setup_logging(config.log_level)
        
        logger.info(f"Starting PDF document processing")
        logger.info(f"PDF path: {config.pdf_path}")
        logger.info(f"Output directory: {config.output_dir}")
        logger.info(f"Output format: {config.output_format}")
        
        # Create output directory if it doesn't exist
        output_dir_path = Path(config.output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Process the PDF document
        docling_document = process_pdf_document(config.pdf_path, config.output_dir, config.config_file)
        
        # Save the output as JSON (standard format)
        output_file = save_output(docling_document, config.output_dir)
        
        # Load the JSON output for formatting
        with open(output_file, 'r', encoding='utf-8') as f:
            document_data = json.load(f)
        
        # Create a formatter with the specified configuration
        formatter = OutputFormatter(config.get_formatter_config())
        
        # Save the formatted output
        formatted_output_file = formatter.save_formatted_output(
            document_data,
            config.output_dir,
            config.output_format
        )
        
        logger.info(f"Document processing completed successfully")
        logger.info(f"Standard output saved to: {output_file}")
        logger.info(f"Formatted output saved to: {formatted_output_file}")
        
        return 0
    except Exception as e:
        logger.error(f"An error occurred during document processing: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
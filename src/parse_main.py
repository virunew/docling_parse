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
"""
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

# Import docling library components
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
except ImportError as e:
    logging.error(f"Error importing docling library: {e}")
    logging.error("Please install the docling library.")
    sys.exit(1)

# Import the element map builder
try:
    from element_map_builder import build_element_map
    # Import the new content extractor module
    from content_extractor import (
        extract_text_content, 
        extract_table_content, 
        extract_image_content, 
        is_furniture, 
        find_sibling_text_in_sequence, 
        get_captions
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
        
        return errors


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
        
        # Create output directory if it doesn't exist
        output_dir_path = Path(config.output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Process the PDF document
        docling_document = process_pdf_document(config.pdf_path, config.output_dir, config.config_file)
        
        # Save the output as JSON
        output_file = save_output(docling_document, config.output_dir)
        
        logger.info(f"Document processing completed successfully")
        logger.info(f"Output saved to: {output_file}")
        
        return 0
    except Exception as e:
        logger.error(f"An error occurred during document processing: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
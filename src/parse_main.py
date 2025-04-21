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
from dotenv import load_dotenv
load_dotenv()
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union



 

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
except ImportError as e:
    logging.error(f"Error importing element_map_builder: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("docling_parser")


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


def setup_logging(log_level):
    """Set up logging with the specified verbosity level."""
    # Convert string log level to numeric value
    numeric_level = getattr(logging, log_level.upper(), None)
    
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure root logger
    logging.getLogger().setLevel(numeric_level)
    
    # Configure our module logger
    logger.setLevel(numeric_level)
    
    # Add file handler if we want to log to file as well
    log_file = Path("logs") / "docling_parser.log"
    log_file.parent.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    logger.addHandler(file_handler)
    
    logger.debug(f"Logging configured at level {log_level}")


def process_pdf_document(pdf_path, output_dir, config_file=None):
    """
    Process a PDF document and extract its content.
    
    Args:
        pdf_path: Path to the PDF document
        output_dir: Directory to save output files
        config_file: Path to the configuration file (optional)
    
    Returns:
        DoclingDocument: The converted document object
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing PDF document: {pdf_path}")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Set up pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0  # Adjust image resolution if needed
        pipeline_options.generate_page_images = True  # Generate images for pages
        pipeline_options.generate_picture_images = True  # Generate images for pictures
        pipeline_options.allow_external_plugins = True
        pipeline_options.do_picture_description = True
        pipeline_options.do_table_structure = True
        pipeline_options.generate_picture_images = True
        
        # Enable external plugins if a config file is provided
        if config_file and Path(config_file).exists():
            pipeline_options.allow_external_plugins = True
            logger.info(f"Using configuration file: {config_file}")
            # Load environment variables for docling configuration
            os.environ["DOCLING_CONFIG_FILE"] = str(Path(config_file).absolute())
        
        # Create a DocumentConverter instance
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Convert the PDF document
        logger.debug(f"Starting document conversion")
        conversion_result = doc_converter.convert(Path(pdf_path))
        
        if conversion_result.status != "success":
            logger.error(f"Document conversion failed: {conversion_result.status}")
            raise Exception(f"Document conversion failed: {conversion_result.status}")
            
        docling_document = conversion_result.document
        logger.info(f"Document successfully converted: {len(docling_document.pages)} pages found")
        
        # Return the DoclingDocument directly
        return docling_document
        
    except Exception as e:
        logger.exception(f"Error processing PDF document: {e}")
        raise


def save_output(docling_document, output_dir):
    """
    Save the DoclingDocument directly to the output directory as JSON.
    
    This function serializes a DoclingDocument object to a standardized JSON format
    using the object's built-in export_to_dict method. The resulting JSON follows
    the schema defined in the DoclingDocument specification, ensuring compatibility
    with other tools that consume this format.
    
    The output JSON file contains the complete document structure including:
    - Document metadata (name, version, schema)
    - Text elements with their content and attributes
    - Page information and structure
    - Body and furniture hierarchies
    - References between elements
    
    Args:
        docling_document: The DoclingDocument object to serialize
        output_dir: Directory to save the output JSON file (will be created if it doesn't exist)
        
    Returns:
        Path to the created JSON file
        
    Raises:
        TypeError: If docling_document lacks the export_to_dict method
        IOError: If the file cannot be written to the specified location
        Exception: For any other serialization errors
    """
    try:
        # Validate input
        if not hasattr(docling_document, 'export_to_dict') or not callable(getattr(docling_document, 'export_to_dict')):
            raise TypeError("Object does not have an export_to_dict method. Not a valid DoclingDocument.")
            
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Define output file path
        output_file = output_path / docling_document.name + ".json"
        
        logger.info(f"Saving DoclingDocument to {output_file}")
        
        # Export the docling document to dict and save as JSON
        try:
            doc_dict = docling_document.export_to_dict()
            with open(output_file, "w") as f:
                json.dump(doc_dict, f, indent=2)
            
            logger.info(f"DoclingDocument saved successfully to {output_file}")
            return output_file
            
        except AttributeError as e:
            logger.error(f"Failed to export DoclingDocument: {e}")
            raise TypeError(f"DoclingDocument export_to_dict method failed: {e}")
            
        except (json.JSONDecodeError, json.JSONEncoder) as e:
            logger.error(f"JSON serialization error: {e}")
            raise Exception(f"Failed to serialize DoclingDocument to JSON: {e}")
            
    except IOError as e:
        logger.error(f"Failed to write output file: {e}")
        raise IOError(f"Could not write to {output_dir}: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in save_output: {e}")
        raise


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
        setup_logging(config.log_level)
        
        logging.info(f"Starting PDF document processing")
        logging.info(f"PDF path: {config.pdf_path}")
        logging.info(f"Output directory: {config.output_dir}")
        
        # Create output directory if it doesn't exist
        output_dir_path = Path(config.output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Process the PDF document
        docling_document = process_pdf_document(config.pdf_path, config.output_dir, config.config_file)
        
        # Save the output as JSON
        output_file = save_output(docling_document, config.output_dir)
        
        logging.info(f"Document processing completed successfully")
        logging.info(f"Output saved to: {output_file}")
        
        return 0
    except Exception as e:
        logging.error(f"An error occurred during document processing: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
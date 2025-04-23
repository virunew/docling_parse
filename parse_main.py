"""
Docling Parse Main Module

This module serves as the entry point for the document parsing application.
It handles configuration, argument parsing, logging setup,
and the main execution flow for processing PDF documents.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import docling

from src.parse_helper import save_output, process_pdf_document
from src.sql_formatter import SQLFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Configuration:
    """
    Configuration for the document parsing application.

    Manages configuration settings such as input paths, output directories,
    and various processing options.
    """

    def __init__(self):
        """Initialize with default configuration values."""
        self.pdf_path = None
        self.output_dir = "output"
        self.log_level = "INFO"
        self.description_token_limit = 1024
        self.extract_images = True
        self.enhance_process_images = True
        self.process_images_in_parallel = True
        self.image_min_size = 100
        self.image_scale_factor = 2.0
        self.image_format = "PNG"
        self.image_quality = 95
        self.format = "json"  # Default format is 'json', can also be 'sql'

    def load_from_env(self) -> None:
        """
        Load configuration values from environment variables.

        Environment variables take precedence over default values
        but can be overridden by command-line arguments.
        """
        # Map environment variables to configuration attributes
        env_vars = {
            "PDF_PATH": "pdf_path",
            "OUTPUT_DIR": "output_dir",
            "LOG_LEVEL": "log_level",
            "DESCRIPTION_TOKEN_LIMIT": "description_token_limit",
            "EXTRACT_IMAGES": "extract_images",
            "ENHANCE_PROCESS_IMAGES": "enhance_process_images",
            "PROCESS_IMAGES_IN_PARALLEL": "process_images_in_parallel",
            "IMAGE_MIN_SIZE": "image_min_size",
            "IMAGE_SCALE_FACTOR": "image_scale_factor",
            "IMAGE_FORMAT": "image_format",
            "IMAGE_QUALITY": "image_quality",
            "FORMAT": "format"
        }

        # Set configuration from environment variables
        for env_var, attr in env_vars.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert string boolean values to actual booleans
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                # Convert numeric values
                elif attr in (
                    "description_token_limit",
                    "image_min_size",
                    "image_quality",
                ):
                    value = int(value)
                elif attr == "image_scale_factor":
                    value = float(value)

                setattr(self, attr, value)

    def update_from_args(self, args) -> None:
        """
        Update configuration values from command-line arguments.

        Args:
            args: Parsed command-line arguments
        """
        # Update each attribute if provided in args
        for attr in vars(self):
            value = getattr(args, attr, None)
            if value is not None:
                setattr(self, attr, value)

    def validate(self) -> bool:
        """
        Validate the configuration settings.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Check if PDF path is provided and exists
        if not self.pdf_path:
            logger.error("PDF path is required")
            return False

        pdf_path = Path(self.pdf_path)
        if not pdf_path.exists():
            logger.error(f"PDF file does not exist: {pdf_path}")
            return False

        # Check if output directory is valid
        output_dir = Path(self.output_dir)
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True)
                logger.info(f"Created output directory: {output_dir}")
            except Exception as e:
                logger.error(f"Failed to create output directory: {e}")
                return False

        # Validate image extraction settings
        if self.extract_images:
            if self.image_min_size < 0:
                logger.error("Image minimum size cannot be negative")
                return False
            if self.image_scale_factor <= 0:
                logger.error("Image scale factor must be positive")
                return False
            if self.image_quality < 1 or self.image_quality > 100:
                logger.error("Image quality must be between 1 and 100")
                return False

        # Validate format
        if self.format not in ["json", "sql"]:
            logger.error("Format must be either 'json' or 'sql'")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary of configuration values
        """
        return {attr: getattr(self, attr) for attr in vars(self)}

    def __str__(self) -> str:
        """
        Return a string representation of the configuration.

        Returns:
            str: String representation
        """
        return str(self.to_dict())

    def get_image_extraction_config(self) -> Dict[str, Any]:
        """
        Get configuration values for image extraction.

        Returns:
            Dict[str, Any]: Dictionary of image extraction configuration
        """
        return {
            "extract_images": self.extract_images,
            "enhance_process_images": self.enhance_process_images,
            "process_images_in_parallel": self.process_images_in_parallel,
            "image_min_size": self.image_min_size,
            "image_scale_factor": self.image_scale_factor,
            "image_format": self.image_format,
            "image_quality": self.image_quality,
        }


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Process PDF documents and convert to JSON with enhanced metadata extraction"
    )

    # Required arguments
    parser.add_argument(
        "--pdf_path", 
        type=str, 
        help="Path to the PDF file to process (required)"
    )

    # Output configuration
    parser.add_argument(
        "--output_dir", 
        type=str, 
        help="Directory to save output files (default: 'output')"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "sql"],
        help="Output format: 'json' or 'sql' (default: 'json')"
    )

    # Logging configuration
    parser.add_argument(
        "--log_level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)",
    )

    # Description configuration
    parser.add_argument(
        "--description_token_limit",
        type=int,
        help="Token limit for AI descriptions (default: 1024)",
    )

    # Image extraction configuration
    parser.add_argument(
        "--extract_images",
        type=bool,
        help="Whether to extract images from the PDF (default: True)",
    )
    parser.add_argument(
        "--enhance_process_images",
        type=bool,
        help="Use enhanced image processing with AI descriptions (default: True)",
    )
    parser.add_argument(
        "--process_images_in_parallel",
        type=bool,
        help="Process images in parallel (default: True)",
    )
    parser.add_argument(
        "--image_min_size",
        type=int,
        help="Minimum size of images to extract in pixels (default: 100)",
    )
    parser.add_argument(
        "--image_scale_factor",
        type=float,
        help="Scale factor for image extraction (default: 2.0)",
    )
    parser.add_argument(
        "--image_format",
        type=str,
        choices=["PNG", "JPEG", "WEBP"],
        help="Format for extracted images (default: PNG)",
    )
    parser.add_argument(
        "--image_quality",
        type=int,
        help="Quality for JPEG/WEBP images (1-100, default: 95)",
    )

    return parser.parse_args()


def main():
    """
    Main function to process PDF documents.

    This function serves as the entry point for the application,
    handling configuration, document processing, and output generation.
    """
    # Initialize and validate configuration
    config = Configuration()
    config.load_from_env()
    args = parse_arguments()
    config.update_from_args(args)

    if not config.validate():
        logger.critical("Invalid configuration. Exiting.")
        sys.exit(1)

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, config.log_level))

    logger.info(f"Starting document processing with configuration: {config}")

    try:
        # Process the document
        document = process_pdf_document(
            config.pdf_path,
            config.output_dir,
            image_extraction_config=config.get_image_extraction_config(),
        )

        # Save the output based on the configured format
        if config.format == "sql":
            # Use SQL formatter for database-compatible output
            sql_formatter = SQLFormatter()
            output_file = sql_formatter.save_formatted_output(
                document,
                config.output_dir
            )
            logger.info(f"SQL output saved to {output_file}")
        else:
            # Use standard JSON output
            output_file = save_output(document, config.output_dir)
            logger.info(f"JSON output saved to {output_file}")

        logger.info("Document processing completed successfully")

    except Exception as e:
        logger.critical(f"Error processing document: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 
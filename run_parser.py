#!/usr/bin/env python3
"""
Run Parser Script

A simple script to run the PDF parser with the fixes for:
1. Storing images as external files instead of embedding them in JSON
2. Properly identifying all element types in the document
3. Generating proper breadcrumbs and filtering furniture from context

Usage:
    python run_parser.py <pdf_file> <output_dir> [--format <format>]

Example:
    python run_parser.py sample.pdf output --format json
"""

import sys
import os
from pathlib import Path
import argparse

# Ensure we can import from the correct paths
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import the main module
import parse_main

def main():
    """Main function to parse arguments and run the parser"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run the PDF parser with fixes for image storage, element identification, and breadcrumb generation."
    )
    
    parser.add_argument(
        "pdf_path",
        help="Path to the input PDF file"
    )
    
    parser.add_argument(
        "output_dir",
        help="Directory for output files"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "md", "html", "csv"],
        default="json",
        help="Output format (default: json)"
    )
    
    parser.add_argument(
        "--log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging verbosity level (default: INFO)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Build sys.argv for parse_main.py
    sys.argv = [
        "parse_main.py",
        "--pdf_path", args.pdf_path,
        "--output_dir", args.output_dir,
        "--output_format", args.format,
        "--log_level", args.log_level
    ]
    
    # Run the main function
    return_code = parse_main.main()
    
    # Print summary
    if return_code == 0:
        print(f"\nParsing completed successfully!")
        output_dir = Path(args.output_dir)
        
        # Show which files were generated
        print("\nFiles generated:")
        print(f"  - {output_dir / 'docling_document.json'} (Original output)")
        print(f"  - {output_dir / 'fixed_document.json'} (Fixed metadata)")
        
        output_file = None
        if args.format == "json":
            output_file = output_dir / "document.json"
        elif args.format == "md":
            output_file = output_dir / f"{Path(args.pdf_path).stem}.md"
        elif args.format == "html":
            output_file = output_dir / f"{Path(args.pdf_path).stem}.html"
        elif args.format == "csv":
            output_file = output_dir / f"{Path(args.pdf_path).stem}.csv"
        
        if output_file and output_file.exists():
            print(f"  - {output_file} (Formatted output)")
        
        # Check for images directory
        images_dir = output_dir / "images"
        if images_dir.exists():
            image_count = len(list(images_dir.glob("*.*")))
            print(f"  - {images_dir} (Image directory with {image_count} extracted images)")
    else:
        print("\nParsing failed. Check the logs for details.")
    
    return return_code

if __name__ == "__main__":
    sys.exit(main()) 
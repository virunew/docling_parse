#!/usr/bin/env python3
"""
Test all common docling imports to verify that imports work with PYTHONPATH from .env
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables first, including PYTHONPATH
load_dotenv()

print(f"Current directory: {os.getcwd()}")
print(f"PYTHONPATH environment variable: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"sys.path: {sys.path}")

print("\nTesting docling imports...")

try:
    # Import common classes from docling.datamodel
    from docling.datamodel.base_models import InputFormat
    print("✅ Successfully imported InputFormat")
    
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    print("✅ Successfully imported PdfPipelineOptions")
    
    from docling.datamodel.document import ConversionResult
    print("✅ Successfully imported ConversionResult")
    
    # Import document converter
    from docling.document_converter import DocumentConverter, PdfFormatOption
    print("✅ Successfully imported DocumentConverter and PdfFormatOption")
    
    # Test creating a pipeline options object
    options = PdfPipelineOptions()
    options.generate_page_images = True
    print("✅ Successfully created PdfPipelineOptions object")
    
    # All imports worked!
    print("\nAll docling imports successful! The PYTHONPATH environment variable is configured correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nThe docling imports failed. Please check your .env file and PYTHONPATH configuration.") 
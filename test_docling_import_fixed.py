#!/usr/bin/env python3
"""
Test script to diagnose docling import issues with the fix applied
"""
import sys
import os

# Import our fix module first
import docling_import_fix

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")
print(f"Current working directory: {os.getcwd()}")

try:
    from docling.datamodel.base_models import InputFormat
    print("Successfully imported InputFormat from docling.datamodel.base_models")
    
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    print("Successfully imported PdfPipelineOptions from docling.datamodel.pipeline_options")
    
    from docling.document_converter import DocumentConverter
    print("Successfully imported DocumentConverter from docling.document_converter")
    
    print("All imports successful!")
    
except ImportError as e:
    print(f"Error importing docling: {e}")
    
    # Try to see if the package exists but in a different location
    try:
        import importlib.util
        spec = importlib.util.find_spec("docling.datamodel")
        if spec:
            print(f"Found docling.datamodel spec at: {spec.origin}")
        else:
            print("Could not find docling.datamodel specification in sys.path")
    except Exception as e2:
        print(f"Error checking docling spec: {e2}") 
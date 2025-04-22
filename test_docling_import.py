#!/usr/bin/env python3
"""
Test script to diagnose docling import issues
"""
import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")
print(f"Current working directory: {os.getcwd()}")

try:
    import docling
    print(f"docling package found at: {docling.__file__}")
    print(f"docling version: {getattr(docling, '__version__', 'Unknown')}")
    
    from docling.datamodel.base_models import InputFormat
    print("Successfully imported InputFormat from docling.datamodel.base_models")
    
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    print("Successfully imported PdfPipelineOptions from docling.datamodel.pipeline_options")
    
    from docling.document_converter import DocumentConverter
    print("Successfully imported DocumentConverter from docling.document_converter")
    
except ImportError as e:
    print(f"Error importing docling: {e}")
    
    # Try to see if the package exists but in a different location
    try:
        import importlib.util
        spec = importlib.util.find_spec("docling")
        if spec:
            print(f"Found docling spec at: {spec.origin}")
        else:
            print("Could not find docling specification in sys.path")
    except Exception as e2:
        print(f"Error checking docling spec: {e2}") 
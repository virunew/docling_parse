#!/usr/bin/env python
"""
Command-line interface for PDF image extraction and saving.

This module provides a command-line interface for extracting and saving images 
from PDF documents, with support for batch processing multiple documents.
"""

# Fix docling imports
import docling_fix

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from docling.document_converter import DocumentConverter
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pdf_image_pipeline import PDFImagePipeline

# Configure logging
logger = logging.getLogger(__name__) 
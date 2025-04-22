"""
Docling Import Fix Module

This module allows importing from the local docling package by setting up the proper import paths.

Usage:
    import docling_import_fix
    from docling.datamodel.base_models import InputFormat
"""

import sys
import os
from pathlib import Path

# Get the path to the local docling package
docling_dir = Path(__file__).parent / "docling"
docling_package_dir = docling_dir / "docling"

# Add the docling/docling directory to sys.path if it's not already there
if str(docling_package_dir) not in sys.path:
    sys.path.insert(0, str(docling_package_dir))

# Log what we're doing
print(f"Added {docling_package_dir} to Python path to fix docling imports") 
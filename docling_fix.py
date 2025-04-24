"""
Docling Import Fix Module

This module allows importing from the local docling package by setting up the proper import paths.

Usage:
    import docling_fix
    from docling.datamodel.base_models import InputFormat
"""

import sys
import os
from pathlib import Path
import logging

def fix_docling_imports():
    """
    Add the necessary paths to sys.path to fix docling imports.
    
    Returns:
        bool: True if paths were adjusted, False if they were already correct
    """
    # Get the current directory and paths
    current_dir = Path(os.getcwd())
    docling_dir = current_dir / "docling"  
    docling_package_dir = docling_dir

    # Debug
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', '')}")
    print(f"Current directory: {current_dir}")
    print(f"Docling directory: {docling_dir}")
    
    # Clear previous docling paths to avoid confusion
    sys.path = [p for p in sys.path if 'docling_parse/docling' not in p]
    
    # Add the project root to find any local modules
    sys.path.insert(0, str(current_dir))
    
    # Add the docling directory (parent of the docling package)
    sys.path.insert(0, str(docling_dir))

    # Ensure there are no duplicate paths
    sys.path = list(dict.fromkeys(sys.path))
    
    print(f"Updated sys.path: {sys.path}")
    
    # Create an empty __init__.py file in any missing package directories
    ensure_init_file(docling_dir)
    ensure_init_file(docling_dir / "docling")
    ensure_init_file(docling_dir / "docling" / "datamodel")
    
    return True

def ensure_init_file(directory):
    """Create __init__.py file if it doesn't exist"""
    if not directory.exists():
        print(f"Warning: Directory does not exist: {directory}")
        return
        
    init_file = directory / "__init__.py"
    if not init_file.exists():
        print(f"Creating missing __init__.py in {directory}")
        init_file.touch()

# Automatically fix imports when this module is imported
fixed = fix_docling_imports()
 
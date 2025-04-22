"""
Docling Import Fix Helper

This module fixes the docling imports by adding the correct paths to sys.path.
Import this at the top of any file that needs to import from docling.
"""

import sys
import os
from pathlib import Path

def fix_docling_imports():
    """
    Add the necessary paths to sys.path to fix docling imports.
    
    Returns:
        bool: True if paths were adjusted, False if they were already correct
    """
    # Get the current directory and paths
    current_dir = Path(os.getcwd())
    docling_dir = current_dir / "docling"  
    docling_package_dir = docling_dir / "docling"
    
    # Debug
    print(f"Current directory: {current_dir}")
    print(f"Docling directory: {docling_dir}")
    print(f"Docling package directory: {docling_package_dir}")
    print(f"sys.path before: {sys.path}")
    
    # Add both paths - but don't remove existing paths to avoid breaking anything
    paths_added = False
    
    # Add the parent directory first so 'import docling' works
    if str(docling_dir.parent) not in sys.path:
        sys.path.insert(0, str(docling_dir.parent))
        paths_added = True
        
    # Add the docling directory so 'from docling.X import Y' works
    if str(docling_dir) not in sys.path:
        sys.path.insert(0, str(docling_dir))
        paths_added = True
        
    # Add the docling/docling directory so imports inside the package work
    if docling_package_dir.exists() and str(docling_package_dir) not in sys.path:
        sys.path.insert(0, str(docling_package_dir))
        paths_added = True
    
    print(f"sys.path after: {sys.path}")
    return paths_added

# Automatically fix imports when this module is imported
fixed = fix_docling_imports() 
"""
Docling Import Helper

This module verifies that docling imports are working correctly.
It relies on the PYTHONPATH being set correctly in the .env file,
which should include the docling directory and the src directory.

Environment variables from .env should already be loaded by the main program.
"""

import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

def check_docling_environment():
    """
    Verify that the docling environment is properly configured.
    
    Returns:
        bool: True if the environment appears properly configured
    """
    # Check if PYTHONPATH includes docling
    pythonpath = os.environ.get('PYTHONPATH', '')
    logger.debug(f"Current PYTHONPATH: {pythonpath}")
    
    if 'docling' not in pythonpath:
        logger.warning("PYTHONPATH does not contain 'docling'. Import errors may occur.")
        return False
    
    # Check PROJECT_HOME is set
    project_home = os.environ.get('PROJECT_HOME', '')
    if not project_home:
        logger.warning("PROJECT_HOME not set in environment. Path resolution may fail.")
        return False
    
    return True

# Automatically check environment when this module is imported
environment_ok = check_docling_environment() 
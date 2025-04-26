#!/usr/bin/env python
"""
Creates a test PDF document with duplicated images for deduplication testing.

This script uses reportlab to create a PDF with two images:
- A red square image that appears twice in the document
- A blue square image that appears once

This allows testing that image deduplication works correctly.
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image
import io
import tempfile

def create_red_image():
    """Create a red square image and save to a temporary file."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img = Image.new('RGB', (100, 100), color='red')
        img.save(tmp, format='PNG')
        return tmp.name

def create_blue_image():
    """Create a blue square image and save to a temporary file."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(tmp, format='PNG')
        return tmp.name

def create_test_pdf(output_path):
    """
    Create a test PDF document with duplicate images.
    
    Args:
        output_path: Path where the PDF should be saved
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create temporary image files
    red_img_path = create_red_image()
    blue_img_path = create_blue_image()
    
    try:
        # Create a canvas
        c = canvas.Canvas(output_path)
        c.setFont("Helvetica", 12)
        
        # Add title
        c.drawString(1*inch, 10*inch, "Test PDF for Image Deduplication")
        c.drawString(1*inch, 9.5*inch, "This PDF contains duplicate images to test deduplication functionality.")
        
        # First instance of the red image
        c.drawString(1*inch, 9*inch, "Red Image (First Instance):")
        c.drawImage(red_img_path, 1*inch, 7.5*inch, width=1.5*inch, height=1.5*inch)
        
        # Second instance of the red image (same image, should be deduplicated)
        c.drawString(1*inch, 7*inch, "Red Image (Second Instance - Duplicate):")
        c.drawImage(red_img_path, 1*inch, 5.5*inch, width=1.5*inch, height=1.5*inch)
        
        # Blue image (different image)
        c.drawString(1*inch, 5*inch, "Blue Image:")
        c.drawImage(blue_img_path, 1*inch, 3.5*inch, width=1.5*inch, height=1.5*inch)
        
        # Add explanation
        c.drawString(1*inch, 3*inch, "The red image appears twice in this document but should only be saved once.")
        c.drawString(1*inch, 2.75*inch, "The HTML output should still show both instances of the red image.")
        c.drawString(1*inch, 2.5*inch, "The blue image appears only once.")
        
        # Save the PDF
        c.save()
        return output_path
    finally:
        # Clean up temporary files
        for path in [red_img_path, blue_img_path]:
            try:
                os.unlink(path)
            except:
                pass

if __name__ == "__main__":
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Default output path
    output_path = os.path.join(script_dir, "samples", "test.pdf")
    
    # Create samples directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create the test PDF
    created_path = create_test_pdf(output_path)
    print(f"Created test PDF at: {created_path}") 
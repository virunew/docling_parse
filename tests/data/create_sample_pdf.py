#!/usr/bin/env python3
"""
Create Sample PDF

This script creates a simple PDF document with text and an image for testing.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import blue, red, green, black
from PIL import Image
import io
import tempfile


def create_sample_image(filename, size=(300, 200), color=(255, 0, 0)):
    """
    Create a simple image for testing.
    
    Args:
        filename: The filename to save the image to
        size: The size of the image (width, height)
        color: The RGB color of the image
        
    Returns:
        The path to the saved image
    """
    img = Image.new('RGB', size, color=color)
    img.save(filename)
    return filename


def create_sample_pdf(output_path):
    """
    Create a sample PDF with text and an image.
    
    Args:
        output_path: Path where to save the PDF
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Add a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Sample PDF Document")
    
    # Add some text
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 2 * inch, "This is a sample PDF document created for testing.")
    c.drawString(1 * inch, height - 2.5 * inch, "It includes both text and an image.")
    
    # Add a heading for the image
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 3.5 * inch, "Sample Image")
    
    # Create temporary image files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and add the first image
        img_path1 = os.path.join(tmpdir, "sample_image1.png")
        create_sample_image(img_path1, color=(255, 0, 0))
        c.drawImage(img_path1, 1 * inch, height - 6.5 * inch, width=3 * inch, height=2 * inch)
        
        # Add a caption for the image
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(1 * inch, height - 7 * inch, "Figure 1: A sample image for testing image extraction.")
        
        # Add some more text
        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, height - 8 * inch, "This text appears after the image.")
        
        # Start a new page
        c.showPage()
        
        # Add content to the second page
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 1 * inch, "Second Page")
        
        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, height - 2 * inch, "This is the second page of our sample document.")
        
        # Create and add the second image
        img_path2 = os.path.join(tmpdir, "sample_image2.png")
        create_sample_image(img_path2, color=(0, 0, 255))
        c.drawImage(img_path2, 1 * inch, height - 5 * inch, width=3 * inch, height=2 * inch)
        
        # Add a caption for the second image
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(1 * inch, height - 5.5 * inch, "Figure 2: Another sample image with a different color.")
        
        # Save the PDF
        c.save()
    
    print(f"Sample PDF created at {output_path}")


if __name__ == "__main__":
    # Create the sample PDF in the data directory
    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "sample.pdf"
    
    create_sample_pdf(str(output_path)) 
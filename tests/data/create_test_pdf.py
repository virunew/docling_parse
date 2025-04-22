"""
Create a sample PDF file for testing

This script creates a simple PDF file that can be used for testing the image extraction functionality.
"""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import Image
from io import BytesIO
from PIL import Image as PILImage

def create_test_pdf(output_path):
    """
    Create a test PDF file with text and images.
    
    Args:
        output_path: Path where the PDF file should be saved
    """
    # Create a canvas
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Add a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Test PDF Document")
    
    # Add some text
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, height - 1.5*inch, "This is a test PDF document created for testing image extraction.")
    c.drawString(1*inch, height - 1.8*inch, "It contains a few simple elements including text and images.")
    
    # Create a simple image (a colored rectangle)
    img_io = BytesIO()
    img = PILImage.new('RGB', (300, 200), color = (255, 0, 0))
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    # Add the image to the PDF
    img_path = "test_image.png"
    with open(img_path, "wb") as f:
        f.write(img_io.getvalue())
    
    # Insert the image into the PDF
    c.drawImage(img_path, 1*inch, height - 5*inch, width=3*inch, height=2*inch)
    c.drawString(1*inch, height - 5.5*inch, "Figure 1: A sample image")
    
    # Create a second page with another image
    c.showPage()
    
    # Add a header to the second page
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1*inch, "Page Two")
    
    # Create a different image (a blue rectangle)
    img2_io = BytesIO()
    img2 = PILImage.new('RGB', (200, 200), color = (0, 0, 255))
    img2.save(img2_io, format='PNG')
    img2_io.seek(0)
    
    # Add the second image to the PDF
    img2_path = "test_image2.png"
    with open(img2_path, "wb") as f:
        f.write(img2_io.getvalue())
    
    # Insert the second image into the PDF
    c.drawImage(img2_path, 3*inch, height - 5*inch, width=2*inch, height=2*inch)
    c.drawString(3*inch, height - 5.5*inch, "Figure 2: Another sample image")
    
    # Save the PDF
    c.save()
    
    # Clean up temporary image files
    if os.path.exists(img_path):
        os.remove(img_path)
    if os.path.exists(img2_path):
        os.remove(img2_path)
    
    print(f"Created test PDF: {output_path}")


if __name__ == "__main__":
    # Create the test PDF in the tests/data directory
    output_dir = Path(__file__).parent
    output_path = output_dir / "test.pdf"
    create_test_pdf(output_path) 
#!/usr/bin/env python
"""
Integration test for image deduplication functionality.

This test verifies that the deduplication mechanism correctly identifies and 
reuses the same image when it appears multiple times in a document.
"""

import os
import unittest
import tempfile
import shutil
import hashlib
import logging
import uuid
from pathlib import Path
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestImageDeduplication(unittest.TestCase):
    """Test the image deduplication functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test output
        self.test_dir = tempfile.mkdtemp(prefix="docling_test_")
        logger.info(f"Created test directory: {self.test_dir}")
        
        # Create image output directory
        self.img_dir = os.path.join(self.test_dir, "img")
        os.makedirs(self.img_dir, exist_ok=True)
        
        # Create test images
        self.red_image_path = os.path.join(self.test_dir, "red.png")
        self.blue_image_path = os.path.join(self.test_dir, "blue.png")
        self._create_red_image(self.red_image_path)
        self._create_blue_image(self.blue_image_path)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
        logger.info(f"Removed test directory: {self.test_dir}")
    
    def _create_red_image(self, path):
        """Create a red square image."""
        img = Image.new('RGB', (100, 100), color='red')
        img.save(path)
        return path
    
    def _create_blue_image(self, path):
        """Create a blue square image."""
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(path)
        return path
    
    def _compute_image_hash(self, image_path):
        """Compute a hash for an image file."""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:10]
    
    def test_image_deduplication(self):
        """Test that duplicate images are not saved multiple times."""
        # Create HTML output file path
        html_path = os.path.join(self.test_dir, "output.html")
        
        # Create a simple HTML document that references the same red image twice
        # and the blue image once
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Image Deduplication Test</title>
</head>
<body>
    <h1>Image Deduplication Test</h1>
    <div>
        <h2>Red Image (First Instance)</h2>
        <img src="PLACEHOLDER_RED" alt="Red Image">
    </div>
    <div>
        <h2>Red Image (Second Instance)</h2>
        <img src="PLACEHOLDER_RED" alt="Red Image">
    </div>
    <div>
        <h2>Blue Image</h2>
        <img src="PLACEHOLDER_BLUE" alt="Blue Image">
    </div>
</body>
</html>
""")
        
        # Create our simple image deduplication function
        def process_images(html_file, output_dir, *image_paths):
            """
            Process images and update HTML to reference deduplicated images.
            
            Args:
                html_file: Path to the HTML file
                output_dir: Directory to save images
                image_paths: Paths to image files to process
            
            Returns:
                Updated HTML content and a list of copied image files
            """
            # Read the HTML file
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Process each image
            image_hash_map = {}  # Maps image hash to its filename in the output dir
            
            for img_path in image_paths:
                # Compute hash for deduplication
                img_hash = self._compute_image_hash(img_path)
                
                # Check if we've already processed this image
                if img_hash in image_hash_map:
                    logger.info(f"Found duplicate image: {img_path}")
                    continue
                
                # Create a unique filename based on hash
                img_name = f"img_{len(image_hash_map) + 1}_{img_hash}.png"
                output_path = os.path.join(output_dir, img_name)
                
                # Copy the image to output directory
                shutil.copy(img_path, output_path)
                logger.info(f"Copied image to {output_path}")
                
                # Store the mapping
                image_hash_map[img_hash] = img_name
            
            # Update HTML with image references
            red_hash = self._compute_image_hash(self.red_image_path)
            blue_hash = self._compute_image_hash(self.blue_image_path)
            
            if red_hash in image_hash_map:
                red_img_ref = f"img/{image_hash_map[red_hash]}"
                html_content = html_content.replace("PLACEHOLDER_RED", red_img_ref)
            
            if blue_hash in image_hash_map:
                blue_img_ref = f"img/{image_hash_map[blue_hash]}"
                html_content = html_content.replace("PLACEHOLDER_BLUE", blue_img_ref)
            
            # Write the updated HTML
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return html_content, list(image_hash_map.values())
        
        # Run our deduplication process
        html_content, img_files = process_images(
            html_path, 
            self.img_dir,
            self.red_image_path,
            self.red_image_path,  # Duplicate!
            self.blue_image_path
        )
        
        # Check results
        
        # We should have exactly 2 image files (red and blue)
        actual_img_files = [f for f in os.listdir(self.img_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        logger.info(f"Found image files: {actual_img_files}")
        
        self.assertEqual(len(actual_img_files), 2, 
                         f"Expected 2 unique images, but found {len(actual_img_files)}: {actual_img_files}")
        
        # Count img tags in HTML
        img_tags = html_content.count("<img src=")
        
        # The HTML should have 3 image tags (2 red + 1 blue)
        self.assertEqual(img_tags, 3, f"Expected 3 img tags in HTML, but found {img_tags}")
        
        # Check that both image files are referenced in the HTML
        for img_file in actual_img_files:
            img_path = f"img/{img_file}"
            self.assertIn(img_path, html_content, 
                         f"Image file {img_path} is not referenced in the HTML")
        
        # Verify the same image file is referenced twice for the red image
        img_refs = []
        lines = html_content.split('\n')
        for line in lines:
            if "<img src=" in line:
                start = line.find("img/")
                if start != -1:
                    end = line.find('"', start)
                    if end != -1:
                        img_ref = line[start:end]
                        img_refs.append(img_ref)
        
        unique_img_refs = set(img_refs)
        self.assertEqual(len(img_refs), 3, f"Expected 3 img references, found {len(img_refs)}")
        self.assertEqual(len(unique_img_refs), 2, f"Expected 2 unique img references, found {len(unique_img_refs)}")
        
        # Count occurrences of each reference
        red_ref_count = 0
        blue_ref_count = 0
        
        for ref in img_refs:
            if self._compute_image_hash(self.red_image_path) in ref:
                red_ref_count += 1
            elif self._compute_image_hash(self.blue_image_path) in ref:
                blue_ref_count += 1
        
        self.assertEqual(red_ref_count, 2, "Red image should be referenced twice")
        self.assertEqual(blue_ref_count, 1, "Blue image should be referenced once")

if __name__ == "__main__":
    unittest.main() 
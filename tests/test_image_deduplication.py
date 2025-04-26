#!/usr/bin/env python3
"""
Test Image Deduplication Functionality

This test module verifies that the base64 to file conversion process
properly deduplicates images to prevent duplicate files in the output directory.
"""

import unittest
import os
import base64
import tempfile
import shutil
import json
import hashlib
from pathlib import Path

# Import the function to test
from src.utils import replace_base64_with_file_references

class TestImageDeduplication(unittest.TestCase):
    """Test case for image deduplication functionality."""
    
    def setUp(self):
        """Set up test environment with temp directory and sample data."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.doc_id = "test_document"
        
        # Sample base64 PNG data (1x1 pixel, different colors)
        self.red_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        self.blue_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPj/HwADBwIAMCbHYQAAAABJRU5ErkJggg=="
        
        # Create sample document data with duplicate images
        self.sample_data = {
            "items": [
                {
                    "id": 1,
                    "base64_data": f"data:image/png;base64,{self.red_pixel_base64}",
                    "mime_type": "image/png"
                },
                {
                    "id": 2,
                    "base64_data": f"data:image/png;base64,{self.blue_pixel_base64}",
                    "mime_type": "image/png"
                },
                {
                    "id": 3,
                    "base64_data": f"data:image/png;base64,{self.red_pixel_base64}",  # Duplicate of id 1
                    "mime_type": "image/png"
                },
                {
                    "id": 4,
                    "base64_data": f"data:image/png;base64,{self.blue_pixel_base64}",  # Duplicate of id 2
                    "mime_type": "image/png"
                },
                {
                    "id": 5,
                    "base64_data": f"data:image/png;base64,{self.red_pixel_base64}",  # Duplicate of id 1
                    "mime_type": "image/png"
                },
                {
                    "id": 6,
                    "base64_data": f"data:image/png;base64,{self.blue_pixel_base64}",  # Duplicate of id 2
                    "mime_type": "image/png"
                }
            ]
        }
        
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory and its contents
        shutil.rmtree(self.test_dir)
        
    def test_image_deduplication(self):
        """Test that duplicate images are not saved multiple times."""
        # Process the sample data
        processed_data = replace_base64_with_file_references(
            self.sample_data, 
            self.test_dir, 
            self.doc_id
        )
        
        # Check the images directory
        images_dir = Path(self.test_dir) / self.doc_id / "images"
        self.assertTrue(images_dir.exists(), "Images directory should be created")
        
        # Count the files in the images directory
        image_files = list(images_dir.glob("*.png"))
        
        # There should be exactly 2 image files (red and blue pixels)
        self.assertEqual(len(image_files), 2, 
                        f"Expected 2 unique image files, found {len(image_files)}: {[f.name for f in image_files]}")
        
        # Check that the standardized names are used for first two images
        std_image_names = [f"picture_{i}.png" for i in range(1, 3)]
        for name in std_image_names:
            self.assertTrue((images_dir / name).exists(), 
                           f"Standardized image name {name} should exist")
        
        # Check that all processed items reference either standardized names
        file_paths = set()
        for item in processed_data["items"]:
            self.assertIn('external_file', item, 
                         "Each item should have an external_file reference")
            file_paths.add(item['external_file'])
            
        # There should be exactly 2 unique file paths
        self.assertEqual(len(file_paths), 2, 
                        f"Expected 2 unique file paths, found {len(file_paths)}: {file_paths}")
        
    def test_preservation_of_existing_files(self):
        """Test that existing files are preserved and referenced correctly."""
        # Create the images directory
        images_dir = Path(self.test_dir) / self.doc_id / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a sample picture_1.png file
        sample_file = images_dir / "picture_1.png"
        # Decode and save the red pixel
        with open(sample_file, 'wb') as f:
            f.write(base64.b64decode(self.red_pixel_base64))
        
        # Process the sample data with both red and blue pixels
        processed_data = replace_base64_with_file_references(
            self.sample_data, 
            self.test_dir, 
            self.doc_id
        )
        
        # Count the files in the images directory
        image_files = list(images_dir.glob("*.png"))
        
        # There should be exactly 2 image files (existing red and new blue)
        self.assertEqual(len(image_files), 2, 
                        f"Expected 2 unique image files, found {len(image_files)}: {[f.name for f in image_files]}")
        
        # Check that all red pixel items reference the same file
        red_refs = set()
        blue_refs = set()
        
        # Group references by item type (red or blue)
        for item in processed_data["items"]:
            if item['id'] in [1, 3, 5]:  # Red pixel items
                red_refs.add(item['external_file'])
            else:  # Blue pixel items
                blue_refs.add(item['external_file'])
        
        # All red pixel references should be the same
        self.assertEqual(len(red_refs), 1, 
                       f"Expected 1 unique reference for red pixels, found {len(red_refs)}: {red_refs}")
        
        # All blue pixel references should be the same
        self.assertEqual(len(blue_refs), 1, 
                       f"Expected 1 unique reference for blue pixels, found {len(blue_refs)}: {blue_refs}")
        
        # Red and blue references should be different
        self.assertNotEqual(next(iter(red_refs)), next(iter(blue_refs)),
                          "Red and blue pixel references should be different")
        
if __name__ == "__main__":
    unittest.main() 
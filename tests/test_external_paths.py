"""
Test script to verify external path functionality
"""
import json
import tempfile
from pathlib import Path
import base64
import sys
import os

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the functions to test
from src.parse_helper import process_extracted_images
from format_standardized_output import create_standardized_output

def test_process_extracted_images():
    """Test process_extracted_images function with external paths"""
    print("Testing process_extracted_images function...")
    
    # Create test data with raw image data
    test_image_data = b'Test image binary data'
    test_images_data = {
        "images": [
            {
                "raw_data": test_image_data,
                "data_uri": f"data:image/png;base64,{base64.b64encode(test_image_data).decode('utf-8')}",
                "metadata": {
                    "id": "test_image_1",
                    "format": "image/png",
                    "description": "Test image"
                }
            }
        ]
    }
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_path = temp_dir_path
        images_dir = temp_dir_path / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Process the images
        process_extracted_images(test_images_data, images_dir, output_path)
        
        # Print results
        print("After processing:")
        print(json.dumps(test_images_data, indent=2))
        print(f"Raw data removed: {'raw_data' not in test_images_data['images'][0]}")
        print(f"External path added: {'external_path' in test_images_data['images'][0]}")
        print(f"File path in metadata: {'file_path' in test_images_data['images'][0]['metadata']}")
        
        # Verify the file was saved
        expected_file_path = images_dir / "test_image_1.png"
        print(f"Image file exists: {expected_file_path.exists()}")
        
        # Verify JSON file was created
        json_path = output_path / "images_data.json"
        print(f"JSON file exists: {json_path.exists()}")
        
        return test_images_data

def test_standardized_output_with_external_paths():
    """Test create_standardized_output function with external paths"""
    print("\nTesting create_standardized_output with external paths...")
    
    # Create sample document with external paths
    sample_doc = {
        "pictures": [
            {
                "id": "1",
                "external_path": "images/image1.png",
                "page_number": 1
            },
            {
                "id": "2",
                "metadata": {
                    "file_path": "images/image2.jpg"
                },
                "page_number": 2
            },
            # Mixed case - has both data_uri and external_path (external_path should be prioritized)
            {
                "id": "3",
                "external_path": "images/image3.gif",
                "data_uri": "data:image/gif;base64,test123",
                "page_number": 3
            }
        ]
    }
    
    # Create standardized output
    output = create_standardized_output(sample_doc)
    
    # Print results
    image_chunks = [chunk for chunk in output["chunks"] if chunk["format"] == "image"]
    print(f"Number of image chunks: {len(image_chunks)}")
    print("Image chunks:")
    print(json.dumps(image_chunks, indent=2))
    
    # Verify external paths were used
    print("Verification:")
    print(f"First chunk uses external path: {image_chunks[0]['content'] == 'images/image1.png'}")
    print(f"Second chunk uses file_path: {image_chunks[1]['content'] == 'images/image2.jpg'}")
    print(f"Third chunk prioritizes external_path: {image_chunks[2]['content'] == 'images/image3.gif'}")
    
    return output

def test_integration():
    """Test integration between both functions"""
    print("\nTesting integration between process_extracted_images and create_standardized_output...")
    
    # First process images
    images_data = test_process_extracted_images()
    
    # Then create standardized output from the processed images
    if "images" in images_data and len(images_data["images"]) > 0:
        sample_doc = {
            "pictures": [images_data["images"][0]]
        }
        
        # Create standardized output
        output = create_standardized_output(sample_doc)
        
        # Print results
        image_chunks = [chunk for chunk in output["chunks"] if chunk["format"] == "image"]
        print(f"Number of image chunks in integrated test: {len(image_chunks)}")
        print("Image chunks:")
        print(json.dumps(image_chunks, indent=2))
        
        # Verify external path was used
        if len(image_chunks) > 0:
            print(f"Chunk uses external path: {image_chunks[0]['content'] == images_data['images'][0]['external_path']}")
            print(f"Is marked as external: {image_chunks[0]['metadata']['is_external']}")
    
    return True

if __name__ == "__main__":
    test_process_extracted_images()
    test_standardized_output_with_external_paths()
    test_integration() 
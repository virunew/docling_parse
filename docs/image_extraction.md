# PDF Image Extraction Module

This module provides enhanced functionality to extract, process, and organize images from PDF documents using the docling library.

## Overview

The image extraction module is designed to:

1. Extract all images from PDF documents using the docling library
2. Save extracted images in an organized folder structure based on the original document name
3. Maintain relationships between images and their surrounding text content
4. Support various image formats (JPEG, PNG, TIFF, etc.)
5. Provide utility functions for image processing operations
6. Implement robust error handling

## Directory Structure

The image extraction module creates the following directory structure for each processed PDF file:

```
output_dir/
└── document_name/
    ├── images/
    │   ├── picture_1.png
    │   ├── picture_2.jpeg
    │   └── ...
    ├── element_map.json
    └── images_data.json
```

- **document_name/**: A folder named after the PDF file (without extension)
- **images/**: Contains all extracted images from the document
- **element_map.json**: Contains the document's structure and element relationships
- **images_data.json**: Contains metadata and relationship information for all extracted images

## Usage

### Basic Usage

```python
from image_extraction_module import process_pdf_for_images

# Process a PDF document
images_data = process_pdf_for_images(
    pdf_path="document.pdf",
    output_dir="output"
)

# Access extracted images data
for image in images_data.get("images", []):
    metadata = image.get("metadata", {})
    image_id = metadata.get("id")
    file_path = metadata.get("file_path")
    print(f"Image {image_id} saved to {file_path}")
```

### With Configuration

```python
config = {
    'images_scale': 2.0,                # Control image resolution
    'do_picture_description': True,     # Extract image descriptions
    'do_table_structure': True,         # Process tables in the document
    'allow_external_plugins': True      # Allow external docling plugins
}

images_data = process_pdf_for_images(
    pdf_path="document.pdf",
    output_dir="output",
    config=config
)
```

### Advanced Usage

For more control over the extraction process, you can use the `EnhancedImageExtractor` class directly:

```python
from image_extraction_module import EnhancedImageExtractor

# Create an extractor instance with custom configuration
extractor = EnhancedImageExtractor(config={
    'images_scale': 3.0,
    'do_picture_description': True
})

# Extract and save images
images_data = extractor.extract_and_save_images(
    pdf_path="document.pdf",
    output_dir="output"
)
```

## Image Data Structure

The module produces an `images_data.json` file with the following structure:

```json
{
  "document_name": "example",
  "total_pages": 10,
  "images": [
    {
      "metadata": {
        "id": "picture_1",
        "docling_ref": "#/pictures/0",
        "page_number": 3,
        "bounds": {"x": 100, "y": 200, "width": 300, "height": 200},
        "description": "A diagram showing the system architecture",
        "format": "image/png",
        "size": {"width": 600, "height": 400},
        "file_path": "images/picture_1.png"
      },
      "data_uri": "data:image/png;base64,...",
      "relationships": {
        "preceding_text": "As shown in the diagram below:",
        "following_text": "Figure 1: System Architecture Diagram",
        "caption": "Figure 1: System Architecture Diagram",
        "references": [
          {"page": 2, "text": "See Figure 1 for details."}
        ]
      }
    }
    // More images...
  ]
}
```

## Error Handling

The module provides robust error handling:

- `FileNotFoundError`: If the PDF file doesn't exist
- `RuntimeError`: For general extraction errors
- Custom exceptions for specific error scenarios:
  - `CorruptedImageError`: For corrupted images
  - `UnsupportedFormatError`: For unsupported image formats
  - `ExtractionFailureError`: For failures in the extraction process
  - `PermissionError`: For permission-related issues

## Integration

The module is fully integrated with `parse_main.py` and automatically used when processing PDF documents. If the enhanced extraction fails for any reason, the system will fall back to the legacy extraction method. 
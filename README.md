# Docling PDF Parser

This project provides enhanced PDF document parsing capabilities using the Docling library. It extracts text, images, tables, and metadata from PDF documents and structures them into a standardized format for downstream applications.

## Features

- PDF document parsing with Docling's powerful document understanding capabilities
- Enhanced image extraction with parallel processing
- Automatic image-text relationship detection
- Detailed metadata extraction and organization
- Robust error handling and retry mechanisms
- Standardized JSON output format

## Installation

### Prerequisites

- Python 3.8 or higher
- Docling library (included in the repository)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/docling_parse.git
   cd docling_parse
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Process a PDF file with default settings:

```bash
python src/parse_main.py --pdf_path your-document.pdf --output_dir output
```

### Configuration

You can customize the parsing process by providing a configuration file:

```bash
python src/parse_main.py --pdf_path your-document.pdf --output_dir output --config_file config.json
```

Example configuration file:
```json
{
  "pdf_pipeline_options": {
    "images_scale": 2.0,
    "generate_page_images": true,
    "generate_picture_images": true,
    "do_picture_description": true,
    "do_table_structure": true,
    "allow_external_plugins": true
  },
  "image_extraction": {
    "max_workers": 8,
    "max_retries": 3,
    "processing_timeout": 300,
    "retry_delay": 1.0,
    "backoff_factor": 2.0
  }
}
```

### Environment Variables

You can also configure the parser using environment variables:

- `DOCLING_PDF_PATH`: Path to input PDF file
- `DOCLING_OUTPUT_DIR`: Directory for output files
- `DOCLING_LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `DOCLING_CONFIG_FILE`: Optional path to a configuration file

These can be set in a `.env` file in the project root.

## Output Structure

The parser generates the following outputs:

- `{document_name}.json`: The main output file containing the entire document structure
- `{document_name}/element_map.json`: A map of all document elements with their relationships
- `{document_name}/element_map_with_metadata.json`: Enhanced element map with metadata
- `{document_name}/images_data.json`: Metadata about extracted images
- `{document_name}/images/`: Directory containing all extracted images

### JSON Structure

The main output file has the following structure:

```json
{
  "name": "document_name",
  "texts": [...],
  "tables": [...],
  "pictures": [...],
  "metadata": {...},
  "images_data": {
    "images": [
      {
        "metadata": {
          "id": "picture_1",
          "format": "image/png",
          "file_path": "document_name/images/picture_1.png",
          "page": 1,
          "width": 500,
          "height": 300
        }
      }
    ],
    "extraction_stats": {
      "successful": 10,
      "failed": 0,
      "retried": 2,
      "total_time": 5.23
    }
  }
}
```

## Enhanced Image Extraction

The image extraction module provides several advanced features:

- **Parallel Processing**: Extracts images concurrently for improved performance
- **Automatic Retries**: Retries failed extractions with exponential backoff
- **Error Resilience**: Continues processing even if some images fail
- **Image-Text Relationships**: Analyzes relationships between images and surrounding text
- **Detailed Statistics**: Provides extraction metrics for debugging and monitoring

Configure the image extraction process via the `image_extraction` section in the config file:

```json
{
  "image_extraction": {
    "max_workers": 8,        // Number of parallel workers
    "max_retries": 3,        // Number of retry attempts for failed extractions
    "processing_timeout": 300, // Timeout for the entire process in seconds
    "retry_delay": 1.0,      // Initial delay between retries in seconds
    "backoff_factor": 2.0    // Factor by which delay increases with each retry
  }
}
```

## Standardized Output Format

The standardized output format is a structured representation of the document content that follows the specified schema requirements. It consists of:

1. **Chunks Array**: Content elements from the document, organized with the following fields:
   - `block_id`: Sequential identifier
   - `content_type`: "text", "table", or "image"
   - `master_index`: Page number
   - `coords_x/y/cx/cy`: Position and size on the page
   - `text_block`: Text content or image caption with context
   - `table_block`: JSON string of table data
   - `external_files`: Path to image files
   - `header_text`: Breadcrumb navigation
   - `special_field1`: JSON string of additional metadata
   - Plus additional fields as required by the schema

2. **Furniture Array**: Contains page headers, footers, and other elements not part of the main content.

3. **Source Metadata**: Information about the source document including filename and mimetype.

### Usage

The standardized output is generated by the `save_standardized_output` function, which processes the document data and creates the required JSON structure:

```python
from src.format_standardized_output import save_standardized_output

# Process document data
standardized_output_file = save_standardized_output(
    document_data,
    output_directory,
    pdf_file_path
)
```

The standardized output is saved to a JSON file in the specified output directory, with the filename pattern `{document_name}_standardized.json`.

### Testing

The standardized output format has been extensively tested with:
- Basic unit tests for each component function
- Complex document tests with tables and images
- Integration tests to verify proper inclusion in the main pipeline
- Standalone tests to validate format structure and requirements

All tests demonstrate that the standardized output format correctly handles text, tables, and images, properly separates content and furniture elements, and includes all required metadata fields.

## Development

### Project Structure

```
├── docling/              # Docling library
├── src/
│   ├── parse_main.py           # Main entry point
│   ├── parse_helper.py         # Document processing functions
│   ├── docling_integration.py  # Integration with docling library
│   ├── element_map_builder.py  # Builds document element map
│   ├── image_extraction_module.py # Enhanced image extraction
│   ├── pdf_image_extractor.py  # Base image extraction functionality
│   ├── metadata_extractor.py   # Extracts element metadata
│   └── logger_config.py        # Logging configuration
├── tests/
│   ├── data/                   # Test data files
│   ├── test_image_extraction_module.py # Image extraction tests
│   └── test_integration.py     # Integration tests
├── requirements.txt      # Dependencies
└── README.md            # This file
```

### Running Tests

Run the unit tests with:

```bash
python -m unittest discover tests
```

## License

[Specify the license here]

## Acknowledgements

This project builds upon the powerful Docling document understanding library.
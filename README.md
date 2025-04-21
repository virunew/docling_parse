# docling_parse

A Python library for parsing PDF documents using the Docling library and generating a standardized DoclingDocument JSON representation.

## Overview

This library provides functionality to:

1. Process PDF documents using the Docling library
2. Extract structured content (text, images, tables, etc.)
3. Generate a standardized DoclingDocument JSON representation 
4. Save the output for further processing or analysis

The DoclingDocument JSON format provides a consistent representation of document content that can be easily consumed by other applications.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/docling_parse.git
cd docling_parse

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command-line Interface

The simplest way to use the library is through its command-line interface:

```bash
python src/parse_main.py --pdf_path=your_document.pdf --output_dir=output
```

Options:
- `--pdf_path, -p`: Path to the input PDF file (required)
- `--output_dir, -o`: Directory for output files (default: 'output')
- `--log_level, -l`: Logging verbosity level (DEBUG, INFO, WARNING, ERROR)
- `--config_file, -c`: Path to additional configuration file

### Environment Variables

You can also set configuration through environment variables in a `.env` file:

```
DOCLING_PDF_PATH=/path/to/your/document.pdf
DOCLING_OUTPUT_DIR=output
DOCLING_LOG_LEVEL=INFO
DOCLING_CONFIG_FILE=/path/to/config.json
```

### Python API

```python
from src.parse_main import process_pdf_document, save_output

# Process a PDF document
docling_document = process_pdf_document(
    "your_document.pdf", 
    "output_directory",
    config_file="optional_config.json"
)

# Save the document as JSON
output_file = save_output(docling_document, "output_directory")
print(f"Document saved to: {output_file}")
```

## DoclingDocument JSON Format

The output is saved as a JSON file called `element_map.json` in the specified output directory. The JSON follows the DoclingDocument schema with the following structure:

```json
{
  "schema_name": "DoclingDocument",
  "version": "1.3.0",
  "name": "document_name",
  "origin": {
    "mimetype": "application/pdf",
    "binary_hash": 1234567890,
    "filename": "original_file.pdf"
  },
  "body": {
    "self_ref": "#/body",
    "children": [...],
    "content_layer": "body",
    "name": "_root_",
    "label": "unspecified"
  },
  "furniture": {
    "self_ref": "#/furniture",
    "children": [...],
    "content_layer": "furniture",
    "name": "_root_",
    "label": "unspecified"
  },
  "texts": [...],
  "groups": [...],
  "pages": [...]
}
```

Key elements include:
- `body`: Main content of the document
- `furniture`: Headers, footers, and other page decorations
- `texts`: Text elements with content and attributes
- `groups`: Groupings of related elements

## Testing

Run unit tests with:

```bash
# Run all tests
python -m unittest discover tests

# Run specific tests
python -m unittest tests/test_docling_document_serialization.py
```

For a quick test of the DoclingDocument serialization on a real PDF:

```bash
python tests/run_parse_test.py path/to/document.pdf
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
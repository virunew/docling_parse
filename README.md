# Docling PDF Parser

A PDF document parser that extracts structured content from PDF files using the docling library.

## Features

- Extracts text and structure from PDF documents
- Extracts images from PDF documents with metadata
- Builds a complete element map of document components
- Analyzes relationships between images and surrounding text
- Saves the document structure and images as JSON

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/docling_parse.git
   cd docling_parse
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure the docling library is installed (follow docling installation instructions).

## Usage

### Command Line Interface

```bash
python src/parse_main.py --pdf <path_to_pdf> --output <output_directory> --log-level INFO
```

Options:
- `--pdf <path>`: Path to the PDF document to process
- `--output <directory>`: Directory to save output files
- `--log-level <level>`: Log level (DEBUG, INFO, WARNING, ERROR)
- `--config <file>`: Optional path to a configuration file

### Environment Variables

You can also set options using environment variables:
- `DOCLING_PDF_PATH`: Path to input PDF file
- `DOCLING_OUTPUT_DIR`: Directory for output files
- `DOCLING_LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `DOCLING_CONFIG_FILE`: Optional path to a configuration file

### Output

The parser generates the following output:
1. A JSON file containing the document structure
2. Extracted images saved in an `images` directory
3. An `images_data.json` file with metadata about the extracted images

## PDF Image Extraction

The `pdf_image_extractor.py` module provides functionality to extract images from PDF documents. It is integrated with the main parsing flow to automatically extract and process images.

### Features

- Extracts embedded images from PDF documents
- Captures image metadata (size, format, page number, position)
- Analyzes relationships with surrounding text content
- Supports various image formats (PNG, JPEG, etc.)
- Handles multi-page documents

### Integration

The PDF image extractor is integrated into the main parsing flow as follows:

1. `parse_main.py` calls `process_pdf_document()` to process the PDF
2. Within `process_pdf_document()`, an instance of `PDFImageExtractor` is created
3. `extract_images()` is called to extract images from the PDF
4. Extracted images are saved to the `images` directory
5. Image metadata and relationships are saved to `images_data.json`
6. `save_output()` integrates image data into the final JSON output

## Testing

Run the tests with:

```bash
python -m unittest discover tests
```

You can also run individual test modules:

```bash
python tests/test_with_mocks.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
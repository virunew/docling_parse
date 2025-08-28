# Docling Parse

This project seems to use docling parsing for LLMWare. The overall objective is to bring docling's accuracy to llmware RAG framework for parsin gtasks.

## Key Features

- Processes PDF documents using the Docling library
- Extracts text, tables, and images with proper formatting
- Generates hierarchical breadcrumb paths based on section headers
- Saves images as external files instead of embedding them in JSON
- Filters out furniture elements (headers, footers) from context snippets
- Outputs in various formats: JSON, Markdown, HTML, CSV

## Recent Fixes

This version includes important fixes for three major issues:

1. **External Image Storage**: Images are now saved as external files instead of being embedded as base64 data in the JSON. This significantly reduces the size of the output JSON file and improves performance.

2. **Complete Element Information**: All document elements (text, tables, images) are now properly identified and included in the element map, ensuring no content is missed.

3. **Improved Breadcrumbs and Context**: 
   - Breadcrumbs now correctly represent the document's hierarchical structure based on section headers
   - Furniture elements (headers, footers, page numbers) are filtered out from context snippets to provide cleaner, more relevant context

## Installation

### Prerequisites

- Python 3.7+
- Docling library (included)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/docling_parse.git
   cd docling_parse
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running from Command Line

Use the `run_parser.py` script for the simplest way to run the parser:

```bash
python run_parser.py input.pdf output_dir --format json
```

### Arguments

- `pdf_path`: Path to the input PDF file (required)
- `output_dir`: Directory for output files (required)
- `--format`: Output format (choices: json, md, html, csv; default: json)
- `--log_level`: Logging verbosity level (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL; default: INFO)

### Direct Usage of parse_main.py

For more advanced options, you can use the main parser directly:

```bash
python parse_main.py --pdf_path input.pdf --output_dir output --output_format json
```

Additional options:
- `--include_metadata`/`--no_metadata`: Include/exclude metadata in output
- `--include_page_breaks`/`--no_page_breaks`: Include/exclude page break markers
- `--include_captions`/`--no_captions`: Include/exclude captions for tables and images
- `--image_base_url`: Base URL for image links in output
- `--config_file`: Path to additional configuration file

## Output Files

The parser generates several output files:

- `docling_document.json`: Raw output from the Docling library
- `fixed_document.json`: The document with metadata fixes applied (external image references, proper breadcrumbs, filtered context)
- `document.json` (or other format based on `--format`): The final formatted output

## Environment Variables

You can set the following environment variables in a `.env` file:

- `DOCLING_PDF_PATH`: Default path to input PDF file
- `DOCLING_OUTPUT_DIR`: Default directory for output files
- `DOCLING_LOG_LEVEL`: Default logging verbosity
- `DOCLING_CONFIG_FILE`: Default path to a configuration file
- `DOCLING_OUTPUT_FORMAT`: Default output format
- `DOCLING_IMAGE_BASE_URL`: Default base URL for image links
- `DOCLING_INCLUDE_METADATA`: Whether to include metadata in output
- `DOCLING_INCLUDE_PAGE_BREAKS`: Whether to include page break markers
- `DOCLING_INCLUDE_CAPTIONS`: Whether to include captions for tables and images

## Testing

Run the tests to verify that the parser is working correctly:

```bash
cd tests
python -m test_integration
```

This will run integration tests that verify:
1. Images are properly saved as external files
2. All element types are correctly identified
3. Breadcrumbs are generated properly and furniture is filtered from context

## Project Structure

- `parse_main.py`: Main entry point for the application
- `src/`: Directory containing the parser modules
  - `json_metadata_fixer.py`: Module to fix metadata issues in the parsed document
  - `content_extractor.py`: Extract content from different element types
  - `metadata_extractor.py`: Extract and format metadata
  - `element_map_builder.py`: Build a map of elements from the document
  - `pdf_image_extractor.py`: Extract images from PDF documents
  - `parse_helper.py`: Helper functions for parsing
  - `output_formatter.py`: Format output in different formats
- `tests/`: Directory containing tests
- `run_parser.py`: Simple script to run the parser

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

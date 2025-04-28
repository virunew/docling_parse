# Docling Parse

A Python tool for parsing PDF documents using the Docling library, extracting content with proper structure, and generating standardized output.

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

# Docling BreadcrumbChunker

An enhanced document chunker for the Docling library that generates complete hierarchical breadcrumb paths for document chunks.

## Overview

The `BreadcrumbChunker` extends the base chunker functionality in Docling to create complete breadcrumb paths that preserve the full hierarchical structure of the document. This is particularly useful for documents with complex section numbering and nested headings.

## Features

- **Full Hierarchical Breadcrumbs**: Generates breadcrumbs that include all levels of the document hierarchy for each chunk
- **Section Number Awareness**: Recognizes document section numbering patterns (e.g., "3.2.1.") to correctly nest headings
- **Special Handling for Unnumbered Headings**: Properly handles unnumbered headings (e.g., "Shall", "Should", "May") by nesting them under their parent sections

## Example Output

A document chunk containing the text "The word 'shall' be used to state a binding requirement..." might have a breadcrumb path like:

```json
{
  "headings": "3.2.2. Definitions > 3.2.2.1. Obligation of Requirement Wording > Shall",
  ...
}
```

## Implementation Details

The chunker works by:

1. Tracking the full breadcrumb path at each heading level
2. Using regex pattern matching to extract section numbers from headings
3. Determining the appropriate parent level for each heading
4. Creating synthetic levels for unnumbered headings to maintain the hierarchy

## Usage

```python
from breadcrumb_chunker import BreadcrumbChunker
from docling.document_converter import DocumentConverter
from docling.document_converter import PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Create and configure the document converter
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 2.0
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True
pipeline_options.do_ocr = False

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Convert a document
conv_res = doc_converter.convert('/path/to/document.pdf')

# Create and use the chunker
chunker = BreadcrumbChunker(merge_list_items=True)
chunks = chunker.chunk(conv_res.document)

# Process the chunks
for chunk in chunks:
    print(f"Text: {chunk.text}")
    print(f"Breadcrumb: {chunk.meta.headings}")
    print("---")
```

## Testing

Run the tests with:

```bash
python tests/test_breadcrumb_chunker.py
```

# Docling JSON Parser - Breadcrumb Chunker

This README explains the implementation of our `breadcrumb_chunker.py` module and how it integrates with the document processing pipeline through `externally_ref_images.py`.

## Overview

The BreadcrumbChunker is a specialized document processor that extracts structured content from Docling documents while preserving hierarchical context through breadcrumb paths. It addresses the key requirement of maintaining document structure when converting complex, nested document data into standardized chunks suitable for database storage.

## Implementation Approach

### Core Functionality

The BreadcrumbChunker works by:

1. **Hierarchical Context Tracking**: As it traverses document elements, it tracks the hierarchical path of section headers to create breadcrumb trails.

2. **Element Classification**: Distinguishes between content types (text, images, tables) and processes each appropriately.

3. **Image Reference Mapping**: Maintains relationships between image references in the document and their external storage locations.

4. **Metadata Enrichment**: Attaches contextual metadata including page numbers, coordinates, and surrounding content.

## Integration with Docling

The chunker leverages Docling's document model to:

- Access the document's structured representation
- Retrieve image data via the Docling API
- Maintain reference integrity for document elements
- Preserve the document's reading order

## Usage Example

As demonstrated in `externally_ref_images.py`, the BreadcrumbChunker is used as follows:

```python
# Initialize the chunker
chunker = BreadcrumbChunker(merge_list_items=True)

# Process the document with image reference mapping
chunks = chunker.chunk(document, image_ref_map=image_ref_map)

# The resulting chunks contain structured content with breadcrumb paths
```

## Output Format

The chunker generates structured content that can be mapped to the standardized JSON format required for database ingestion. This format includes:

- Hierarchical breadcrumb paths
- Content type classification (text, table, image)
- Coordinate information for visual placement
- External file references for images
- Contextual metadata for search and navigation

## Key Features

- **Full Header Preservation**: Breadcrumbs include complete header text without truncation
- **Image Reference Management**: Maintains paths to externally stored images
- **Structural Context**: Preserves document hierarchy for improved navigation
- **Metadata Enrichment**: Includes page numbers, coordinates, and contextual information
# PDF Document Parser Tests

This directory contains test files for the PDF document parsing application with image extraction functionality.

## Test Structure

The test suite is organized into several test files:

- **test_pdf_image_extraction_integration.py**: Tests the integration of the PDF Image Extractor module with parse_main.py
- **test_parse_helper_image_integration.py**: Tests the image extraction integration with the parse_helper module
- **integration_test_parse_main.py**: End-to-end tests for the entire workflow

## Test Data Requirements

Some tests require PDF test files to run properly. These tests are marked with `pytest.mark.skipif` and will be skipped if no test files are available. To run these tests:

1. Create a directory named `test_data` in the root of the project (at the same level as `src` and `tests` directories)
2. Add one or more PDF files to this directory
3. Run the tests

## Running Tests

To run all tests:

```bash
# From the project root
python -m pytest tests/

# With more details
python -m pytest tests/ -v
```

To run specific test files:

```bash
# Run just the PDF image extraction tests
python -m pytest tests/test_pdf_image_extraction_integration.py

# Run just the parse_helper tests
python -m pytest tests/test_parse_helper_image_integration.py

# Run just the end-to-end tests
python -m pytest tests/integration_test_parse_main.py
```

To run specific test methods:

```bash
# Run a specific test method
python -m pytest tests/test_pdf_image_extraction_integration.py::TestPDFImageExtractionIntegration::test_extract_images_from_processed_document
```

## Test Coverage

The test suite covers:

1. PDF document processing with docling library
2. Image extraction from PDF documents
3. Building element maps for document structure
4. Integration of image data with document output
5. Command-line argument processing
6. Configuration loading from different sources
7. Error handling throughout the application

## Mocking Strategy

The tests use pytest's mocking capabilities to avoid actual PDF processing in most cases. Key components that are mocked include:

- The docling `DocumentConverter` class
- The PDF processing pipeline
- File I/O operations in some tests
- The `PDFImageExtractor` image extraction process

However, some integration tests may process actual PDF files if they are available in the `test_data` directory.

## Adding New Tests

When adding new tests:

1. Follow the existing test structure
2. Use pytest fixtures for setup and teardown
3. Mock external dependencies appropriately
4. Add proper assertions to verify behavior
5. Add skipif markers for tests requiring specific data

## Troubleshooting

If tests are failing, check:

1. Python environment has all required dependencies
2. Test data exists (if required)
3. Mock objects are configured correctly
4. The pytest version is compatible (requires pytest 6.0+) 
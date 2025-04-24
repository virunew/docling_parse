# SQL Format Test Plan

This document outlines the testing strategy for the SQL format output features in the Docling PDF parser.

## Test Coverage

### Unit Tests

1. **SQL Formatter Tests** (`test_sql_formatter.py`)
   - Test the `process_docling_json_to_sql_format` function
   - Verify correct conversion of document data to SQL-compatible format
   - Check handling of text, table, and image elements
   - Validate required fields are present in output

2. **SQL Insert Generator Tests** (`test_sql_insert_generator.py`)
   - Test string escaping for different SQL dialects
   - Verify identifier formatting
   - Test generation of document, content, and furniture INSERT statements
   - Validate dialect-specific syntax (PostgreSQL, MySQL, SQLite)
   - Check SQL output file generation

3. **Standardized Output Format Tests** (`test_format_standardized_output.py`)
   - Test utility functions (is_furniture, extract_content_type, etc.)
   - Verify text, table, and image block formatting
   - Test chunk building with required fields
   - Validate the complete standardized output structure

### Integration Tests

1. **SQL Integration Tests** (`test_integration_sql.py`)
   - Test SQL output via direct API calls
   - Verify SQL format parameters are correctly applied
   - Test SQL dialect selection
   - Check standardized format integration
   - Validate SQL INSERT statement generation

2. **Command-Line Interface Tests** (`test_cli.py`)
   - Test basic command-line usage with SQL output format
   - Verify SQL dialect selection via command line
   - Test standardized format option
   - Validate SQL INSERT statement generation
   - Check environment variable configuration

## Manual Testing

1. **Basic SQL Output**
   - Run `python parse_main.py --pdf_path sample.pdf --output_dir output --output-format sql`
   - Verify `sample_sql.json` is created with correct structure

2. **SQL Dialect Selection**
   - Test each dialect:
     ```
     python parse_main.py --pdf_path sample.pdf --output_dir output --output-format sql --sql-dialect postgresql
     python parse_main.py --pdf_path sample.pdf --output_dir output --output-format sql --sql-dialect mysql
     python parse_main.py --pdf_path sample.pdf --output_dir output --output-format sql --sql-dialect sqlite
     ```
   - Check differences in identifier quoting and string escaping

3. **SQL INSERT Statement Generation**
   - Run `python parse_main.py --pdf_path sample.pdf --output_dir output --output-format sql --sql-inserts`
   - Verify `sample_inserts.sql` contains valid SQL
   - Try importing into a real database (optional)

4. **Standardized Format**
   - Run `python parse_main.py --pdf_path sample.pdf --output_dir output --output-format sql --standardized-format`
   - Verify `sample_standardized.json` conforms to expected schema
   - Check that all required fields are present

5. **Combined Options**
   - Test with multiple options:
     ```
     python parse_main.py --pdf_path sample.pdf --output_dir output --output-format sql --standardized-format --sql-inserts --sql-dialect mysql
     ```
   - Verify correct handling of all parameters

6. **Environment Variable Configuration**
   - Create a `.env` file with:
     ```
     DOCLING_OUTPUT_FORMAT=sql
     DOCLING_SQL_DIALECT=mysql
     DOCLING_STANDARDIZED_FORMAT=true
     DOCLING_SQL_INSERTS=true
     ```
   - Run `python parse_main.py --pdf_path sample.pdf --output_dir output`
   - Verify settings from environment variables are applied

## Test Validation Criteria

For each SQL output file, verify:

1. **Chunks Array**
   - Required fields: block_id, content_type, file_type, master_index, coords_x/y/cx/cy
   - Text content in text_block field
   - Table data in table_block field (JSON string)
   - Image paths in external_files field
   - Breadcrumbs in header_text field

2. **Furniture Array**
   - Contains page headers, footers, and other furniture elements
   - Text is preserved correctly

3. **Source Metadata**
   - Filename, mimetype, and hash information is preserved

For SQL INSERT statements, verify:

1. **Document Inserts**
   - Document metadata fields in INSERT statement
   - Proper quoting and escaping based on dialect

2. **Content Chunk Inserts**
   - One INSERT per content chunk
   - All required fields included
   - Text properly escaped

3. **Furniture Inserts**
   - Furniture elements correctly inserted
   - Proper quoting and escaping

## Regression Testing

When making changes to SQL format functionality, run:

1. All unit tests with `python -m unittest discover tests`
2. Integration tests with `python -m unittest tests/test_integration_sql.py`
3. CLI tests with `python -m unittest tests/test_cli.py`

## Performance Considerations

For large documents, monitor:

1. Memory usage during SQL format generation
2. Processing time for different output formats
3. File size of generated SQL output (especially INSERT statements) 
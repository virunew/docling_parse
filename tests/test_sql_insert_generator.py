"""
Test module for the SQLInsertGenerator class.

This module contains tests for the SQLInsertGenerator class, which generates SQL INSERT
statements from standardized document data.
"""

import unittest
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any

from src.sql_insert_generator import SQLInsertGenerator
from src.output_formatter import OutputFormatter


class TestSQLInsertGenerator(unittest.TestCase):
    """
    Test cases for the SQLInsertGenerator class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create sample document data
        self.document_data = {
            "metadata": {
                "document_id": "test-doc-001",
                "title": "Test Document",
                "author": "Test Author",
                "date": "2023-04-15",
                "source": "test-source"
            },
            "content": [
                {
                    "type": "heading",
                    "text": "Introduction",
                    "level": 1
                },
                {
                    "type": "paragraph",
                    "text": "This is a test paragraph with 'quotes' and \"double quotes\"."
                },
                {
                    "type": "furniture",
                    "furniture_type": "table",
                    "caption": "Sample Table",
                    "data": {
                        "headers": ["Column 1", "Column 2"],
                        "rows": [["Value 1", "Value 2"], ["Value 3", "Value 4"]]
                    }
                }
            ]
        }
        
        # Create SQLInsertGenerator instances for different dialects
        self.pg_generator = SQLInsertGenerator(dialect="postgresql")
        self.mysql_generator = SQLInsertGenerator(dialect="mysql")
        self.sqlite_generator = SQLInsertGenerator(dialect="sqlite")
    
    def test_string_escaping(self):
        """
        Test string escaping for different SQL dialects.
        """
        test_string = "Test with 'quotes' and \"double quotes\" and \\backslashes"
        
        # PostgreSQL
        pg_escaped = self.pg_generator.escape_string(test_string)
        self.assertIn("''quotes''", pg_escaped)
        
        # MySQL
        mysql_escaped = self.mysql_generator.escape_string(test_string)
        self.assertIn("\\'quotes\\'", mysql_escaped)
        
        # SQLite
        sqlite_escaped = self.sqlite_generator.escape_string(test_string)
        self.assertIn("''quotes''", sqlite_escaped)
        
        # Test NULL handling
        self.assertEqual("NULL", self.pg_generator.escape_string(None))
    
    def test_identifier_formatting(self):
        """
        Test identifier formatting for different SQL dialects.
        """
        identifier = "column_name"
        
        # PostgreSQL
        pg_formatted = self.pg_generator.format_identifier(identifier)
        self.assertEqual('"column_name"', pg_formatted)
        
        # MySQL
        mysql_formatted = self.mysql_generator.format_identifier(identifier)
        self.assertEqual('`column_name`', mysql_formatted)
        
        # SQLite
        sqlite_formatted = self.sqlite_generator.format_identifier(identifier)
        self.assertEqual('"column_name"', sqlite_formatted)
    
    def test_generate_document_insert(self):
        """
        Test generating SQL INSERT statement for document metadata.
        """
        metadata = self.document_data["metadata"]
        
        # PostgreSQL
        pg_insert = self.pg_generator.generate_document_insert(metadata)
        self.assertIn('INSERT INTO "documents"', pg_insert)
        self.assertIn('"document_id"', pg_insert)
        self.assertIn('"title"', pg_insert)
        self.assertIn('E\'Test Document\'', pg_insert)
        
        # MySQL
        mysql_insert = self.mysql_generator.generate_document_insert(metadata)
        self.assertIn('INSERT INTO `documents`', mysql_insert)
        self.assertIn('`document_id`', mysql_insert)
        self.assertIn('`title`', mysql_insert)
        self.assertIn('\'Test Document\'', mysql_insert)
        
        # SQLite
        sqlite_insert = self.sqlite_generator.generate_document_insert(metadata)
        self.assertIn('INSERT INTO "documents"', sqlite_insert)
        self.assertIn('"document_id"', sqlite_insert)
        self.assertIn('"title"', sqlite_insert)
        self.assertIn('\'Test Document\'', sqlite_insert)
    
    def test_generate_content_inserts(self):
        """
        Test generating SQL INSERT statements for content chunks.
        """
        document_id = self.document_data["metadata"]["document_id"]
        content = self.document_data["content"]
        
        # PostgreSQL
        pg_inserts = self.pg_generator.generate_chunk_inserts(document_id, content)
        self.assertIn('INSERT INTO "document_chunks"', pg_inserts)
        self.assertIn('"chunk_id"', pg_inserts)
        self.assertIn('"type"', pg_inserts)
        self.assertIn('E\'Introduction\'', pg_inserts)
        self.assertIn('"level"', pg_inserts)
        
        # Check that furniture items are not included
        self.assertNotIn('table', pg_inserts)
        
        # MySQL
        mysql_inserts = self.mysql_generator.generate_chunk_inserts(document_id, content)
        self.assertIn('INSERT INTO `document_chunks`', mysql_inserts)
        self.assertIn('`chunk_id`', mysql_inserts)
        self.assertIn('`type`', mysql_inserts)
        self.assertIn('\'Introduction\'', mysql_inserts)
        
        # SQLite
        sqlite_inserts = self.sqlite_generator.generate_chunk_inserts(document_id, content)
        self.assertIn('INSERT INTO "document_chunks"', sqlite_inserts)
        self.assertIn('"chunk_id"', sqlite_inserts)
        self.assertIn('"type"', sqlite_inserts)
        self.assertIn('\'Introduction\'', sqlite_inserts)
    
    def test_generate_furniture_inserts(self):
        """
        Test generating SQL INSERT statements for furniture items.
        """
        document_id = self.document_data["metadata"]["document_id"]
        furniture_items = [item for item in self.document_data["content"] if item.get("type") == "furniture"]
        
        # PostgreSQL
        pg_inserts = self.pg_generator.generate_furniture_inserts(document_id, furniture_items)
        self.assertIn('INSERT INTO "document_furniture"', pg_inserts)
        self.assertIn('"furniture_id"', pg_inserts)
        self.assertIn('"type"', pg_inserts)
        self.assertIn('E\'table\'', pg_inserts)
        self.assertIn('"data"', pg_inserts)
        
        # MySQL
        mysql_inserts = self.mysql_generator.generate_furniture_inserts(document_id, furniture_items)
        self.assertIn('INSERT INTO `document_furniture`', mysql_inserts)
        self.assertIn('`furniture_id`', mysql_inserts)
        self.assertIn('`type`', mysql_inserts)
        self.assertIn('\'table\'', mysql_inserts)
        self.assertIn('`data`', mysql_inserts)
        
        # SQLite
        sqlite_inserts = self.sqlite_generator.generate_furniture_inserts(document_id, furniture_items)
        self.assertIn('INSERT INTO "document_furniture"', sqlite_inserts)
        self.assertIn('"furniture_id"', sqlite_inserts)
        self.assertIn('"type"', sqlite_inserts)
        self.assertIn('\'table\'', sqlite_inserts)
        self.assertIn('"data"', sqlite_inserts)
    
    def test_generate_sql_inserts(self):
        """
        Test generating complete SQL INSERT statements for a document.
        """
        # PostgreSQL
        pg_sql = self.pg_generator.generate_sql_inserts(self.document_data)
        
        # Check headers and comments
        self.assertIn('-- SQL INSERT statements for document', pg_sql)
        self.assertIn('-- Generated on', pg_sql)
        self.assertIn('-- Using dialect: postgresql', pg_sql)
        
        # Check document insert section
        self.assertIn('-- Document insert', pg_sql)
        self.assertIn('INSERT INTO "documents"', pg_sql)
        
        # Check content chunks section
        self.assertIn('-- Content chunk inserts', pg_sql)
        self.assertIn('INSERT INTO "document_chunks"', pg_sql)
        
        # Check furniture section
        self.assertIn('-- Furniture inserts', pg_sql)
        self.assertIn('INSERT INTO "document_furniture"', pg_sql)
        
        # MySQL and SQLite
        mysql_sql = self.mysql_generator.generate_sql_inserts(self.document_data)
        self.assertIn('-- Using dialect: mysql', mysql_sql)
        
        sqlite_sql = self.sqlite_generator.generate_sql_inserts(self.document_data)
        self.assertIn('-- Using dialect: sqlite', sqlite_sql)
    
    def test_save_sql_inserts(self):
        """
        Test saving SQL INSERT statements to a file.
        """
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save PostgreSQL inserts
            output_path = self.pg_generator.save_sql_inserts(
                self.document_data, 
                temp_dir, 
                filename="test_pg_inserts.sql"
            )
            
            # Check that the file exists
            self.assertTrue(os.path.exists(output_path))
            
            # Check the file content
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn('-- SQL INSERT statements for document', content)
            self.assertIn('INSERT INTO "documents"', content)
            self.assertIn('INSERT INTO "document_chunks"', content)
            self.assertIn('INSERT INTO "document_furniture"', content)
            
            # Test with auto-generated filename
            output_path = self.mysql_generator.save_sql_inserts(
                self.document_data, 
                temp_dir
            )
            
            # Check that the file exists and has expected name pattern
            self.assertTrue(os.path.exists(output_path))
            self.assertIn('test-doc-001_mysql_inserts.sql', output_path)
    
    def test_integration_with_output_formatter(self):
        """
        Test integration with the OutputFormatter class.
        """
        # Create a configuration for the OutputFormatter that includes SQL output
        config = {
            "include_sql": True,
            "sql_dialect": "postgresql",
            "output_dir": None  # Will be set to a temp dir during the test
        }
        
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set the output directory in the config
            config["output_dir"] = temp_dir
            
            # Create an OutputFormatter instance
            formatter = OutputFormatter(config)
            
            # Add the SQL formatter method to the OutputFormatter
            def format_as_sql(document_data: Dict[str, Any], save_to_file: bool = False) -> str:
                """Format the document data as SQL INSERT statements."""
                try:
                    sql_generator = SQLInsertGenerator(dialect=config.get("sql_dialect", "postgresql"))
                    sql_inserts = sql_generator.generate_sql_inserts(document_data)
                    
                    if save_to_file and config.get("output_dir"):
                        sql_generator.save_sql_inserts(
                            document_data,
                            config["output_dir"]
                        )
                    
                    return sql_inserts
                except Exception as e:
                    return f"Error generating SQL: {str(e)}"
            
            # Replace or add the format_as_sql method to the formatter
            setattr(formatter, "format_as_sql", format_as_sql)
            
            # Call the new method
            sql_output = formatter.format_as_sql(self.document_data, save_to_file=True)
            
            # Check the output
            self.assertIn('-- SQL INSERT statements for document', sql_output)
            self.assertIn('INSERT INTO "documents"', sql_output)
            
            # Check if the file was created
            expected_filename = f"{self.document_data['metadata']['document_id']}_postgresql_inserts.sql"
            expected_filepath = os.path.join(temp_dir, expected_filename)
            self.assertTrue(os.path.exists(expected_filepath))
            
            # Read the file and verify its contents
            with open(expected_filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            self.assertEqual(sql_output, file_content)


if __name__ == '__main__':
    unittest.main() 
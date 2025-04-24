"""
SQL Insert Generator for document parsing output.

This module provides a class for generating SQL INSERT statements
from parsed document data for insertion into a database.
"""

import os
import re
import uuid
import json
import logging
from typing import Dict, Any, List, Union, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class SQLInsertGenerator:
    """
    Generate SQL INSERT statements from parsed document data.
    
    This class converts document data into SQL INSERT statements
    for various SQL dialects (PostgreSQL, MySQL, SQLite).
    """
    
    def __init__(self, dialect: str = "postgresql"):
        """
        Initialize the SQL Insert Generator.
        
        Args:
            dialect: SQL dialect to use ('postgresql', 'mysql', 'sqlite')
        """
        self.dialect = dialect.lower()
        
        # Validate dialect
        valid_dialects = ["postgresql", "mysql", "sqlite"]
        if self.dialect not in valid_dialects:
            raise ValueError(f"Invalid SQL dialect: {dialect}. Must be one of: {', '.join(valid_dialects)}")
        
        logger.info(f"Initialized SQLInsertGenerator with dialect: {self.dialect}")
        
        # Set up dialect-specific quoting and escaping
        if self.dialect == "postgresql":
            self.id_quote = '"'
            self.string_quote = "'"
            self.string_escape = self._escape_string_postgresql
            self.escape_identifier = self._escape_identifier_postgresql
            self.null_value = "NULL"
        elif self.dialect == "mysql":
            self.id_quote = '`'
            self.string_quote = "'"
            self.string_escape = self._escape_string_mysql
            self.escape_identifier = self._escape_identifier_mysql
            self.null_value = "NULL"
        elif self.dialect == "sqlite":
            self.id_quote = '"'
            self.string_quote = "'"
            self.string_escape = self._escape_string_sqlite
            self.escape_identifier = self._escape_identifier_sqlite
            self.null_value = "NULL"
    
    def _escape_string_postgresql(self, s: str) -> str:
        """
        Escape a string for PostgreSQL.
        
        Args:
            s: String to escape
            
        Returns:
            Escaped string
        """
        if s is None:
            return self.null_value
        return s.replace("'", "''")
    
    def _escape_string_mysql(self, s: str) -> str:
        """
        Escape a string for MySQL.
        
        Args:
            s: String to escape
            
        Returns:
            Escaped string
        """
        if s is None:
            return self.null_value
        return s.replace("\\", "\\\\").replace("'", "\\'").replace("\r", "\\r").replace("\n", "\\n")
    
    def _escape_string_sqlite(self, s: str) -> str:
        """
        Escape a string for SQLite.
        
        Args:
            s: String to escape
            
        Returns:
            Escaped string
        """
        if s is None:
            return self.null_value
        return s.replace("'", "''")
    
    def _escape_identifier_postgresql(self, identifier: str) -> str:
        """
        Escape an identifier for PostgreSQL.
        
        Args:
            identifier: Identifier to escape
            
        Returns:
            Escaped identifier
        """
        return f'{self.id_quote}{identifier.replace(self.id_quote, self.id_quote+self.id_quote)}{self.id_quote}'
    
    def _escape_identifier_mysql(self, identifier: str) -> str:
        """
        Escape an identifier for MySQL.
        
        Args:
            identifier: Identifier to escape
            
        Returns:
            Escaped identifier
        """
        return f'{self.id_quote}{identifier.replace(self.id_quote, self.id_quote+self.id_quote)}{self.id_quote}'
    
    def _escape_identifier_sqlite(self, identifier: str) -> str:
        """
        Escape an identifier for SQLite.
        
        Args:
            identifier: Identifier to escape
            
        Returns:
            Escaped identifier
        """
        return f'{self.id_quote}{identifier.replace(self.id_quote, self.id_quote+self.id_quote)}{self.id_quote}'
    
    def quote_string(self, value: Any) -> str:
        """
        Quote and escape a string value.
        
        Args:
            value: Value to quote and escape
            
        Returns:
            Quoted and escaped string
        """
        if value is None:
            return self.null_value
        
        if isinstance(value, bool):
            if self.dialect == "postgresql":
                return str(value).lower()
            elif self.dialect == "mysql":
                return "1" if value else "0"
            else:  # sqlite
                return "1" if value else "0"
        
        if isinstance(value, (int, float)):
            return str(value)
        
        # Handle datetime
        if isinstance(value, datetime):
            if self.dialect == "postgresql":
                return f"'{value.isoformat()}'"
            elif self.dialect == "mysql":
                return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
            else:  # sqlite
                return f"'{value.isoformat()}'"
        
        # Handle other types
        return f"{self.string_quote}{self.string_escape(str(value))}{self.string_quote}"
    
    def generate_document_insert(self, document_data: Dict[str, Any]) -> str:
        """
        Generate SQL INSERT statement for document metadata.
        
        Args:
            document_data: Document data
            
        Returns:
            SQL INSERT statement for document metadata
        """
        metadata = document_data.get("metadata", {})
        
        # Ensure document_id exists
        if "document_id" not in metadata:
            metadata["document_id"] = str(uuid.uuid4())
        
        # Extract relevant fields
        fields = [
            "document_id",
            "title",
            "author",
            "created_date",
            "last_modified_date",
            "source_file",
            "source_type",
            "page_count"
        ]
        
        # Include fields that exist in metadata
        columns = []
        values = []
        
        for field in fields:
            if field in metadata:
                columns.append(self.escape_identifier(field))
                values.append(self.quote_string(metadata[field]))
        
        # Generate INSERT statement
        columns_str = ", ".join(columns)
        values_str = ", ".join(values)
        
        document_table = self.escape_identifier("documents")
        insert_stmt = f"INSERT INTO {document_table} ({columns_str}) VALUES ({values_str});"
        
        return insert_stmt
    
    def generate_content_inserts(self, document_data: Dict[str, Any]) -> List[str]:
        """
        Generate SQL INSERT statements for document content.
        
        Args:
            document_data: Document data
            
        Returns:
            List of SQL INSERT statements for document content
        """
        metadata = document_data.get("metadata", {})
        content = document_data.get("content", [])
        
        # Ensure document_id exists
        document_id = metadata.get("document_id", str(uuid.uuid4()))
        
        # Generate INSERT statements for content
        insert_statements = []
        content_table = self.escape_identifier("document_content")
        
        for i, item in enumerate(content):
            # Skip furniture items (will be handled separately)
            if item.get("type") == "furniture":
                continue
                
            item_type = item.get("type", "unknown")
            text = item.get("text", "")
            seq_num = item.get("seq_num", i + 1)
            page_num = item.get("page_num")
            
            # Basic required fields
            columns = [
                self.escape_identifier("document_id"),
                self.escape_identifier("seq_num"),
                self.escape_identifier("content_type"),
                self.escape_identifier("content_text")
            ]
            
            values = [
                self.quote_string(document_id),
                self.quote_string(seq_num),
                self.quote_string(item_type),
                self.quote_string(text)
            ]
            
            # Optional fields
            if page_num is not None:
                columns.append(self.escape_identifier("page_num"))
                values.append(self.quote_string(page_num))
            
            # Add any additional fields that might be useful
            for field in ["heading_level", "list_type", "list_marker", "is_bold", "is_italic"]:
                if field in item:
                    columns.append(self.escape_identifier(field))
                    values.append(self.quote_string(item[field]))
            
            # Generate INSERT statement
            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            
            insert_stmt = f"INSERT INTO {content_table} ({columns_str}) VALUES ({values_str});"
            insert_statements.append(insert_stmt)
        
        return insert_statements
    
    def generate_furniture_inserts(self, document_data: Dict[str, Any]) -> List[str]:
        """
        Generate SQL INSERT statements for document furniture.
        
        Args:
            document_data: Document data
            
        Returns:
            List of SQL INSERT statements for document furniture
        """
        metadata = document_data.get("metadata", {})
        content = document_data.get("content", [])
        
        # Ensure document_id exists
        document_id = metadata.get("document_id", str(uuid.uuid4()))
        
        # Generate INSERT statements for furniture items
        insert_statements = []
        furniture_table = self.escape_identifier("document_furniture")
        
        for i, item in enumerate(content):
            # Only process furniture items
            if item.get("type") != "furniture":
                continue
                
            furniture_type = item.get("furniture_type", "unknown")
            seq_num = item.get("seq_num", i + 1)
            page_num = item.get("page_num")
            
            # Basic required fields
            columns = [
                self.escape_identifier("document_id"),
                self.escape_identifier("seq_num"),
                self.escape_identifier("furniture_type")
            ]
            
            values = [
                self.quote_string(document_id),
                self.quote_string(seq_num),
                self.quote_string(furniture_type)
            ]
            
            # Optional fields
            if page_num is not None:
                columns.append(self.escape_identifier("page_num"))
                values.append(self.quote_string(page_num))
            
            # Handle different furniture types
            if furniture_type == "image":
                for field in ["image_url", "alt_text", "caption"]:
                    if field in item:
                        columns.append(self.escape_identifier(field))
                        values.append(self.quote_string(item[field]))
            elif furniture_type == "table":
                if "table_data" in item:
                    # Store table data as a JSON string
                    table_data_json = json.dumps(item["table_data"])
                    columns.append(self.escape_identifier("table_data"))
                    values.append(self.quote_string(table_data_json))
                
                if "caption" in item:
                    columns.append(self.escape_identifier("caption"))
                    values.append(self.quote_string(item["caption"]))
            
            # Generate INSERT statement
            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            
            insert_stmt = f"INSERT INTO {furniture_table} ({columns_str}) VALUES ({values_str});"
            insert_statements.append(insert_stmt)
        
        return insert_statements
    
    def generate_sql_inserts(self, document_data: Dict[str, Any]) -> str:
        """
        Generate SQL INSERT statements for the entire document.
        
        Args:
            document_data: Document data
            
        Returns:
            Complete SQL INSERT statements as a string
        """
        statements = []
        
        # Add header comment with metadata
        metadata = document_data.get("metadata", {})
        title = metadata.get("title", "Untitled Document")
        doc_id = metadata.get("document_id", str(uuid.uuid4()))
        
        header = [
            f"-- SQL INSERT statements for document: {title}",
            f"-- Document ID: {doc_id}",
            f"-- Generated on: {datetime.now().isoformat()}",
            f"-- SQL Dialect: {self.dialect}",
            ""
        ]
        
        # Add document metadata insert
        statements.append(self.generate_document_insert(document_data))
        
        # Add content inserts
        content_inserts = self.generate_content_inserts(document_data)
        if content_inserts:
            statements.append("")
            statements.append("-- Document content inserts")
            statements.extend(content_inserts)
        
        # Add furniture inserts
        furniture_inserts = self.generate_furniture_inserts(document_data)
        if furniture_inserts:
            statements.append("")
            statements.append("-- Document furniture inserts")
            statements.extend(furniture_inserts)
        
        # Combine all statements
        all_statements = "\n".join(header + statements)
        
        return all_statements
    
    def save_sql_inserts(self, document_data: Dict[str, Any], output_dir: str, filename: str = None) -> str:
        """
        Save SQL INSERT statements to a file.
        
        Args:
            document_data: Document data
            output_dir: Directory to save the SQL file
            filename: Optional custom filename
            
        Returns:
            Path to the saved SQL file
        """
        # Generate SQL INSERT statements
        sql_inserts = self.generate_sql_inserts(document_data)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            metadata = document_data.get("metadata", {})
            doc_id = metadata.get("document_id", str(uuid.uuid4()))
            safe_id = re.sub(r'[^\w]', '_', doc_id)
            filename = f"{safe_id}_{self.dialect}.sql"
        
        # Ensure filename has .sql extension
        if not filename.endswith(".sql"):
            filename += ".sql"
        
        # Save to file
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sql_inserts)
        
        logger.info(f"Saved SQL INSERT statements to {output_path}")
        
        return output_path 
"""
Mock Docling Module

This module provides mock classes and functions for testing purposes to simulate
the behavior of the docling library without requiring its installation.
"""

import json
from pathlib import Path


# Base models
class InputFormat:
    """Mock enum for input formats."""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"


class BoundingBox:
    """Mock bounding box class."""
    def __init__(self, l=0, t=0, r=100, b=100):
        self.l = l  # left
        self.t = t  # top
        self.r = r  # right
        self.b = b  # bottom
        self.width = r - l
        self.height = b - t


# Pipeline options
class PdfPipelineOptions:
    """Mock PDF pipeline options class."""
    def __init__(self):
        self.images_scale = 2.0
        self.generate_page_images = True
        self.generate_picture_images = True
        self.allow_external_plugins = True
        self.do_picture_description = True
        self.do_table_structure = True


# Document converter
class PdfFormatOption:
    """Mock PDF format option class."""
    def __init__(self, pipeline_options=None):
        self.pipeline_options = pipeline_options or PdfPipelineOptions()


class ConversionResult:
    """Mock conversion result class."""
    def __init__(self, document, status="success"):
        self.document = document
        self.status = status
        self.input = MockInput(Path("sample.pdf"))


class DocumentConverter:
    """Mock document converter class."""
    def __init__(self, format_options=None):
        self.format_options = format_options or {}

    def convert(self, path):
        """Mock convert method."""
        # Create a mock document based on the path
        doc = MockDocument(path)
        return ConversionResult(doc, status="success")


# Mock document classes
class MockPicture:
    """Mock picture class."""
    def __init__(self, index, data=b"mock image data"):
        self.self_ref = f"#/pictures/{index}"
        self.bounds = BoundingBox()
        self.description = f"This is a mock picture {index}"
        self.metadata = {"format": "image/png"}
        self.image_data = data
        self.image_path = None


class MockPage:
    """Mock page class."""
    def __init__(self, page_no):
        self.page_no = page_no
        self.pictures = []


class MockDocument:
    """Mock document class."""
    def __init__(self, path):
        self.path = path
        self.name = Path(path).stem
        self.pages = {0: MockPage(1), 1: MockPage(2)}
        self.pictures = [MockPicture(0), MockPicture(1)]
        for i, page in enumerate(self.pages.values()):
            # Add pictures to pages
            if i < len(self.pictures):
                page.pictures.append(self.pictures[i])
    
    def export_to_dict(self):
        """Export document to dictionary."""
        return {
            "name": self.name,
            "pages": [{"page_no": page.page_no} for page in self.pages.values()],
            "pictures": [
                {
                    "self_ref": pic.self_ref,
                    "bounds": {
                        "l": pic.bounds.l,
                        "t": pic.bounds.t,
                        "r": pic.bounds.r,
                        "b": pic.bounds.b,
                        "width": pic.bounds.width,
                        "height": pic.bounds.height
                    },
                    "description": pic.description
                }
                for pic in self.pictures
            ]
        }
    
    def export_to_markdown(self):
        """Mock export to markdown method."""
        return f"# {self.name}\n\nMock document content"


class MockInput:
    """Mock input class."""
    def __init__(self, file_path):
        self.file = file_path 
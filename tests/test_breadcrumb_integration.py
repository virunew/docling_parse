import unittest
import sys
import os
import json
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.json_metadata_fixer import fix_metadata, determine_header_level, get_element_position
from src.parse_helper import save_output


class TestBreadcrumbIntegration(unittest.TestCase):
    """Test the hierarchical breadcrumb generation in an integration scenario."""
    
    def setUp(self):
        """Set up temporary test directory."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir)
    
    def test_hierarchical_breadcrumb_generation(self):
        """Test that breadcrumbs include the full hierarchy in a realistic document."""
        # Create a test document structure with headers at different levels
        document_data = {
            "texts": [
                {"text": "Main Document Title", "label": "section_header", "font_size": 20},
                {"text": "Introduction paragraph", "label": "paragraph"},
                {"text": "Chapter 1", "label": "section_header", "font_size": 18},
                {"text": "Chapter 1 content", "label": "paragraph"},
                {"text": "Section 1.1", "label": "section_header", "font_size": 16},
                {"text": "Section 1.1 content", "label": "paragraph"},
                {"text": "Subsection 1.1.1", "label": "section_header", "font_size": 14},
                {"text": "Subsection 1.1.1 content", "label": "paragraph"}
            ],
            "element_map": {
                "#/texts/0": {"self_ref": "#/texts/0", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/1": {"self_ref": "#/texts/1", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/2": {"self_ref": "#/texts/2", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/3": {"self_ref": "#/texts/3", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/4": {"self_ref": "#/texts/4", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/5": {"self_ref": "#/texts/5", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/6": {"self_ref": "#/texts/6", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/7": {"self_ref": "#/texts/7", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}, 
                                                  "special_field1": "{'breadcrumb': ''}"}}
            },
            "body": {
                "elements": [
                    {"$ref": "#/texts/0"},
                    {"$ref": "#/texts/1"},
                    {"$ref": "#/texts/2"},
                    {"$ref": "#/texts/3"},
                    {"$ref": "#/texts/4"},
                    {"$ref": "#/texts/5"},
                    {"$ref": "#/texts/6"},
                    {"$ref": "#/texts/7"}
                ]
            },
            "source_metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf"
            }
        }
        
        # Save the test document data to a temporary file
        test_file = os.path.join(self.test_dir, "test_document.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(document_data, f)
        
        # Debug: Print header information before fixing metadata
        print("\nHeader information before processing:")
        for i, text in enumerate(document_data["texts"]):
            if text.get("label") == "section_header":
                level = determine_header_level(text)
                print(f"  #{i}: {text.get('text')} (font_size: {text.get('font_size')}, level: {level})")
        
        # Apply metadata fixes, including breadcrumb generation
        fixed_data = fix_metadata(document_data, self.test_dir)
        
        # Debug: Print all breadcrumbs generated
        print("\nBreadcrumbs generated:")
        for elem_id, element in fixed_data["element_map"].items():
            if "extracted_metadata" in element and "special_field2" in element["extracted_metadata"]:
                breadcrumb = element["extracted_metadata"]["special_field2"]
                print(f"  {elem_id}: {breadcrumb}")
        
        # Debug: Extract the positions for the elements
        print("\nElement positions:")
        for elem_id, element in fixed_data["element_map"].items():
            position = get_element_position(element, fixed_data)
            print(f"  {elem_id}: position {position}")
        
        # Check breadcrumbs at different levels
        # Content at subsection level should have full hierarchy
        subsection_content = fixed_data["element_map"]["#/texts/7"]
        expected_subsection_breadcrumb = "Main Document Title > Chapter 1 > Section 1.1 > Subsection 1.1.1"
        actual_subsection_breadcrumb = subsection_content["extracted_metadata"]["special_field2"]
        
        print(f"\nSubsection Breadcrumb Test:")
        print(f"  Expected: '{expected_subsection_breadcrumb}'")
        print(f"  Actual: '{actual_subsection_breadcrumb}'")
        
        self.assertEqual(
            actual_subsection_breadcrumb,
            expected_subsection_breadcrumb,
            "Subsection content should have full hierarchy in breadcrumb"
        )
        
        # Content at section level
        section_content = fixed_data["element_map"]["#/texts/5"]
        expected_section_breadcrumb = "Main Document Title > Chapter 1 > Section 1.1"
        actual_section_breadcrumb = section_content["extracted_metadata"]["special_field2"]
        
        print(f"\nSection Breadcrumb Test:")
        print(f"  Expected: '{expected_section_breadcrumb}'")
        print(f"  Actual: '{actual_section_breadcrumb}'")
        
        self.assertEqual(
            actual_section_breadcrumb,
            expected_section_breadcrumb,
            "Section content should have hierarchy up to section level in breadcrumb"
        )
        
        # Content at chapter level
        chapter_content = fixed_data["element_map"]["#/texts/3"]
        expected_chapter_breadcrumb = "Main Document Title > Chapter 1"
        actual_chapter_breadcrumb = chapter_content["extracted_metadata"]["special_field2"]
        
        print(f"\nChapter Breadcrumb Test:")
        print(f"  Expected: '{expected_chapter_breadcrumb}'")
        print(f"  Actual: '{actual_chapter_breadcrumb}'")
        
        self.assertEqual(
            actual_chapter_breadcrumb,
            expected_chapter_breadcrumb,
            "Chapter content should have hierarchy up to chapter level in breadcrumb"
        )
        
        # Content after title
        intro_content = fixed_data["element_map"]["#/texts/1"]
        expected_intro_breadcrumb = "Main Document Title"
        actual_intro_breadcrumb = intro_content["extracted_metadata"]["special_field2"]
        
        print(f"\nIntro Breadcrumb Test:")
        print(f"  Expected: '{expected_intro_breadcrumb}'")
        print(f"  Actual: '{actual_intro_breadcrumb}'")
        
        self.assertEqual(
            actual_intro_breadcrumb,
            expected_intro_breadcrumb,
            "Introduction content should have just the title in breadcrumb"
        )


if __name__ == "__main__":
    unittest.main() 
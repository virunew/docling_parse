#!/usr/bin/env python3
"""
Debug script for breadcrumb generator
"""

from src.breadcrumb_generator import get_hierarchical_breadcrumb

def main():
    # Simple test case to debug
    sample_sequence = [
        {"id": "h1_1", "text": "Document Title", "metadata": {"type": "h1"}, "label": "section_header"},
        {"id": "p1", "text": "Paragraph 1", "metadata": {"type": "paragraph"}},
        {"id": "h2_1", "text": "Section 1", "metadata": {"type": "h2"}, "label": "section_header"},
        {"id": "p2", "text": "Paragraph 2", "metadata": {"type": "paragraph"}},
        {"id": "h3_1", "text": "Subsection 1.1", "metadata": {"type": "h3"}, "label": "section_header"},
        {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}},
    ]
    
    # Test a paragraph in subsection
    test_element = {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}}
    print("\n\nTesting breadcrumb for paragraph in subsection:")
    breadcrumb = get_hierarchical_breadcrumb(test_element, sample_sequence)
    
    # Expected result
    expected = "Document Title > Section 1 > Subsection 1.1"
    print(f"\nExpected: {expected}")
    print(f"Actual:   {breadcrumb}")
    print(f"Match:    {breadcrumb == expected}")

if __name__ == "__main__":
    main() 
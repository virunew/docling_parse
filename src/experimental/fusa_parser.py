import logging
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.utils.export import generate_multimodal_pages
import json

# Set up logging
logging.basicConfig(level=logging.INFO)

def main():
    #input_pdf_path = Path("/Users/tech9/work/nipl/ItemExtraction/docs/SBW_AI.pdf")  # Update with your PDF path    
    input_pdf_path = Path("/Users/tech9/work/nipl/ItemExtraction/Sample SBW/SBW_AI (2)-pages-4.pdf")  # Update with your PDF path
    output_dir = Path("output_pages4")  # Directory to save output files
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = 2.0  # Adjust image resolution if needed
    pipeline_options.generate_page_images = True  # Generate images for pages
    pipeline_options.generate_picture_images = True  # Generate images for pictures

    # Create a DocumentConverter instance
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Convert the PDF document
    conv_res = doc_converter.convert(input_pdf_path)

    # Save the document in various formats
    doc_filename = conv_res.input.file.stem
    conv_res.document.save_as_json(output_dir / f"{doc_filename}.json")
    conv_res.document.save_as_markdown(output_dir / f"{doc_filename}.md")

    # Export images and tables with references
    for page_no, page in conv_res.document.pages.items():
        page_image_filename = output_dir / f"{doc_filename}-page-{page_no}.png"
        with page_image_filename.open("wb") as fp:
            page.image.pil_image.save(fp, format="PNG")

    for table_ix, table in enumerate(conv_res.document.tables):
        table_df = table.export_to_dataframe()
        table_filename = output_dir / f"{doc_filename}-table-{table_ix + 1}.md"
        with table_filename.open("w") as fp:
            fp.write(table.export_to_markdown())

    # Generate multimodal pages for chunking
    rows = []
    for (
        content_text,
        content_md,
        content_dt,
        page_cells,
        page_segments,
        page,
    ) in generate_multimodal_pages(conv_res):
        rows.append({
            "document": conv_res.input.file.name,
            "page": page.page_no,
            "content_text": content_text,
            "content_md": content_md,
            "content_dt": content_dt,
            "cells": page_cells,
            "segments": page_segments,
        })

    # Save the chunked data
    chunked_output_filename = output_dir / f"{doc_filename}-chunks.json"
    with chunked_output_filename.open("w") as fp:
        json.dump(rows, fp, indent=4)

    logging.info(f"Document processed and saved in {output_dir}")

if __name__ == "__main__":
    main()

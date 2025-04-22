import logging

# Fix docling imports
import docling_fix
import os
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_pdf_to_markdown_with_images(pdf_path: str, output_dir: str, image_subdir: str = "images"):
    """
    Converts a PDF document to Markdown, preserving images.

    Args:
        pdf_path: Path to the input PDF file.
        output_dir: Directory where the Markdown file and images folder will be saved.
        image_subdir: Name of the subdirectory within output_dir to save images.
                      Defaults to "images". The Markdown file will reference images
                      using relative paths based on this subdirectory name.
    """
    pdf_file = Path(pdf_path)
    output_path = Path(output_dir)
    markdown_output_file = output_path / f"{pdf_file.stem}.md"
    image_output_folder = output_path / image_subdir

    # --- Input Validation ---
    if not pdf_file.is_file():
        logging.error(f"Input PDF not found: {pdf_path}")
        raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

    # --- Ensure Output Directory Exists ---
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured output directory exists: {output_path}")
    except OSError as e:
        logging.error(f"Could not create output directory {output_path}: {e}")
        raise

    # --- Configure PDF Pipeline Options ---
    # Key configuration:
    # - images_scale: Controls the resolution of extracted images and enables image generation.
    #   A value > 0 is needed to keep images. Scale 1.0 is 72 DPI, 2.0 is 144 DPI, etc.
    # - generate_picture_images: Ensures image data is generated specifically for PictureItem elements.
    # - image_folder=image_subdir: Specifies the *relative* path name that will be used
    #   in the markdown links and where `export_markdown` will save the actual image files.
    pdf_options = PdfPipelineOptions(
        images_scale=2.0, # Use scale to enable image extraction (e.g., 2.0 for higher res)
        generate_picture_images=True, # Ensure images are generated for picture elements
        image_folder=image_subdir  # This name is used for relative paths in Markdown
    )
    logging.info(f"Configured PDF pipeline options: images_scale=2.0, generate_picture_images=True, image_folder='{image_subdir}'")

    # --- Initialize Document Converter ---
    # Pass format-specific options during initialization
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)
        }
    )
    logging.info("Initialized DocumentConverter with PDF format options.")

    # --- Perform Conversion ---
    try:
        logging.info(f"Starting conversion for: {pdf_path}")
        # The converter processes the PDF and extracts content, including image data,
        # based on the options provided during initialization.
        # Use 'source' argument instead of 'file_path'. Input format is inferred or already set.
        result = converter.convert(
            source=str(pdf_file)
            # No need to pass input_format or pipeline_options here
        )
        docling_document = result.document
        logging.info(f"Successfully converted PDF to DoclingDocument.")

        # --- Export to Markdown ---
        logging.info(f"Exporting DoclingDocument to Markdown: {markdown_output_file}")
        # The export_markdown method will:
        # 1. Create the Markdown file.
        # 2. Create the image subdirectory (output_path / image_subdir) if it doesn't exist.
        # 3. Save the actual image files (extracted during conversion) into that subdirectory.
        # 4. Generate Markdown text, referencing images using relative paths
        #    like `![alt text](./{image_subdir}/image_name.png)`.
        docling_document.export_to_markdown(
           # No need to specify image folder again here, it uses the info
            # embedded during the conversion step via PdfPipelineOptions.
        )

        
        logging.info(f"Successfully exported Markdown and saved images to: {output_path}")

    except Exception as e:
        logging.error(f"An error occurred during conversion or export: {e}")
        raise # Re-raise the exception after logging

# --- Example Usage ---
if __name__ == "__main__":
    # --- Configuration ---
    # IMPORTANT: Replace with the actual path to your PDF file


    #INPUT_PDF = "/Users/tech9/work/nipl/ItemExtraction/docs/SBW_AI.pdf"
    INPUT_PDF = '/Users/tech9/work/nipl/ItemExtraction/Sample SBW/SBW_AI (2)-pages-4.pdf'
    # IMPORTANT: Replace with the desired output directory
    OUTPUT_DIRECTORY = "output_generated"
    # Optional: Change the name of the folder where images will be stored
    IMAGE_SUBFOLDER = "assets"

    # --- Basic Check ---
    if INPUT_PDF == "path/to/your/document.pdf":
        print("Please update the INPUT_PDF variable in the script with the actual path to your PDF.")
    else:
        try:
            convert_pdf_to_markdown_with_images(
                pdf_path=INPUT_PDF,
                output_dir=OUTPUT_DIRECTORY,
                image_subdir=IMAGE_SUBFOLDER
            )
            print("\nConversion complete!")
            print(f"Markdown file saved to: {Path(OUTPUT_DIRECTORY) / Path(INPUT_PDF).stem}.md")
            print(f"Images saved to: {Path(OUTPUT_DIRECTORY) / IMAGE_SUBFOLDER}")
        except FileNotFoundError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            logging.exception("Unexpected error details:") # Log stack trace for debugging

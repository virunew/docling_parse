import json
import logging
import os
# Fix docling imports
import logging
import time
from pathlib import Path

from dotenv import load_dotenv

# Replace the import for CustomChunker with BreadcrumbChunker
from final_approach.breadcrumb_chunker import BreadcrumbChunker
load_dotenv()

print("\n"+os.getenv('PYTHONPATH'))

from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
_log = logging.getLogger(__name__)

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
 

from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

IMAGE_RESOLUTION_SCALE = 2.0

def main():
    logging.basicConfig(level=logging.INFO)

    input_doc_path =  Path('/Users/tech9/work/nipl/ItemExtraction/SBW_AI sample page10-11.pdf')
    output_dir = Path("scratch/sample-page10-11")

    # Important: For operating with page images, we must keep them, otherwise the DocumentConverter
    # will destroy them for cleaning up memory.
    # This is done by setting PdfPipelineOptions.images_scale, which also defines the scale of images.
    # scale=1 correspond of a standard 72 DPI image
    # The PdfPipelineOptions.generate_* are the selectors for the document elements which will be enriched
    # with the image field
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True
    pipeline_options.do_ocr = False
    

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start_time = time.time()

    conv_res = doc_converter.convert(input_doc_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    doc_filename = conv_res.input.file.stem
    
    # --- Build Image Reference Map --- 
    image_ref_map: dict[str, str] = {}
    picture_counter = 0
    
    # First pass to save images and create the map
    for element, _level in conv_res.document.iterate_items():
        if isinstance(element, PictureItem):
            picture_counter += 1
            # Create relative path for the map
            relative_image_filename = f"{doc_filename}-picture-{picture_counter}.png"
            image_ref_map[element.self_ref] = relative_image_filename
            
            # Save the image to the output directory
            full_image_path = output_dir / relative_image_filename
            try:
                # Ensure the element has image data before saving
                img = element.get_image(conv_res.document)
                if img:
                     with full_image_path.open("wb") as fp:
                         img.save(fp, "PNG")
                else:
                     _log.warning(f"PictureItem {element.self_ref} has no image data to save.")
            except Exception as e:
                _log.error(f"Error saving image for {element.self_ref}: {e}")
        # We only need the map for PictureItems currently
        # elif isinstance(element, TableItem):
        #     # Table saving logic (if needed separately) could go here
        #     pass 

    # #Save page images
    # for page_no, page in conv_res.document.pages.items():
    #     page_no = page.page_no
    #     page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
    #     with page_image_filename.open("wb") as fp:
    #         page.image.pil_image.save(fp, format="PNG")

    # #Save images of figures and tables
    # table_counter = 0
    # for element, _level in conv_res.document.iterate_items():
    #     if isinstance(element, TableItem):
    #         table_counter += 1
    #         element_image_filename = (
    #             output_dir / f"{doc_filename}-table-{table_counter}.png"
    #         )
    #         with element_image_filename.open("wb") as fp:
    #             element.get_image(conv_res.document).save(fp, "PNG")

    # # Save markdown with embedded pictures
    # md_filename = output_dir / f"{doc_filename}-with-images.md"
    # conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.EMBEDDED)

    # Save markdown with externally referenced pictures
    # md_filename = output_dir / f"{doc_filename}-with-image-refs.md"
    # conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.REFERENCED)

    # # Save HTML with externally referenced pictures
    # html_filename = output_dir / f"{doc_filename}-with-image-refs.html"
    # conv_res.document.save_as_html(html_filename, image_mode=ImageRefMode.REFERENCED)

    # # Save YAML with externally referenced pictures
    # yaml_filename = output_dir / f"{doc_filename}-with-image-refs.yaml"
    # conv_res.document.save_as_yaml(yaml_filename, image_mode=ImageRefMode.REFERENCED)

    # # Save as element tree
    # tree_filename = output_dir / f"{doc_filename}-element-tree.txt"
    # str_tree = conv_res.document.export_to_element_tree()
    # with tree_filename.open("w") as fp:
    #     fp.write(str_tree)

    # export as dict
    # dict_filename = output_dir / f"{doc_filename}-dict.json"
    # exported_dict=conv_res.document.export_to_dict()
    # with dict_filename.open("w") as fp:
    #     json.dump(exported_dict, fp)

    end_time = time.time() - start_time
    _log.info(f"Document converted and artifacts saved in {end_time:.2f} seconds.")

    # --- Chunking --- 
    _log.info("Starting chunking process...")
    chunker = BreadcrumbChunker(merge_list_items=True) # merge_list_items might not be relevant now
    
    # Pass the document and the image map to the chunker
    chunks = chunker.chunk(conv_res.document, image_ref_map=image_ref_map)
    
    # Process and print chunks
    chunk_counter = 0
    for chunk in chunks:
        chunk_counter += 1
        #print(chunk) # Print the pydantic model representation
        print(chunk.model_dump_json()+'\n') # Print JSON representation
        
    _log.info(f"Chunking complete. Generated {chunk_counter} chunks.")

if __name__ == "__main__":
        main()
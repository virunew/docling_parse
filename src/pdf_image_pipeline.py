"""
PDF Image Pipeline Module

This module provides an integrated pipeline for extracting and saving images from
PDF documents processed through the docling document converter.

Classes:
    PDFImagePipeline: Coordinates the extraction and saving of images from PDFs.
"""

# Fix docling imports
import docling_fix

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Import the necessary components
from pdf_image_extractor import PDFImageExtractor
# Assuming there's an ImageSaver module that we'll need to implement

# Configure logging
logger = logging.getLogger(__name__)

class PDFImagePipeline:
    """
    Provides a complete pipeline for extracting and saving images from PDF documents.
    
    This class coordinates the image extraction and saving process, handling the
    interaction between the PDFImageExtractor and ImageSaver components.
    """
    
    def __init__(
        self, 
        output_dir: str,
        metadata_dir: Optional[str] = None,
        image_min_size: int = 100,
        analyze_content: bool = True
    ):
        """
        Initialize the PDF image pipeline.
        
        Args:
            output_dir: Directory where extracted images will be saved
            metadata_dir: Optional directory for metadata files (defaults to output_dir)
            image_min_size: Minimum image dimension (width/height) to extract
            analyze_content: Whether to analyze text content around images
        """
        self.output_dir = Path(output_dir)
        self.metadata_dir = Path(metadata_dir) if metadata_dir else self.output_dir
        self.image_min_size = image_min_size
        self.analyze_content = analyze_content
        
        # Create the image saver
        self.image_saver = ImageSaver(str(self.output_dir), str(self.metadata_dir))
        
        logger.info(f"Initialized PDFImagePipeline with output directory: {self.output_dir}")
        logger.debug(f"Pipeline settings: min_size={image_min_size}, analyze_content={analyze_content}")
    
    def process_document(
        self, 
        docling_document: Any,
        element_map: Optional[Dict] = None,
        document_id: Optional[str] = None,
        save_images: bool = True
    ) -> Dict[str, Any]:
        """
        Process a docling document to extract and optionally save images.
        
        Args:
            docling_document: A docling Document object
            element_map: Optional element map for content relationships
            document_id: Optional document identifier
            save_images: Whether to save the images to disk
            
        Returns:
            Dictionary with extraction and saving results
        """
        logger.info(f"Processing document: {getattr(docling_document, 'name', 'Unnamed document')}")
        
        result = {
            "extraction": None,
            "saving": None
        }
        
        try:
            # 1. Extract images from the document
            extractor = PDFImageExtractor(
                docling_document, 
                element_map,
                min_size=self.image_min_size,
                analyze_content=self.analyze_content
            )
            extracted_data = extractor.extract_images()
            result["extraction"] = extracted_data
            
            # 2. Save the images if requested
            if save_images and "images" in extracted_data and extracted_data["images"]:
                logger.info(f"Saving {len(extracted_data['images'])} extracted images")
                saving_result = self.image_saver.save_images(extracted_data, document_id)
                result["saving"] = saving_result
            elif save_images:
                logger.warning("No images to save")
                result["saving"] = {"error": "No images extracted", "saved_count": 0}
            else:
                logger.info("Image saving skipped as requested")
                
            return result
            
        except Exception as e:
            logger.error(f"Error in PDF image pipeline: {str(e)}")
            result["error"] = str(e)
            return result
    
    def batch_process(
        self, 
        documents: List[Any],
        element_maps: Optional[List[Dict]] = None,
        document_ids: Optional[List[str]] = None,
        save_intermediate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch mode.
        
        Args:
            documents: List of docling Document objects
            element_maps: Optional list of element maps (must match documents length if provided)
            document_ids: Optional list of document IDs (must match documents length if provided)
            save_intermediate: Whether to save results after each document
            
        Returns:
            List of result dictionaries, one per document
        """
        results = []
        
        for i, doc in enumerate(documents):
            try:
                # Get the corresponding element map and ID if provided
                element_map = element_maps[i] if element_maps and i < len(element_maps) else None
                doc_id = document_ids[i] if document_ids and i < len(document_ids) else None
                
                # Process the document
                logger.info(f"Processing document {i+1}/{len(documents)}")
                result = self.process_document(doc, element_map, doc_id)
                results.append(result)
                
                # Save intermediate results if requested
                if save_intermediate:
                    self._save_intermediate_result(result, i)
                    
            except Exception as e:
                logger.error(f"Error processing document {i+1}: {str(e)}")
                results.append({"error": str(e)})
        
        # Save summary of batch processing
        self._save_batch_summary(results)
        
        return results
    
    def _save_intermediate_result(self, result: Dict[str, Any], index: int) -> None:
        """
        Save intermediate processing result to disk.
        
        Args:
            result: The processing result dictionary
            index: The index of the document in the batch
        """
        try:
            # Create directory for intermediate results if it doesn't exist
            intermediate_dir = self.output_dir / "intermediate"
            intermediate_dir.mkdir(exist_ok=True)
            
            # Save the result as JSON
            result_file = intermediate_dir / f"document_{index}_result.json"
            
            # Clone the result to avoid modifying the original
            result_copy = json.loads(json.dumps(result))
            
            # Remove large binary data to keep the file size manageable
            if "extraction" in result_copy and "images" in result_copy["extraction"]:
                for img in result_copy["extraction"]["images"]:
                    if "data" in img:
                        img["data"] = "... [data URI removed to save space] ..."
            
            with open(result_file, 'w') as f:
                json.dump(result_copy, f, indent=2)
                
            logger.debug(f"Saved intermediate result to {result_file}")
            
        except Exception as e:
            logger.error(f"Error saving intermediate result: {str(e)}")
    
    def _save_batch_summary(self, results: List[Dict[str, Any]]) -> None:
        """
        Save a summary of batch processing results.
        
        Args:
            results: List of all processing results
        """
        try:
            # Count successes and failures
            total = len(results)
            extraction_success = sum(1 for r in results if r.get("extraction") and not r.get("extraction", {}).get("error"))
            saving_success = sum(1 for r in results if r.get("saving") and r.get("saving", {}).get("saved_count", 0) > 0)
            
            # Calculate total images
            total_extracted = sum(len(r.get("extraction", {}).get("images", [])) for r in results)
            total_saved = sum(r.get("saving", {}).get("saved_count", 0) for r in results)
            
            # Create summary
            summary = {
                "total_documents": total,
                "extraction_success": extraction_success,
                "saving_success": saving_success,
                "total_extracted_images": total_extracted,
                "total_saved_images": total_saved,
                "success_rate": f"{(saving_success/total)*100:.1f}%" if total > 0 else "0%",
                "documents": [
                    {
                        "document_name": r.get("extraction", {}).get("document_name", f"Document {i}"),
                        "images_extracted": len(r.get("extraction", {}).get("images", [])),
                        "images_saved": r.get("saving", {}).get("saved_count", 0),
                        "has_error": bool(r.get("error") or r.get("extraction", {}).get("error") or r.get("saving", {}).get("error"))
                    } for i, r in enumerate(results)
                ]
            }
            
            # Save to file
            summary_file = self.output_dir / "batch_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
            logger.info(f"Batch processing complete: {summary['total_saved_images']} images saved from {total} documents")
            logger.info(f"Batch summary saved to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error saving batch summary: {str(e)}")

# Example usage when run directly
if __name__ == "__main__":
    import sys
    from docling.convert import DocumentConverter
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 3:
        print("Usage: python pdf_image_pipeline.py <pdf_file> <output_directory>")
        sys.exit(1)
    
    try:
        # Get parameters
        pdf_path = sys.argv[1]
        output_dir = sys.argv[2]
        
        # Convert the PDF document using docling
        converter = DocumentConverter()
        document = converter.convert_file(pdf_path)
        
        # Create and run the pipeline
        pipeline = PDFImagePipeline(output_dir)
        result = pipeline.process_document(document)
        
        # Print summary
        if "saving" in result and result["saving"]:
            saved = result["saving"]["saved_count"]
            total = result["saving"]["total_count"]
            print(f"Processed {pdf_path}")
            print(f"Extracted and saved {saved} of {total} images")
            print(f"Results saved to: {output_dir}")
        else:
            print("No images were extracted or saved")
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1) 
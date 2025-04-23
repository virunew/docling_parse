import json
import os
import logging
from format_standardized_output import save_standardized_output

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OutputFormatter:
    def __init__(self, output_configuration, output_dir="output_main"):
        """
        Initialize the OutputFormatter with configuration settings
        
        Args:
            output_configuration (dict): Configuration for output format
            output_dir (str): Directory where output will be saved
        """
        self.output_config = output_configuration
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"OutputFormatter initialized with config: {output_configuration}")
        logger.info(f"Output directory: {self.output_dir}")
        
    def save_formatted_output(self, document_data, base_filename):
        """
        Save the formatted output according to the configuration
        
        Args:
            document_data (dict): The document data from the raw output
            base_filename (str): Base filename for output
            
        Returns:
            dict: Paths to the saved output files
        """
        output_files = {}
        
        # Generate standardized JSON output using format_standardized_output module
        if self.output_config.get("json", True):
            standardized_output_path = os.path.join(self.output_dir, f"{base_filename}_standardized.json")
            output_files["json"] = save_standardized_output(document_data, standardized_output_path)
            logger.info(f"Saved standardized JSON output to: {output_files['json']}")
        
        # Generate CSV output if configured
        if self.output_config.get("csv", False):
            csv_path = self._generate_csv(document_data, base_filename)
            output_files["csv"] = csv_path
            
        # Generate text output if configured
        if self.output_config.get("text", False):
            text_path = self._generate_text(document_data, base_filename)
            output_files["text"] = text_path
            
        return output_files
    
    def _generate_csv(self, document_data, base_filename):
        """
        Generate CSV output from document data
        
        Args:
            document_data (dict): The document data
            base_filename (str): Base filename for output
            
        Returns:
            str: Path to the generated CSV file
        """
        import csv
        
        output_path = os.path.join(self.output_dir, f"{base_filename}.csv")
        
        try:
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                writer.writerow(['Type', 'Content', 'Page', 'ID'])
                
                # Write text content
                if "content" in document_data and "paragraphs" in document_data["content"]:
                    for item in document_data["content"]["paragraphs"]:
                        writer.writerow([
                            "text",
                            item.get("text", ""),
                            item.get("page_number", ""),
                            item.get("id", "")
                        ])
                
                # Write image content
                if "content" in document_data and "pictures" in document_data["content"]:
                    for item in document_data["content"]["pictures"]:
                        writer.writerow([
                            "image",
                            item.get("caption", ""),
                            item.get("page_number", ""),
                            item.get("id", "")
                        ])
                        
            logger.info(f"Generated CSV output at: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating CSV: {str(e)}")
            return None
    
    def _generate_text(self, document_data, base_filename):
        """
        Generate simple text output from document data
        
        Args:
            document_data (dict): The document data
            base_filename (str): Base filename for output
            
        Returns:
            str: Path to the generated text file
        """
        output_path = os.path.join(self.output_dir, f"{base_filename}.txt")
        
        try:
            with open(output_path, 'w') as f:
                f.write(f"Document: {base_filename}\n\n")
                
                # Write metadata if available
                if "metadata" in document_data:
                    f.write("=== Metadata ===\n")
                    for key, value in document_data["metadata"].items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")
                
                # Write text content
                if "content" in document_data and "paragraphs" in document_data["content"]:
                    f.write("=== Text Content ===\n")
                    for item in document_data["content"]["paragraphs"]:
                        page = item.get("page_number", "")
                        text = item.get("text", "")
                        f.write(f"[Page {page}] {text}\n\n")
                
                # Write image captions
                if "content" in document_data and "pictures" in document_data["content"]:
                    f.write("=== Images ===\n")
                    for item in document_data["content"]["pictures"]:
                        page = item.get("page_number", "")
                        caption = item.get("caption", "No caption")
                        f.write(f"[Page {page}] Image: {caption}\n\n")
                        
            logger.info(f"Generated text output at: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating text output: {str(e)}")
            return None 
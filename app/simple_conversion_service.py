import os
import shutil
from pathlib import Path
import magic
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ConversionService:
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
    def convert_document(self, input_path: str, output_format: str) -> Dict[str, Any]:
        """
        Simple conversion service - mainly handles text extraction
        """
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                return {
                    "success": False,
                    "error": f"Input file not found: {input_path}"
                }
            
            # For now, only support text extraction from existing text files
            if output_format == "text" or output_format == "txt":
                return self.extract_text_file(input_path)
            else:
                return {
                    "success": False,
                    "error": f"Format {output_format} not supported in simplified version"
                }
                
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_text(self, file_path: str) -> str:
        """Extract text content from file"""
        try:
            file_path = Path(file_path)
            
            # Handle different file types
            if file_path.suffix.lower() in ['.txt', '.md', '.csv']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            else:
                # For other formats, try to read as text
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except:
                    return f"Could not extract text from {file_path.name}"
                    
        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            return f"Error extracting text: {str(e)}"
    
    def extract_text_file(self, input_path: str) -> Dict[str, Any]:
        """Handle text file conversion"""
        try:
            content = self.extract_text(input_path)
            
            # Create output file in conversions directory
            conversions_dir = self.storage_path / "conversions"
            conversions_dir.mkdir(exist_ok=True)
            
            input_file = Path(input_path)
            output_filename = f"{input_file.stem}_converted.txt"
            output_path = conversions_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "output_path": str(output_path),
                "file_size": output_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Text conversion error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
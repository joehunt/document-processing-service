"""
Document Conversion Service

This module provides document format conversion capabilities using LibreOffice
and handles text extraction from various document formats including PDF, Word,
Excel, PowerPoint, and text files.

Dependencies:
- LibreOffice (headless mode) for document conversion
- python-magic for MIME type detection
- Various Python libraries for specific format handling (PyPDF2, python-docx, pandas)

Author: Generated with Claude Code
"""

import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import magic
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ConversionService:
    """
    Document conversion service that handles multiple document formats.
    
    This service provides two main functions:
    1. Document format conversion (e.g., PDF to text, Word to HTML)
    2. Text extraction from documents for AI processing
    
    Supported formats:
    - Input: PDF, DOCX, DOC, XLSX, XLS, PPT, PPTX, TXT, RTF, ODT, ODS, ODP
    - Output: PDF, TXT, CSV, HTML
    
    The service uses LibreOffice in headless mode for conversions and
    specialized libraries for direct text extraction when possible.
    """
    def __init__(self, storage_path: str = "/app/storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
    def convert_document(self, input_path: str, output_format: str) -> Dict[str, Any]:
        """
        Convert document to specified format using LibreOffice
        
        Args:
            input_path: Path to input document
            output_format: Target format (pdf, txt, csv, html)
            
        Returns:
            Dict with conversion results
        """
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Create temporary directory for conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Determine LibreOffice conversion parameters
                if output_format == "pdf":
                    filter_name = "writer_pdf_Export"
                    extension = ".pdf"
                elif output_format == "txt":
                    filter_name = "Text (encoded)"
                    extension = ".txt"
                elif output_format == "csv":
                    filter_name = "Text - txt - csv (StarCalc)"
                    extension = ".csv"
                elif output_format == "html":
                    filter_name = "HTML (StarWriter)"
                    extension = ".html"
                else:
                    raise ValueError(f"Unsupported output format: {output_format}")
                
                # Run LibreOffice conversion
                cmd = [
                    "libreoffice",
                    "--headless",
                    "--convert-to", output_format,
                    "--outdir", str(temp_path),
                    str(input_file)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
                
                # Find the converted file
                converted_files = list(temp_path.glob(f"*{extension}"))
                if not converted_files:
                    raise RuntimeError("No converted file found")
                
                converted_file = converted_files[0]
                
                # Move to permanent storage
                output_filename = f"{input_file.stem}_{output_format}{extension}"
                output_path = self.storage_path / "conversions" / output_filename
                output_path.parent.mkdir(exist_ok=True)
                
                shutil.move(str(converted_file), str(output_path))
                
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "file_size": output_path.stat().st_size,
                    "format": output_format
                }
                
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "format": output_format
            }
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from various document formats"""
        try:
            file_type = magic.from_file(file_path, mime=True)
            
            if file_type == "application/pdf":
                return self._extract_pdf_text(file_path)
            elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               "application/msword"]:
                return self._extract_docx_text(file_path)
            elif file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               "application/vnd.ms-excel"]:
                return self._extract_excel_text(file_path)
            elif file_type in ["application/vnd.openxmlformats-officedocument.presentationml.presentation",
                               "application/vnd.ms-powerpoint"]:
                return self._extract_powerpoint_text(file_path)
            elif file_type.startswith("text/"):
                return self._safe_read_text(file_path)
            else:
                # Fallback: convert to text using LibreOffice
                result = self.convert_document(file_path, "txt")
                if result["success"]:
                    return self._safe_read_text(result["output_path"])
                else:
                    raise RuntimeError(f"Could not extract text: {result['error']}")
                    
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return ""
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2"""
        try:
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                # Try older pypdf2 import
                from pypdf2 import PdfFileReader as PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            
            # Handle both new and old PyPDF2 API
            if hasattr(reader, 'pages'):
                # New API
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            else:
                # Old API
                for i in range(reader.getNumPages()):
                    page = reader.getPage(i)
                    text += page.extractText() + "\n"
            return text
        except ImportError:
            raise RuntimeError("PyPDF2/pypdf2 not available for PDF text extraction")
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            raise RuntimeError("python-docx not available for DOCX text extraction")
    
    def _extract_excel_text(self, file_path: str) -> str:
        """Extract text from Excel files"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_string()
        except ImportError:
            raise RuntimeError("pandas/openpyxl not available for Excel text extraction")
    
    def _extract_powerpoint_text(self, file_path: str) -> str:
        """Extract text from PowerPoint files using LibreOffice conversion"""
        try:
            # Convert to text using LibreOffice
            result = self.convert_document(file_path, "txt")
            if result["success"]:
                return self._safe_read_text(result["output_path"])
            else:
                raise RuntimeError(f"PowerPoint conversion failed: {result['error']}")
        except Exception as e:
            logger.error(f"PowerPoint text extraction failed: {str(e)}")
            return f"Error extracting PowerPoint text: {str(e)}"
    
    def _safe_read_text(self, file_path: str) -> str:
        """Safely read text from file with fallback encodings"""
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # If all encodings fail, read as binary and decode with errors ignored
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return f"Error reading file: {str(e)}"
"""
PDF Processing utilities for Royal Enfield Knowledge Base
Handles PDF text extraction, metadata extraction, and content preprocessing
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import PyPDF2

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    pdfplumber = None

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Handles PDF text extraction and preprocessing
    """
    
    def __init__(self):
        """Initialize PDF processor"""
        self.supported_formats = ['.pdf']
    
    def extract_text_from_pdf(self, file_path: str, method: str = 'auto') -> Dict[str, Any]:
        """
        Extract text from PDF using specified method
        
        Args:
            file_path: Path to the PDF file
            method: Extraction method ('pypdf2', 'pdfplumber', 'auto')
            
        Returns:
            Dict[str, Any]: Extraction result with text and metadata
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            if method == 'auto':
                # Try pdfplumber first, fallback to PyPDF2
                result = self._extract_with_pdfplumber(file_path)
                if not result['success'] or not result['text'].strip():
                    logger.warning("pdfplumber extraction failed or empty, trying PyPDF2")
                    result = self._extract_with_pypdf2(file_path)
            elif method == 'pdfplumber':
                result = self._extract_with_pdfplumber(file_path)
            elif method == 'pypdf2':
                result = self._extract_with_pypdf2(file_path)
            else:
                raise ValueError(f"Unsupported extraction method: {method}")
            
            if result['success']:
                # Post-process the extracted text
                result['text'] = self._clean_extracted_text(result['text'])
                result['word_count'] = len(result['text'].split())
                result['char_count'] = len(result['text'])
                
                logger.info(f"Successfully extracted {result['word_count']} words from PDF")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return {
                'success': False,
                'text': '',
                'pages': [],
                'metadata': {},
                'error': str(e)
            }
    
    def _extract_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text using pdfplumber (better for complex layouts)
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extraction result
        """
        if not PDFPLUMBER_AVAILABLE:
            return {
                'success': False,
                'text': '',
                'pages': [],
                'metadata': {},
                'error': 'pdfplumber not available'
            }
        
        try:
            pages_data = []
            full_text = ""
            
            with pdfplumber.open(file_path) as pdf:
                metadata = {
                    'total_pages': len(pdf.pages),
                    'extraction_method': 'pdfplumber'
                }
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            page_text = page_text.strip()
                            full_text += page_text + "\n\n"
                            
                            # Extract page-level metadata
                            page_info = {
                                'page_number': page_num,
                                'text': page_text,
                                'char_count': len(page_text),
                                'word_count': len(page_text.split()) if page_text else 0
                            }
                            
                            # Try to extract tables if present
                            tables = page.extract_tables()
                            if tables:
                                page_info['tables_count'] = len(tables)
                                # Convert tables to text
                                for table in tables:
                                    table_text = self._table_to_text(table)
                                    page_info['text'] += f"\n\nTable:\n{table_text}"
                            
                            pages_data.append(page_info)
                        else:
                            logger.warning(f"No text extracted from page {page_num}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                        continue
            
            return {
                'success': True,
                'text': full_text.strip(),
                'pages': pages_data,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return {
                'success': False,
                'text': '',
                'pages': [],
                'metadata': {},
                'error': str(e)
            }
    
    def _extract_with_pypdf2(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text using PyPDF2 (fallback method)
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extraction result
        """
        try:
            pages_data = []
            full_text = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata = {
                    'total_pages': len(pdf_reader.pages),
                    'extraction_method': 'pypdf2'
                }
                
                # Extract PDF metadata if available
                if pdf_reader.metadata:
                    metadata.update({
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', '')
                    })
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            page_text = page_text.strip()
                            full_text += page_text + "\n\n"
                            
                            page_info = {
                                'page_number': page_num,
                                'text': page_text,
                                'char_count': len(page_text),
                                'word_count': len(page_text.split()) if page_text else 0
                            }
                            pages_data.append(page_info)
                        else:
                            logger.warning(f"No text extracted from page {page_num}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                        continue
            
            return {
                'success': True,
                'text': full_text.strip(),
                'pages': pages_data,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return {
                'success': False,
                'text': '',
                'pages': [],
                'metadata': {},
                'error': str(e)
            }
    
    def _table_to_text(self, table: List[List[str]]) -> str:
        """
        Convert table data to readable text format
        
        Args:
            table: Table data as list of lists
            
        Returns:
            str: Formatted table text
        """
        if not table:
            return ""
        
        try:
            # Filter out None values and convert to strings
            cleaned_table = []
            for row in table:
                cleaned_row = [str(cell) if cell is not None else "" for cell in row]
                cleaned_table.append(cleaned_row)
            
            # Create simple text representation
            table_text = []
            for row in cleaned_table:
                row_text = " | ".join(row)
                table_text.append(row_text)
            
            return "\n".join(table_text)
            
        except Exception as e:
            logger.warning(f"Failed to convert table to text: {e}")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page breaks and form feeds
        text = re.sub(r'[\f\r]', '\n', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_sections(self, text: str, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract sections from the document based on headings and structure
        
        Args:
            text: Full document text
            pages_data: Page-by-page data
            
        Returns:
            List[Dict[str, Any]]: Identified sections
        """
        try:
            sections = []
            
            # Common section patterns for motorcycle manuals
            section_patterns = [
                r'^(CHAPTER\s+\d+.*?)$',
                r'^(\d+\.\s+[A-Z][A-Z\s]+)$',
                r'^([A-Z][A-Z\s]{10,})$',
                r'^(MAINTENANCE.*?)$',
                r'^(SPECIFICATIONS.*?)$',
                r'^(TROUBLESHOOTING.*?)$',
                r'^(SAFETY.*?)$',
                r'^(OPERATION.*?)$',
                r'^(ENGINE.*?)$',
                r'^(ELECTRICAL.*?)$',
                r'^(FUEL.*?)$',
                r'^(BRAKES.*?)$',
                r'^(TRANSMISSION.*?)$'
            ]
            
            lines = text.split('\n')
            current_section = None
            current_content = []
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check if line matches section pattern
                is_section_header = False
                for pattern in section_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        is_section_header = True
                        break
                
                if is_section_header:
                    # Save previous section if exists
                    if current_section and current_content:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content).strip(),
                            'start_line': sections[-1]['end_line'] + 1 if sections else 1,
                            'end_line': line_num
                        })
                    
                    # Start new section
                    current_section = line
                    current_content = []
                else:
                    # Add to current section content
                    if current_section:
                        current_content.append(line)
            
            # Add final section
            if current_section and current_content:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content).strip(),
                    'start_line': sections[-1]['end_line'] + 1 if sections else 1,
                    'end_line': len(lines)
                })
            
            # If no sections found, create a single section
            if not sections:
                sections.append({
                    'title': 'Complete Document',
                    'content': text,
                    'start_line': 1,
                    'end_line': len(lines)
                })
            
            logger.info(f"Identified {len(sections)} sections in document")
            return sections
            
        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
            return [{
                'title': 'Complete Document',
                'content': text,
                'start_line': 1,
                'end_line': len(text.split('\n'))
            }]
    
    def validate_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Validate PDF file and check if it's processable
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: Validation result
        """
        try:
            validation_result = {
                'valid': False,
                'readable': False,
                'has_text': False,
                'page_count': 0,
                'file_size': 0,
                'errors': []
            }
            
            # Check file existence and size
            pdf_path = Path(file_path)
            if not pdf_path.exists():
                validation_result['errors'].append("File does not exist")
                return validation_result
            
            validation_result['file_size'] = pdf_path.stat().st_size
            
            # Try to open with PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    validation_result['page_count'] = len(pdf_reader.pages)
                    validation_result['readable'] = True
                    
                    # Check if PDF has extractable text
                    sample_text = ""
                    for i, page in enumerate(pdf_reader.pages[:3]):  # Check first 3 pages
                        try:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                sample_text += page_text
                                break
                        except:
                            continue
                    
                    if sample_text.strip():
                        validation_result['has_text'] = True
                        validation_result['valid'] = True
                    else:
                        validation_result['errors'].append("PDF appears to contain no extractable text")
                        
            except Exception as e:
                validation_result['errors'].append(f"Cannot read PDF: {str(e)}")
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'readable': False,
                'has_text': False,
                'page_count': 0,
                'file_size': 0,
                'errors': [f"Validation failed: {str(e)}"]
            }
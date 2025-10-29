"""
Text Chunking and Preprocessing for Royal Enfield Knowledge Base
Handles intelligent text chunking, content preprocessing, and metadata tagging
"""

import re
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class TextChunker:
    """
    Handles intelligent text chunking for optimal retrieval performance
    """
    
    def __init__(self, chunk_size: int = 1000, overlap_size: int = 200):
        """
        Initialize text chunker
        
        Args:
            chunk_size: Target size for each chunk in characters
            overlap_size: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = 100  # Minimum viable chunk size
    
    def chunk_document(self, text: str, pages_data: List[Dict[str, Any]], 
                      sections: List[Dict[str, Any]], document_name: str) -> List[Dict[str, Any]]:
        """
        Chunk document text into optimal pieces for retrieval
        
        Args:
            text: Full document text
            pages_data: Page-by-page information
            sections: Document sections
            document_name: Name of the document
            
        Returns:
            List[Dict[str, Any]]: List of text chunks with metadata
        """
        try:
            chunks = []
            
            # Process each section separately for better context
            for section in sections:
                section_chunks = self._chunk_section(
                    section, pages_data, document_name, len(chunks)
                )
                chunks.extend(section_chunks)
            
            # Post-process chunks
            chunks = self._post_process_chunks(chunks)
            
            logger.info(f"Created {len(chunks)} chunks from document: {document_name}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document: {e}")
            return []
    
    def _chunk_section(self, section: Dict[str, Any], pages_data: List[Dict[str, Any]], 
                      document_name: str, chunk_offset: int) -> List[Dict[str, Any]]:
        """
        Chunk a specific section of the document
        
        Args:
            section: Section information
            pages_data: Page data for context
            document_name: Document name
            chunk_offset: Starting chunk number
            
        Returns:
            List[Dict[str, Any]]: Chunks for this section
        """
        section_text = section['content']
        section_title = section['title']
        
        if len(section_text) <= self.chunk_size:
            # Section fits in one chunk
            return [self._create_chunk(
                content=section_text,
                chunk_id=f"{document_name}_chunk_{chunk_offset + 1:03d}",
                section_title=section_title,
                pages_data=pages_data,
                document_name=document_name,
                chunk_index=chunk_offset
            )]
        
        # Split section into multiple chunks
        chunks = []
        sentences = self._split_into_sentences(section_text)
        
        current_chunk = ""
        current_sentences = []
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Create chunk with current content
                chunk = self._create_chunk(
                    content=current_chunk.strip(),
                    chunk_id=f"{document_name}_chunk_{len(chunks) + chunk_offset + 1:03d}",
                    section_title=section_title,
                    pages_data=pages_data,
                    document_name=document_name,
                    chunk_index=len(chunks) + chunk_offset,
                    sentences=current_sentences.copy()
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                current_sentences = [sentence]
            else:
                current_chunk = potential_chunk
                current_sentences.append(sentence)
        
        # Add final chunk if there's remaining content
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                chunk_id=f"{document_name}_chunk_{len(chunks) + chunk_offset + 1:03d}",
                section_title=section_title,
                pages_data=pages_data,
                document_name=document_name,
                chunk_index=len(chunks) + chunk_offset,
                sentences=current_sentences
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, content: str, chunk_id: str, section_title: str,
                     pages_data: List[Dict[str, Any]], document_name: str,
                     chunk_index: int, sentences: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a chunk with comprehensive metadata
        
        Args:
            content: Chunk text content
            chunk_id: Unique chunk identifier
            section_title: Title of the section this chunk belongs to
            pages_data: Page information for context
            document_name: Name of the source document
            chunk_index: Index of this chunk in the document
            sentences: List of sentences in this chunk
            
        Returns:
            Dict[str, Any]: Chunk with metadata
        """
        # Determine page number(s) for this chunk
        page_numbers = self._determine_chunk_pages(content, pages_data)
        
        # Extract key topics and terms
        topics = self._extract_topics(content)
        
        # Calculate content statistics
        word_count = len(content.split())
        char_count = len(content)
        
        chunk = {
            'chunk_id': chunk_id,
            'content': content,
            'metadata': {
                'document_name': document_name,
                'section': section_title,
                'page_numbers': page_numbers,
                'chunk_index': chunk_index,
                'word_count': word_count,
                'char_count': char_count,
                'topics': topics,
                'created_at': datetime.now().isoformat(),
                'chunk_type': self._classify_chunk_type(content, section_title)
            }
        }
        
        # Add sentence information if available
        if sentences:
            chunk['metadata']['sentence_count'] = len(sentences)
        
        return chunk
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using intelligent rules
        
        Args:
            text: Text to split
            
        Returns:
            List[str]: List of sentences
        """
        # Handle common abbreviations that shouldn't trigger sentence breaks
        abbreviations = ['Mr.', 'Mrs.', 'Dr.', 'Prof.', 'Inc.', 'Ltd.', 'Co.', 'Corp.',
                        'vs.', 'etc.', 'i.e.', 'e.g.', 'cf.', 'al.', 'Fig.', 'No.',
                        'Vol.', 'Ch.', 'Sec.', 'min.', 'max.', 'avg.', 'approx.']
        
        # Temporarily replace abbreviations
        temp_text = text
        for i, abbr in enumerate(abbreviations):
            temp_text = temp_text.replace(abbr, f"__ABBR_{i}__")
        
        # Split on sentence endings
        sentences = re.split(r'[.!?]+\s+', temp_text)
        
        # Restore abbreviations and clean up
        restored_sentences = []
        for sentence in sentences:
            for i, abbr in enumerate(abbreviations):
                sentence = sentence.replace(f"__ABBR_{i}__", abbr)
            
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter out very short fragments
                restored_sentences.append(sentence)
        
        return restored_sentences
    
    def _get_overlap_text(self, text: str) -> str:
        """
        Get overlap text from the end of current chunk
        
        Args:
            text: Current chunk text
            
        Returns:
            str: Overlap text for next chunk
        """
        if len(text) <= self.overlap_size:
            return text
        
        # Try to find a good break point (sentence or word boundary)
        overlap_start = len(text) - self.overlap_size
        
        # Look for sentence boundary
        sentence_match = re.search(r'[.!?]\s+', text[overlap_start:])
        if sentence_match:
            return text[overlap_start + sentence_match.end():]
        
        # Look for word boundary
        word_match = re.search(r'\s+', text[overlap_start:])
        if word_match:
            return text[overlap_start + word_match.end():]
        
        # Fallback to character boundary
        return text[overlap_start:]
    
    def _determine_chunk_pages(self, content: str, pages_data: List[Dict[str, Any]]) -> List[int]:
        """
        Determine which pages this chunk content comes from
        
        Args:
            content: Chunk content
            pages_data: Page information
            
        Returns:
            List[int]: List of page numbers
        """
        page_numbers = []
        
        # Sample some unique phrases from the chunk
        sample_phrases = self._extract_sample_phrases(content)
        
        for page_info in pages_data:
            page_text = page_info.get('text', '')
            page_number = page_info.get('page_number')
            
            # Check if any sample phrases appear in this page
            for phrase in sample_phrases:
                if phrase.lower() in page_text.lower():
                    if page_number not in page_numbers:
                        page_numbers.append(page_number)
                    break
        
        return sorted(page_numbers) if page_numbers else [1]  # Default to page 1
    
    def _extract_sample_phrases(self, content: str, num_phrases: int = 3) -> List[str]:
        """
        Extract sample phrases from content for page matching
        
        Args:
            content: Content to sample from
            num_phrases: Number of phrases to extract
            
        Returns:
            List[str]: Sample phrases
        """
        sentences = self._split_into_sentences(content)
        if not sentences:
            return []
        
        # Take phrases from beginning, middle, and end
        phrases = []
        if len(sentences) >= 1:
            phrases.append(sentences[0][:50])  # First 50 chars of first sentence
        if len(sentences) >= 2:
            mid_idx = len(sentences) // 2
            phrases.append(sentences[mid_idx][:50])  # Middle sentence
        if len(sentences) >= 3:
            phrases.append(sentences[-1][:50])  # Last sentence
        
        return phrases[:num_phrases]
    
    def _extract_topics(self, content: str) -> List[str]:
        """
        Extract key topics and terms from chunk content
        
        Args:
            content: Chunk content
            
        Returns:
            List[str]: List of identified topics
        """
        topics = []
        
        # Motorcycle-specific terms and topics
        motorcycle_terms = [
            'engine', 'motor', 'cylinder', 'piston', 'valve', 'carburetor', 'fuel',
            'brake', 'clutch', 'transmission', 'gear', 'chain', 'sprocket',
            'tire', 'wheel', 'suspension', 'shock', 'fork', 'handlebar',
            'throttle', 'accelerator', 'speedometer', 'tachometer',
            'oil', 'coolant', 'battery', 'spark plug', 'air filter',
            'maintenance', 'service', 'inspection', 'repair', 'replacement',
            'safety', 'warning', 'caution', 'procedure', 'specification',
            'torque', 'pressure', 'temperature', 'voltage', 'amperage'
        ]
        
        content_lower = content.lower()
        
        # Find motorcycle-related terms
        for term in motorcycle_terms:
            if term in content_lower:
                topics.append(term)
        
        # Extract capitalized terms (likely important concepts)
        capitalized_terms = re.findall(r'\b[A-Z][A-Z\s]{2,20}\b', content)
        for term in capitalized_terms[:5]:  # Limit to top 5
            clean_term = term.strip()
            if len(clean_term) > 3 and clean_term not in topics:
                topics.append(clean_term.lower())
        
        # Extract numbered items (procedures, specifications)
        numbered_items = re.findall(r'\d+\.\s*([A-Za-z\s]{5,30})', content)
        for item in numbered_items[:3]:  # Limit to top 3
            clean_item = item.strip().lower()
            if clean_item not in topics:
                topics.append(clean_item)
        
        return topics[:10]  # Limit to top 10 topics
    
    def _classify_chunk_type(self, content: str, section_title: str) -> str:
        """
        Classify the type of content in this chunk
        
        Args:
            content: Chunk content
            section_title: Section title
            
        Returns:
            str: Chunk type classification
        """
        content_lower = content.lower()
        section_lower = section_title.lower()
        
        # Classification based on content patterns
        if 'specification' in section_lower or 'spec' in section_lower:
            return 'specifications'
        elif 'maintenance' in section_lower or 'service' in section_lower:
            return 'maintenance'
        elif 'troubleshoot' in section_lower or 'problem' in section_lower:
            return 'troubleshooting'
        elif 'safety' in section_lower or 'warning' in section_lower:
            return 'safety'
        elif 'operation' in section_lower or 'procedure' in section_lower:
            return 'procedures'
        elif re.search(r'\d+\.\s*\w+', content):  # Contains numbered steps
            return 'procedures'
        elif re.search(r'warning|caution|danger', content_lower):
            return 'safety'
        elif re.search(r'specification|spec|dimension|weight|capacity', content_lower):
            return 'specifications'
        elif re.search(r'maintenance|service|replace|check|inspect', content_lower):
            return 'maintenance'
        else:
            return 'general'
    
    def _post_process_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Post-process chunks to ensure quality and consistency
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            List[Dict[str, Any]]: Processed chunks
        """
        processed_chunks = []
        
        for chunk in chunks:
            content = chunk['content'].strip()
            
            # Skip chunks that are too short or empty
            if len(content) < self.min_chunk_size:
                logger.debug(f"Skipping short chunk: {chunk['chunk_id']}")
                continue
            
            # Clean up content
            content = self._clean_chunk_content(content)
            chunk['content'] = content
            
            # Update metadata
            chunk['metadata']['word_count'] = len(content.split())
            chunk['metadata']['char_count'] = len(content)
            
            processed_chunks.append(chunk)
        
        # Renumber chunks sequentially
        for i, chunk in enumerate(processed_chunks):
            chunk['metadata']['chunk_index'] = i
            # Update chunk_id to reflect new numbering
            doc_name = chunk['metadata']['document_name']
            chunk['chunk_id'] = f"{doc_name}_chunk_{i + 1:03d}"
        
        return processed_chunks
    
    def _clean_chunk_content(self, content: str) -> str:
        """
        Clean and normalize chunk content
        
        Args:
            content: Raw chunk content
            
        Returns:
            str: Cleaned content
        """
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove page numbers and headers/footers
        content = re.sub(r'\b\d+\s*$', '', content)  # Page numbers at end
        content = re.sub(r'^\s*\d+\s*', '', content)  # Page numbers at start
        
        # Remove repeated dashes or underscores
        content = re.sub(r'[-_]{3,}', '', content)
        
        # Normalize punctuation spacing
        content = re.sub(r'\s*([.!?])\s*', r'\1 ', content)
        
        return content.strip()
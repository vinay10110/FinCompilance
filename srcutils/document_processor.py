import fitz  # PyMuPDF
import PyPDF2
from typing import List, Dict, Any, Optional, Tuple
import os
from datetime import datetime
import re
from .text_processor import TextProcessor

class DocumentProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.metadata_patterns = {
            'document_type': re.compile(
                r'(circular|notification|guideline|directive|policy)\s*:?',
                re.IGNORECASE
            ),
            'reference_number': re.compile(
                r'ref(?:erence)?\.?\s*(?:no\.?)?[:.]?\s*([\w\-./]+)',
                re.IGNORECASE
            ),
            'department': re.compile(
                r'department\s+of\s+([^.]+)',
                re.IGNORECASE
            )
        }
    
    def process_document(self, 
                        file_path: str,
                        extract_images: bool = False) -> Dict[str, Any]:
        """Process a PDF document and extract relevant information"""
        # Extract text and metadata
        text, metadata = self._extract_pdf_content(file_path)
        
        # Extract requirements
        requirements = self.text_processor.extract_requirements(text)
        
        # Extract key information
        result = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'processed_date': datetime.now().isoformat(),
            'metadata': metadata,
            'requirements': requirements,
            'key_phrases': self.text_processor.extract_key_phrases(text),
            'dates': [d.isoformat() for d in self.text_processor.extract_dates(text)],
            'document_structure': self._analyze_document_structure(text)
        }
        
        # Add image information if requested
        if extract_images:
            result['images'] = self._extract_images(file_path)
        
        # Analyze requirement relationships
        result['requirement_dependencies'] = self.text_processor.extract_dependencies(
            requirements
        )
        result['potential_conflicts'] = self.text_processor.identify_potential_conflicts(
            requirements
        )
        
        return result
    
    def compare_documents(self,
                         old_path: str,
                         new_path: str) -> Dict[str, Any]:
        """Compare two versions of a document and identify changes"""
        # Extract content from both documents
        old_text, old_metadata = self._extract_pdf_content(old_path)
        new_text, new_metadata = self._extract_pdf_content(new_path)
        
        # Get change summary
        changes = self.text_processor.summarize_changes(old_text, new_text)
        
        # Add metadata comparison
        metadata_changes = self._compare_metadata(old_metadata, new_metadata)
        
        return {
            'content_changes': changes,
            'metadata_changes': metadata_changes,
            'old_version': {
                'file_path': old_path,
                'metadata': old_metadata
            },
            'new_version': {
                'file_path': new_path,
                'metadata': new_metadata
            }
        }
    
    def _extract_pdf_content(self, 
                           file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text content and metadata from PDF"""
        text = ""
        metadata = {}
        
        try:
            # Try PyMuPDF first for better text extraction
            doc = fitz.open(file_path)
            
            # Extract metadata
            metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'keywords': doc.metadata.get('keywords', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', ''),
                'page_count': len(doc)
            }
            
            # Extract text with layout preservation
            for page in doc:
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: (b[1], b[0]))  # Sort by y, then x
                page_text = "\n".join(b[4] for b in blocks)
                text += page_text + "\n\n"
            
            doc.close()
            
        except Exception as e:
            # Fallback to PyPDF2
            print(f"PyMuPDF extraction failed, falling back to PyPDF2: {str(e)}")
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    
                    # Extract metadata
                    metadata = {
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'subject': reader.metadata.get('/Subject', ''),
                        'keywords': reader.metadata.get('/Keywords', ''),
                        'creation_date': reader.metadata.get('/CreationDate', ''),
                        'modification_date': reader.metadata.get('/ModDate', ''),
                        'page_count': len(reader.pages)
                    }
                    
                    # Extract text
                    for page in reader.pages:
                        text += page.extract_text() + "\n\n"
            
            except Exception as e:
                raise Exception(f"Failed to extract PDF content: {str(e)}")
        
        # Extract additional metadata from content
        content_metadata = self._extract_content_metadata(text)
        metadata.update(content_metadata)
        
        return text.strip(), metadata
    
    def _extract_content_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from document content"""
        metadata = {}
        
        # Extract using patterns
        for key, pattern in self.metadata_patterns.items():
            matches = pattern.findall(text)
            if matches:
                metadata[key] = matches[0].strip()
        
        # Extract dates
        dates = self.text_processor.extract_dates(text)
        if dates:
            metadata['document_date'] = dates[0].isoformat()
        
        return metadata
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the structure of the document"""
        sections = []
        current_section = None
        section_pattern = re.compile(
            r'^(?:[0-9.]+\s+)?([A-Z][^.!?]*?)(?::|\.|\n)',
            re.MULTILINE
        )
        
        # Split text into lines and analyze structure
        lines = text.split('\n')
        for line in lines:
            # Check for new section
            section_match = section_pattern.match(line.strip())
            if section_match:
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': section_match.group(1).strip(),
                    'content': [],
                    'subsections': []
                }
            elif current_section:
                current_section['content'].append(line.strip())
        
        # Add last section
        if current_section:
            sections.append(current_section)
        
        return {
            'sections': sections,
            'section_count': len(sections)
        }
    
    def _extract_images(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF document"""
        images = []
        
        try:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc):
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    if base_image:
                        images.append({
                            'page_number': page_num + 1,
                            'image_index': img_index + 1,
                            'width': base_image['width'],
                            'height': base_image['height'],
                            'format': base_image['ext'],
                            'size': len(base_image['image'])
                        })
            
            doc.close()
            
        except Exception as e:
            print(f"Failed to extract images: {str(e)}")
        
        return images
    
    def _compare_metadata(self,
                         old_metadata: Dict[str, Any],
                         new_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Compare metadata between document versions"""
        changes = {
            'added': {},
            'removed': {},
            'modified': {}
        }
        
        # Find added and modified fields
        for key, new_value in new_metadata.items():
            if key not in old_metadata:
                changes['added'][key] = new_value
            elif old_metadata[key] != new_value:
                changes['modified'][key] = {
                    'old': old_metadata[key],
                    'new': new_value
                }
        
        # Find removed fields
        for key in old_metadata:
            if key not in new_metadata:
                changes['removed'][key] = old_metadata[key]
        
        return changes
    
    def extract_table_data(self,
                          file_path: str,
                          page_numbers: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Extract tabular data from PDF"""
        tables = []
        
        try:
            doc = fitz.open(file_path)
            
            # Process specified pages or all pages
            pages = page_numbers if page_numbers else range(len(doc))
            
            for page_num in pages:
                page = doc[page_num]
                
                # Find table-like structures
                blocks = page.get_text("dict")["blocks"]
                tables.extend(
                    self._identify_and_extract_tables(blocks, page_num)
                )
            
            doc.close()
            
        except Exception as e:
            print(f"Failed to extract tables: {str(e)}")
        
        return tables
    
    def _identify_and_extract_tables(self,
                                   blocks: List[Dict[str, Any]],
                                   page_num: int) -> List[Dict[str, Any]]:
        """Identify and extract table structures from page blocks"""
        tables = []
        current_table = None
        
        # Sort blocks by vertical position
        blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
        
        for block in blocks:
            # Check if block is likely part of a table
            if self._is_table_block(block):
                if not current_table:
                    current_table = {
                        'page_number': page_num + 1,
                        'bbox': list(block["bbox"]),
                        'rows': []
                    }
                
                # Add content to current row
                row_content = self._extract_block_content(block)
                if row_content:
                    current_table['rows'].append(row_content)
            
            elif current_table:
                # End of table detected
                if len(current_table['rows']) > 1:  # Minimum 2 rows for a table
                    tables.append(current_table)
                current_table = None
        
        # Add last table if exists
        if current_table and len(current_table['rows']) > 1:
            tables.append(current_table)
        
        return tables
    
    def _is_table_block(self, block: Dict[str, Any]) -> bool:
        """Determine if a block is likely part of a table"""
        # Check for table indicators
        if block.get("lines") and len(block["lines"]) > 0:
            # Check for consistent spacing
            line_spacing = [
                block["lines"][i+1]["bbox"][1] - block["lines"][i]["bbox"][3]
                for i in range(len(block["lines"])-1)
            ]
            if line_spacing and max(line_spacing) - min(line_spacing) < 2:
                return True
        
        return False
    
    def _extract_block_content(self, block: Dict[str, Any]) -> List[str]:
        """Extract content from a block"""
        content = []
        
        if block.get("lines"):
            for line in block["lines"]:
                if line.get("spans"):
                    text = " ".join(
                        span.get("text", "").strip()
                        for span in line["spans"]
                    )
                    if text:
                        content.append(text)
        
        return content
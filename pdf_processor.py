"""
PDF Processing module for Educational Roguelike Game
Extracts and processes text from PDF files for question generation
"""

import pdfplumber
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

import config
from database import pdf_manager

# Import OCR processor if available
try:
    from ocr_processor import extract_text_with_ocr, PDFOCRProcessor
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR processor not available. Scanned PDFs may not be processed correctly.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF text extraction and preprocessing"""

    def __init__(self):
        self.min_text_length = 100  # Minimum characters to consider valid
        self.max_chunk_size = 4000  # Maximum chunk size for API processing

    def extract_text_from_pdf(self, pdf_path: str, use_ocr: bool = None) -> Dict:
        """
        Extract all text from a PDF file with automatic OCR fallback

        Args:
            pdf_path: Path to PDF file
            use_ocr: Force OCR usage (None = auto-detect, True = force, False = disable)

        Returns:
            Dict with keys: text, num_pages, metadata, chunks, extraction_method
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                metadata = pdf.metadata or {}
                num_pages = len(pdf.pages)

                # Try text extraction first
                full_text = ""
                page_texts = []
                needs_ocr = False

                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    page_texts.append({
                        'page_num': i,
                        'text': page_text,
                        'char_count': len(page_text)
                    })
                    full_text += f"\n\n--- Page {i} ---\n\n{page_text}"

                # Check if we got sufficient text
                if len(full_text.strip()) < self.min_text_length:
                    needs_ocr = True
                    logger.warning(f"Insufficient text extracted ({len(full_text)} chars), may need OCR")

                # Determine if OCR should be used
                should_use_ocr = use_ocr if use_ocr is not None else (needs_ocr and config.OCR_ENABLED)

                extraction_method = 'text'
                ocr_stats = None

                # Use OCR if needed and available
                if should_use_ocr:
                    if OCR_AVAILABLE:
                        logger.info("Using OCR to extract text from PDF...")
                        ocr_result = extract_text_with_ocr(str(pdf_path))
                        
                        if ocr_result['success'] and len(ocr_result['text']) > len(full_text):
                            logger.info(f"OCR extracted more text: {len(ocr_result['text'])} vs {len(full_text)} chars")
                            full_text = ocr_result['text']
                            extraction_method = 'ocr'
                            ocr_stats = {
                                'pages_with_ocr': ocr_result['pages_with_ocr'],
                                'avg_confidence': ocr_result['avg_confidence']
                            }
                        else:
                            logger.warning("OCR did not improve text extraction, using original")
                    else:
                        logger.warning("OCR requested but not available. Install: pip install pytesseract pillow opencv-python")

                # Clean the text
                full_text = self.clean_text(full_text)

                # Validate we have enough text
                if len(full_text.strip()) < self.min_text_length:
                    raise ValueError(
                        f"Insufficient text extracted from PDF ({len(full_text)} chars). "
                        "PDF may be scanned images without OCR, or contain no readable text."
                    )

                # Split into manageable chunks for question generation
                chunks = self.split_into_chunks(full_text)

                # Extract topics/sections
                topics = self.extract_topics(full_text)

                result = {
                    'text': full_text,
                    'num_pages': num_pages,
                    'total_chars': len(full_text),
                    'metadata': metadata,
                    'page_texts': page_texts,
                    'chunks': chunks,
                    'topics': topics,
                    'title': metadata.get('Title') or pdf_path.stem,
                    'extraction_method': extraction_method,
                    'ocr_stats': ocr_stats
                }

                logger.info(f"Extracted {len(full_text)} characters from {num_pages} pages using {extraction_method}")
                logger.info(f"Found {len(topics)} topics, created {len(chunks)} chunks")

                return result

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise

    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers (common patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        # Remove headers/footers (repeated text)
        # This is a simple implementation; can be improved

        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def split_into_chunks(self, text: str, chunk_size: int = None) -> List[Dict]:
        """
        Split text into semantic chunks for processing

        Tries to split at paragraph boundaries to maintain context
        """
        chunk_size = chunk_size or self.max_chunk_size

        # Split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""
        chunk_id = 1

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunks.append({
                        'chunk_id': chunk_id,
                        'text': current_chunk.strip(),
                        'char_count': len(current_chunk)
                    })
                    chunk_id += 1
                    current_chunk = para
                else:
                    # Single paragraph is too large, split it
                    sentences = re.split(r'[.!?]+\s+', para)
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > chunk_size:
                            if current_chunk:
                                chunks.append({
                                    'chunk_id': chunk_id,
                                    'text': current_chunk.strip(),
                                    'char_count': len(current_chunk)
                                })
                                chunk_id += 1
                            current_chunk = sentence
                        else:
                            current_chunk += " " + sentence
            else:
                current_chunk += "\n\n" + para

        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'chunk_id': chunk_id,
                'text': current_chunk.strip(),
                'char_count': len(current_chunk)
            })

        return chunks

    def extract_topics(self, text: str) -> List[str]:
        """
        Extract potential topics/sections from the text

        Looks for common heading patterns:
        - All caps lines
        - Lines starting with numbers (1. Topic, 1.1 Topic)
        - Lines that are short and followed by content
        """
        topics = []

        # Pattern 1: Lines in all caps (likely headers)
        caps_pattern = r'^([A-Z][A-Z\s]{3,50})$'

        # Pattern 2: Numbered sections
        numbered_pattern = r'^(\d+\.?\d*\.?\s+[A-Z][A-Za-z\s]{3,50})'

        # Pattern 3: Common heading words
        heading_pattern = r'^(Chapter|Section|Part|Unit|Lesson|Introduction|Conclusion|Summary)\s+\d*:?\s*([A-Za-z\s]{3,50})'

        lines = text.split('\n')
        for line in lines:
            line = line.strip()

            # Check all caps
            caps_match = re.match(caps_pattern, line, re.MULTILINE)
            if caps_match:
                topics.append(caps_match.group(1).title())
                continue

            # Check numbered
            numbered_match = re.match(numbered_pattern, line)
            if numbered_match:
                topics.append(numbered_match.group(1).strip())
                continue

            # Check heading keywords
            heading_match = re.match(heading_pattern, line, re.IGNORECASE)
            if heading_match:
                topics.append(f"{heading_match.group(1)} {heading_match.group(2)}".strip())

        # Remove duplicates while preserving order
        seen = set()
        unique_topics = []
        for topic in topics:
            if topic not in seen:
                seen.add(topic)
                unique_topics.append(topic)

        return unique_topics[:20]  # Limit to 20 topics

    def estimate_question_capacity(self, text_length: int) -> int:
        """
        Estimate how many questions can be generated from text

        Rule of thumb: 1 question per 200-300 words
        """
        words = text_length / 5  # Rough estimate: avg 5 chars per word
        estimated_questions = int(words / 250)
        return max(10, estimated_questions)  # Minimum 10 questions

    def validate_pdf(self, pdf_path: str) -> Tuple[bool, str]:
        """
        Validate if a PDF is suitable for processing

        Returns:
            (is_valid, error_message)
        """
        pdf_path = Path(pdf_path)

        # Check file exists
        if not pdf_path.exists():
            return False, "File not found"

        # Check file size (max 16MB as per config)
        file_size = pdf_path.stat().st_size
        if file_size > config.MAX_CONTENT_LENGTH:
            return False, f"File too large: {file_size / 1024 / 1024:.1f}MB (max 16MB)"

        # Try to open and extract a page
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return False, "PDF has no pages"

                # Try to extract text from first page
                first_page_text = pdf.pages[0].extract_text() or ""

                if len(first_page_text) < self.min_text_length:
                    # Check if OCR is available
                    if config.OCR_ENABLED and OCR_AVAILABLE:
                        return True, "PDF appears to be scanned. OCR will be used for text extraction."
                    else:
                        return False, (
                            "PDF appears to have no extractable text (might be scanned images). "
                            "Enable OCR by installing: pip install pytesseract pillow opencv-python"
                        )

                return True, "PDF is valid"

        except Exception as e:
            return False, f"Error reading PDF: {str(e)}"


class PDFManager:
    """High-level PDF management with database integration"""

    def __init__(self):
        self.processor = PDFProcessor()

    def process_and_store_pdf(self, pdf_path: str, filename: str = None) -> Dict:
        """
        Process a PDF and store it in the database

        Returns:
            Dict with pdf_id, stats, and extracted data
        """
        pdf_path = Path(pdf_path)
        filename = filename or pdf_path.name

        # Validate PDF
        is_valid, error_msg = self.processor.validate_pdf(pdf_path)
        if not is_valid:
            raise ValueError(error_msg)

        # Extract text
        extracted_data = self.processor.extract_text_from_pdf(pdf_path)

        # Check if PDF already exists
        existing_pdf = pdf_manager.get_pdf_by_filepath(str(pdf_path))

        if existing_pdf:
            logger.info(f"PDF already exists in database: {filename}")
            pdf_id = existing_pdf['id']
        else:
            # Store in database
            pdf_id = pdf_manager.add_pdf(
                filename=filename,
                filepath=str(pdf_path),
                title=extracted_data['title'],
                num_pages=extracted_data['num_pages'],
                total_chars=extracted_data['total_chars']
            )
            logger.info(f"Added PDF to database with ID: {pdf_id}")

        # Prepare result
        result = {
            'pdf_id': pdf_id,
            'filename': filename,
            'title': extracted_data['title'],
            'num_pages': extracted_data['num_pages'],
            'total_chars': extracted_data['total_chars'],
            'topics': extracted_data['topics'],
            'chunks': extracted_data['chunks'],
            'estimated_questions': self.processor.estimate_question_capacity(
                extracted_data['total_chars']
            ),
            'text': extracted_data['text']  # Full text for question generation
        }

        return result

    def get_pdf_for_study(self, pdf_id: int) -> Optional[Dict]:
        """
        Get PDF information for starting a study session

        Returns PDF metadata and basic stats
        """
        pdf_info = pdf_manager.get_pdf(pdf_id)

        if not pdf_info:
            return None

        # Get question count
        from database import question_manager
        question_count = question_manager.get_question_count(pdf_id)

        return {
            **pdf_info,
            'question_count': question_count,
            'ready_to_play': question_count >= config.MIN_QUESTIONS_TO_START
        }


# ═══════════════════════════════════════════════════════════════════
# 🚀 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def save_uploaded_file(file, upload_folder: Path = None) -> str:
    """
    Save an uploaded file to the PDF directory

    Returns:
        Path to saved file
    """
    upload_folder = upload_folder or config.PDF_DIR

    # Generate safe filename
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)

    # Check for duplicates and add number if needed
    filepath = upload_folder / filename
    counter = 1
    while filepath.exists():
        name, ext = filename.rsplit('.', 1)
        filename = f"{name}_{counter}.{ext}"
        filepath = upload_folder / filename
        counter += 1

    # Save file
    file.save(str(filepath))
    logger.info(f"Saved uploaded file: {filepath}")

    return str(filepath)

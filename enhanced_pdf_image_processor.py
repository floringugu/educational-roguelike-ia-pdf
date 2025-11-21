"""
Enhanced PDF and Image Processing module for Educational Roguelike Game
Supports:
- Text-based PDFs (original functionality)
- Scanned PDFs (using OCR)
- Direct images (JPG, PNG, WEBP, etc.)

Requires: pytesseract, pdf2image, Pillow
"""

import pdfplumber
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from PIL import Image
import io

# OCR Support
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("OCR not available. Install: pip install pytesseract pdf2image Pillow")

import config
from database import pdf_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedPDFProcessor:
    """Handles PDF, scanned PDF, and image text extraction"""

    def __init__(self):
        self.min_text_length = 100
        self.max_chunk_size = 4000
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        
        # OCR configuration
        self.ocr_enabled = OCR_AVAILABLE
        if self.ocr_enabled:
            # Configure tesseract path if needed (Windows)
            # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            pass
        else:
            logger.warning("⚠️ OCR disabled - scanned PDFs and images won't work")

    def extract_text_from_file(self, file_path: str) -> Dict:
        """
        Universal text extraction from PDF or image
        
        Returns:
            Dict with keys: text, num_pages, metadata, chunks, source_type
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_ext in self.supported_image_formats:
            return self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    def _extract_from_pdf(self, pdf_path: Path) -> Dict:
        """
        Extract text from PDF - tries text extraction first, then OCR
        """
        try:
            # Try text extraction first (faster)
            with pdfplumber.open(pdf_path) as pdf:
                metadata = pdf.metadata or {}
                num_pages = len(pdf.pages)
                
                full_text = ""
                page_texts = []
                text_found = False
                
                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    
                    if len(page_text.strip()) > 50:  # Meaningful text threshold
                        text_found = True
                    
                    page_texts.append({
                        'page_num': i,
                        'text': page_text,
                        'char_count': len(page_text)
                    })
                    full_text += f"\n\n--- Page {i} ---\n\n{page_text}"
                
                # If sufficient text was extracted, use it
                if text_found and len(full_text.strip()) >= self.min_text_length:
                    logger.info(f"✅ Extracted text from PDF: {len(full_text)} characters")
                    return self._build_result(
                        full_text, 
                        num_pages, 
                        metadata, 
                        page_texts, 
                        pdf_path,
                        source_type="pdf_text"
                    )
                
                # If no text or insufficient text, try OCR
                logger.info("⚠️ Insufficient text extracted, attempting OCR...")
                return self._extract_pdf_with_ocr(pdf_path, num_pages, metadata)
                
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            # Try OCR as fallback
            if self.ocr_enabled:
                logger.info("Attempting OCR as fallback...")
                return self._extract_pdf_with_ocr(pdf_path)
            raise

    def _extract_pdf_with_ocr(self, pdf_path: Path, num_pages: int = None, metadata: dict = None) -> Dict:
        """
        Extract text from PDF using OCR (for scanned PDFs)
        """
        if not self.ocr_enabled:
            raise RuntimeError(
                "OCR not available. Install required packages:\n"
                "pip install pytesseract pdf2image Pillow\n"
                "Also install Tesseract: https://github.com/tesseract-ocr/tesseract"
            )
        
        logger.info(f"🔍 Starting OCR on PDF: {pdf_path.name}")
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(
                str(pdf_path),
                dpi=300,  # Higher DPI = better quality but slower
                fmt='png'
            )
            
            num_pages = len(images)
            full_text = ""
            page_texts = []
            
            for i, image in enumerate(images, 1):
                logger.info(f"  OCR processing page {i}/{num_pages}...")
                
                # Perform OCR on the image
                page_text = pytesseract.image_to_string(
                    image,
                    lang='spa+eng',  # Spanish + English (adjust as needed)
                    config='--psm 6'  # Assume uniform text block
                )
                
                page_texts.append({
                    'page_num': i,
                    'text': page_text,
                    'char_count': len(page_text),
                    'method': 'ocr'
                })
                
                full_text += f"\n\n--- Page {i} ---\n\n{page_text}"
            
            logger.info(f"✅ OCR completed: {len(full_text)} characters extracted")
            
            return self._build_result(
                full_text,
                num_pages,
                metadata or {},
                page_texts,
                pdf_path,
                source_type="pdf_ocr"
            )
            
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            raise RuntimeError(f"Failed to extract text via OCR: {str(e)}")

    def _extract_from_image(self, image_path: Path) -> Dict:
        """
        Extract text from image file using OCR
        """
        if not self.ocr_enabled:
            raise RuntimeError(
                "OCR not available. Install required packages:\n"
                "pip install pytesseract Pillow"
            )
        
        logger.info(f"🖼️ Extracting text from image: {image_path.name}")
        
        try:
            # Open and process image
            image = Image.open(image_path)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(
                image,
                lang='spa+eng',  # Spanish + English
                config='--psm 6'
            )
            
            logger.info(f"✅ Extracted {len(text)} characters from image")
            
            # Build result similar to PDF
            page_texts = [{
                'page_num': 1,
                'text': text,
                'char_count': len(text),
                'method': 'ocr'
            }]
            
            metadata = {
                'Title': image_path.stem,
                'Format': image.format,
                'Size': f"{image.width}x{image.height}",
                'Mode': image.mode
            }
            
            return self._build_result(
                text,
                1,  # Single "page"
                metadata,
                page_texts,
                image_path,
                source_type="image_ocr"
            )
            
        except Exception as e:
            logger.error(f"Failed to extract text from image: {str(e)}")
            raise

    def _build_result(self, full_text: str, num_pages: int, metadata: dict, 
                     page_texts: List[Dict], file_path: Path, source_type: str) -> Dict:
        """
        Build standardized result dictionary
        """
        # Clean the text
        full_text = self.clean_text(full_text)
        
        # Split into chunks
        chunks = self.split_into_chunks(full_text)
        
        # Extract topics
        topics = self.extract_topics(full_text)
        
        result = {
            'text': full_text,
            'num_pages': num_pages,
            'total_chars': len(full_text),
            'metadata': metadata,
            'page_texts': page_texts,
            'chunks': chunks,
            'topics': topics,
            'title': metadata.get('Title') or file_path.stem,
            'source_type': source_type,  # 'pdf_text', 'pdf_ocr', or 'image_ocr'
            'file_type': file_path.suffix
        }
        
        logger.info(f"📊 Processing complete:")
        logger.info(f"   - Characters: {len(full_text)}")
        logger.info(f"   - Pages: {num_pages}")
        logger.info(f"   - Topics: {len(topics)}")
        logger.info(f"   - Chunks: {len(chunks)}")
        logger.info(f"   - Source: {source_type}")
        
        return result

    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s\-.,;:!?¿¡()[\]{}"\'/\\@#$%&*+=<>áéíóúñÁÉÍÓÚÑüÜ]', '', text)
        
        return text.strip()

    def split_into_chunks(self, text: str, chunk_size: int = None) -> List[Dict]:
        """Split text into semantic chunks"""
        chunk_size = chunk_size or self.max_chunk_size
        
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_id = 1
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
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
                    # Single paragraph too large
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
        
        if current_chunk.strip():
            chunks.append({
                'chunk_id': chunk_id,
                'text': current_chunk.strip(),
                'char_count': len(current_chunk)
            })
        
        return chunks

    def extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        topics = []
        
        # All caps pattern
        caps_pattern = r'^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{3,50})$'
        
        # Numbered sections
        numbered_pattern = r'^(\d+\.?\d*\.?\s+[A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s]{3,50})'
        
        # Common headings
        heading_pattern = r'^(Capítulo|Sección|Parte|Unidad|Lección|Introducción|Conclusión|Resumen|Chapter|Section|Part|Unit|Lesson|Introduction|Conclusion|Summary)\s+\d*:?\s*([A-Za-záéíóúñ\s]{3,50})'
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Check patterns
            for pattern in [caps_pattern, numbered_pattern, heading_pattern]:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    topic = match.group(1) if len(match.groups()) == 1 else f"{match.group(1)} {match.group(2)}"
                    topics.append(topic.strip())
                    break
        
        # Remove duplicates
        seen = set()
        unique_topics = []
        for topic in topics:
            if topic not in seen:
                seen.add(topic)
                unique_topics.append(topic)
        
        return unique_topics[:20]

    def estimate_question_capacity(self, text_length: int) -> int:
        """Estimate number of questions from text"""
        words = text_length / 5
        estimated_questions = int(words / 250)
        return max(10, estimated_questions)

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if file is suitable for processing
        
        Returns:
            (is_valid, message)
        """
        file_path = Path(file_path)
        
        # Check existence
        if not file_path.exists():
            return False, "Archivo no encontrado"
        
        # Check file size
        file_size = file_path.stat().st_size
        max_size = getattr(config, 'MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        
        if file_size > max_size:
            return False, f"Archivo demasiado grande: {file_size / 1024 / 1024:.1f}MB (máx {max_size / 1024 / 1024}MB)"
        
        if file_size == 0:
            return False, "Archivo vacío"
        
        # Check file type
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.pdf':
            return self._validate_pdf(file_path)
        elif file_ext in self.supported_image_formats:
            return self._validate_image(file_path)
        else:
            return False, f"Tipo de archivo no soportado: {file_ext}"

    def _validate_pdf(self, pdf_path: Path) -> Tuple[bool, str]:
        """Validate PDF file"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return False, "PDF no tiene páginas"
                
                # Try to extract text from first page
                first_page_text = pdf.pages[0].extract_text() or ""
                
                # If no text and OCR is available, it's still valid
                if len(first_page_text) < self.min_text_length:
                    if self.ocr_enabled:
                        return True, "PDF válido (se usará OCR para extraer texto)"
                    else:
                        return False, "PDF parece ser escaneado pero OCR no está disponible"
                
                return True, "PDF válido con texto extraíble"
                
        except Exception as e:
            return False, f"Error al leer PDF: {str(e)}"

    def _validate_image(self, image_path: Path) -> Tuple[bool, str]:
        """Validate image file"""
        if not self.ocr_enabled:
            return False, "Las imágenes requieren OCR. Instala: pip install pytesseract pdf2image Pillow"
        
        try:
            image = Image.open(image_path)
            
            # Check dimensions
            if image.width < 100 or image.height < 100:
                return False, "Imagen demasiado pequeña"
            
            if image.width > 10000 or image.height > 10000:
                return False, "Imagen demasiado grande"
            
            return True, "Imagen válida (se usará OCR)"
            
        except Exception as e:
            return False, f"Error al leer imagen: {str(e)}"


class EnhancedFileManager:
    """Enhanced file management with support for PDFs and images"""
    
    def __init__(self):
        self.processor = EnhancedPDFProcessor()
    
    def process_and_store_file(self, file_path: str, filename: str = None) -> Dict:
        """
        Process file (PDF or image) and store in database
        
        Returns:
            Dict with file_id, stats, and extracted data
        """
        file_path = Path(file_path)
        filename = filename or file_path.name
        
        # Validate file
        is_valid, message = self.processor.validate_file(file_path)
        if not is_valid:
            raise ValueError(message)
        
        logger.info(f"✅ Validation: {message}")
        
        # Extract text
        extracted_data = self.processor.extract_text_from_file(file_path)
        
        # Check if already exists
        existing_file = pdf_manager.get_pdf_by_filepath(str(file_path))
        
        if existing_file:
            logger.info(f"Archivo ya existe en la base de datos: {filename}")
            file_id = existing_file['id']
        else:
            # Store in database
            file_id = pdf_manager.add_pdf(
                filename=filename,
                filepath=str(file_path),
                title=extracted_data['title'],
                num_pages=extracted_data['num_pages'],
                total_chars=extracted_data['total_chars']
            )
            logger.info(f"Archivo agregado a la base de datos con ID: {file_id}")
        
        # Prepare result
        result = {
            'file_id': file_id,
            'filename': filename,
            'title': extracted_data['title'],
            'num_pages': extracted_data['num_pages'],
            'total_chars': extracted_data['total_chars'],
            'topics': extracted_data['topics'],
            'chunks': extracted_data['chunks'],
            'estimated_questions': self.processor.estimate_question_capacity(
                extracted_data['total_chars']
            ),
            'text': extracted_data['text'],
            'source_type': extracted_data['source_type'],
            'file_type': extracted_data['file_type']
        }
        
        return result


# ═══════════════════════════════════════════════════════════════════
# 🚀 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder: Path = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Save uploaded file with validation
    
    Returns:
        (filepath, error_message)
    """
    if not file or not file.filename:
        return None, "No se proporcionó archivo"
    
    # Check if allowed
    if not allowed_file(file.filename):
        return None, "Tipo de archivo no permitido. Use PDF o imágenes (JPG, PNG, etc.)"
    
    upload_folder = upload_folder or getattr(config, 'PDF_DIR', Path('data/pdfs'))
    upload_folder = Path(upload_folder)
    upload_folder.mkdir(parents=True, exist_ok=True)
    
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    
    # Handle duplicates
    filepath = upload_folder / filename
    counter = 1
    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
    ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
    
    while filepath.exists():
        filename = f"{base_name}_{counter}.{ext}"
        filepath = upload_folder / filename
        counter += 1
        
        if counter > 1000:
            return None, "Demasiados archivos con nombres similares"
    
    try:
        file.save(str(filepath))
        logger.info(f"Archivo guardado: {filepath}")
        return str(filepath), None
    except Exception as e:
        logger.error(f"Error al guardar archivo: {e}")
        return None, f"Error al guardar archivo: {str(e)}"


def check_ocr_installation() -> Dict:
    """
    Check if OCR dependencies are installed
    
    Returns:
        Dict with installation status
    """
    status = {
        'ocr_available': OCR_AVAILABLE,
        'missing_packages': [],
        'installation_command': None
    }
    
    if not OCR_AVAILABLE:
        try:
            import pytesseract
        except ImportError:
            status['missing_packages'].append('pytesseract')
        
        try:
            from pdf2image import convert_from_path
        except ImportError:
            status['missing_packages'].append('pdf2image')
        
        try:
            from PIL import Image
        except ImportError:
            status['missing_packages'].append('Pillow')
        
        if status['missing_packages']:
            status['installation_command'] = f"pip install {' '.join(status['missing_packages'])}"
    
    return status


if __name__ == "__main__":
    # Test OCR installation
    print("🔍 Checking OCR Installation...")
    status = check_ocr_installation()
    
    if status['ocr_available']:
        print("✅ OCR está disponible")
    else:
        print("⚠️ OCR NO está disponible")
        print(f"   Paquetes faltantes: {', '.join(status['missing_packages'])}")
        print(f"   Instalar con: {status['installation_command']}")
        print("\n   También necesitas instalar Tesseract:")
        print("   - Linux: sudo apt-get install tesseract-ocr")
        print("   - Mac: brew install tesseract")
        print("   - Windows: https://github.com/tesseract-ocr/tesseract/wiki")

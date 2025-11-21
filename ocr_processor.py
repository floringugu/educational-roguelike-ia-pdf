"""
OCR Module for Educational Roguelike Game
Processes scanned PDFs and image-based documents using OCR
Supports multiple OCR engines: Tesseract, EasyOCR, PaddleOCR
"""

import logging
import hashlib
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# 🔍 OCR ENGINE WRAPPER
# ═══════════════════════════════════════════════════════════════════

class OCREngine:
    """Base class for OCR engines"""
    
    def __init__(self):
        self.name = "base"
        self.languages = config.TESSERACT_LANG.split('+')
    
    def extract_text(self, image) -> Tuple[str, float]:
        """
        Extract text from image
        
        Returns:
            (text, confidence)
        """
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if OCR engine is available"""
        raise NotImplementedError


class TesseractOCR(OCREngine):
    """Tesseract OCR engine"""
    
    def __init__(self):
        super().__init__()
        self.name = "tesseract"
        
        try:
            import pytesseract
            from PIL import Image
            
            self.pytesseract = pytesseract
            self.Image = Image
            
            # Set tesseract command path if provided
            if config.TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
            
            self.available = True
            logger.info("Tesseract OCR initialized successfully")
            
        except ImportError as e:
            self.available = False
            logger.warning(f"Tesseract not available: {e}")
    
    def is_available(self) -> bool:
        return self.available
    
    def extract_text(self, image) -> Tuple[str, float]:
        """Extract text using Tesseract"""
        if not self.available:
            return "", 0.0
        
        try:
            # Convert to PIL Image if needed
            if not isinstance(image, self.Image.Image):
                image = self.Image.fromarray(image)
            
            # Extract text with detailed data
            data = self.pytesseract.image_to_data(
                image,
                lang=config.TESSERACT_LANG,
                config=config.TESSERACT_CONFIG,
                output_type=self.pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract text
            text = self.pytesseract.image_to_string(
                image,
                lang=config.TESSERACT_LANG,
                config=config.TESSERACT_CONFIG
            )
            
            return text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return "", 0.0


class EasyOCR(OCREngine):
    """EasyOCR engine - deep learning based"""
    
    def __init__(self):
        super().__init__()
        self.name = "easyocr"
        
        try:
            import easyocr
            
            # Map language codes
            lang_map = {
                'spa': 'es',
                'eng': 'en'
            }
            langs = [lang_map.get(lang, lang) for lang in self.languages]
            
            self.reader = easyocr.Reader(langs, gpu=False)
            self.available = True
            logger.info("EasyOCR initialized successfully")
            
        except ImportError as e:
            self.available = False
            logger.warning(f"EasyOCR not available: {e}")
    
    def is_available(self) -> bool:
        return self.available
    
    def extract_text(self, image) -> Tuple[str, float]:
        """Extract text using EasyOCR"""
        if not self.available:
            return "", 0.0
        
        try:
            import numpy as np
            
            # Convert to numpy array if needed
            if not isinstance(image, np.ndarray):
                image = np.array(image)
            
            # Read text
            results = self.reader.readtext(image)
            
            # Combine text and calculate average confidence
            texts = []
            confidences = []
            
            for bbox, text, conf in results:
                if conf >= config.OCR_MIN_CONFIDENCE / 100:
                    texts.append(text)
                    confidences.append(conf * 100)
            
            combined_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return combined_text, avg_confidence
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return "", 0.0


class PaddleOCR(OCREngine):
    """PaddleOCR engine - fast and accurate"""
    
    def __init__(self):
        super().__init__()
        self.name = "paddleocr"
        
        try:
            from paddleocr import PaddleOCR as POCREngine
            
            # Map language codes
            lang = 'es' if 'spa' in self.languages else 'en'
            
            self.ocr = POCREngine(
                use_angle_cls=True,
                lang=lang,
                use_gpu=False,
                show_log=False
            )
            self.available = True
            logger.info("PaddleOCR initialized successfully")
            
        except ImportError as e:
            self.available = False
            logger.warning(f"PaddleOCR not available: {e}")
    
    def is_available(self) -> bool:
        return self.available
    
    def extract_text(self, image) -> Tuple[str, float]:
        """Extract text using PaddleOCR"""
        if not self.available:
            return "", 0.0
        
        try:
            import numpy as np
            
            # Convert to numpy array if needed
            if not isinstance(image, np.ndarray):
                image = np.array(image)
            
            # Perform OCR
            results = self.ocr.ocr(image, cls=True)
            
            if not results or not results[0]:
                return "", 0.0
            
            # Extract text and confidence
            texts = []
            confidences = []
            
            for line in results[0]:
                text = line[1][0]
                conf = line[1][1] * 100
                
                if conf >= config.OCR_MIN_CONFIDENCE:
                    texts.append(text)
                    confidences.append(conf)
            
            combined_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return combined_text, avg_confidence
            
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            return "", 0.0


# ═══════════════════════════════════════════════════════════════════
# 🖼️ IMAGE PREPROCESSING
# ═══════════════════════════════════════════════════════════════════

class ImagePreprocessor:
    """Preprocess images for better OCR results"""
    
    def __init__(self):
        try:
            import cv2
            import numpy as np
            from PIL import Image
            
            self.cv2 = cv2
            self.np = np
            self.Image = Image
            self.available = True
            
        except ImportError as e:
            self.available = False
            logger.warning(f"Image preprocessing not available: {e}")
    
    def preprocess(self, image) -> any:
        """
        Apply preprocessing to improve OCR accuracy
        
        Steps:
        1. Convert to grayscale
        2. Denoise
        3. Deskew
        4. Remove borders
        5. Enhance contrast
        """
        if not self.available or not config.OCR_PREPROCESSING:
            return image
        
        try:
            # Convert PIL Image to cv2 format
            if isinstance(image, self.Image.Image):
                image = self.np.array(image)
            
            # 1. Grayscale
            if config.OCR_PREPROCESS_OPTIONS.get('grayscale', True):
                if len(image.shape) == 3:
                    image = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY)
            
            # 2. Denoise
            if config.OCR_PREPROCESS_OPTIONS.get('denoise', True):
                image = self.cv2.fastNlMeansDenoising(image)
            
            # 3. Deskew
            if config.OCR_PREPROCESS_OPTIONS.get('deskew', True):
                image = self._deskew(image)
            
            # 4. Remove borders
            if config.OCR_PREPROCESS_OPTIONS.get('remove_borders', True):
                image = self._remove_borders(image)
            
            # 5. Enhance contrast
            if config.OCR_PREPROCESS_OPTIONS.get('enhance_contrast', True):
                image = self._enhance_contrast(image)
            
            return image
            
        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}")
            return image
    
    def _deskew(self, image):
        """Correct skewed images"""
        coords = self.np.column_stack(self.np.where(image > 0))
        angle = self.cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        if abs(angle) > 0.5:  # Only deskew if angle is significant
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = self.cv2.getRotationMatrix2D(center, angle, 1.0)
            image = self.cv2.warpAffine(
                image, M, (w, h),
                flags=self.cv2.INTER_CUBIC,
                borderMode=self.cv2.BORDER_REPLICATE
            )
        
        return image
    
    def _remove_borders(self, image):
        """Remove black borders"""
        # Find contours
        contours, _ = self.cv2.findContours(
            image, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE
        )
        
        if contours:
            # Get bounding box of largest contour
            c = max(contours, key=self.cv2.contourArea)
            x, y, w, h = self.cv2.boundingRect(c)
            
            # Crop to bounding box with small margin
            margin = 10
            y_start = max(0, y - margin)
            y_end = min(image.shape[0], y + h + margin)
            x_start = max(0, x - margin)
            x_end = min(image.shape[1], x + w + margin)
            
            image = image[y_start:y_end, x_start:x_end]
        
        return image
    
    def _enhance_contrast(self, image):
        """Enhance contrast using CLAHE"""
        clahe = self.cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)


# ═══════════════════════════════════════════════════════════════════
# 📄 PDF OCR PROCESSOR
# ═══════════════════════════════════════════════════════════════════

class PDFOCRProcessor:
    """Process PDFs with OCR for scanned documents"""
    
    def __init__(self):
        self.ocr_engine = self._initialize_ocr_engine()
        self.preprocessor = ImagePreprocessor()
        self.cache_dir = config.OCR_CACHE_DIR if config.OCR_CACHE_ENABLED else None
    
    def _initialize_ocr_engine(self) -> OCREngine:
        """Initialize the best available OCR engine"""
        engine_name = config.OCR_ENGINE.lower()
        
        # Try requested engine first
        if engine_name == 'tesseract':
            engine = TesseractOCR()
            if engine.is_available():
                return engine
        
        elif engine_name == 'easyocr':
            engine = EasyOCR()
            if engine.is_available():
                return engine
        
        elif engine_name == 'paddleocr':
            engine = PaddleOCR()
            if engine.is_available():
                return engine
        
        # Fallback to any available engine
        logger.warning(f"Requested engine '{engine_name}' not available, trying fallbacks...")
        
        for EngineClass in [TesseractOCR, EasyOCR, PaddleOCR]:
            engine = EngineClass()
            if engine.is_available():
                logger.info(f"Using fallback OCR engine: {engine.name}")
                return engine
        
        raise RuntimeError(
            "No OCR engine available. Please install: "
            "pip install pytesseract pillow opencv-python"
        )
    
    def _get_cache_key(self, pdf_path: str, page_num: int) -> str:
        """Generate cache key for a PDF page"""
        key_string = f"{pdf_path}:{page_num}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load OCR result from cache"""
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save OCR result to cache"""
        if not self.cache_dir:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    def process_pdf_page(self, pdf_path: str, page_num: int, page_obj) -> Dict:
        """
        Process a single PDF page with OCR
        
        Returns:
            Dict with: text, confidence, method (ocr/text)
        """
        # Check cache first
        cache_key = self._get_cache_key(pdf_path, page_num)
        cached_result = self._load_from_cache(cache_key)
        
        if cached_result:
            logger.debug(f"Using cached OCR for page {page_num}")
            return cached_result
        
        result = {
            'page_num': page_num,
            'text': '',
            'confidence': 0.0,
            'method': 'none'
        }
        
        try:
            # Try text extraction first
            text = page_obj.extract_text() or ""
            
            if len(text.strip()) >= config.min_text_length if hasattr(config, 'min_text_length') else 50:
                # Sufficient text extracted
                result['text'] = text
                result['confidence'] = 100.0
                result['method'] = 'text'
                logger.info(f"Page {page_num}: Extracted text directly ({len(text)} chars)")
            
            elif config.OCR_ENABLED:
                # Need OCR
                logger.info(f"Page {page_num}: Performing OCR...")
                ocr_text, confidence = self._perform_ocr_on_page(page_obj)
                
                if ocr_text and confidence >= config.OCR_MIN_CONFIDENCE:
                    result['text'] = ocr_text
                    result['confidence'] = confidence
                    result['method'] = 'ocr'
                    logger.info(f"Page {page_num}: OCR successful (confidence: {confidence:.1f}%)")
                else:
                    logger.warning(f"Page {page_num}: OCR failed or low confidence")
                    if config.OCR_FALLBACK_TO_TEXT and text:
                        result['text'] = text
                        result['confidence'] = 50.0
                        result['method'] = 'text_fallback'
            
            else:
                logger.warning(f"Page {page_num}: No text and OCR disabled")
        
        except Exception as e:
            logger.error(f"Error processing page {page_num}: {e}")
        
        # Save to cache
        if result['text']:
            self._save_to_cache(cache_key, result)
        
        return result
    
    def _perform_ocr_on_page(self, page_obj) -> Tuple[str, float]:
        """Perform OCR on a PDF page"""
        try:
            from pdf2image import convert_from_path
            from PIL import Image
            import io
            
            # Convert page to image
            # Method 1: Try to get image directly from page
            images = []
            
            # Get images from page object
            if hasattr(page_obj, 'images'):
                for img in page_obj.images:
                    try:
                        image = Image.open(io.BytesIO(img['stream'].get_data()))
                        images.append(image)
                    except:
                        pass
            
            # Method 2: Render entire page as image
            if not images:
                # This requires pdf2image which uses poppler
                # For now, we'll use a simpler approach with pdfplumber
                try:
                    # Get page as image using pdfplumber
                    pil_image = page_obj.to_image(resolution=config.OCR_DPI).original
                    images.append(pil_image)
                except Exception as e:
                    logger.error(f"Could not convert page to image: {e}")
                    return "", 0.0
            
            # Process each image
            all_text = []
            all_confidence = []
            
            for image in images:
                # Preprocess
                processed_image = self.preprocessor.preprocess(image)
                
                # Perform OCR
                text, confidence = self.ocr_engine.extract_text(processed_image)
                
                if text:
                    all_text.append(text)
                    all_confidence.append(confidence)
            
            # Combine results
            combined_text = '\n\n'.join(all_text)
            avg_confidence = sum(all_confidence) / len(all_confidence) if all_confidence else 0
            
            return combined_text, avg_confidence
        
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return "", 0.0
    
    def process_pdf_parallel(self, pdf_path: str, pages: List) -> List[Dict]:
        """
        Process multiple PDF pages in parallel
        
        Args:
            pdf_path: Path to PDF file
            pages: List of page objects
        
        Returns:
            List of page results
        """
        results = []
        
        # Process in parallel
        with ThreadPoolExecutor(max_workers=config.OCR_BATCH_SIZE) as executor:
            future_to_page = {
                executor.submit(self.process_pdf_page, pdf_path, i + 1, page): i
                for i, page in enumerate(pages)
            }
            
            for future in as_completed(future_to_page):
                page_idx = future_to_page[future]
                try:
                    result = future.result()
                    results.append((page_idx, result))
                except Exception as e:
                    logger.error(f"Page {page_idx + 1} processing failed: {e}")
                    results.append((page_idx, {
                        'page_num': page_idx + 1,
                        'text': '',
                        'confidence': 0.0,
                        'method': 'error'
                    }))
        
        # Sort by page number
        results.sort(key=lambda x: x[0])
        
        return [r[1] for r in results]


# ═══════════════════════════════════════════════════════════════════
# 🚀 HIGH-LEVEL API
# ═══════════════════════════════════════════════════════════════════

def extract_text_with_ocr(pdf_path: str) -> Dict:
    """
    Extract text from PDF with automatic OCR fallback
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Dict with extracted text and metadata
    """
    import pdfplumber
    
    processor = PDFOCRProcessor()
    
    with pdfplumber.open(pdf_path) as pdf:
        logger.info(f"Processing PDF with {len(pdf.pages)} pages")
        
        # Process all pages
        page_results = processor.process_pdf_parallel(pdf_path, pdf.pages)
        
        # Combine results
        full_text = []
        total_confidence = []
        methods_used = []
        
        for result in page_results:
            if result['text']:
                full_text.append(f"\n\n--- Page {result['page_num']} ---\n\n{result['text']}")
                total_confidence.append(result['confidence'])
                methods_used.append(result['method'])
        
        # Calculate statistics
        avg_confidence = sum(total_confidence) / len(total_confidence) if total_confidence else 0
        ocr_pages = sum(1 for m in methods_used if m == 'ocr')
        text_pages = sum(1 for m in methods_used if m == 'text')
        
        combined_text = ''.join(full_text)
        
        return {
            'text': combined_text,
            'total_pages': len(pdf.pages),
            'pages_processed': len(page_results),
            'pages_with_text': text_pages,
            'pages_with_ocr': ocr_pages,
            'avg_confidence': avg_confidence,
            'total_chars': len(combined_text),
            'success': len(combined_text) > 100
        }


def test_ocr_engine() -> Dict:
    """
    Test if OCR is working correctly
    
    Returns:
        Dict with test results
    """
    try:
        processor = PDFOCRProcessor()
        
        return {
            'ocr_enabled': config.OCR_ENABLED,
            'engine': processor.ocr_engine.name,
            'engine_available': processor.ocr_engine.is_available(),
            'preprocessing_available': processor.preprocessor.available,
            'cache_enabled': config.OCR_CACHE_ENABLED,
            'cache_dir': str(config.OCR_CACHE_DIR) if config.OCR_CACHE_ENABLED else None,
            'languages': config.TESSERACT_LANG,
            'success': True
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'OCR not properly configured. Install: pip install pytesseract pillow opencv-python'
        }


# ═══════════════════════════════════════════════════════════════════
# 📝 EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor.py <pdf_file>")
        print("\nTesting OCR configuration...")
        result = test_ocr_engine()
        print(f"\nOCR Test Results:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    print(f"Processing PDF: {pdf_file}")
    print("=" * 60)
    
    result = extract_text_with_ocr(pdf_file)
    
    print(f"\nResults:")
    print(f"  Total pages: {result['total_pages']}")
    print(f"  Pages processed: {result['pages_processed']}")
    print(f"  Text extraction: {result['pages_with_text']} pages")
    print(f"  OCR used: {result['pages_with_ocr']} pages")
    print(f"  Average confidence: {result['avg_confidence']:.1f}%")
    print(f"  Total characters: {result['total_chars']}")
    print(f"  Success: {result['success']}")
    
    if result['text']:
        print(f"\nFirst 500 characters:")
        print(result['text'][:500])
        print("...")

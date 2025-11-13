# parser.py (improved PDF parsing with fallbacks)
import PyPDF2
from docx import Document
from pdfminer.high_level import extract_text

# Optional OCR support
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    Image = None
    pytesseract = None
    OCR_AVAILABLE = False

import os
import platform
# If on Windows, try to set common tesseract path automatically
if OCR_AVAILABLE and platform.system().lower().startswith('win'):
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    ]
    for p in common_paths:
        if os.path.exists(p):
            try:
                pytesseract.pytesseract.tesseract_cmd = p
                break
            except Exception:
                pass

# Optional PDF->image support for OCR fallback
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except Exception:
    convert_from_path = None
    PDF2IMAGE_AVAILABLE = False

class ResumeParser:
    """Parser for extracting text from various resume formats."""
    
    def parse(self, file_path):
        """
        Parse resume file and extract text content.
        Returns a single text string ('' if nothing extracted).
        """
        suffix = file_path.lower()
        if suffix.endswith('.pdf'):
            return self._parse_pdf(file_path)
        elif suffix.endswith('.docx'):
            return self._parse_docx(file_path)
        elif suffix.endswith('.txt'):
            return self._parse_txt(file_path)
        elif any(suffix.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            return self._parse_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
            
    def _parse_txt(self, file_path):
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error parsing TXT file: {str(e)}")
    
    def _parse_pdf(self, file_path):
        """Extract text from PDF file using pdfminer, PyPDF2 fallback and OCR fallback."""
        try:
            # 1) Try pdfminer (best for text PDFs)
            try:
                text = extract_text(file_path)
                if text and text.strip():
                    return text
            except Exception:
                text = ''

            # 2) Try PyPDF2 per-page extraction (some PDFs)
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    pages_text = []
                    for page in reader.pages:
                        try:
                            t = page.extract_text()
                            if t:
                                pages_text.append(t)
                        except Exception:
                            pages_text.append('')
                    combined = '\n'.join(pages_text).strip()
                    if combined:
                        return combined
            except Exception:
                pass

            # 3) OCR fallback (image/PDF scanned) if available
            if OCR_AVAILABLE and PDF2IMAGE_AVAILABLE:
                try:
                    poppler_path = None
                    if platform.system().lower().startswith('win'):
                        possible = [
                            r"C:\Program Files\poppler-23.05.0\Library\bin",
                            r"C:\Program Files\poppler-21.03.0\Library\bin",
                            r"C:\Program Files\poppler\Library\bin",
                            r"C:\poppler\bin"
                        ]
                        for pp in possible:
                            if os.path.exists(pp):
                                poppler_path = pp
                                break
                    images = convert_from_path(file_path, poppler_path=poppler_path) if poppler_path else convert_from_path(file_path)
                    ocr_text = []
                    for img in images:
                        try:
                            ocr_text.append(pytesseract.image_to_string(img))
                        except Exception:
                            ocr_text.append('')
                    combined = '\n'.join(ocr_text).strip()
                    if combined:
                        return combined
                except Exception:
                    pass

            # Nothing extracted
            return ''
        except Exception as e:
            raise Exception(f"Error parsing PDF file: {str(e)}")
    
    def _parse_docx(self, file_path):
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise Exception(f"Error parsing DOCX file: {str(e)}")

    def _parse_image(self, file_path):
        """Extract text from image files using Tesseract OCR (pytesseract)."""
        if not OCR_AVAILABLE:
            raise Exception("OCR libraries not installed (Pillow/pytesseract). Install 'pillow' and 'pytesseract' and ensure Tesseract is installed on your system.")
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            return text
        except Exception as e:
            raise Exception(f"Error parsing image file via OCR: {str(e)}")
# ----------------------------------------------------------------------
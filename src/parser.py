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

# Auto-detect Tesseract (Windows)
if OCR_AVAILABLE and platform.system().lower().startswith('win'):
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break

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
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error parsing TXT file: {str(e)}")

    # ------------------------------------------------------------
    # ✅ NEW: Very robust PDF extractor
    # ------------------------------------------------------------
    def _parse_pdf(self, file_path):
        """Extract text from PDF using pdfminer, PyPDF2, and OCR fallback."""
        try:
            # --- 1. Try pdfminer (best for text-based PDFs) ---
            text = extract_text(file_path)
            if text and text.strip():
                return text.strip()

            # --- 2. Try PyPDF2 (some PDFs decode only with this) ---
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    pages_text = []

                    for page in reader.pages:
                        try:
                            ptext = page.extract_text() or ''
                        except Exception:
                            ptext = ''
                        pages_text.append(ptext)

                    combined = "\n".join(pages_text).strip()
                    if combined:
                        return combined
            except Exception:
                pass

            # --- 3. OCR fallback for scanned/image PDFs ---
            if OCR_AVAILABLE and PDF2IMAGE_AVAILABLE:
                try:
                    poppler_path = None

                    # Auto-detect Poppler on Windows
                    if platform.system().lower().startswith('win'):
                        possible = [
                            r"C:\poppler\Library\bin",
                            r"C:\poppler\bin",
                            r"C:\Program Files\poppler-23.05.0\Library\bin",
                            r"C:\Program Files\poppler-24.02.0\Library\bin"
                        ]
                        for p in possible:
                            if os.path.exists(p):
                                poppler_path = p
                                break

                    # Convert PDF pages to images
                    images = convert_from_path(
                        file_path,
                        poppler_path=poppler_path
                    ) if poppler_path else convert_from_path(file_path)

                    ocr_text = []
                    for img in images:
                        try:
                            ocr_text.append(pytesseract.image_to_string(img))
                        except Exception:
                            ocr_text.append("")

                    final = "\n".join(ocr_text).strip()
                    if final:
                        return final

                except Exception:
                    pass

            # --- Final fallback ---
            return ""

        except Exception as e:
            raise Exception(f"Error parsing PDF file: {str(e)}")

    def _parse_docx(self, file_path):
        try:
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            raise Exception(f"Error parsing DOCX file: {str(e)}")

    def _parse_image(self, file_path):
        if not OCR_AVAILABLE:
            raise Exception(
                "OCR libraries not installed. Install pillow + pytesseract + Tesseract."
            )
        try:
            img = Image.open(file_path)
            return pytesseract.image_to_string(img)
        except Exception as e:
            raise Exception(f"Error parsing image file via OCR: {str(e)}")

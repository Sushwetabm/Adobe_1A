# from PIL import Image
# import pytesseract
# import re
# import statistics

# class StructureAnalysisAgent:
#     def __init__(self, doc):
#         self.doc = doc

#     def extract_structure(self):
#         structure_data = []

#         for i, page in enumerate(self.doc, start=1):
#             blocks = page.get_text("dict")["blocks"]
#             text_lines = sum(len(b.get("lines", [])) for b in blocks if b.get("type") == 0)

#             if text_lines < 15:
#                 pix = page.get_pixmap(dpi=300)
#                 img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
#                 ocr_text = pytesseract.image_to_string(img)

#                 for idx, line in enumerate(ocr_text.splitlines()):
#                     line = self._normalize_ocr_text(line)
#                     if not line:
#                         continue
#                     structure_data.append({
#                         "text":      line,
#                         "font_size": 16,
#                         "font":      "OCR",
#                         "bold":      False,
#                         "italic":    False,
#                         "bbox":      [0, idx * 20, pix.width, (idx + 1) * 20],
#                         "page":      i,
#                         "ocr":       True
#                     })
#                 continue

#             span_sizes = []
#             for block in blocks:
#                 if block.get("type") != 0:
#                     continue
#                 for line in block["lines"]:
#                     for span in line["spans"]:
#                         span_sizes.append(span["size"])

#             if not span_sizes:
#                 continue

#             median_size = statistics.median(span_sizes)

#             for block in blocks:
#                 if block.get("type") != 0:
#                     continue
#                 for line in block["lines"]:
#                     text = " ".join(s["text"] for s in line["spans"]).strip()
#                     if not text:
#                         continue

#                     span0 = line["spans"][0]
#                     size = span0["size"]
#                     font = span0["font"]
#                     is_bold = "bold" in font.lower()
#                     is_italic = "italic" in font.lower()
#                     y0 = line["bbox"][1]

#                     is_heading = (
#                         size >= median_size + 1 and
#                         len(text) < 100 and
#                         (is_bold or is_italic or re.match(r'^(\d+[\.\)]?\s*)?([A-Z][a-z]+\s*){1,6}$', text))
#                     )

#                     structure_data.append({
#                         "text":      text,
#                         "font_size": size,
#                         "font":      font,
#                         "bold":      is_bold,
#                         "italic":    is_italic,
#                         "bbox":      line["bbox"],
#                         "page":      i,
#                         "ocr":       False,
#                         "is_heading": is_heading
#                     })

#         return structure_data

#     def _normalize_ocr_text(self, text):
#         text = re.sub(r'(\b\w)\s(\w\b)', r'\1\2', text)
#         text = re.sub(r'\s{2,}', ' ', text)
#         return text.strip()


import re
import statistics
import json
from PIL import Image
import pytesseract
import fitz

class StructureAnalysisAgent:
    def __init__(self, all_elements_path, pdf_path):
        """
        :param all_elements_path: Path to all_elements_result.json produced by the model.
        :param pdf_path: Path to the original PDF file, needed for fallback OCR extraction.
        """
        self.all_elements_path = all_elements_path
        self.pdf_path = pdf_path

        with open(all_elements_path, "r", encoding="utf-8") as f:
            self.all_elements = json.load(f)

        self.fitz_doc = fitz.open(pdf_path)

    def extract_structure(self):
        structure_data = []

        for i, page_elements in enumerate(self.all_elements["pages"], start=1):
            # Filter only doc_title and paragraph_title!
            page_text_elements = [
                el for el in page_elements["elements"]
                if el.get("type") in {"doc_title", "paragraph_title"}
                and (el.get("text") or "").strip()
            ]

            if page_text_elements:
                # We'll still compute median_size, just for info, but no heading check needed
                span_sizes = [el["font_size"] for el in page_text_elements if "font_size" in el]
                median_size = statistics.median(span_sizes) if span_sizes else 12

                for el in page_text_elements:
                    text = el["text"].strip()
                    size = el.get("font_size", median_size)
                    font = el.get("font", "")
                    is_bold = "bold" in font.lower()
                    is_italic = "italic" in font.lower()
                    bbox = el.get("bbox", [0, 0, 0, 0])

                    # Treat all as heading without any checks
                    structure_data.append({
                        "text":     text,
                        "font_size":size,
                        "font":     font,
                        "bold":     is_bold,
                        "italic":   is_italic,
                        "bbox":     bbox,
                        "page":     i,
                        "ocr":      False,
                        "is_heading": True,    # Always True here
                        "type":     el["type"]  # Original type for reference
                    })
            else:
                # Fallback logic unchanged (direct extraction and OCR)
                page = self.fitz_doc[i - 1]
                blocks = page.get_text("dict")["blocks"]
                text_lines = sum(len(b.get("lines", [])) for b in blocks if b.get("type") == 0)

                if text_lines < 15:
                    # OCR fallback
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img)

                    for idx, line in enumerate(ocr_text.splitlines()):
                        line = self._normalize_ocr_text(line)
                        if not line:
                            continue
                        structure_data.append({
                            "text":     line,
                            "font_size":16,
                            "font":     "OCR",
                            "bold":     False,
                            "italic":   False,
                            "bbox":     [0, idx * 20, pix.width, (idx + 1) * 20],
                            "page":     i,
                            "ocr":      True
                        })
                else:
                    # Standard PDF extraction with heuristics unchanged
                    span_sizes = []
                    for block in blocks:
                        if block.get("type") != 0:
                            continue
                        for line in block["lines"]:
                            for span in line["spans"]:
                                span_sizes.append(span["size"])
                    if not span_sizes:
                        continue
                    median_size = statistics.median(span_sizes)
                    for block in blocks:
                        if block.get("type") != 0:
                            continue
                        for line in block["lines"]:
                            text = " ".join(s["text"] for s in line["spans"]).strip()
                            if not text:
                                continue
                            span0 = line["spans"][0]
                            size = span0["size"]
                            font = span0["font"]
                            is_bold = "bold" in font.lower()
                            is_italic = "italic" in font.lower()
                            bbox = line["bbox"]
                            is_heading = (
                                size >= median_size + 1 and
                                len(text) < 100 and
                                (is_bold or is_italic or re.match(r'^(\d+[\.\)]?\s*)?([A-Z][a-z]+\s*){1,6}$', text))
                            )
                            structure_data.append({
                                "text":     text,
                                "font_size":size,
                                "font":     font,
                                "bold":     is_bold,
                                "italic":   is_italic,
                                "bbox":     bbox,
                                "page":     i,
                                "ocr":      False,
                                "is_heading": is_heading
                            })
        
        return structure_data


    def _page_has_only_images(self, page_data):
        """
        Check if page contains only image elements (no text-based elements)
        """
        text_element_types = {"doc_title", "paragraph_title", "text", "paragraph", "list", "table"}
        
        for element in page_data["elements"]:
            if element.get("type") in text_element_types:
                return False
        
        # Check if there are any image/figure elements
        image_element_types = {"image", "figure", "chart"}
        has_images = any(el.get("type") in image_element_types for el in page_data["elements"])
        
        return has_images

    def _extract_with_ocr(self, page_index):
        """
        Extract text using OCR for image-only pages
        """
        results = []
        try:
            page = self.fitz_doc[page_index]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = pytesseract.image_to_string(img)

            for idx, line in enumerate(ocr_text.splitlines()):
                line = self._normalize_ocr_text(line)
                if not line:
                    continue
                    
                results.append({
                    "text": line,
                    "font_size": 16,
                    "font": "OCR",
                    "bold": False,
                    "italic": False,
                    "bbox": [0, idx * 20, pix.width, (idx + 1) * 20],
                    "page": page_index + 1,
                    "ocr": True,
                    "is_heading": self._is_likely_heading(line),
                    "type": "ocr_text",
                    "confidence": 0.8
                })
        except Exception as e:
            print(f"OCR extraction failed for page {page_index + 1}: {e}")
            
        return results

    def _extract_with_pymupdf(self, page_index):
        """
        Extract text using PyMuPDF for pages with text but no detected titles
        """
        results = []
        try:
            page = self.fitz_doc[page_index]
            blocks = page.get_text("dict")["blocks"]
            
            # Get font sizes for analysis
            span_sizes = []
            for block in blocks:
                if block.get("type") != 0:  # Skip non-text blocks
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        span_sizes.append(span["size"])
            
            if not span_sizes:
                return results
                
            median_size = statistics.median(span_sizes)

            for block in blocks:
                if block.get("type") != 0:
                    continue
                    
                for line in block["lines"]:
                    text = " ".join(s["text"] for s in line["spans"]).strip()
                    if not text:
                        continue

                    span0 = line["spans"][0]
                    size = span0["size"]
                    font = span0["font"]
                    is_bold = "bold" in font.lower()
                    is_italic = "italic" in font.lower()
                    bbox = line["bbox"]

                    # Only include potential headings
                    is_heading = (
                        size >= median_size + 1 and
                        len(text) < 100 and
                        (is_bold or is_italic or re.match(r'^(\d+[\.\)]?\s*)?([A-Z][a-z]+\s*){1,6}$', text))
                    )
                    
                    if is_heading:  # Only add if it's likely a heading
                        results.append({
                            "text": text,
                            "font_size": size,
                            "font": font,
                            "bold": is_bold,
                            "italic": is_italic,
                            "bbox": bbox,
                            "page": page_index + 1,
                            "ocr": False,
                            "is_heading": True,
                            "type": "pymupdf_heading",
                            "confidence": 0.9
                        })
        except Exception as e:
            print(f"PyMuPDF extraction failed for page {page_index + 1}: {e}")
            
        return results

    def _is_likely_heading(self, text):
        """
        Simple heuristic to determine if OCR text is likely a heading
        """
        if len(text) > 100:
            return False
            
        # Check for common heading patterns
        if re.match(r'^(\d+[\.\)]?\s*)?([A-Z][a-z]+\s*){1,6}$', text):
            return True
            
        # Check if it's mostly uppercase or title case
        if text.isupper() or text.istitle():
            return True
            
        return False

    def _normalize_ocr_text(self, text):
        """
        Normalize OCR text by fixing common OCR errors
        """
        # Fix spacing issues
        text = re.sub(r'(\b\w)\s(\w\b)', r'\1\2', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'fitz_doc'):
            self.fitz_doc.close()
# class StructureAnalysisAgent:
#     def __init__(self, doc):
#         self.doc = doc

#     def extract_structure(self):
#         structure_data = []
#         for i, page in enumerate(self.doc, start=1):
#             # Use 'dict' to get detailed structure including lines and spans
#             blocks = page.get_text("dict")["blocks"]
#             for block in blocks:
#                 if block["type"] != 0:  # only process text blocks
#                     continue
#                 for line in block["lines"]:
#                     # Combine all spans in a line to form a single text entry
#                     line_text = " ".join(s["text"] for s in line["spans"]).strip()
                    
#                     if not line_text or not line["spans"]:
#                         continue

#                     # Use the style of the first span to represent the whole line
#                     first_span = line["spans"][0]
#                     font_size = first_span["size"]
                    
#                     # Skip very small fonts often found in headers/footers
#                     if font_size < 7:
#                         continue

#                     structure_data.append({
#                         "text": line_text,
#                         "font_size": font_size,
#                         "font": first_span["font"],
#                         "bold": "bold" in first_span["font"].lower(),
#                         "italic": "italic" in first_span["font"].lower(),
#                         "bbox": line["bbox"],  # Use the line's bounding box
#                         "page": i
#                     })
#         return structure_data

# class StructureAnalysisAgent:
#     def __init__(self, doc):
#         self.doc = doc

#     def extract_structure(self):
#         structure_data = []
#         for i, page in enumerate(self.doc, start=1):
#             # Use 'dict' to get detailed structure including lines and spans
#             blocks = page.get_text("dict")["blocks"]
#             for block in blocks:
#                 if block["type"] != 0:  # only process text blocks
#                     continue
#                 for line in block["lines"]:
#                     # Combine all spans in a line to form a single text entry
#                     line_text = " ".join(s["text"] for s in line["spans"]).strip()
                    
#                     if not line_text or not line["spans"]:
#                         continue

#                     # Use the style of the first span to represent the whole line
#                     first_span = line["spans"][0]
#                     font_size = first_span["size"]
                    
#                     # Skip very small fonts often found in headers/footers
#                     if font_size < 7:
#                         continue

#                     structure_data.append({
#                         "text": line_text,
#                         "font_size": font_size,
#                         "font": first_span["font"],
#                         "bold": "bold" in first_span["font"].lower(),
#                         "italic": "italic" in first_span["font"].lower(),
#                         "bbox": line["bbox"],  # Use the line's bounding box
#                         "page": i
#                     })
#         return structure_data
# agents/structure_agent.py
from PIL import Image
import pytesseract
import re
import statistics

class StructureAnalysisAgent:
    def __init__(self, doc):
        self.doc = doc
        print(f"[DEBUG] Loaded StructureAnalysisAgent from {__file__}")

    def extract_structure(self):
        structure_data = []

        for i, page in enumerate(self.doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            text_lines = sum(len(b.get("lines", [])) for b in blocks if b.get("type") == 0)

            if text_lines < 15:
                print(f"[DEBUG] OCR fallback on page {i}: only {text_lines} native text lines")
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img)

                for idx, line in enumerate(ocr_text.splitlines()):
                    line = self._normalize_ocr_text(line)
                    if not line:
                        continue
                    structure_data.append({
                        "text":      line,
                        "font_size": 16,
                        "font":      "OCR",
                        "bold":      False,
                        "italic":    False,
                        "bbox":      [0, idx * 20, pix.width, (idx + 1) * 20],
                        "page":      i,
                        "ocr":       True
                    })
                continue

            # Collect span features for statistics
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
                    y0 = line["bbox"][1]

                    # Heuristic score for heading likelihood
                    is_heading = (
                        size >= median_size + 1 and
                        len(text) < 100 and
                        (is_bold or is_italic or re.match(r'^(\d+[\.\)]?\s*)?([A-Z][a-z]+\s*){1,6}$', text))
                    )

                    structure_data.append({
                        "text":      text,
                        "font_size": size,
                        "font":      font,
                        "bold":      is_bold,
                        "italic":    is_italic,
                        "bbox":      line["bbox"],
                        "page":      i,
                        "ocr":       False,
                        "is_heading": is_heading
                    })

        return structure_data

    def _normalize_ocr_text(self, text):
        text = re.sub(r'(\b\w)\s(\w\b)', r'\1\2', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

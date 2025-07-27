from PIL import Image
import pytesseract
import re
import statistics

class StructureAnalysisAgent:
    def __init__(self, doc):
        self.doc = doc

    def extract_structure(self):
        structure_data = []

        for i, page in enumerate(self.doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            text_lines = sum(len(b.get("lines", [])) for b in blocks if b.get("type") == 0)

            if text_lines < 15:
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

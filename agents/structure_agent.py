class StructureAnalysisAgent:
    def __init__(self, doc):
        self.doc = doc

    def extract_structure(self):
        structure_data = []
        for i, page in enumerate(self.doc, start=1):
            # Use 'dict' to get detailed structure including lines and spans
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] != 0:  # only process text blocks
                    continue
                for line in block["lines"]:
                    # Combine all spans in a line to form a single text entry
                    line_text = " ".join(s["text"] for s in line["spans"]).strip()
                    
                    if not line_text or not line["spans"]:
                        continue

                    # Use the style of the first span to represent the whole line
                    first_span = line["spans"][0]
                    font_size = first_span["size"]
                    
                    # Skip very small fonts often found in headers/footers
                    if font_size < 7:
                        continue

                    structure_data.append({
                        "text": line_text,
                        "font_size": font_size,
                        "font": first_span["font"],
                        "bold": "bold" in first_span["font"].lower(),
                        "italic": "italic" in first_span["font"].lower(),
                        "bbox": line["bbox"],  # Use the line's bounding box
                        "page": i
                    })
        return structure_data
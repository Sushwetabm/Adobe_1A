class StructureAnalysisAgent:
    def __init__(self, doc):
        self.doc = doc

    def extract_structure(self):
        structure_data = []
        for i, page in enumerate(self.doc):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] != 0: continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        structure_data.append({
                            "text": span["text"].strip(),
                            "font_size": span["size"],
                            "font": span["font"],
                            "bold": "Bold" in span["font"],
                            "italic": "Italic" in span["font"],
                            "bbox": span["bbox"],
                            "page": i + 1
                        })
        return structure_data

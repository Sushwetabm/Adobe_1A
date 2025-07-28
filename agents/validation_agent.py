
from collections import Counter
import re

class ValidationAgent:
    def __init__(self, headings, all_structure):
        self.headings = headings
        self.all_structure = all_structure

    def validate(self):
        def clean_spacing(txt):
            txt = re.sub(r'(\b\w)\s(\w\b)', r'\1\2', txt)
            txt = re.sub(r'\s{2,}', ' ', txt)
            return txt.strip()

        def is_poster_like_page(page_data):
            return any(x.get("ocr", False) for x in page_data)

        try:
            pages = sorted({x["page"] for x in self.all_structure})
            final_outline = []
            final_title = ""

            # TITLE
            page1 = [x for x in self.all_structure if x["page"] == 1 and not x.get("ocr", False)]
            if page1:
                valid_fr_items = [x for x in page1 if isinstance(x.get("font_ratio"), (int, float))]
                if valid_fr_items:
                    max_fr = max(x["font_ratio"] for x in valid_fr_items)
                    cands = [x for x in valid_fr_items if x["font_ratio"] >= max_fr * 0.9]
                    if cands:
                        cands.sort(key=lambda x: (x["bbox"][1], x["bbox"][0]))
                        final_title = clean_spacing("  ".join(x["text"] for x in cands))
                    else:
                        big = max(valid_fr_items, key=lambda x: x["font_size"])
                        final_title = clean_spacing(big["text"])

            structural_keywords = [
                "table of contents", "acknowledgements", "references",
                "introduction", "conclusion", "appendix", "overview", "revision history"
            ]

            for pg in pages:
                page_data = [x for x in self.all_structure if x["page"] == pg]

                if is_poster_like_page(page_data):
                    ocr_lines = [x for x in page_data if x.get("ocr", False)]
                    mixed = [x for x in ocr_lines if re.search(r"[a-z]", x["text"])]
                    candidates = mixed if mixed else ocr_lines
                    if not candidates:
                        continue
                    try:
                        best = max(candidates, key=lambda x: (len(x["text"].strip()), x["bbox"][1]))
                        final_outline.append({
                            "level": "H1",
                            "text": clean_spacing(best["text"]) + " ",
                            "page": pg
                        })
                    except Exception as e:
                        print(f"[ERROR] Poster fallback failed on page {pg}: {e}")
                    continue

                page_headings = [h for h in self.headings if h["page"] == pg]
                texts = [clean_spacing(h["text"]) for h in page_headings]
                counts = Counter(texts)
                page_headings = [
                    h for h in page_headings
                    if counts[clean_spacing(h["text"])] <= 3
                ]

                for h in sorted(page_headings, key=lambda h: h["bbox"][1]):
                    txt = clean_spacing(h["text"])

                    if len(txt) < 3:
                        continue  # ignore too short
                    if re.fullmatch(r"\d+\.?", txt):
                        continue  # only numeric
                    if any(k in txt.lower() for k in ["copyright", "this document may be copied"]):
                        continue
                    final_outline.append({
                        "level": h["level"],
                        "text": txt + (" " if not txt.endswith(" ") else ""),
                        "page": pg
                    })

            return {
                "title": final_title.strip(),
                "outline": final_outline
            }

        except Exception as e:
            print(f"[FATAL] ValidationAgent crashed: {e}")
            return {"title": "", "outline": []}

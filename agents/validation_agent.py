
# from collections import Counter
# import re

# class ValidationAgent:
#     def __init__(self, headings, all_structure):
#         self.headings = headings
#         self.all_structure = all_structure

#     def validate(self):
#         # 1) Deduplicate over‑repeated headings (but be more lenient)
#         texts = [h["text"].strip() for h in self.headings]
#         counts = Counter(texts)
#         # Allow up to 3 occurrences instead of 2 for things like chapter titles
#         self.headings = [h for h in self.headings if counts[h["text"].strip()] <= 3]

#         # 2) Enhanced title detection
#         page1 = [x for x in self.all_structure if x["page"] == 1 and len(x["text"].strip()) > 5]
#         if not page1:
#             title = "Untitled"
#             title_parts = []
#         else:
#             # Find max font_ratio on page 1
#             max_fr = max(x["font_ratio"] for x in page1)
            
#             # Only consider spans that are significantly larger (top 10% font ratio)
#             # and are likely titles (short, prominent text)
#             title_candidates = []
#             for x in page1:
#                 if (x["font_ratio"] >= max_fr * 0.9 and 
#                     len(x["text"].strip().split()) <= 10 and  # Titles are usually short
#                     x["bbox"][1] <= max(item["bbox"][1] for item in page1[:5])):  # Near top of page
#                     title_candidates.append(x)
            
#             if title_candidates:
#                 title_parts = sorted(title_candidates, key=lambda x: (x["bbox"][1], x["bbox"][0]))
#                 title = "  ".join(x["text"].strip() for x in title_parts)
#             else:
#                 # Fallback: use largest font on page 1
#                 largest_item = max(page1, key=lambda x: x["font_size"])
#                 title = largest_item["text"].strip()
#                 title_parts = [largest_item]

#         # 3) Build outline with MUCH more lenient title filtering
#         title_texts = set()
#         for part in title_parts:
#             # Only exclude exact matches, not partial matches
#             title_texts.add(part["text"].strip())
        
#         outline = sorted(self.headings, key=lambda h: (h["page"], h["bbox"][1]))
#         clean = []
        
#         # Pattern to identify clear structural headings that should never be excluded
#         numbered_pattern = re.compile(r"^\d+(\.\d+)*\.?\s")
#         structural_keywords = ["table of contents", "acknowledgements", "references", 
#                              "introduction", "conclusion", "appendix", "bibliography"]
        
#         for h in outline:
#             txt = h["text"].strip()
            
#             # Never exclude numbered headings or clear structural elements
#             is_numbered = numbered_pattern.match(txt.lower())
#             is_structural = any(keyword in txt.lower() for keyword in structural_keywords)
            
#             # Only exclude if it's an EXACT title match and not a structural heading
#             should_exclude = (txt in title_texts and not is_numbered and not is_structural)
            
#             if not should_exclude:
#                 clean.append({
#                     "level": h["level"],
#                     "text": txt if txt.endswith(" ") else txt + " ",
#                     "page": h["page"]
#                 })

#         # 4) Fix heading levels if they seem wrong
#         clean = self._fix_heading_levels(clean)
        
#         return {"title": title, "outline": clean}
    
#     def _fix_heading_levels(self, outline):
#         """Fix heading level progression to ensure proper hierarchy"""
#         if not outline:
#             return outline
            
#         # Pattern for numbered headings
#         numbered_pattern = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?\.?\s")
        
#         # Analyze numbering patterns
#         for item in outline:
#             match = numbered_pattern.match(item["text"])
#             if match:
#                 level1, level2, level3 = match.groups()
#                 if level1 and not level2:  # e.g., "1. Introduction"
#                     item["level"] = "H1"
#                 elif level1 and level2 and not level3:  # e.g., "2.1 Subsection"
#                     item["level"] = "H2"
#                 elif level1 and level2 and level3:  # e.g., "2.1.1 Subsubsection"
#                     item["level"] = "H3"
        
#         return outline


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

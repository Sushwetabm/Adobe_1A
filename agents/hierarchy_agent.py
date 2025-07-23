
# from collections import defaultdict
# import re

# class HierarchyAgent:
#     def __init__(self, processed_data, visual_features=None, text_features=None):
#         self.data = processed_data

#     def rank_headings(self):
#         # 1. Group all text items by their visual style (font size and boldness)
#         styles = defaultdict(list)
#         for item in self.data:
#             # Use precise font sizes but round to 0.5 for grouping similar sizes
#             rounded_size = round(item["font_size"] * 2) / 2
#             style_key = (rounded_size, item["bold"])
#             styles[style_key].append(item)

#         if not styles:
#             return []

#         # 2. Find the primary style (most common style in the document)
#         primary_style = max(styles, key=lambda k: len(styles[k]))
#         primary_size, primary_is_bold = primary_style

#         # 3. Pre-filter to identify document type
#         if self._is_form_document():
#             # For forms, be very strict - only very large or very bold text
#             return self._detect_form_headings(styles, primary_style)

#         # 4. For regular documents, use enhanced heading detection
#         return self._detect_document_headings(styles, primary_style)

#     def _is_form_document(self):
#         """Detect if this is a form document (should have minimal/no outline)"""
#         total_items = len(self.data)
#         if total_items == 0:
#             return False
            
#         # Count indicators of forms
#         form_indicators = 0
        
#         # 1. High ratio of single numbers/letters (form field labels)
#         single_chars = sum(1 for item in self.data 
#                           if len(item["text"].strip()) <= 3 and 
#                           re.match(r'^\d+\.?$|^[A-Z]\.?$', item["text"].strip()))
        
#         # 2. High ratio of short text (< 3 words)
#         short_text = sum(1 for item in self.data if len(item["text"].split()) < 3)
        
#         # 3. Presence of form-like patterns
#         form_patterns = [
#             r'name\s*:?$', r'date\s*:?$', r'signature', r'address\s*:?$',
#             r'application\s+form', r'serial\s+no', r's\.no', r'amount'
#         ]
#         form_text_count = sum(1 for item in self.data 
#                              for pattern in form_patterns
#                              if re.search(pattern, item["text"].lower()))
        
#         # Decision criteria
#         single_char_ratio = single_chars / total_items
#         short_text_ratio = short_text / total_items
#         form_text_ratio = form_text_count / total_items
        
#         # It's likely a form if:
#         return (single_char_ratio > 0.2 or  # >20% single characters
#                 (short_text_ratio > 0.7 and form_text_ratio > 0.1))  # >70% short text + form patterns

#     def _detect_form_headings(self, styles, primary_style):
#         """Very conservative heading detection for forms"""
#         primary_size, primary_is_bold = primary_style
        
#         headings = []
#         for style, items in styles.items():
#             size, is_bold = style
            
#             # Only detect headings that are significantly larger AND in meaningful text
#             if (size > primary_size + 2 and  # Much larger font
#                 all(len(item["text"].split()) >= 3 for item in items)):  # Multi-word text only
                
#                 for item in items:
#                     # Additional filter: must look like a real heading
#                     text = item["text"].strip().lower()
#                     if (not re.match(r'^\d+\.?\s*$', text) and  # Not just numbers
#                         not re.match(r'^[a-z]+\s*:?\s*$', text) and  # Not single words with colon
#                         len(text) > 5):  # Reasonable length
#                         item["level"] = "H1"
#                         headings.append(item)
        
#         return headings

#     def _detect_document_headings(self, styles, primary_style):
#         """Enhanced heading detection for regular documents"""
#         primary_size, primary_is_bold = primary_style
        
#         heading_styles = {}
#         numbered_pattern = re.compile(r"^\d+(\.\d+)*\.?\s+\w+")  # Must have text after number
        
#         for style, items in styles.items():
#             size, is_bold = style
            
#             # Enhanced criteria for document headings
#             is_larger = size > primary_size + 0.3  # Slightly larger
#             is_bolder = is_bold and not primary_is_bold
            
#             # Check for meaningful numbered headings (not just form numbers)
#             meaningful_numbered = any(
#                 numbered_pattern.match(item["text"]) and 
#                 len(item["text"].split()) >= 2  # At least 2 words
#                 for item in items
#             )
            
#             # Check for structural keywords
#             structural_keywords = [
#                 'introduction', 'conclusion', 'references', 'acknowledgement',
#                 'table of contents', 'abstract', 'summary', 'overview',
#                 'chapter', 'section', 'appendix', 'bibliography'
#             ]
#             has_structural = any(
#                 any(keyword in item["text"].lower() for keyword in structural_keywords)
#                 for item in items
#             )
            
#             # Check if isolated and different from primary
#             is_isolated_and_different = (
#                 style != primary_style and 
#                 any(item.get("is_isolated", False) for item in items) and
#                 len(items) < len(styles[primary_style]) / 3  # Not too common
#             )
            
#             if (is_larger or is_bolder or meaningful_numbered or 
#                 has_structural or is_isolated_and_different):
                
#                 # Final filter: exclude very short or form-like text
#                 filtered_items = []
#                 for item in items:
#                     text = item["text"].strip()
#                     if (len(text) > 2 and  # Not too short
#                         not re.match(r'^\d+\.?\s*$', text) and  # Not just numbers
#                         not re.match(r'^[A-Za-z]\s*:?\s*$', text)):  # Not single letters
#                         filtered_items.append(item)
                
#                 if filtered_items:
#                     heading_styles[style] = filtered_items

#         if not heading_styles:
#             return []

#         # Ranking with multiple factors
#         def get_heading_score(style):
#             size, is_bold = style
#             items = heading_styles[style]
            
#             score = size  # Base score from font size
            
#             if is_bold:
#                 score += 1
            
#             # Strong bonus for meaningful numbered sections
#             if any(numbered_pattern.match(item["text"]) for item in items):
#                 score += 3
            
#             # Bonus for structural keywords
#             structural_keywords = [
#                 'introduction', 'conclusion', 'references', 'acknowledgement',
#                 'table of contents', 'abstract', 'summary', 'overview'
#             ]
#             if any(any(kw in item["text"].lower() for kw in structural_keywords) 
#                    for item in items):
#                 score += 2
                
#             return score

#         ranked_styles = sorted(heading_styles.keys(), key=get_heading_score, reverse=True)

#         # Assign levels based on content analysis
#         level_map = {}
        
#         # Group by numbering patterns
#         h1_styles = []  # Top-level sections (1., 2., 3.)
#         h2_styles = []  # Sub-sections (1.1, 2.1, etc.)
#         h3_styles = []  # Other headings
        
#         for style in ranked_styles:
#             items = heading_styles[style]
            
#             has_toplevel = any(re.match(r"^\d+\.\s+\w+", item["text"]) for item in items)
#             has_sublevel = any(re.match(r"^\d+\.\d+\s+\w+", item["text"]) for item in items)
            
#             if has_toplevel and not has_sublevel:
#                 h1_styles.append(style)
#             elif has_sublevel:
#                 h2_styles.append(style)
#             else:
#                 h3_styles.append(style)
        
#         # Assign levels
#         level_counter = 1
#         for style_group in [h1_styles, h2_styles, h3_styles]:
#             for style in style_group:
#                 if level_counter <= 3:
#                     level_map[style] = f"H{level_counter}"
#                     level_counter += 1

#         # If no clear numbering, fall back to size-based assignment
#         if not level_map and ranked_styles:
#             for i, style in enumerate(ranked_styles[:3]):
#                 level_map[style] = f"H{i + 1}"

#         # Build final headings list
#         headings = []
#         for item in self.data:
#             item_style = (round(item["font_size"] * 2) / 2, item["bold"])
#             if item_style in level_map:
#                 item["level"] = level_map[item_style]
#                 headings.append(item)
        
#         return headings

from collections import defaultdict, Counter
from statistics import mean, pstdev
from utils.helpers import is_toc_page

class HierarchyAnalysisAgent:
    def __init__(self, processed_data, visual_features=None, text_features=None):
        self.structure_data = processed_data
        self.visual = visual_features
        self.text = text_features

    def score_line(self, line, font_size_stats):
        score = 0
        size = line["font_size"]
        mean_size = font_size_stats["mean"]
        std_size = font_size_stats["std"]

        # Normalize font size (z-score)
        if std_size > 0:
            z_score = (size - mean_size) / std_size
            score += z_score * 2
        if line.get("bold"): score += 1.0
        if line["bbox"][1] < 200: score += 0.75
        if line.get("ocr"): score -= 0.5

        # Short/Long text penalty
        wc = len(line["text"].split())
        if 2 <= wc <= 10:
            score += 0.5
        elif wc > 20:
            score -= 1.0
        elif wc <= 1:
            score -= 0.5  # prevent 1-word lines

        # Form detection: punish colon-ended labels
        if line["text"].strip().endswith(":"):
            score -= 0.8
        return score

    def determine_levels(self, top_lines):
        sizes = sorted(set(l["font_size"] for l in top_lines))
        levels = {}
        if not sizes: return levels
        sizes.sort(reverse=True)
        levels[sizes[0]] = "H1"
        if len(sizes) > 1: levels[sizes[1]] = "H2"
        if len(sizes) > 2: levels[sizes[2]] = "H3"
        return levels

    def is_form_like(self):
        """Heuristic: If >5 short labels with numbers like '1.', '2.', etc., on first page"""
        p1_lines = [l for l in self.structure_data if l["page"] == 1]
        numbered = sum(1 for l in p1_lines if l["text"].strip().split()[0].rstrip(".").isdigit())
        colon_ended = sum(1 for l in p1_lines if l["text"].strip().endswith(":"))
        return (numbered + colon_ended) >= 5

    def rank_headings(self):
        if not self.structure_data:
            return {"title": "", "outline": []}

        font_sizes = [line["font_size"] for line in self.structure_data]
        font_size_stats = {
            "mean": mean(font_sizes),
            "std": pstdev(font_sizes) if len(font_sizes) > 1 else 1.0
        }

        # Score all lines
        scored = []
        for line in self.structure_data:
            if is_toc_page(self.structure_data, line["page"]): continue  # ❌ skip ToC pages
            score = self.score_line(line, font_size_stats)
            scored.append((score, line))

        scored.sort(reverse=True, key=lambda x: x[0])
        top_k = max(5, int(0.05 * len(scored)))
        top_lines = [line for score, line in scored[:top_k]]

        level_map = self.determine_levels(top_lines)

        outline = []
        seen = set()
        for line in top_lines:
            txt = line["text"]
            if txt in seen: continue
            seen.add(txt)
            outline.append({
                "level": level_map.get(line["font_size"], "H3"),
                "text": txt,
                "page": line["page"],
                "bbox": line["bbox"]
            })

        # Detect title on Page 1, max length line
        title = ""
        title_cands = [l for l in outline if l["level"] == "H1" and l["page"] == 1]
        if title_cands:
            title = max(title_cands, key=lambda x: len(x["text"]))["text"]

        # ⛔ In form mode, return only title
        if self.is_form_like():
            return {
                "title": title.strip(),
                "outline": []  # ✅ don't add title to outline
            }


        return {
            "title": title.strip(),
            "outline": outline
        }

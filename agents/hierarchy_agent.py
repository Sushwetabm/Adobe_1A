# # hierarchy_agent.py

# from collections import defaultdict

# class HierarchyAgent:
#     def __init__(self, processed_data, visual_features=None, text_features=None):
#         self.data = processed_data

#     def rank_headings(self):
#         # 1. Group all text items by their visual style (font size and boldness)
#         styles = defaultdict(list)
#         for item in self.data:
#             style_key = (round(item["font_size"]), item["bold"])
#             styles[style_key].append(item)

#         if not styles:
#             return []

#         # 2. Find the primary style (most common style in the document)
#         primary_style = max(styles, key=lambda k: len(styles[k]))
#         primary_size, primary_is_bold = primary_style

#         # 3. A style is a "heading style" ONLY if it meets strict criteria.
#         # This is the key change to prevent misidentifying form labels.
#         heading_styles = {}
#         for style, items in styles.items():
#             size, is_bold = style
            
#             # CRITERIA: A heading MUST be either:
#             #   a) Noticeably larger than the primary text, OR
#             #   b) Bolder than the primary text (and not tiny)
#             is_larger = size > primary_size + 1 # At least 1pt larger to be significant
#             is_bolder = is_bold and not primary_is_bold and size >= primary_size - 1

#             if style != primary_style and (is_larger or is_bolder):
#                  # Another check: filter out styles that are extremely common, as they might be body text
#                 if len(items) > len(styles[primary_style]) / 2:
#                     continue
#                 heading_styles[style] = items

#         if not heading_styles:
#             return [] # No styles met the strict heading criteria, return an empty outline.

#         # 4. Rank the confirmed heading styles by prominence (font size descending)
#         ranked_heading_styles = sorted(heading_styles.keys(), key=lambda s: s[0], reverse=True)

#         # 5. Map the top-ranked styles to H1, H2, H3
#         level_map = {}
#         for i, style in enumerate(ranked_heading_styles):
#             level = f"H{i + 1}"
#             if i < 3: # H1, H2, H3
#                 level_map[style] = level
#             else:
#                 break

#         # 6. Build the final list of headings
#         headings = []
#         for item in self.data:
#             item_style = (round(item["font_size"]), item["bold"])
#             if item_style in level_map:
#                 item["level"] = level_map[item_style]
#                 headings.append(item)
        
#         return headings

from collections import defaultdict
import re

class HierarchyAgent:
    def __init__(self, processed_data, visual_features=None, text_features=None):
        self.data = processed_data

    def rank_headings(self):
        # 1. Group all text items by their visual style (font size and boldness)
        styles = defaultdict(list)
        for item in self.data:
            # Use precise font sizes but round to 0.5 for grouping similar sizes
            rounded_size = round(item["font_size"] * 2) / 2
            style_key = (rounded_size, item["bold"])
            styles[style_key].append(item)

        if not styles:
            return []

        # 2. Find the primary style (most common style in the document)
        primary_style = max(styles, key=lambda k: len(styles[k]))
        primary_size, primary_is_bold = primary_style

        # 3. Pre-filter to identify document type
        if self._is_form_document():
            # For forms, be very strict - only very large or very bold text
            return self._detect_form_headings(styles, primary_style)

        # 4. For regular documents, use enhanced heading detection
        return self._detect_document_headings(styles, primary_style)

    def _is_form_document(self):
        """Detect if this is a form document (should have minimal/no outline)"""
        total_items = len(self.data)
        if total_items == 0:
            return False
            
        # Count indicators of forms
        form_indicators = 0
        
        # 1. High ratio of single numbers/letters (form field labels)
        single_chars = sum(1 for item in self.data 
                          if len(item["text"].strip()) <= 3 and 
                          re.match(r'^\d+\.?$|^[A-Z]\.?$', item["text"].strip()))
        
        # 2. High ratio of short text (< 3 words)
        short_text = sum(1 for item in self.data if len(item["text"].split()) < 3)
        
        # 3. Presence of form-like patterns
        form_patterns = [
            r'name\s*:?$', r'date\s*:?$', r'signature', r'address\s*:?$',
            r'application\s+form', r'serial\s+no', r's\.no', r'amount'
        ]
        form_text_count = sum(1 for item in self.data 
                             for pattern in form_patterns
                             if re.search(pattern, item["text"].lower()))
        
        # Decision criteria
        single_char_ratio = single_chars / total_items
        short_text_ratio = short_text / total_items
        form_text_ratio = form_text_count / total_items
        
        # It's likely a form if:
        return (single_char_ratio > 0.2 or  # >20% single characters
                (short_text_ratio > 0.7 and form_text_ratio > 0.1))  # >70% short text + form patterns

    def _detect_form_headings(self, styles, primary_style):
        """Very conservative heading detection for forms"""
        primary_size, primary_is_bold = primary_style
        
        headings = []
        for style, items in styles.items():
            size, is_bold = style
            
            # Only detect headings that are significantly larger AND in meaningful text
            if (size > primary_size + 2 and  # Much larger font
                all(len(item["text"].split()) >= 3 for item in items)):  # Multi-word text only
                
                for item in items:
                    # Additional filter: must look like a real heading
                    text = item["text"].strip().lower()
                    if (not re.match(r'^\d+\.?\s*$', text) and  # Not just numbers
                        not re.match(r'^[a-z]+\s*:?\s*$', text) and  # Not single words with colon
                        len(text) > 5):  # Reasonable length
                        item["level"] = "H1"
                        headings.append(item)
        
        return headings

    def _detect_document_headings(self, styles, primary_style):
        """Enhanced heading detection for regular documents"""
        primary_size, primary_is_bold = primary_style
        
        heading_styles = {}
        numbered_pattern = re.compile(r"^\d+(\.\d+)*\.?\s+\w+")  # Must have text after number
        
        for style, items in styles.items():
            size, is_bold = style
            
            # Enhanced criteria for document headings
            is_larger = size > primary_size + 0.3  # Slightly larger
            is_bolder = is_bold and not primary_is_bold
            
            # Check for meaningful numbered headings (not just form numbers)
            meaningful_numbered = any(
                numbered_pattern.match(item["text"]) and 
                len(item["text"].split()) >= 2  # At least 2 words
                for item in items
            )
            
            # Check for structural keywords
            structural_keywords = [
                'introduction', 'conclusion', 'references', 'acknowledgement',
                'table of contents', 'abstract', 'summary', 'overview',
                'chapter', 'section', 'appendix', 'bibliography'
            ]
            has_structural = any(
                any(keyword in item["text"].lower() for keyword in structural_keywords)
                for item in items
            )
            
            # Check if isolated and different from primary
            is_isolated_and_different = (
                style != primary_style and 
                any(item.get("is_isolated", False) for item in items) and
                len(items) < len(styles[primary_style]) / 3  # Not too common
            )
            
            if (is_larger or is_bolder or meaningful_numbered or 
                has_structural or is_isolated_and_different):
                
                # Final filter: exclude very short or form-like text
                filtered_items = []
                for item in items:
                    text = item["text"].strip()
                    if (len(text) > 2 and  # Not too short
                        not re.match(r'^\d+\.?\s*$', text) and  # Not just numbers
                        not re.match(r'^[A-Za-z]\s*:?\s*$', text)):  # Not single letters
                        filtered_items.append(item)
                
                if filtered_items:
                    heading_styles[style] = filtered_items

        if not heading_styles:
            return []

        # Ranking with multiple factors
        def get_heading_score(style):
            size, is_bold = style
            items = heading_styles[style]
            
            score = size  # Base score from font size
            
            if is_bold:
                score += 1
            
            # Strong bonus for meaningful numbered sections
            if any(numbered_pattern.match(item["text"]) for item in items):
                score += 3
            
            # Bonus for structural keywords
            structural_keywords = [
                'introduction', 'conclusion', 'references', 'acknowledgement',
                'table of contents', 'abstract', 'summary', 'overview'
            ]
            if any(any(kw in item["text"].lower() for kw in structural_keywords) 
                   for item in items):
                score += 2
                
            return score

        ranked_styles = sorted(heading_styles.keys(), key=get_heading_score, reverse=True)

        # Assign levels based on content analysis
        level_map = {}
        
        # Group by numbering patterns
        h1_styles = []  # Top-level sections (1., 2., 3.)
        h2_styles = []  # Sub-sections (1.1, 2.1, etc.)
        h3_styles = []  # Other headings
        
        for style in ranked_styles:
            items = heading_styles[style]
            
            has_toplevel = any(re.match(r"^\d+\.\s+\w+", item["text"]) for item in items)
            has_sublevel = any(re.match(r"^\d+\.\d+\s+\w+", item["text"]) for item in items)
            
            if has_toplevel and not has_sublevel:
                h1_styles.append(style)
            elif has_sublevel:
                h2_styles.append(style)
            else:
                h3_styles.append(style)
        
        # Assign levels
        level_counter = 1
        for style_group in [h1_styles, h2_styles, h3_styles]:
            for style in style_group:
                if level_counter <= 3:
                    level_map[style] = f"H{level_counter}"
                    level_counter += 1

        # If no clear numbering, fall back to size-based assignment
        if not level_map and ranked_styles:
            for i, style in enumerate(ranked_styles[:3]):
                level_map[style] = f"H{i + 1}"

        # Build final headings list
        headings = []
        for item in self.data:
            item_style = (round(item["font_size"] * 2) / 2, item["bold"])
            if item_style in level_map:
                item["level"] = level_map[item_style]
                headings.append(item)
        
        return headings
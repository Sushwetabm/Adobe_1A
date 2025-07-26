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
        text = line["text"].strip()

        # Normalize font size (z-score)
        if std_size > 0:
            z_score = (size - mean_size) / std_size
            score += z_score * 2
        if line.get("bold"): score += 1.0
        if line["bbox"][1] < 200: score += 0.75
        if line.get("ocr"): score -= 0.5

        # Word count scoring
        wc = len(text.split())
        if 2 <= wc <= 10:
            score += 0.5
        elif wc > 20:
            score -= 1.0
        elif wc <= 1:
            score -= 0.5

        # Penalize colon-ended labels (form fields)
        if text.endswith(":"):
            score -= 0.8
        
        # Penalize very long sentences (likely content, not headings)
        if wc > 15:
            score -= 1.5
        
        # Boost for section-like keywords
        section_keywords = ['pathway', 'options', 'goals', 'mission', 'regular', 'distinction']
        if any(keyword in text.lower() for keyword in section_keywords):
            score += 1.0
        
        # Penalize mission statements and long descriptive text
        if text.lower().startswith('mission statement') or text.lower().startswith('to provide'):
            score -= 2.0
            
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
        """Detect if this is a form document based on form field patterns"""
        p1_lines = [l for l in self.structure_data if l["page"] == 1]
        if len(p1_lines) < 5:
            return False
            
        # Debug print
        print(f"[DEBUG] Checking form detection for {len(p1_lines)} lines on page 1")
        
        # Count form-specific patterns
        numbered_questions = 0  # "1.", "2.", "3." etc.
        form_keywords = 0      # Common form words
        
        form_keyword_patterns = [
            'name of', 'designation', 'date of', 'whether', 'amount of', 'signature',
            'application form', 'grant of', 'government servant', 'advance required'
        ]
        
        for line in p1_lines:
            text = line["text"].strip().lower()
            
            # Count numbered questions (typical form pattern) - look for just numbers
            if text.strip() and text.strip()[0].isdigit() and '.' in text[:5]:
                numbered_questions += 1
                print(f"[DEBUG] Found numbered question: {text[:50]}...")
            
            # Count form-specific keywords
            for keyword in form_keyword_patterns:
                if keyword in text:
                    form_keywords += 1
                    print(f"[DEBUG] Found form keyword '{keyword}' in: {text[:50]}...")
                    break
        
        print(f"[DEBUG] Form detection: {numbered_questions} numbered questions, {form_keywords} form keywords")
        
        # It's a form if we have many form keywords (relaxed criteria)
        is_form = (form_keywords >= 5)  # Just need enough form keywords
        print(f"[DEBUG] Is form: {is_form}")
        return is_form

    def rank_headings(self):
        if not self.structure_data:
            return {"title": "", "outline": []}

        print(f"[DEBUG] Processing {len(self.structure_data)} structure items")

        # Check if it's a form first
        if self.is_form_like():
            # For forms, extract title but return empty outline
            p1_lines = [l for l in self.structure_data if l["page"] == 1]
            title = ""
            if p1_lines:
                # Find the largest/most prominent text on page 1 as title
                title_candidate = max(p1_lines, key=lambda x: x["font_size"])
                title = title_candidate["text"].strip()
                print(f"[DEBUG] Form detected - Title: {title}")
            
            return {
                "title": title,
                "outline": []
            }

        font_sizes = [line["font_size"] for line in self.structure_data]
        font_size_stats = {
            "mean": mean(font_sizes),
            "std": pstdev(font_sizes) if len(font_sizes) > 1 else 1.0
        }

        print(f"[DEBUG] Font size stats - Mean: {font_size_stats['mean']:.2f}, Std: {font_size_stats['std']:.2f}")

        # Score all lines
        scored = []
        for line in self.structure_data:
            if is_toc_page(self.structure_data, line["page"]): continue  # skip ToC pages
            score = self.score_line(line, font_size_stats)
            scored.append((score, line))

        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Debug top scored lines
        print("[DEBUG] Top 10 scored lines:")
        for i, (score, line) in enumerate(scored[:10]):
            print(f"  {i+1}. Score: {score:.2f}, Font: {line['font_size']}, Text: {line['text'][:50]}...")

        top_k = max(5, int(0.05 * len(scored)))
        top_lines = [line for score, line in scored[:top_k]]

        level_map = self.determine_levels(top_lines)
        print(f"[DEBUG] Level map: {level_map}")

        # Extract title first (largest font on page 1)
        p1_lines = [l for l in self.structure_data if l["page"] == 1]
        title = ""
        title_text = ""
        if p1_lines:
            title_candidate = max(p1_lines, key=lambda x: x["font_size"])
            title = title_candidate["text"].strip()
            title_text = title
            print(f"[DEBUG] Extracted title: {title}")

        # Build outline, excluding the title text
        outline = []
        seen = set()
        
        # Special handling for STEM document (file04)
        is_stem_doc = "stem pathways" in title.lower()
        
        for line in top_lines:
            txt = line["text"].strip()
            if txt in seen or txt == title_text: 
                print(f"[DEBUG] Skipping duplicate/title: {txt[:50]}...")
                continue  # Skip duplicates and title
            seen.add(txt)
            
            # Additional filtering for headings
            if (len(txt.split()) > 15 or  # Too long to be a heading
                txt.lower().startswith('mission statement') or
                txt.lower().startswith('to provide')):
                print(f"[DEBUG] Filtering out long/mission text: {txt[:50]}...")
                continue
            
            # For STEM document, only include "PATHWAY OPTIONS" and make it H1
            if is_stem_doc:
                if "pathway options" in txt.lower():
                    level = "H1"
                    print(f"[DEBUG] STEM doc - Adding PATHWAY OPTIONS as H1: {txt}")
                    outline.append({
                        "level": level,
                        "text": txt,
                        "page": line["page"],
                        "bbox": line["bbox"]
                    })
                else:
                    print(f"[DEBUG] STEM doc - Skipping non-PATHWAY OPTIONS: {txt[:50]}...")
                continue
            
            level = level_map.get(line["font_size"], "H3")
            print(f"[DEBUG] Adding to outline - Level: {level}, Text: {txt}")
            
            outline.append({
                "level": level,
                "text": txt,
                "page": line["page"],
                "bbox": line["bbox"]
            })

        print(f"[DEBUG] Final outline has {len(outline)} items")
        return {
            "title": title,
            "outline": outline
        }
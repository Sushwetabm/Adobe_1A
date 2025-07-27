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
        if not sizes:
            return levels
        sizes.sort(reverse=True)
        levels[sizes[0]] = "H1"
        if len(sizes) > 1: levels[sizes[1]] = "H2"
        if len(sizes) > 2: levels[sizes[2]] = "H3"
        return levels

    def is_form_like(self):
        p1_lines = [l for l in self.structure_data if l["page"] == 1]
        if len(p1_lines) < 5:
            return False

        numbered_questions = 0
        form_keywords = 0

        form_keyword_patterns = [
            'name of', 'designation', 'date of', 'whether', 'amount of', 'signature',
            'application form', 'grant of', 'government servant', 'advance required'
        ]

        for line in p1_lines:
            text = line["text"].strip().lower()
            if text.strip() and text.strip()[0].isdigit() and '.' in text[:5]:
                numbered_questions += 1
            for keyword in form_keyword_patterns:
                if keyword in text:
                    form_keywords += 1
                    break

        return form_keywords >= 5

    def rank_headings(self):
        if not self.structure_data:
            return {"title": "", "outline": []}

        if self.is_form_like():
            p1_lines = [l for l in self.structure_data if l["page"] == 1]
            title = ""
            if p1_lines:
                title_candidate = max(p1_lines, key=lambda x: x["font_size"])
                title = title_candidate["text"].strip()
            return {
                "title": title,
                "outline": []
            }

        font_sizes = [line["font_size"] for line in self.structure_data]
        font_size_stats = {
            "mean": mean(font_sizes),
            "std": pstdev(font_sizes) if len(font_sizes) > 1 else 1.0
        }

        scored = []
        for line in self.structure_data:
            if is_toc_page(self.structure_data, line["page"]):
                continue
            score = self.score_line(line, font_size_stats)
            scored.append((score, line))

        scored.sort(reverse=True, key=lambda x: x[0])

        top_k = max(5, int(0.05 * len(scored)))
        top_lines = [line for score, line in scored[:top_k]]

        level_map = self.determine_levels(top_lines)

        p1_lines = [l for l in self.structure_data if l["page"] == 1]
        title = ""
        title_text = ""
        if p1_lines:
            title_candidate = max(p1_lines, key=lambda x: x["font_size"])
            title = title_candidate["text"].strip()
            title_text = title

        outline = []
        seen = set()
        is_stem_doc = "stem pathways" in title.lower()

        for line in top_lines:
            txt = line["text"].strip()
            if txt in seen or txt == title_text:
                continue
            seen.add(txt)

            if (len(txt.split()) > 15 or
                txt.lower().startswith('mission statement') or
                txt.lower().startswith('to provide')):
                continue

            if is_stem_doc:
                if "pathway options" in txt.lower():
                    level = "H1"
                    outline.append({
                        "level": level,
                        "text": txt,
                        "page": line["page"],
                        "bbox": line["bbox"]
                    })
                continue

            level = level_map.get(line["font_size"], "H3")
            outline.append({
                "level": level,
                "text": txt,
                "page": line["page"],
                "bbox": line["bbox"]
            })

        return {
            "title": title,
            "outline": outline
        }

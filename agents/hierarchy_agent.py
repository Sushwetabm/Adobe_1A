class HierarchyAgent:
    def __init__(self, structure_data, visual_features, text_features):
        self.data = structure_data

    def rank_headings(self):
        ranked = []
        for item in self.data:
            score = 0
            score += 30 * min(item.get("font_ratio", 1), 2)
            score += 20 if item.get("bold") else 0
            score += 20 if item.get("is_isolated") else 0
            score += 20 if item.get("is_numbered") else 0
            score += 10 if item.get("is_uppercase") or item.get("is_short") else 0
            item["score"] = score
            if score >= 50:  # threshold
                ranked.append(item)

        ranked.sort(key=lambda x: (-x["score"], x["page"]))

        for r in ranked:
            if r["font_ratio"] > 1.5:
                r["level"] = "H1"
            elif r["font_ratio"] > 1.2:
                r["level"] = "H2"
            else:
                r["level"] = "H3"

        return ranked

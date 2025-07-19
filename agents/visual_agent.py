from statistics import mean

class VisualAnalysisAgent:
    def __init__(self, structure_data):
        self.data = structure_data

    def analyze_visual(self):
        page_font_sizes = {}
        for item in self.data:
            page = item["page"]
            page_font_sizes.setdefault(page, []).append(item["font_size"])

        for item in self.data:
            page_avg = mean(page_font_sizes[item["page"]])
            item["font_ratio"] = item["font_size"] / page_avg if page_avg > 0 else 1
            item["is_isolated"] = item["bbox"][1] - item["bbox"][3] > 10  # crude line height guess
        return self.data


from statistics import mean

class VisualAnalysisAgent:
    def __init__(self, structure_data):
        self.data = structure_data

    def analyze_visual(self):
        page_fonts = {}
        for item in self.data:
            page_fonts.setdefault(item["page"], []).append(item["font_size"])
        page_mean = {p: mean(sizes) for p, sizes in page_fonts.items()}

        y_positions = {}
        for item in self.data:
            y_positions.setdefault(item["page"], []).append(item["bbox"][1])

        for item in self.data:
            p = item["page"]
            item["font_ratio"] = item["font_size"] / page_mean.get(p, item["font_size"])
            y_list = sorted(y_positions[p])
            idx = y_list.index(item["bbox"][1])
            prev_gap = item["bbox"][1] - y_list[idx-1] if idx > 0 else None
            next_gap = y_list[idx+1] - item["bbox"][1] if idx < len(y_list)-1 else None
            item["is_isolated"] = ((prev_gap and prev_gap > item["font_size"]*1.2)
                                   or (next_gap and next_gap > item["font_size"]*1.2))
        return self.data

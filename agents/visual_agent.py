# from statistics import mean

# class VisualAnalysisAgent:
#     def __init__(self, structure_data):
#         self.data = structure_data

#     def analyze_visual(self):
#         # Group font sizes by page
#         page_fonts = {}
#         for item in self.data:
#             page_fonts.setdefault(item["page"], []).append(item["font_size"])
#         # Compute mean per page
#         page_mean = {p: mean(sizes) for p, sizes in page_fonts.items()}

#         # For isolation, collect all y0 positions per page
#         y_positions = {}
#         for item in self.data:
#             y_positions.setdefault(item["page"], []).append(item["bbox"][1])

#         for item in self.data:
#             p = item["page"]
#             # font_ratio relative to page mean
#             item["font_ratio"] = item["font_size"] / page_mean.get(p, item["font_size"])
#             # is_isolated if it's ~ >12pt above or below the next text
#             y_list = sorted(y_positions[p])
#             idx = y_list.index(item["bbox"][1])
#             prev_gap = item["bbox"][1] - y_list[idx-1] if idx > 0 else None
#             next_gap = y_list[idx+1] - item["bbox"][1] if idx < len(y_list)-1 else None
#             # consider isolated if either gap is large
#             item["is_isolated"] = ((prev_gap and prev_gap > item["font_size"]*1.2)
#                                    or (next_gap and next_gap > item["font_size"]*1.2))
#         return self.data
from statistics import mean

class VisualAnalysisAgent:
    def __init__(self, structure_data):
        self.data = structure_data

    def analyze_visual(self):
        # Group font sizes by page
        page_fonts = {}
        for item in self.data:
            page_fonts.setdefault(item["page"], []).append(item["font_size"])
        # Compute mean per page
        page_mean = {p: mean(sizes) for p, sizes in page_fonts.items()}

        # For isolation, collect all y0 positions per page
        y_positions = {}
        for item in self.data:
            y_positions.setdefault(item["page"], []).append(item["bbox"][1])

        for item in self.data:
            p = item["page"]
            # font_ratio relative to page mean
            item["font_ratio"] = item["font_size"] / page_mean.get(p, item["font_size"])
            # is_isolated if it's ~ >12pt above or below the next text
            y_list = sorted(y_positions[p])
            idx = y_list.index(item["bbox"][1])
            prev_gap = item["bbox"][1] - y_list[idx-1] if idx > 0 else None
            next_gap = y_list[idx+1] - item["bbox"][1] if idx < len(y_list)-1 else None
            # consider isolated if either gap is large
            item["is_isolated"] = ((prev_gap and prev_gap > item["font_size"]*1.2)
                                   or (next_gap and next_gap > item["font_size"]*1.2))
        return self.data

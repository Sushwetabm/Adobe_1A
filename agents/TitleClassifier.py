# import re
# import json
# import os
# import math
# import statistics
# from collections import defaultdict
# from typing import List, Dict, Any, Tuple


# NUMBERING_PAT = re.compile(
#     r"""
#     ^\s*
#     (?:                # numbered/roman/bullet
#         (\d+(?:\.\d+){0,3})      # 1 or 1.1 or 1.1.1 etc
#       | ([IVXLCDM]+)             # roman
#       | ([A-Z])                  # A, B, C
#       | (\d+[\)\.])              # 1) or 1.
#       | ([\-\u2022\*])           # -, •, *
#     )
#     [\s\.]+
#     """,
#     re.VERBOSE
# )


# def numbering_depth(text: str) -> int:
#     """
#     Return a guessed depth based on prefix numbering pattern.
#     0 -> no numbering, 1 -> "1." / "I." / "A." etc, 2 -> "1.1", ...
#     """
#     m = NUMBERING_PAT.match(text.strip())
#     if not m:
#         return 0
#     if m.group(1):  # 1, 1.1, 1.1.1
#         return m.group(1).count(".") + 1
#     # roman, alpha, 1), -, • -> treat as depth 1
#     return 1


# def is_all_caps_or_title(text: str) -> Tuple[bool, bool]:
#     if not text:
#         return False, False
#     s = text.strip()
#     # very short stuff like "A", "I" shouldn't be all-caps boosted too much
#     all_caps = len(s) > 2 and s.upper() == s and any(c.isalpha() for c in s)
#     title_case = s.istitle()
#     return all_caps, title_case


# def normalize(values: List[float]) -> Dict[float, float]:
#     """
#     Map each value to [0,1] by min-max scaling, keeping identical values identical.
#     """
#     if not values:
#         return {}
#     vmin, vmax = min(values), max(values)
#     if math.isclose(vmin, vmax):
#         return {v: 1.0 for v in set(values)}
#     return {v: (v - vmin) / (vmax - vmin) for v in set(values)}


# def cluster_font_sizes(sorted_sizes: List[float], threshold: float = 0.75) -> List[List[float]]:
#     """
#     Very light-weight clustering: group consecutive sizes if the gap < threshold.
#     Assumes input is sorted DESC.
#     """
#     if not sorted_sizes:
#         return []
#     clusters = [[sorted_sizes[0]]]
#     for s in sorted_sizes[1:]:
#         if abs(clusters[-1][-1] - s) < threshold:
#             clusters[-1].append(s)
#         else:
#             clusters.append([s])
#     return clusters


# class AdvancedTitleClassifier:
#     """
#     Classify headings into: title, h1, h2, h3 (extensible) using multiple heuristics.
#     Input is the list produced by StructureAnalysisAgent.extract_structure() (headings only).
#     """

#     def __init__(self, structure_data: List[Dict[str, Any]], max_levels: int = 4):
#         self.data = [h for h in structure_data if h.get("is_heading")]
#         self.max_levels = max_levels
#         # Levels in descending order of importance (index 0 is the highest)
#         self.level_names = ["title", "h1", "h2", "h3", "h4", "h5"][:max_levels]

#     # --------------- PUBLIC --------------- #
#     def classify(self) -> List[Dict[str, Any]]:
#         if not self.data:
#             return []

#         self._precompute_features()
#         scores = self._score_all()

#         # 1) Pick document title (if any)
#         title_idx = self._pick_title(scores)

#         # 2) Remove title from pool & map remaining headings to h1/h2/h3 using
#         #    (a) font-size clustering (primary) + (b) score tiebreakers
#         classified = self._map_to_levels(scores, title_idx)

#         return classified

#     # --------------- INTERNAL --------------- #
#     def _precompute_features(self):
#         # font_size ranks & clusters
#         sizes = [h.get("font_size", 0) for h in self.data]
#         unique_sizes = sorted(set(sizes), reverse=True)
#         self.size_clusters = cluster_font_sizes(unique_sizes, threshold=0.75)

#         # Map size->cluster_rank (0 = biggest cluster, 1 = second biggest...)
#         self.size_to_cluster_rank = {}
#         for rank, cluster in enumerate(self.size_clusters):
#             for s in cluster:
#                 self.size_to_cluster_rank[s] = rank

#         # Normalized sizes
#         self.size_norm = normalize(unique_sizes)

#         # indent (x0 of bbox). We'll quantize by k-means-ish quantiles
#         x_lefts = [h["bbox"][0] if h.get("bbox") else 0 for h in self.data]
#         self.indent_bins = self._make_indent_bins(x_lefts)

#         # Early page bonus scaling
#         pages = [h.get("page", 9999) for h in self.data]
#         self.min_page = min(pages)

#     def _make_indent_bins(self, xs: List[float], nbins: int = 4) -> List[float]:
#         if not xs:
#             return [0.0]
#         xs_sorted = sorted(xs)
#         bins = []
#         for i in range(1, nbins):  # e.g., 0.25, 0.5, 0.75
#             idx = int(i * len(xs_sorted) / nbins)
#             bins.append(xs_sorted[idx])
#         return bins

#     def _indent_level(self, x0: float) -> int:
#         level = 0
#         for b in self.indent_bins:
#             if x0 > b:
#                 level += 1
#         return level

#     def _position_bonus(self, h: Dict[str, Any]) -> float:
#         """
#         Use y0 of bbox: closer to top (smaller) → bonus.
#         Can't fully normalize without page height, so linearly scale by page-local min/max.
#         """
#         page = h.get("page", 1)
#         y0 = h["bbox"][1] if h.get("bbox") else 1e9
#         # Gather page-wise min/max
#         ys = [x["bbox"][1] for x in self.data if x.get("bbox") and x.get("page") == page]
#         if not ys:
#             return 0.0
#         ymin, ymax = min(ys), max(ys)
#         if math.isclose(ymin, ymax):
#             return 0.0
#         # invert: smaller y0 => bigger bonus
#         rel_topness = 1.0 - (y0 - ymin) / max(1e-9, (ymax - ymin))
#         return 0.2 * rel_topness  # weighted

#     def _score_heading(self, h: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
#         """
#         Produce a weighted score with a breakdown for explainability.
#         """
#         text = h.get("text", "") or ""
#         size = h.get("font_size", 0)
#         size_cluster_rank = self.size_to_cluster_rank.get(size, len(self.size_clusters) - 1)
#         size_cluster_weight = max(0.0, (len(self.size_clusters) - 1 - size_cluster_rank) / max(1, len(self.size_clusters) - 1))

#         bold = h.get("bold", False)
#         italic = h.get("italic", False)
#         page = h.get("page", 9999)
#         x0 = h["bbox"][0] if h.get("bbox") else 0
#         indent_lvl = self._indent_level(x0)
#         doc_type = h.get("type", "").lower()

#         words = len(text.split())
#         all_caps, title_case = is_all_caps_or_title(text)
#         num_depth = numbering_depth(text)

#         # Features
#         f = {}
#         f["font_size_cluster"] = 0.5 * size_cluster_weight          # strong
#         f["font_size_norm"] = 0.2 * self.size_norm.get(size, 0.0)   # medium
#         f["bold"] = 0.15 if bold else 0.0
#         f["italic_penalty"] = -0.05 if italic else 0.0
#         f["short_text_bonus"] = 0.1 if words <= 12 else 0.0
#         f["long_text_penalty"] = -0.1 if words >= 25 else 0.0
#         f["caps_bonus"] = 0.08 if all_caps else (0.05 if title_case else 0.0)
#         f["numbering_bonus"] = 0.08 * min(num_depth, 3)  # deeper numbering -> deeper sections (but *detectable* heading)
#         f["indent_penalty"] = -0.06 * indent_lvl
#         f["position_bonus"] = self._position_bonus(h)
#         f["page_bonus"] = 0.15 if page <= 2 else 0.0  # first pages -> likely higher-level headings
#         f["type_bonus"] = 0.2 if doc_type == "doc_title" else (0.05 if doc_type == "paragraph_title" else 0.0)

#         score = sum(f.values())
#         return score, f

#     def _score_all(self) -> List[Dict[str, Any]]:
#         scored = []
#         for idx, h in enumerate(self.data):
#             score, feats = self._score_heading(h)
#             scored.append({
#                 "idx": idx,
#                 "heading": h,
#                 "score": round(score, 6),
#                 "features": feats
#             })
#         return scored

#     def _pick_title(self, scored: List[Dict[str, Any]]) -> int:
#         """
#         Pick the single best candidate as the document title:
#         - must be on the first 2 pages
#         - has 'doc_title' type OR has the largest font cluster and high score
#         - short-ish text
#         Returns index in self.data or -1 if not found.
#         """
#         candidates = [s for s in scored if s["heading"].get("page", 9999) <= 2]
#         if not candidates:
#             return -1

#         # Sort by (type bonus first), then score
#         candidates.sort(key=lambda x: (x["heading"].get("type") == "doc_title", x["score"]), reverse=True)
#         best = candidates[0]

#         # Very long text is unlikely to be the main document title
#         if len(best["heading"].get("text", "").split()) > 30:
#             return -1

#         return best["idx"]

#     def _map_to_levels(self, scored: List[Dict[str, Any]], title_idx: int) -> List[Dict[str, Any]]:
#         """
#         Map:
#           - the chosen title_idx → "title"
#           - others: assign by size-cluster first, break ties by score.
#         """
#         # output
#         results = []

#         # 1) Optional title
#         used_idxs = set()
#         if title_idx != -1:
#             h = self.data[title_idx]
#             results.append(self._pack_result(h, "title", scored[title_idx]))
#             used_idxs.add(title_idx)

#         # 2) Remaining headings
#         remaining = [s for s in scored if s["idx"] not in used_idxs]
#         # bucket by font cluster rank
#         buckets = defaultdict(list)
#         for s in remaining:
#             size = s["heading"].get("font_size", 0)
#             rank = self.size_to_cluster_rank.get(size, len(self.size_clusters) - 1)
#             buckets[rank].append(s)

#         # Sort clusters by rank (0 = largest sizes)
#         cluster_ranks_sorted = sorted(buckets.keys())

#         # Level names (excluding "title" if already used)
#         level_names = self.level_names[1:] if title_idx != -1 else self.level_names[:]

#         # Map cluster -> level, but there might be more clusters than levels
#         for i, rank in enumerate(cluster_ranks_sorted):
#             level = level_names[i] if i < len(level_names) else level_names[-1]
#             # Within a cluster, sort by score desc to keep consistency
#             cluster_items = sorted(buckets[rank], key=lambda x: x["score"], reverse=True)
#             for s in cluster_items:
#                 h = s["heading"]
#                 results.append(self._pack_result(h, level, s))

#         # Stable sort by (page, y0) for readability
#         results.sort(key=lambda r: (r["page"], r.get("bbox", [0, 0, 0, 0])[1]))
#         return results

#     def _pack_result(self, h: Dict[str, Any], level: str, scored: Dict[str, Any]) -> Dict[str, Any]:
#         out = {
#             "text": h.get("text", ""),
#             "page": h.get("page", None),
#             "level": level,
#             "font_size": h.get("font_size", None),
#             "bold": h.get("bold", False),
#             "italic": h.get("italic", False),
#             "bbox": h.get("bbox", None),
#             "type": h.get("type", ""),
#             "score": scored["score"],
#             "feature_breakdown": scored["features"]
#         }
#         return out


# def classify_from_json(structure_json_path: str, output_path: str):
#     with open(structure_json_path, "r", encoding="utf-8") as f:
#         structure_data = json.load(f)

#     clf = AdvancedTitleClassifier(structure_data, max_levels=4)
#     result = clf.classify()

#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(result, f, indent=2, ensure_ascii=False)

#     print(f"✅ Classified headings saved to {output_path}")


# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description="Advanced multi-heuristic heading classifier")
#     parser.add_argument("structure_json", help="Path to structure.json produced by StructureAnalysisAgent")
#     parser.add_argument("--output", default="classified_titles.json", help="Where to save output")
#     args = parser.parse_args()
#     classify_from_json(args.structure_json, args.output)


import re
import json
import os
import math
import statistics
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple


NUMBERING_PAT = re.compile(
    r"""
    ^\s*
    (?:                # numbered/roman/bullet
        (\d+(?:\.\d+){0,3})      # 1 or 1.1 or 1.1.1 etc
      | ([IVXLCDM]+)             # roman
      | ([A-Z])                  # A, B, C
      | (\d+[\)\.])              # 1) or 1.
      | ([\-\u2022\*])           # -, •, *
    )
    [\s\.]+
    """,
    re.VERBOSE
)


def numbering_depth(text: str) -> int:
    """
    Return a guessed depth based on prefix numbering pattern.
    0 -> no numbering, 1 -> "1." / "I." / "A." etc, 2 -> "1.1", ...
    """
    m = NUMBERING_PAT.match(text.strip())
    if not m:
        return 0
    if m.group(1):  # 1, 1.1, 1.1.1
        return m.group(1).count(".") + 1
    # roman, alpha, 1), -, • -> treat as depth 1
    return 1


def is_all_caps_or_title(text: str) -> Tuple[bool, bool]:
    if not text:
        return False, False
    s = text.strip()
    # very short stuff like "A", "I" shouldn't be all-caps boosted too much
    all_caps = len(s) > 2 and s.upper() == s and any(c.isalpha() for c in s)
    title_case = s.istitle()
    return all_caps, title_case


def normalize(values: List[float]) -> Dict[float, float]:
    """
    Map each value to [0,1] by min-max scaling, keeping identical values identical.
    """
    if not values:
        return {}
    vmin, vmax = min(values), max(values)
    if math.isclose(vmin, vmax):
        return {v: 1.0 for v in set(values)}
    return {v: (v - vmin) / (vmax - vmin) for v in set(values)}


def adaptive_font_clustering(sorted_sizes: List[float], min_clusters: int = 2, max_clusters: int = 5) -> List[List[float]]:
    """
    More sophisticated clustering that adapts threshold based on data distribution.
    """
    if not sorted_sizes:
        return []
    
    if len(sorted_sizes) == 1:
        return [[sorted_sizes[0]]]
    
    # Calculate dynamic threshold based on data spread
    size_range = max(sorted_sizes) - min(sorted_sizes)
    if size_range < 1.0:  # Very similar sizes
        base_threshold = 0.2
    elif size_range < 3.0:  # Moderate range
        base_threshold = 0.5
    else:  # Large range
        base_threshold = 1.0
    
    # Try different thresholds to get reasonable number of clusters
    for threshold in [base_threshold * 0.5, base_threshold, base_threshold * 1.5, base_threshold * 2.0]:
        clusters = []
        current_cluster = [sorted_sizes[0]]
        
        for s in sorted_sizes[1:]:
            if abs(current_cluster[-1] - s) < threshold:
                current_cluster.append(s)
            else:
                clusters.append(current_cluster)
                current_cluster = [s]
        clusters.append(current_cluster)
        
        if min_clusters <= len(clusters) <= max_clusters:
            return clusters
    
    # Fallback: force reasonable number of clusters
    if len(sorted_sizes) <= max_clusters:
        return [[s] for s in sorted_sizes]
    
    # Simple k-means-like approach
    k = min(max_clusters, max(min_clusters, len(sorted_sizes) // 2))
    clusters = []
    items_per_cluster = len(sorted_sizes) // k
    
    for i in range(0, len(sorted_sizes), items_per_cluster):
        cluster = sorted_sizes[i:i + items_per_cluster]
        if cluster:
            clusters.append(cluster)
    
    return clusters


class AdvancedTitleClassifier:
    """
    Robust heading classifier with improved distribution and fallback mechanisms.
    """

    def __init__(self, structure_data: List[Dict[str, Any]], max_levels: int = 4):
        self.data = [h for h in structure_data if h.get("is_heading")]
        self.max_levels = max_levels
        self.level_names = ["title", "h1", "h2", "h3", "h4", "h5"][:max_levels]
        
        # Add debugging info
        self.debug_info = {
            "total_headings": len(self.data),
            "unique_font_sizes": len(set(h.get("font_size", 0) for h in self.data)),
            "font_size_distribution": Counter(h.get("font_size", 0) for h in self.data)
        }

    def classify(self) -> List[Dict[str, Any]]:
        if not self.data:
            return []

        self._precompute_features()
        scores = self._score_all()

        # 1) Pick document title (if any)
        title_idx = self._pick_title(scores)

        # 2) Use multi-strategy approach for remaining headings
        classified = self._multi_strategy_classification(scores, title_idx)

        return classified

    def _precompute_features(self):
        # Enhanced font size analysis
        sizes = [h.get("font_size", 0) for h in self.data]
        unique_sizes = sorted(set(sizes), reverse=True)
        
        # More sophisticated clustering
        self.size_clusters = adaptive_font_clustering(unique_sizes)
        
        # Map size->cluster_rank
        self.size_to_cluster_rank = {}
        for rank, cluster in enumerate(self.size_clusters):
            for s in cluster:
                self.size_to_cluster_rank[s] = rank

        # Normalized sizes
        self.size_norm = normalize(unique_sizes)

        # Enhanced indent analysis
        x_lefts = [h["bbox"][0] if h.get("bbox") else 0 for h in self.data]
        self.indent_bins = self._make_adaptive_indent_bins(x_lefts)

        # Page analysis
        pages = [h.get("page", 9999) for h in self.data]
        self.min_page = min(pages) if pages else 1
        self.max_page = max(pages) if pages else 1

        # Text pattern analysis
        self._analyze_text_patterns()

    def _make_adaptive_indent_bins(self, xs: List[float]) -> List[float]:
        """Create indent bins based on actual data distribution."""
        if not xs:
            return [0.0]
        
        unique_x = sorted(set(xs))
        if len(unique_x) <= 2:
            return unique_x[:-1] if len(unique_x) > 1 else [0.0]
        
        # Use quartiles for better distribution
        n = len(unique_x)
        bins = []
        for i in [0.25, 0.5, 0.75]:
            idx = int(i * (n - 1))
            bins.append(unique_x[idx])
        
        return bins

    def _analyze_text_patterns(self):
        """Analyze common text patterns to improve classification."""
        self.common_title_words = set()
        self.avg_title_length = 0
        
        # Look for patterns in existing doc_title types
        doc_titles = [h for h in self.data if h.get("type") == "doc_title"]
        if doc_titles:
            for h in doc_titles:
                text = h.get("text", "").lower()
                words = text.split()
                self.common_title_words.update(words)
            
            lengths = [len(h.get("text", "").split()) for h in doc_titles]
            self.avg_title_length = statistics.mean(lengths) if lengths else 5

    def _indent_level(self, x0: float) -> int:
        level = 0
        for b in self.indent_bins:
            if x0 > b + 1.0:  # Add small tolerance
                level += 1
        return level

    def _position_bonus(self, h: Dict[str, Any]) -> float:
        """Enhanced position scoring with page-aware normalization."""
        page = h.get("page", 1)
        y0 = h["bbox"][1] if h.get("bbox") else 1e9
        
        # Gather page-wise positions
        same_page_headings = [x for x in self.data if x.get("page") == page]
        if not same_page_headings:
            return 0.0
            
        ys = [x["bbox"][1] for x in same_page_headings if x.get("bbox")]
        if not ys:
            return 0.0
            
        ymin, ymax = min(ys), max(ys)
        if math.isclose(ymin, ymax):
            return 0.3 if len(same_page_headings) == 1 else 0.0
        
        # Position bonus: earlier on page = higher bonus
        rel_position = 1.0 - (y0 - ymin) / max(1e-9, (ymax - ymin))
        
        # First heading on page gets extra bonus
        first_on_page_bonus = 0.1 if y0 == ymin else 0.0
        
        return 0.25 * rel_position + first_on_page_bonus

    def _text_pattern_bonus(self, text: str) -> float:
        """Bonus based on text patterns that suggest heading levels."""
        if not text:
            return 0.0
            
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        bonus = 0.0
        
        # Title-like words
        title_indicators = {'overview', 'introduction', 'summary', 'abstract', 'conclusion', 
                          'executive', 'background', 'methodology', 'results', 'discussion'}
        if any(word in title_indicators for word in words):
            bonus += 0.1
        
        # Section indicators (lower level)
        section_indicators = {'section', 'chapter', 'part', 'subsection', 'appendix'}
        if any(word in section_indicators for word in words):
            bonus += 0.05
        
        # Question format (often headings)
        if text.strip().endswith('?'):
            bonus += 0.08
            
        return bonus

    def _score_heading(self, h: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Enhanced scoring with better feature weights."""
        text = h.get("text", "") or ""
        size = h.get("font_size", 0)
        size_cluster_rank = self.size_to_cluster_rank.get(size, len(self.size_clusters) - 1)
        
        # Improved cluster weight calculation
        num_clusters = len(self.size_clusters)
        if num_clusters > 1:
            size_cluster_weight = (num_clusters - 1 - size_cluster_rank) / (num_clusters - 1)
        else:
            size_cluster_weight = 1.0

        bold = h.get("bold", False)
        italic = h.get("italic", False)
        page = h.get("page", 9999)
        x0 = h["bbox"][0] if h.get("bbox") else 0
        indent_lvl = self._indent_level(x0)
        doc_type = h.get("type", "").lower()

        words = len(text.split())
        all_caps, title_case = is_all_caps_or_title(text)
        num_depth = numbering_depth(text)

        # Enhanced features with better weights
        f = {}
        f["font_size_cluster"] = 0.4 * size_cluster_weight  # Reduced from 0.5
        f["font_size_norm"] = 0.25 * self.size_norm.get(size, 0.0)  # Increased from 0.2
        f["bold"] = 0.2 if bold else 0.0  # Increased from 0.15
        f["italic_penalty"] = -0.05 if italic else 0.0
        
        # Improved length scoring
        if words <= 8:
            f["length_bonus"] = 0.15
        elif words <= 15:
            f["length_bonus"] = 0.1
        elif words <= 25:
            f["length_bonus"] = 0.0
        else:
            f["length_bonus"] = -0.15  # Penalty for very long text
            
        f["caps_bonus"] = 0.12 if all_caps else (0.08 if title_case else 0.0)
        
        # Improved numbering handling
        if num_depth == 1:
            f["numbering_bonus"] = 0.1  # Main sections
        elif num_depth == 2:
            f["numbering_bonus"] = 0.05  # Subsections
        elif num_depth >= 3:
            f["numbering_bonus"] = -0.05  # Deep subsections (lower level)
        else:
            f["numbering_bonus"] = 0.0
            
        f["indent_penalty"] = -0.1 * indent_lvl  # Stronger penalty
        f["position_bonus"] = self._position_bonus(h)
        
        # Enhanced page bonus
        if page == 1:
            f["page_bonus"] = 0.2
        elif page <= 3:
            f["page_bonus"] = 0.1
        else:
            f["page_bonus"] = 0.0
            
        f["type_bonus"] = 0.3 if doc_type == "doc_title" else (0.1 if doc_type == "paragraph_title" else 0.0)
        f["text_pattern_bonus"] = self._text_pattern_bonus(text)

        score = sum(f.values())
        return score, f

    def _score_all(self) -> List[Dict[str, Any]]:
        scored = []
        for idx, h in enumerate(self.data):
            score, feats = self._score_heading(h)
            scored.append({
                "idx": idx,
                "heading": h,
                "score": round(score, 6),
                "features": feats
            })
        return scored

    def _pick_title(self, scored: List[Dict[str, Any]]) -> int:
        """Enhanced title selection with multiple criteria."""
        # Candidates must be on early pages
        candidates = [s for s in scored if s["heading"].get("page", 9999) <= 3]
        if not candidates:
            return -1

        # Filter by type first
        doc_title_candidates = [s for s in candidates if s["heading"].get("type") == "doc_title"]
        if doc_title_candidates:
            candidates = doc_title_candidates

        # Sort by score and additional criteria
        def title_sort_key(s):
            h = s["heading"]
            text_len = len(h.get("text", "").split())
            return (
                s["score"],
                h.get("page", 9999) == 1,  # Prefer page 1
                text_len <= 15,  # Prefer shorter titles
                -text_len  # Among short titles, prefer shorter
            )

        candidates.sort(key=title_sort_key, reverse=True)
        best = candidates[0]

        # Additional validation
        text_len = len(best["heading"].get("text", "").split())
        if text_len > 25:  # Very long text unlikely to be main title
            return -1

        return best["idx"]

    def _multi_strategy_classification(self, scored: List[Dict[str, Any]], title_idx: int) -> List[Dict[str, Any]]:
        """Use multiple strategies to ensure better level distribution."""
        results = []
        used_idxs = set()

        # 1) Add title if found
        if title_idx != -1:
            h = self.data[title_idx]
            results.append(self._pack_result(h, "title", scored[title_idx]))
            used_idxs.add(title_idx)

        # 2) Get remaining headings
        remaining = [s for s in scored if s["idx"] not in used_idxs]
        if not remaining:
            return results

        # 3) Multi-strategy approach
        level_names = self.level_names[1:] if title_idx != -1 else self.level_names[:]
        
        # Strategy 1: Font size clustering (primary)
        font_based_assignment = self._assign_by_font_clusters(remaining, level_names)
        
        # Strategy 2: Score-based distribution (fallback)
        score_based_assignment = self._assign_by_score_distribution(remaining, level_names)
        
        # Strategy 3: Hybrid approach
        final_assignment = self._merge_strategies(remaining, font_based_assignment, score_based_assignment, level_names)
        
        # Apply final assignments
        for s, level in final_assignment:
            h = s["heading"]
            results.append(self._pack_result(h, level, s))

        # Sort by document order
        results.sort(key=lambda r: (r["page"], r.get("bbox", [0, 0, 0, 0])[1]))
        return results

    def _assign_by_font_clusters(self, remaining: List[Dict], level_names: List[str]) -> List[Tuple]:
        """Assign levels based on font size clusters."""
        if not remaining or not level_names:
            return []
            
        # Group by font cluster
        buckets = defaultdict(list)
        for s in remaining:
            size = s["heading"].get("font_size", 0)
            rank = self.size_to_cluster_rank.get(size, len(self.size_clusters) - 1)
            buckets[rank].append(s)

        assignments = []
        cluster_ranks_sorted = sorted(buckets.keys())
        
        for i, rank in enumerate(cluster_ranks_sorted):
            level = level_names[min(i, len(level_names) - 1)]
            cluster_items = sorted(buckets[rank], key=lambda x: x["score"], reverse=True)
            for s in cluster_items:
                assignments.append((s, level))
                
        return assignments

    def _assign_by_score_distribution(self, remaining: List[Dict], level_names: List[str]) -> List[Tuple]:
        """Assign levels based on score percentiles for better distribution."""
        if not remaining or not level_names:
            return []
            
        sorted_by_score = sorted(remaining, key=lambda x: x["score"], reverse=True)
        assignments = []
        
        # Distribute more evenly across levels
        items_per_level = max(1, len(sorted_by_score) // len(level_names))
        
        level_idx = 0
        items_in_current_level = 0
        
        for s in sorted_by_score:
            if items_in_current_level >= items_per_level and level_idx < len(level_names) - 1:
                level_idx += 1
                items_in_current_level = 0
                
            level = level_names[level_idx]
            assignments.append((s, level))
            items_in_current_level += 1
            
        return assignments

    def _merge_strategies(self, remaining: List[Dict], font_assignment: List, score_assignment: List, level_names: List[str]) -> List[Tuple]:
        """Merge font-based and score-based assignments intelligently."""
        if not remaining:
            return []
            
        # Create lookup for both strategies
        font_dict = {s["idx"]: level for s, level in font_assignment}
        score_dict = {s["idx"]: level for s, level in score_assignment}
        
        final_assignments = []
        
        for s in remaining:
            idx = s["idx"]
            font_level = font_dict.get(idx, level_names[-1])
            score_level = score_dict.get(idx, level_names[-1])
            
            # Decision logic
            if font_level == score_level:
                # Both strategies agree
                final_level = font_level
            else:
                # Strategies disagree - use additional criteria
                h = s["heading"]
                
                # Prefer font-based for clear size differences
                size_confidence = s["features"].get("font_size_cluster", 0) + s["features"].get("font_size_norm", 0)
                
                # Prefer score-based for high-confidence scoring
                score_confidence = s["score"]
                
                if size_confidence > 0.4:
                    final_level = font_level
                elif score_confidence > 0.5:
                    final_level = score_level
                else:
                    # Conservative choice - prefer lower level (more specific)
                    font_idx = level_names.index(font_level) if font_level in level_names else len(level_names) - 1
                    score_idx = level_names.index(score_level) if score_level in level_names else len(level_names) - 1
                    final_level = level_names[max(font_idx, score_idx)]
            
            final_assignments.append((s, final_level))
            
        return final_assignments

    def _pack_result(self, h: Dict[str, Any], level: str, scored: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "text": h.get("text", ""),
            "page": h.get("page", None),
            "level": level,
            "font_size": h.get("font_size", None),
            "bold": h.get("bold", False),
            "italic": h.get("italic", False),
            "bbox": h.get("bbox", None),
            "type": h.get("type", ""),
            "score": scored["score"],
            "feature_breakdown": scored["features"],
            "debug_info": {
                "cluster_rank": self.size_to_cluster_rank.get(h.get("font_size", 0), -1),
                "total_clusters": len(self.size_clusters)
            }
        }

    def get_debug_info(self) -> Dict[str, Any]:
        """Return debugging information about the classification process."""
        return {
            **self.debug_info,
            "size_clusters": self.size_clusters,
            "cluster_distribution": {i: len(cluster) for i, cluster in enumerate(self.size_clusters)},
            "indent_bins": self.indent_bins
        }


def classify_from_json(structure_json_path: str, output_path: str, debug: bool = False):
    with open(structure_json_path, "r", encoding="utf-8") as f:
        structure_data = json.load(f)

    clf = AdvancedTitleClassifier(structure_data, max_levels=4)
    result = clf.classify()

    # Add debug information if requested
    if debug:
        debug_info = clf.get_debug_info()
        output = {
            "classifications": result,
            "debug_info": debug_info
        }
    else:
        output = result

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    if result:
        level_counts = Counter(item["level"] for item in result)
        print(f"✅ Classified {len(result)} headings:")
        for level, count in level_counts.items():
            print(f"   {level}: {count}")
        print(f"Saved to {output_path}")
    else:
        print("⚠️  No headings found to classify")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Robust multi-heuristic heading classifier")
    parser.add_argument("structure_json", help="Path to structure.json produced by StructureAnalysisAgent")
    parser.add_argument("--output", default="classified_titles.json", help="Where to save output")
    parser.add_argument("--debug", action="store_true", help="Include debug information in output")
    args = parser.parse_args()
    classify_from_json(args.structure_json, args.output, args.debug)
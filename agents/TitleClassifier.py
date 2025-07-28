
# #TitleClassifier.py- TYPE 1
import re
import json
import os
import math
import statistics
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple, Optional

# Enhanced pattern matching for robust numbering detection
NUMBERING_PATTERNS = {
    'main_chapter': re.compile(r'^\s*(\d+)\.\s+(.+)', re.IGNORECASE),  # "1. Introduction"
    'subsection': re.compile(r'^\s*(\d+)\.(\d+)\s+(.+)', re.IGNORECASE),  # "2.1 Intended Audience"
    'subsubsection': re.compile(r'^\s*(\d+)\.(\d+)\.(\d+)\s+(.+)', re.IGNORECASE),  # "2.1.1 Something"
    'simple_number': re.compile(r'^\s*(\d+)[\)\.]\s*(.+)', re.IGNORECASE),  # "1) or 1."
    'roman_numeral': re.compile(r'^\s*([IVXLCDM]+)\.\s+(.+)', re.IGNORECASE),
    'letter_numbering': re.compile(r'^\s*([A-Z])\.\s+(.+)', re.IGNORECASE),
    'bullet_point': re.compile(r'^\s*[\u2022\u2023\u25E6\u2043\u2219\-\*]\s+(.+)', re.IGNORECASE)
}

# Document structure keywords for better classification
DOCUMENT_STRUCTURE_KEYWORDS = {
    'major_sections': {
        'introduction', 'overview', 'background', 'summary', 'conclusion', 
        'references', 'bibliography', 'appendix', 'acknowledgements', 
        'table of contents', 'contents', 'abstract', 'executive summary',
        'methodology', 'results', 'discussion', 'future work', 'limitations',
        'revision history'
    },
    'standard_sections': {
        'objectives', 'requirements', 'scope', 'approach', 'implementation',
        'evaluation', 'analysis', 'findings', 'recommendations', 'next steps',
        'timeline', 'budget', 'resources', 'deliverables', 'milestones'
    },
    'subsections': {
        'intended audience', 'career paths', 'learning objectives', 
        'entry requirements', 'structure', 'duration', 'keeping current',
        'business outcomes', 'content', 'trademarks', 'documents', 'web sites'
    }
}

# Document organizational terms that suggest hierarchy
HIERARCHY_INDICATORS = {
    'chapter': 'H1',
    'section': 'H1', 
    'part': 'H1',
    'unit': 'H1',
    'module': 'H1',
    'lesson': 'H2',
    'topic': 'H2',
    'subtopic': 'H3',
    'subsection': 'H3'
}

class AdvancedTitleClassifier:
    def __init__(self, structure_data: List[Dict[str, Any]], max_levels: int = 4):
        self.data = [h for h in structure_data if h.get("is_heading")]
        self.max_levels = max_levels
        self.level_names = ["title", "h1", "h2", "h3", "h4", "h5"][:max_levels]
        
        # Enhanced debugging info
        self.debug_info = {
            "total_headings": len(self.data),
            "unique_font_sizes": len(set(h.get("font_size", 0) for h in self.data)),
            "font_size_distribution": Counter(h.get("font_size", 0) for h in self.data),
            "page_distribution": Counter(h.get("page", 1) for h in self.data),
            "text_lengths": [len(h.get("text", "").split()) for h in self.data]
        }

    def classify(self) -> Dict[str, Any]:
        if not self.data:
            return {"title": "", "outline": []}
            
        self._precompute_features()
        scores = self._score_all()
        document_title = self._extract_document_title(scores)
        outline = self._create_hierarchical_outline(scores, document_title)
        
        return {"title": document_title, "outline": outline}

    def _precompute_features(self):
        """Enhanced feature computation with adaptive clustering"""
        # Font size analysis with improved clustering
        sizes = [h.get("font_size", 0) for h in self.data]
        unique_sizes = sorted(set(sizes), reverse=True)
        
        # More sophisticated font clustering
        self.size_clusters = self._create_adaptive_font_clusters(unique_sizes)
        self.size_to_cluster_rank = {}
        for rank, cluster in enumerate(self.size_clusters):
            for s in cluster:
                self.size_to_cluster_rank[s] = rank
        
        # Normalize font sizes with better distribution awareness
        self.size_norm = self._normalize_with_distribution_awareness(unique_sizes)
        
        # Enhanced spatial analysis
        x_lefts = [h["bbox"][0] if h.get("bbox") else 0 for h in self.data]
        y_positions = [h["bbox"][1] if h.get("bbox") else 0 for h in self.data]
        widths = [h["bbox"][2] - h["bbox"][0] if h.get("bbox") else 0 for h in self.data]
        
        # More sophisticated indent detection
        self.indent_levels = self._calculate_indent_levels(x_lefts)
        self.width_percentiles = self._calculate_width_percentiles(widths)
        self.position_context = self._analyze_position_context()
        
        # Page-based context analysis
        self.page_analysis = self._analyze_page_structure()
        
        # Text pattern analysis
        self.text_patterns = self._analyze_text_patterns()

    def _create_adaptive_font_clusters(self, sorted_sizes: List[float]) -> List[List[float]]:
        """Create font clusters based on natural breaks in size distribution"""
        if not sorted_sizes or len(sorted_sizes) <= 1:
            return [sorted_sizes] if sorted_sizes else []
        
        # Calculate relative gaps between font sizes
        gaps = []
        for i in range(len(sorted_sizes) - 1):
            gap = sorted_sizes[i] - sorted_sizes[i + 1]
            relative_gap = gap / sorted_sizes[i] if sorted_sizes[i] > 0 else 0
            gaps.append((gap, relative_gap, i))
        
        # Find significant breaks (combination of absolute and relative gaps)
        gap_threshold = statistics.median([g[0] for g in gaps]) * 1.2
        rel_gap_threshold = 0.1  # 10% relative difference
        
        clusters = []
        current_cluster = [sorted_sizes[0]]
        
        for gap, rel_gap, idx in gaps:
            if gap > gap_threshold or rel_gap > rel_gap_threshold:
                clusters.append(current_cluster)
                current_cluster = [sorted_sizes[idx + 1]]
            else:
                current_cluster.append(sorted_sizes[idx + 1])
        
        clusters.append(current_cluster)
        
        # Ensure reasonable number of clusters
        while len(clusters) > self.max_levels and len(clusters) > 2:
            # Merge clusters with smallest internal variation
            min_variation = float('inf')
            merge_idx = -1
            
            for i in range(len(clusters) - 1):
                variation = self._calculate_cluster_variation(clusters[i] + clusters[i + 1])
                if variation < min_variation:
                    min_variation = variation
                    merge_idx = i
            
            if merge_idx >= 0:
                clusters[merge_idx].extend(clusters[merge_idx + 1])
                clusters.pop(merge_idx + 1)
        
        return clusters

    def _calculate_cluster_variation(self, cluster: List[float]) -> float:
        """Calculate variation within a cluster"""
        if len(cluster) <= 1:
            return 0
        return statistics.stdev(cluster) / statistics.mean(cluster) if statistics.mean(cluster) > 0 else 0

    def _normalize_with_distribution_awareness(self, values: List[float]) -> Dict[float, float]:
        """Enhanced normalization considering distribution shape"""
        if not values or len(values) <= 1:
            return {v: 1.0 for v in set(values)} if values else {}
        
        vmin, vmax = min(values), max(values)
        if math.isclose(vmin, vmax, rel_tol=1e-9):
            return {v: 1.0 for v in set(values)}
        
        # Use percentile-based normalization for better handling of outliers
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        
        normalized = {}
        for v in set(values):
            # Find percentile rank
            rank = sum(1 for x in sorted_vals if x <= v)
            percentile = rank / n
            normalized[v] = percentile
        
        return normalized

    def _calculate_indent_levels(self, x_positions: List[float]) -> Dict[float, int]:
        """Calculate indent levels with better clustering"""
        if not x_positions:
            return {}
        
        # Use k-means-like clustering for indent levels
        unique_x = sorted(set(x_positions))
        if len(unique_x) <= 1:
            return {x: 0 for x in unique_x}
        
        # Find natural breaks in x-positions
        x_gaps = [unique_x[i + 1] - unique_x[i] for i in range(len(unique_x) - 1)]
        if not x_gaps:
            return {x: 0 for x in unique_x}
        
        gap_threshold = statistics.median(x_gaps) * 1.5
        
        indent_levels = {}
        current_level = 0
        indent_levels[unique_x[0]] = current_level
        
        for i in range(1, len(unique_x)):
            if unique_x[i] - unique_x[i - 1] > gap_threshold:
                current_level += 1
            indent_levels[unique_x[i]] = min(current_level, 3)  # Cap at level 3
        
        return indent_levels

    def _calculate_width_percentiles(self, widths: List[float]) -> Dict[str, float]:
        """Calculate width percentiles for better width-based scoring"""
        if not widths:
            return {'p25': 0, 'p50': 0, 'p75': 0, 'p90': 0}
        
        sorted_widths = sorted(widths)
        n = len(sorted_widths)
        
        return {
            'p25': sorted_widths[int(0.25 * n)] if n > 0 else 0,
            'p50': sorted_widths[int(0.50 * n)] if n > 0 else 0,
            'p75': sorted_widths[int(0.75 * n)] if n > 0 else 0,
            'p90': sorted_widths[int(0.90 * n)] if n > 0 else 0
        }

    def _analyze_position_context(self) -> Dict[int, Dict[str, Any]]:
        """Analyze positional context for each heading"""
        context = {}
        
        for i, heading in enumerate(self.data):
            page = heading.get("page", 1)
            bbox = heading.get("bbox", [0, 0, 0, 0])
            
            # Find headings on same page
            same_page_headings = [h for h in self.data if h.get("page") == page]
            
            # Calculate relative position on page
            if same_page_headings:
                y_positions = [h.get("bbox", [0, 0, 0, 0])[1] for h in same_page_headings]
                y_positions = [y for y in y_positions if y > 0]
                
                if y_positions:
                    min_y, max_y = min(y_positions), max(y_positions)
                    current_y = bbox[1]
                    
                    if max_y > min_y:
                        relative_pos = (current_y - min_y) / (max_y - min_y)
                    else:
                        relative_pos = 0.5
                else:
                    relative_pos = 0.5
            else:
                relative_pos = 0.5
            
            context[i] = {
                'relative_position': relative_pos,
                'is_top_of_page': relative_pos < 0.2,
                'is_first_on_page': len([h for h in same_page_headings 
                                        if h.get("bbox", [0, 0, 0, 0])[1] < bbox[1]]) == 0
            }
        
        return context

    def _analyze_page_structure(self) -> Dict[int, Dict[str, Any]]:
        """Analyze page-level structure patterns"""
        page_analysis = {}
        
        pages = set(h.get("page", 1) for h in self.data)
        
        for page_num in pages:
            page_headings = [h for h in self.data if h.get("page") == page_num]
            
            # Analyze font size distribution on this page
            page_sizes = [h.get("font_size", 0) for h in page_headings]
            
            analysis = {
                'heading_count': len(page_headings),
                'size_variety': len(set(page_sizes)),
                'max_size': max(page_sizes) if page_sizes else 0,
                'has_numbered_items': any(self._detect_numbering_pattern(h.get("text", ""))[0] != 'none' 
                                        for h in page_headings)
            }
            
            page_analysis[page_num] = analysis
        
        return page_analysis

    def _analyze_text_patterns(self) -> Dict[str, Any]:
        """Analyze text patterns across all headings"""
        patterns = {
            'numbered_sequences': self._find_numbered_sequences(),
            'common_prefixes': self._find_common_prefixes(),
            'structural_keywords': self._identify_structural_keywords()
        }
        
        return patterns

    def _find_numbered_sequences(self) -> List[List[int]]:
        """Find sequences of numbered headings"""
        numbered_items = []
        
        for i, heading in enumerate(self.data):
            text = heading.get("text", "")
            pattern_type, number, clean_text = self._detect_numbering_pattern(text)
            
            if pattern_type in ['main_chapter', 'simple_number'] and number > 0:
                numbered_items.append((number, i, pattern_type))
        
        # Group consecutive sequences
        numbered_items.sort(key=lambda x: x[0])
        sequences = []
        current_seq = []
        
        for number, idx, pattern_type in numbered_items:
            if not current_seq or number == current_seq[-1][0] + 1:
                current_seq.append((number, idx, pattern_type))
            else:
                if len(current_seq) >= 2:
                    sequences.append([item[1] for item in current_seq])
                current_seq = [(number, idx, pattern_type)]
        
        if len(current_seq) >= 2:
            sequences.append([item[1] for item in current_seq])
        
        return sequences

    def _find_common_prefixes(self) -> Dict[str, List[int]]:
        """Find headings with common prefixes (e.g., "2.1", "2.2", etc.)"""
        prefix_groups = defaultdict(list)
        
        for i, heading in enumerate(self.data):
            text = heading.get("text", "")
            
            # Look for numbered prefixes
            match = re.match(r'^(\d+\.\d+)', text.strip())
            if match:
                main_num = match.group(1).split('.')[0]
                prefix_groups[f"section_{main_num}"].append(i)
        
        # Only keep groups with multiple items
        return {k: v for k, v in prefix_groups.items() if len(v) >= 2}

    def _identify_structural_keywords(self) -> Dict[str, List[int]]:
        """Identify headings with structural keywords"""
        keyword_groups = defaultdict(list)
        
        for i, heading in enumerate(self.data):
            text = heading.get("text", "").lower()
            
            for category, keywords in DOCUMENT_STRUCTURE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        keyword_groups[category].append(i)
                        break
        
        return dict(keyword_groups)

    def _detect_numbering_pattern(self, text: str) -> Tuple[str, int, str]:
        """Enhanced numbering pattern detection with better parsing"""
        text_stripped = text.strip()
        
        # Check each pattern type with more sophisticated matching
        for pattern_name, pattern in NUMBERING_PATTERNS.items():
            match = pattern.match(text_stripped)
            if match:
                if pattern_name == 'main_chapter':
                    return 'main_chapter', int(match.group(1)), match.group(2).strip()
                elif pattern_name == 'subsection':
                    return 'subsection', int(match.group(1)), match.group(3).strip()
                elif pattern_name == 'subsubsection':
                    return 'subsubsection', int(match.group(1)), match.group(4).strip()
                elif pattern_name == 'simple_number':
                    return 'simple_number', int(match.group(1)), match.group(2).strip()
                elif pattern_name in ['roman_numeral', 'letter_numbering']:
                    return pattern_name, 1, match.group(2).strip()
                elif pattern_name == 'bullet_point':
                    return 'bullet_point', 0, match.group(1).strip()
        
        return 'none', 0, text_stripped

    def _classify_by_content_analysis(self, text: str, context: Dict[str, Any] = None) -> Tuple[float, str]:
        """Enhanced content-based classification with context awareness"""
        text_lower = text.lower().strip()
        words = text_lower.split()
        context = context or {}
        
        # Check for document structure keywords with weighted scoring
        max_score = 0.0
        suggested_level = 'H3'
        
        for category, keywords in DOCUMENT_STRUCTURE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if category == 'major_sections':
                        score = 0.9
                        level = 'H1'
                    elif category == 'standard_sections':
                        score = 0.7
                        level = 'H1'
                    elif category == 'subsections':
                        score = 0.8
                        level = 'H2'
                    
                    if score > max_score:
                        max_score = score
                        suggested_level = level
        
        # Check for hierarchy indicators
        for indicator, level in HIERARCHY_INDICATORS.items():
            if indicator in text_lower:
                indicator_score = 0.85
                if indicator_score > max_score:
                    max_score = indicator_score
                    suggested_level = level
        
        # Enhanced length-based heuristics with context
        word_count = len(words)
        char_count = len(text)
        
        # Adjust scoring based on length and context
        if max_score == 0.0:  # No keyword matches
            if word_count <= 2:
                max_score = 0.3
                suggested_level = 'H1'  # Very short often major
            elif word_count <= 5:
                max_score = 0.5
                suggested_level = 'H1' if context.get('is_top_of_page', False) else 'H2'
            elif word_count <= 10:
                max_score = 0.4
                suggested_level = 'H2'
            else:
                max_score = 0.2
                suggested_level = 'H3'
        
        # Context-based adjustments
        if context.get('is_first_on_page', False):
            max_score += 0.1
        
        if context.get('is_top_of_page', False):
            max_score += 0.05
        
        return max_score, suggested_level

    def _score_heading(self, h: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Enhanced scoring with sophisticated multi-parameter analysis"""
        text = h.get("text", "") or ""
        size = h.get("font_size", 0)
        bold = h.get("bold", False)
        italic = h.get("italic", False)
        page = h.get("page", 1)
        bbox = h.get("bbox", [0, 0, 0, 0])
        doc_type = h.get("type", "").lower()
        
        # Get heading index for context lookup
        heading_idx = next((i for i, data_h in enumerate(self.data) if data_h == h), 0)
        position_context = self.position_context.get(heading_idx, {})
        
        # Spatial measurements
        x0, y0, x1, y1 = bbox
        width = x1 - x0
        
        # Enhanced text analysis
        words = text.split()
        word_count = len(words)
        
        # Pattern analysis with context
        pattern_type, pattern_number, clean_text = self._detect_numbering_pattern(text)
        content_score, suggested_level = self._classify_by_content_analysis(text, position_context)
        
        # Initialize feature scores with adjusted weights
        features = {}
        
        # 1. Font Size Features (25% weight) - More nuanced
        size_cluster_rank = self.size_to_cluster_rank.get(size, len(self.size_clusters) - 1)
        num_clusters = len(self.size_clusters)
        
        if num_clusters > 1:
            size_cluster_weight = (num_clusters - 1 - size_cluster_rank) / (num_clusters - 1)
            features["font_size_cluster"] = 0.20 * size_cluster_weight
        else:
            features["font_size_cluster"] = 0.20
        
        features["font_size_norm"] = 0.05 * self.size_norm.get(size, 0.5)
        
        # 2. Enhanced Numbering Pattern Features (30% weight)
        if pattern_type == 'main_chapter':
            features["numbering_bonus"] = 0.25
            # Extra bonus for sequential numbers
            if pattern_number in self._get_sequential_numbers():
                features["numbering_bonus"] += 0.05
        elif pattern_type == 'subsection':
            features["numbering_bonus"] = 0.20
        elif pattern_type == 'subsubsection':
            features["numbering_bonus"] = 0.15
        elif pattern_type == 'simple_number' and pattern_number <= 10:
            features["numbering_bonus"] = 0.18
        else:
            features["numbering_bonus"] = 0.0
        
        # 3. Enhanced Content Analysis Features (20% weight)
        features["content_analysis"] = 0.20 * content_score
        
        # 4. Formatting Features (15% weight)
        features["bold_bonus"] = 0.10 if bold else 0.0
        features["italic_adjustment"] = -0.03 if italic and not bold else 0.0
        
        # Enhanced type-based scoring
        if doc_type == "doc_title":
            features["type_bonus"] = 0.08
        elif doc_type == "paragraph_title":
            features["type_bonus"] = 0.05
        else:
            features["type_bonus"] = 0.0
        
        # 5. Enhanced Spatial Features (10% weight)
        indent_level = self.indent_levels.get(x0, 0)
        features["indent_penalty"] = -0.06 * min(indent_level, 2)
        
        # Width-based scoring with percentiles
        if width > 0:
            if width >= self.width_percentiles['p75']:
                features["width_bonus"] = 0.04
            elif width >= self.width_percentiles['p50']:
                features["width_bonus"] = 0.02
            else:
                features["width_bonus"] = 0.0
        else:
            features["width_bonus"] = 0.0
        
        # 6. Enhanced Position Features (10% weight)
        # Page-based scoring with better distribution
        if page == 1:
            features["page_bonus"] = 0.08
        elif page <= 3:
            features["page_bonus"] = 0.05
        elif page <= 5:
            features["page_bonus"] = 0.03
        else:
            features["page_bonus"] = 0.0
        
        # Position on page with context
        if position_context.get('is_first_on_page', False):
            features["position_bonus"] = 0.02
        elif position_context.get('is_top_of_page', False):
            features["position_bonus"] = 0.01
        else:
            features["position_bonus"] = 0.0
        
        # 7. Enhanced Text Length Features (5% weight)
        if word_count == 1:
            features["length_adjustment"] = -0.02  # Single words less likely
        elif word_count <= 3:
            features["length_adjustment"] = 0.03  # Short phrases good
        elif word_count <= 6:
            features["length_adjustment"] = 0.01  # Medium length okay
        elif word_count <= 12:
            features["length_adjustment"] = 0.0   # Longer neutral
        else:
            features["length_adjustment"] = -0.01  # Very long slightly negative
        
        # 8. Sequence and Context Features (5% weight)
        # Check if part of numbered sequence
        if heading_idx in [idx for seq in self.text_patterns['numbered_sequences'] for idx in seq]:
            features["sequence_bonus"] = 0.03
        else:
            features["sequence_bonus"] = 0.0
        
        # Check if part of subsection group
        for prefix, indices in self.text_patterns['common_prefixes'].items():
            if heading_idx in indices:
                features["subsection_group_bonus"] = 0.02
                break
        else:
            features["subsection_group_bonus"] = 0.0
        
        # 9. Special adjustments for common cases
        text_lower = text.lower()
        
        # Penalize obvious non-headings
        if any(term in text_lower for term in ['copyright', 'version', 'page', '©']):
            features["noise_penalty"] = -0.15
        else:
            features["noise_penalty"] = 0.0
        
        # Bonus for title case
        if text.istitle() and word_count > 1:
            features["title_case_bonus"] = 0.02
        else:
            features["title_case_bonus"] = 0.0
        
        # Calculate final score
        total_score = sum(features.values())
        
        # Apply final contextual adjustments
        if pattern_type in ['main_chapter', 'subsection'] and content_score > 0.5:
            total_score += 0.05  # Boost for numbered + semantic match
        
        return max(0.0, total_score), features

    def _get_sequential_numbers(self) -> set:
        """Get set of numbers that appear in sequence"""
        sequential_nums = set()
        
        for seq in self.text_patterns['numbered_sequences']:
            for idx in seq:
                text = self.data[idx].get("text", "")
                _, number, _ = self._detect_numbering_pattern(text)
                if number > 0:
                    sequential_nums.add(number)
        
        return sequential_nums

    def _score_all(self) -> List[Dict[str, Any]]:
        """Score all headings with enhanced features"""
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

    def _extract_document_title(self, scored: List[Dict[str, Any]]) -> str:
        """Enhanced document title extraction with better logic"""
        if not scored:
            return ""
        
        # Look for titles on first page primarily
        first_page_candidates = [s for s in scored if s["heading"].get("page", 999) <= 1]
        
        if not first_page_candidates:
            first_page_candidates = scored[:3]  # Fallback to first few headings
        
        # Sort by position (top first), then by score
        first_page_candidates.sort(key=lambda x: (
            x["heading"].get("bbox", [0, 999, 0, 0])[1],  # Y position (smaller = higher)
            -x["score"]  # Higher score first
        ))
        
        # Look for explicit document titles first
        doc_title_candidates = [c for c in first_page_candidates 
                              if c["heading"].get("type") == "doc_title"]
        
        if doc_title_candidates:
            # Combine multiple title parts if they're consecutive and related
            title_parts = []
            base_candidate = doc_title_candidates[0]
            base_y = base_candidate["heading"].get("bbox", [0, 0, 0, 0])[1]
            
            for candidate in doc_title_candidates:
                candidate_y = candidate["heading"].get("bbox", [0, 0, 0, 0])[1]
                text = candidate["heading"].get("text", "").strip()
                
                # Include if close vertically and meaningful text
                if abs(candidate_y - base_y) < 50 and self._is_meaningful_title_text(text):
                    title_parts.append(text)
                    if len(title_parts) >= 3:  # Limit to avoid very long titles
                        break
            
            if title_parts:
                combined_title = " ".join(title_parts)
                # Clean up the combined title
                combined_title = re.sub(r'\s+', ' ', combined_title).strip()
                return combined_title
        
        # Fallback: use the highest scoring early candidate
        if first_page_candidates:
            best_candidate = first_page_candidates[0]  # Already sorted by position then score
            return best_candidate["heading"].get("text", "").strip()
        
        return ""

    def _is_meaningful_title_text(self, text: str) -> bool:
        """Check if text is meaningful for a title"""
        if not text or len(text.strip()) < 2:
            return False
        
        text_lower = text.lower().strip()
        
        # Exclude common non-title elements
        exclude_patterns = [
            r'^page\s+\d+',
            r'^version\s+',
            r'copyright',
            r'^\d{4}',
            r'^[a-z]{1,2}\s*',
            r'^\d+\s*'
        ]

        
        for pattern in exclude_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Check reasonable length
        words = text.split()
        if len(words) > 15 or len(text) > 150:
            return False
        
        return True

    def _create_hierarchical_outline(self, scored: List[Dict[str, Any]], document_title: str) -> List[Dict[str, Any]]:
        """Enhanced hierarchical outline generation with better level assignment"""
        outline = []
        
        # Filter out title components more intelligently
        title_text_lower = document_title.lower() if document_title else ""
        title_words = set(title_text_lower.split())
        used_in_title = set()
        
        # More sophisticated title filtering
        for s in scored:
            heading_text = s["heading"].get("text", "").lower()
            heading_words = set(heading_text.split())
            
            # Skip if substantial overlap with title and low uniqueness
            if title_words and len(title_words.intersection(heading_words)) >= min(3, len(title_words) * 0.7):
                # But only if the heading doesn't add significant new content
                unique_words = heading_words - title_words
                if len(unique_words) < 2:
                    used_in_title.add(s["idx"])
        
        # Get candidates for outline, excluding title parts
        outline_candidates = [s for s in scored if s["idx"] not in used_in_title]
        
        # Enhanced level assignment using multiple strategies
        final_assignments = self._assign_hierarchical_levels_advanced(outline_candidates)
        
        # Build outline with assigned levels
        for s, level in final_assignments:
            h = s["heading"]
            outline.append({
                "level": level.upper(),
                "text": h.get("text", "").strip(),
                "page": h.get("page", 1)
            })
        
        # Sort by page and position for proper document order
        outline.sort(key=lambda x: (
            x["page"], 
            self._get_heading_y_position(x["text"], scored)
        ))
        
        return outline

    def _get_heading_y_position(self, text: str, scored: List[Dict[str, Any]]) -> float:
        """Get Y position of heading by text match"""
        for s in scored:
            if s["heading"].get("text", "").strip() == text:
                return s["heading"].get("bbox", [0, 0, 0, 0])[1]
        return 0

    def _assign_hierarchical_levels_advanced(self, candidates: List[Dict]) -> List[Tuple]:
        """Advanced hierarchical level assignment using weighted multi-strategy approach"""
        if not candidates:
            return []
        
        # Strategy 1: Numbering-based hierarchy (highest weight)
        numbering_assignments = self._assign_by_advanced_numbering(candidates)
        
        # Strategy 2: Font and formatting hierarchy
        formatting_assignments = self._assign_by_advanced_formatting(candidates)
        
        # Strategy 3: Content semantic analysis
        semantic_assignments = self._assign_by_semantic_analysis(candidates)
        
        # Strategy 4: Spatial structure analysis
        spatial_assignments = self._assign_by_spatial_structure(candidates)
        
        # Strategy 5: Document flow analysis
        flow_assignments = self._assign_by_document_flow(candidates)
        
        # Weighted combination of all strategies
        final_assignments = self._combine_assignment_strategies(
            candidates,
            [
                (numbering_assignments, 4.0),    # Highest weight - numbering is most reliable
                (formatting_assignments, 2.5),   # Font size/formatting
                (semantic_assignments, 2.0),     # Content meaning
                (spatial_assignments, 1.5),      # Position/indentation
                (flow_assignments, 1.0)          # Document flow patterns
            ]
        )
        
        return final_assignments

    def _assign_by_advanced_numbering(self, candidates: List[Dict]) -> Dict[int, str]:
        """Advanced numbering-based level assignment"""
        assignments = {}
        
        # Build numbering hierarchy map
        numbering_hierarchy = {}
        
        for candidate in candidates:
            text = candidate["heading"].get("text", "")
            pattern_type, pattern_number, clean_text = self._detect_numbering_pattern(text)
            
            if pattern_type == 'main_chapter':
                # Main chapters are always H1
                assignments[candidate["idx"]] = "h1"
                numbering_hierarchy[pattern_number] = "h1"
            
            elif pattern_type == 'subsection':
                # Parse subsection numbers (e.g., "2.1" -> main=2, sub=1)
                parts = text.strip().split('.')
                if len(parts) >= 2:
                    try:
                        main_num = int(parts[0])
                        sub_num = int(parts[1].split()[0])  # Handle "2.1 Title"
                        
                        # Subsections are H2, but check if main number suggests otherwise
                        if main_num in numbering_hierarchy:
                            if numbering_hierarchy[main_num] == "h1":
                                assignments[candidate["idx"]] = "h2"
                            else:
                                assignments[candidate["idx"]] = "h3"
                        else:
                            assignments[candidate["idx"]] = "h2"
                    except (ValueError, IndexError):
                        assignments[candidate["idx"]] = "h2"
            
            elif pattern_type == 'subsubsection':
                assignments[candidate["idx"]] = "h3"
            
            elif pattern_type == 'simple_number':
                # Simple numbers could be main chapters if sequential and reasonable
                if pattern_number <= 10 and self._is_likely_main_chapter(text, pattern_number):
                    assignments[candidate["idx"]] = "h1"
                    numbering_hierarchy[pattern_number] = "h1"
                else:
                    assignments[candidate["idx"]] = "h2"
            
            else:
                # No numbering - use content analysis
                _, suggested_level = self._classify_by_content_analysis(text)
                assignments[candidate["idx"]] = suggested_level.lower()
        
        return assignments

    def _is_likely_main_chapter(self, text: str, number: int) -> bool:
        """Determine if a numbered item is likely a main chapter"""
        text_lower = text.lower()
        
        # Check for chapter indicators
        chapter_indicators = ['introduction', 'overview', 'background', 'methodology', 
                            'results', 'conclusion', 'references', 'appendix']
        
        if any(indicator in text_lower for indicator in chapter_indicators):
            return True
        
        # Check if it's part of a clear sequence
        if number <= 5:  # First few numbers more likely to be main chapters
            return True
        
        # Check text length and structure
        words = text.split()
        if len(words) <= 8 and not any(char.isdigit() for char in text[2:]):
            return True
        
        return False

    def _assign_by_advanced_formatting(self, candidates: List[Dict]) -> Dict[int, str]:
        """Advanced formatting-based assignment with relative analysis"""
        assignments = {}
        
        # Analyze font size distribution more sophisticatedly
        sizes = [c["heading"].get("font_size", 0) for c in candidates]
        unique_sizes = sorted(set(sizes), reverse=True)
        
        if len(unique_sizes) <= 1:
            # All same size - use other factors
            for candidate in candidates:
                bold = candidate["heading"].get("bold", False)
                doc_type = candidate["heading"].get("type", "")
                
                if doc_type == "doc_title" or bold:
                    assignments[candidate["idx"]] = "h1"
                else:
                    assignments[candidate["idx"]] = "h2"
            return assignments
        
        # Create size-based tiers
        if len(unique_sizes) >= 3:
            large_threshold = unique_sizes[0]
            medium_threshold = unique_sizes[1]
            small_threshold = unique_sizes[2]
        elif len(unique_sizes) == 2:
            large_threshold = unique_sizes[0]
            medium_threshold = unique_sizes[1]
            small_threshold = unique_sizes[1]
        else:
            large_threshold = medium_threshold = small_threshold = unique_sizes[0]
        
        for candidate in candidates:
            size = candidate["heading"].get("font_size", 0)
            bold = candidate["heading"].get("bold", False)
            doc_type = candidate["heading"].get("type", "")
            
            # Base assignment on size tier
            if size >= large_threshold:
                base_level = "h1"
            elif size >= medium_threshold:
                base_level = "h2"
            else:
                base_level = "h3"
            
            # Adjust based on formatting
            if bold and base_level == "h2":
                base_level = "h1"  # Promote bold medium text
            elif not bold and base_level == "h1" and size < large_threshold:
                base_level = "h2"  # Demote non-bold large text
            
            # Type-based adjustments
            if doc_type == "doc_title":
                base_level = "h1"
            
            assignments[candidate["idx"]] = base_level
        
        return assignments

    def _assign_by_semantic_analysis(self, candidates: List[Dict]) -> Dict[int, str]:
        """Semantic content analysis for level assignment"""
        assignments = {}
        
        for candidate in candidates:
            text = candidate["heading"].get("text", "")
            score, level = self._classify_by_content_analysis(text)
            
            # Additional semantic checks
            text_lower = text.lower()
            
            # Major document sections
            if any(term in text_lower for term in ['introduction', 'overview', 'conclusion', 
                                                  'references', 'acknowledgements', 'abstract']):
                assignments[candidate["idx"]] = "h1"
            
            # Subsection indicators
            elif any(term in text_lower for term in ['intended audience', 'learning objectives',
                                                   'entry requirements', 'business outcomes']):
                assignments[candidate["idx"]] = "h2"
            
            # Use content analysis result
            else:
                assignments[candidate["idx"]] = level.lower()
        
        return assignments

    def _assign_by_spatial_structure(self, candidates: List[Dict]) -> Dict[int, str]:
        """Spatial structure analysis for level assignment"""
        assignments = {}
        
        for candidate in candidates:
            bbox = candidate["heading"].get("bbox", [0, 0, 0, 0])
            x0 = bbox[0]
            width = bbox[2] - bbox[0] if len(bbox) >= 3 else 0
            
            # Indentation-based assignment
            indent_level = self.indent_levels.get(x0, 0)
            
            if indent_level == 0:
                # No indentation - likely main heading
                if width >= self.width_percentiles['p75']:
                    assignments[candidate["idx"]] = "h1"
                else:
                    assignments[candidate["idx"]] = "h2"
            elif indent_level == 1:
                assignments[candidate["idx"]] = "h2"
            else:
                assignments[candidate["idx"]] = "h3"
        
        return assignments

    def _assign_by_document_flow(self, candidates: List[Dict]) -> Dict[int, str]:
        """Document flow pattern analysis"""
        assignments = {}
        
        # Sort candidates by page and position
        sorted_candidates = sorted(candidates, key=lambda c: (
            c["heading"].get("page", 1),
            c["heading"].get("bbox", [0, 0, 0, 0])[1]
        ))
        
        # Analyze flow patterns
        prev_level = None
        section_depth = 0
        
        for i, candidate in enumerate(sorted_candidates):
            text = candidate["heading"].get("text", "")
            pattern_type, number, clean_text = self._detect_numbering_pattern(text)
            
            # Flow-based decision making
            if pattern_type == 'main_chapter':
                current_level = "h1"
                section_depth = 1
            elif pattern_type == 'subsection':
                current_level = "h2"
                section_depth = 2
            elif i == 0:  # First heading
                current_level = "h1"
                section_depth = 1
            else:
                # Context-based decision
                if prev_level == "h1":
                    current_level = "h2" if section_depth < 3 else "h1"
                elif prev_level == "h2":
                    current_level = "h2"
                else:
                    current_level = "h3"
            
            assignments[candidate["idx"]] = current_level
            prev_level = current_level
        
        return assignments

    def _combine_assignment_strategies(self, candidates: List[Dict], 
                                     strategy_weights: List[Tuple[Dict[int, str], float]]) -> List[Tuple]:
        """Combine multiple assignment strategies with weighted voting"""
        final_assignments = []
        
        for candidate in candidates:
            idx = candidate["idx"]
            level_votes = Counter()
            
            # Collect weighted votes from each strategy
            for assignments, weight in strategy_weights:
                if idx in assignments:
                    level = assignments[idx]
                    level_votes[level] += weight
            
            # Additional contextual boosts
            text = candidate["heading"].get("text", "")
            pattern_type, pattern_number, clean_text = self._detect_numbering_pattern(text)
            
            # Strong boost for clear main chapters
            if pattern_type == 'main_chapter':
                level_votes['h1'] += 3.0
            
            # Boost for subsections
            elif pattern_type == 'subsection':
                level_votes['h2'] += 2.0
            
            # Content-based boosts
            text_lower = text.lower()
            if any(term in text_lower for term in ['introduction', 'overview', 'references']):
                level_votes['h1'] += 1.5
            elif any(term in text_lower for term in ['intended audience', 'learning objectives']):
                level_votes['h2'] += 1.0
            
            # Determine final level
            if level_votes:
                final_level = level_votes.most_common(1)[0][0]
            else:
                # Ultimate fallback
                score = candidate.get("score", 0)
                if score > 0.7:
                    final_level = "h1"
                elif score > 0.4:
                    final_level = "h2"
                else:
                    final_level = "h3"
            
            final_assignments.append((candidate, final_level))
        
        return final_assignments


def classify_from_json(structure_json_path: str, output_path: str, debug: bool = False):
    """Main function to classify titles from JSON structure data"""
    try:
        with open(structure_json_path, "r", encoding="utf-8") as f:
            structure_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Structure file not found: {structure_json_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in structure file: {e}")
        return

    clf = AdvancedTitleClassifier(structure_data, max_levels=4)
    result = clf.classify()

    if debug:
        debug_info = {
            "total_headings": clf.debug_info["total_headings"],
            "font_clusters": len(clf.size_clusters),
            "cluster_sizes": [len(cluster) for cluster in clf.size_clusters],
            "size_distribution": dict(clf.debug_info["font_size_distribution"]),
            "page_distribution": dict(clf.debug_info["page_distribution"]),
            "text_length_stats": {
                "mean": statistics.mean(clf.debug_info["text_lengths"]) if clf.debug_info["text_lengths"] else 0,
                "median": statistics.median(clf.debug_info["text_lengths"]) if clf.debug_info["text_lengths"] else 0
            }
        }
        output = {**result, "debug_info": debug_info}
    else:
        output = result

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"❌ Error: Cannot write to output file: {e}")
        return

    # Print summary
    title = result.get("title", "")
    outline = result.get("outline", [])

    print(f"✅ Document processed:")
    print(f"   Title: {title[:80]}{'...' if len(title) > 80 else ''}")
    print(f"   Outline items: {len(outline)}")
    
    if outline:
        level_counts = Counter(item["level"] for item in outline)
        for level, count in sorted(level_counts.items()):
            print(f"   {level}: {count}")
        
        # Show first few outline items for verification
        print(f"\n📋 First few outline items:")
        for i, item in enumerate(outline[:5]):
            print(f"   {item['level']}: {item['text'][:60]}{'...' if len(item['text']) > 60 else ''} (page {item['page']})")
    
    print(f"\n💾 Saved to: {output_path}")


# Additional utility functions remain the same as in original
def analyze_document_structure(structure_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze document structure to provide insights for classification"""
    headings = [h for h in structure_data if h.get("is_heading")]
    
    if not headings:
        return {"error": "No headings found"}
    
    # Font size analysis
    font_sizes = [h.get("font_size", 0) for h in headings]
    size_stats = {
        "unique_sizes": len(set(font_sizes)),
        "size_range": max(font_sizes) - min(font_sizes) if font_sizes else 0,
        "most_common_size": Counter(font_sizes).most_common(1)[0] if font_sizes else None
    }
    
    # Numbering pattern analysis
    numbering_patterns = {}
    for h in headings:
        text = h.get("text", "")
        for pattern_name, pattern in NUMBERING_PATTERNS.items():
            if pattern.match(text.strip()):
                numbering_patterns[pattern_name] = numbering_patterns.get(pattern_name, 0) + 1
                break
    
    # Content keyword analysis
    keyword_matches = {category: 0 for category in DOCUMENT_STRUCTURE_KEYWORDS.keys()}
    for h in headings:
        text = h.get("text", "").lower()
        for category, keywords in DOCUMENT_STRUCTURE_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                keyword_matches[category] += 1
    
    return {
        "total_headings": len(headings),
        "font_analysis": size_stats,
        "numbering_patterns": numbering_patterns,
        "content_keywords": keyword_matches,
        "page_distribution": Counter(h.get("page", 1) for h in headings)
    }


def validate_classification_results(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and provide feedback on classification results"""
    outline = result.get("outline", [])
    
    if not outline:
        return {"status": "error", "message": "No outline generated"}
    
    # Check level distribution
    level_counts = Counter(item["level"] for item in outline)
    
    # Validation checks
    issues = []
    suggestions = []
    
    # Check if we have reasonable H1 distribution
    h1_count = level_counts.get("H1", 0)
    total_items = len(outline)
    
    if h1_count == 0:
        issues.append("No H1 headings found - document structure may be too flat")
    elif h1_count > total_items * 0.6:
        issues.append("Too many H1 headings - structure may be too flat")
        suggestions.append("Consider adjusting scoring weights to create more hierarchy")
    
    # Check for numbering consistency
    numbered_items = []
    for item in outline:
        text = item["text"]
        if re.match(r'^\d+\.', text.strip()):
            numbered_items.append(item)
    
    if len(numbered_items) > 2:
        numbers = []
        for item in numbered_items:
            match = re.match(r'^(\d+)\.', item["text"].strip())
            if match:
                numbers.append(int(match.group(1)))
        
        if numbers and sorted(numbers) != list(range(min(numbers), max(numbers) + 1)):
            issues.append("Numbered sections are not consecutive")
    
    # Check page distribution
    pages = [item["page"] for item in outline]
    if pages:
        page_span = max(pages) - min(pages)
        if page_span > 0 and h1_count / page_span > 2:
            suggestions.append("High density of H1 headings per page - consider reviewing classification")
    
    return {
        "status": "success" if not issues else "warning",
        "issues": issues,
        "suggestions": suggestions,
        "statistics": {
            "total_items": total_items,
            "level_distribution": dict(level_counts),
            "page_span": max(pages) - min(pages) + 1 if pages else 0,
            "numbered_sections": len(numbered_items)
        }
    }


# Main execution when run as script
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Title Classification for PDF Documents")
    parser.add_argument("structure_json", help="Path to structure JSON file")
    parser.add_argument("--output", "-o", help="Output path for classified results", 
                       default="output/classified_results.json")
    parser.add_argument("--debug", "-d", action="store_true", 
                       help="Include debug information in output")
    parser.add_argument("--analyze", "-a", action="store_true",
                       help="Perform structure analysis before classification")
    parser.add_argument("--validate", "-v", action="store_true",
                       help="Validate classification results")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.structure_json):
        print(f"❌ Error: Structure file not found: {args.structure_json}")
        exit(1)
    
    print("🚀 Enhanced Title Classification")
    print("=" * 50)
    
    if args.analyze:
        print("📊 Analyzing document structure...")
        with open(args.structure_json, "r", encoding="utf-8") as f:
            structure_data = json.load(f)
        
        analysis = analyze_document_structure(structure_data)
        print("📋 Structure Analysis Results:")
        for key, value in analysis.items():
            print(f"   {key}: {value}")
        print()
    
    print("🏷️  Classifying titles...")
    classify_from_json(args.structure_json, args.output, debug=args.debug)
    
    if args.validate:
        print("\n🔍 Validating results...")
        with open(args.output, "r", encoding="utf-8") as f:
            results = json.load(f)
        
        validation = validate_classification_results(results)
        print(f"Validation Status: {validation['status']}")
        
        if validation.get('issues'):
            print("⚠️  Issues found:")
            for issue in validation['issues']:
                print(f"   • {issue}")
        
        if validation.get('suggestions'):
            print("💡 Suggestions:")
            for suggestion in validation['suggestions']:
                print(f"   • {suggestion}")
        
        print("\n📈 Classification Statistics:")
        stats = validation.get('statistics', {})
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print("\n✅ Classification complete!")
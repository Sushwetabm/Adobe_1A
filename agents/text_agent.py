
import re
from utils.helpers import detect_language

class TextAnalysisAgent:
    def __init__(self, structure_data):
        self.data = structure_data
       
        sample_text = " ".join(item["text"] for item in self.data if item["page"] == 1 and len(item["text"]) > 20)
        self.language = detect_language(sample_text) if sample_text else "unknown"

    def analyze_text(self):
        num_pattern = re.compile(r"^\d+(\.\d+)*\s")
        for item in self.data:
            text = item["text"]
            item["is_numbered"] = bool(num_pattern.match(text))
            
            words = [w for w in text.split() if len(w) > 3]
            item["is_uppercase"] = any(w.isupper() for w in words) if words else text.isupper()
            item["is_short"] = len(text.split()) < 5
            
            item["language"] = self.language
            
        return self.data
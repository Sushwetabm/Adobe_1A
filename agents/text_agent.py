import re
from utils.helpers import detect_language

class TextAnalysisAgent:
    def __init__(self, structure_data):
        self.data = structure_data

    def analyze_text(self):
        for item in self.data:
            text = item["text"]
            item["is_numbered"] = bool(re.match(r"^(\d+(\.\d+)*[\.\)])?\s?[A-Z]", text))
            item["is_uppercase"] = text.isupper()
            item["is_short"] = len(text) < 50
            item["language"] = detect_language(text)
        return self.data

class ValidationAgent:
    def __init__(self, headings):
        self.headings = headings

    def validate(self):
        if not self.headings:
            return {"title": "Unknown", "outline": []}

        sorted_headings = sorted(self.headings, key=lambda x: (x["page"], x["bbox"][1]))
        title = sorted_headings[0]["text"] if sorted_headings else "Untitled"

        outline = [
            {"level": h["level"], "text": h["text"], "page": h["page"]}
            for h in sorted_headings
        ]
        return {"title": title, "outline": outline}

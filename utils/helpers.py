import os
from langdetect import detect

def get_pdf_files(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".pdf")]

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def log(message):
    print(f"[LOG] {message}")
# utils/helpers.py

def is_toc_page(structure_data, page_num, threshold=0.4):
    spans = [i for i in structure_data if i["page"] == page_num]
    if not spans:
        return False
    # fraction of lines with >10% dots
    dotty = sum(1 for i in spans if i["text"].count('.') / max(len(i["text"]), 1) > 0.1)
    return (dotty / len(spans)) > threshold

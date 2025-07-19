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

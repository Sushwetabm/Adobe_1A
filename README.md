# PDF Outline Extractor (Adobe_1A)

## 🧾 Introduction

**Adobe_1A** is a document structure extraction tool designed to analyze PDFs and extract meaningful hierarchical outlines using layout detection, visual analysis, and text processing. It leverages the PP-DocLayout-L model from PaddleOCR, integrates multiple specialized agents for different analytical tasks, and supports multi-processing PDF processing for efficiency. This system is ideal for extracting structured content from complex PDFs, such as academic papers, reports, and manuals, without requiring internet access.

---

## 🏗️ Architecture Overview

Adobe_1A uses a modular, agent-based pipeline to process PDFs:

1. **StructureAnalysisAgent**  
   Extracts raw PDF text with font and positional metadata from model outputs.

2. **VisualAnalysisAgent**  
   Analyzes font ratios, formatting, and isolation to identify visual cues for headings.

3. **TextAnalysisAgent**  
   Evaluates text length, patterns, and heading candidates using linguistic features.

4. **HierarchyAgent**  
   Scores and assigns heading levels, building a hierarchical outline.

5. **ValidationAgent**  
   Validates and refines the outline, producing the final structured JSON output.

6. **AdvancedTitleClassifier**  
   (Conditional) Used for documents with clear title structures.

---

## ⚙️ Workflow

1. **Input PDFs**  
   Place your PDF files in the `/app/input` directory.

2. **Model Inference**  
   For each PDF, the system runs `model.py` to generate layout and text extraction results (`*_all_elements_results.json`).

3. **Agentic Pipeline**

   - If the document contains `paragraph_title`, `doc_title`, or `table_title`, the **Advanced Title Classifier Agent** runs to extract the outline using advanced text classification.
   - Otherwise, for documents with text on image or lacking clear titles, the standard pipeline is used:
     - Structure agent parses model output.
     - Visual and text agents analyze features.
     - Hierarchy agent ranks headings and builds the outline.
     - Validation agent ensures output quality.

4. **Output JSONs**  
   Final structured outlines are saved in `/app/output` as `*_classified.json`.

---

## 🚀 Quick Start

### 1. **Requirements**

- Docker
- Python 3.9+ (tested on 3.9/3.10)
- CPU only
- No Internet required

### 2. **Build the Docker Image**

```bash
docker build -t pdf-extractor:test .
```

### 3. **Run the Extractor**

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-extractor:test
```

- Place PDFs in `input/`
- Extracted outlines will appear in `output/`

---

## 📁 Directory Structure

```
Adobe_1A/
├── agents/
│   ├── structure_agent.py
│   ├── visual_agent.py
│   ├── text_agent.py
│   ├── hierarchy_agent.py
│   ├── validation_agent.py
│   └── TitleClassifier.py
├── utils/
│   └── helpers.py
├── input/           # Place your PDFs here
├── output/          # Extracted outlines appear here
├── extract_outline.py
├── model.py         # Runs PP-DocLayout-L inference
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🧠 Agent Details

- **StructureAnalysisAgent**  
  Loads model output and parses text blocks with layout metadata.

- **VisualAnalysisAgent**  
  Computes font sizes, boldness, spacing, and isolation to detect headings visually.

- **TextAnalysisAgent**  
  Uses regex, length, and linguistic cues to identify heading candidates.

- **HierarchyAgent**  
  Assigns heading levels and builds a tree structure for the outline.

- **ValidationAgent**  
  Checks for consistency, removes false positives, and outputs final JSON.

- **AdvancedTitleClassifier**  
  Used for documents with clear title structures (e.g., academic papers, paragraph titles, doc titles, table titles).

---

## 📝 Output Format

Each processed PDF produces a JSON file with a hierarchical outline, including heading levels, text, and positional metadata.

Example:

```json
[
  {
    "level": 1,
    "title": "Introduction",
    "children": [
      {
        "level": 2,
        "title": "Background",
        "children": []
      }
    ]
  }
]
```

---

## 🛠️ Troubleshooting

- Ensure all PDFs are placed in `/app/input`.
- If output JSONs are missing, check logs for errors in model inference or agent processing.
- The pipeline expects model outputs (`*_all_elements_results.json`) for each PDF.

---

## 📚 References

- [PaddleOCR PP-DocLayout-L](https://github.com/PaddlePaddle/PaddleOCR)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

---

## ✨ Contributors

Hansawani Saini
Rishav Sachdeva
Sushweta Bhattacharya

# PDF Outline Extractor (Adobe Hackathon)

This is an agentic system to extract structured outlines from PDFs using 5 cooperating agents.

## 🔧 Requirements

- Docker
- Python 3.9
- CPU only
- No Internet

## 📁 Input/Output

- Input PDFs in `/app/input`
- Output JSONs in `/app/output`

## 🧠 Agent Architecture

1. **StructureAnalysisAgent**: Extract raw PDF text with font/positional metadata
2. **VisualAnalysisAgent**: Analyzes font ratios, formatting, isolation
3. **TextAnalysisAgent**: Checks text length, patterns, headings
4. **HierarchyAgent**: Scores and assigns heading levels
5. **ValidationAgent**: Validates and produces final JSON

## 🚀 Build & Run

```bash
docker build -t pdf-extractor:test .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:test
```

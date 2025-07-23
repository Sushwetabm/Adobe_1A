# import os
# import json
# import time
# import fitz
# from agents.structure_agent import StructureAnalysisAgent
# from agents.visual_agent import VisualAnalysisAgent
# from agents.text_agent import TextAnalysisAgent
# from agents.hierarchy_agent import HierarchyAgent
# from agents.validation_agent import ValidationAgent
# from concurrent.futures import ThreadPoolExecutor
# from utils.helpers import get_pdf_files, log

# INPUT_DIR = "input"
# OUTPUT_DIR = "output"

# def process_pdf(file_path):
#     filename = os.path.basename(file_path)
#     try:
#         start_time = time.time()

#         log(f"🕐 Processing {filename}")
#         doc = fitz.open(file_path)

#         structure_agent = StructureAnalysisAgent(doc)
#         structure_data = structure_agent.extract_structure()

#         visual_agent = VisualAnalysisAgent(structure_data)
#         visual_features = visual_agent.analyze_visual()

#         text_agent = TextAnalysisAgent(structure_data)
#         text_features = text_agent.analyze_text()

#         hierarchy_agent = HierarchyAgent(structure_data, visual_features, text_features)
#         headings = hierarchy_agent.rank_headings()

#         validation_agent = ValidationAgent(headings)
#         final_output = validation_agent.validate()

#         output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
#         with open(output_path, "w", encoding="utf-8") as f:
#             json.dump(final_output, f, indent=2, ensure_ascii=False)

#         end_time = time.time()
#         duration = end_time - start_time
#         log(f"✅ Done: {filename} in {duration:.2f} seconds")

#     except Exception as e:
#         log(f"❌ Error processing {filename}: {e}")

# def main():
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     pdf_files = get_pdf_files(INPUT_DIR)

#     log(f"📂 Found {len(pdf_files)} PDFs in input folder.")
#     start_all = time.time()

#     with ThreadPoolExecutor() as executor:
#         executor.map(process_pdf, pdf_files)

#     end_all = time.time()
#     total_time = end_all - start_all
#     log(f"🏁 All PDFs processed in {total_time:.2f} seconds")

# if __name__ == "__main__":
#     main()
import os
import json
import time
import fitz
from agents.structure_agent import StructureAnalysisAgent
from agents.visual_agent import VisualAnalysisAgent
from agents.text_agent import TextAnalysisAgent
from agents.hierarchy_agent import HierarchyAnalysisAgent as HierarchyAgent
from agents.validation_agent import ValidationAgent
from concurrent.futures import ThreadPoolExecutor
from utils.helpers import get_pdf_files, log

INPUT_DIR = "input"
OUTPUT_DIR = "output"

def process_pdf(file_path):
    filename = os.path.basename(file_path)
    try:
        start_time = time.time()

        log(f"🕐 Processing {filename}")
        doc = fitz.open(file_path)

        structure_agent = StructureAnalysisAgent(doc)
        structure_data = structure_agent.extract_structure()

        visual_agent = VisualAnalysisAgent(structure_data)
        visual_features = visual_agent.analyze_visual()

        text_agent = TextAnalysisAgent(structure_data)
        text_features = text_agent.analyze_text()

        hierarchy_agent = HierarchyAgent(structure_data, visual_features, text_features)
        analysis = hierarchy_agent.rank_headings()
        headings = analysis["outline"]

        validation_agent = ValidationAgent(headings, structure_data)
        final_output = validation_agent.validate()

        output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        end_time = time.time()
        duration = end_time - start_time
        log(f"✅ Done: {filename} in {duration:.2f} seconds")

    except Exception as e:
        log(f"❌ Error processing {filename}: {e}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_files = get_pdf_files(INPUT_DIR)

    log(f"📂 Found {len(pdf_files)} PDFs in input folder.")
    start_all = time.time()

    with ThreadPoolExecutor() as executor:
        executor.map(process_pdf, pdf_files)

    end_all = time.time()
    total_time = end_all - start_all
    log(f"🏁 All PDFs processed in {total_time:.2f} seconds")

if __name__ == "__main__":
    main()

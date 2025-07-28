# # import os
# # import json
# # import time
# # import fitz
# # from agents.structure_agent import StructureAnalysisAgent
# # from agents.visual_agent import VisualAnalysisAgent
# # from agents.text_agent import TextAnalysisAgent
# # from agents.hierarchy_agent import HierarchyAgent
# # from agents.validation_agent import ValidationAgent
# # from concurrent.futures import ThreadPoolExecutor
# # from utils.helpers import get_pdf_files, log

# # INPUT_DIR = "input"
# # OUTPUT_DIR = "output"

# # def process_pdf(file_path):
# #     filename = os.path.basename(file_path)
# #     try:
# #         start_time = time.time()

# #         log(f"🕐 Processing {filename}")
# #         doc = fitz.open(file_path)

# #         structure_agent = StructureAnalysisAgent(doc)
# #         structure_data = structure_agent.extract_structure()

# #         visual_agent = VisualAnalysisAgent(structure_data)
# #         visual_features = visual_agent.analyze_visual()

# #         text_agent = TextAnalysisAgent(structure_data)
# #         text_features = text_agent.analyze_text()

# #         hierarchy_agent = HierarchyAgent(structure_data, visual_features, text_features)
# #         headings = hierarchy_agent.rank_headings()

# #         validation_agent = ValidationAgent(headings)
# #         final_output = validation_agent.validate()

# #         output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
# #         with open(output_path, "w", encoding="utf-8") as f:
# #             json.dump(final_output, f, indent=2, ensure_ascii=False)

# #         end_time = time.time()
# #         duration = end_time - start_time
# #         log(f"✅ Done: {filename} in {duration:.2f} seconds")

# #     except Exception as e:
# #         log(f"❌ Error processing {filename}: {e}")

# # def main():
# #     os.makedirs(OUTPUT_DIR, exist_ok=True)
# #     pdf_files = get_pdf_files(INPUT_DIR)

# #     log(f"📂 Found {len(pdf_files)} PDFs in input folder.")
# #     start_all = time.time()

# #     with ThreadPoolExecutor() as executor:
# #         executor.map(process_pdf, pdf_files)

# #     end_all = time.time()
# #     total_time = end_all - start_all
# #     log(f"🏁 All PDFs processed in {total_time:.2f} seconds")

# # if __name__ == "__main__":
# #     main()
# import os
# import json
# import time
# import fitz
# from agents.structure_agent import StructureAnalysisAgent
# from agents.visual_agent import VisualAnalysisAgent
# from agents.text_agent import TextAnalysisAgent
# from agents.hierarchy_agent import HierarchyAnalysisAgent as HierarchyAgent
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
#         analysis = hierarchy_agent.rank_headings()
#         headings = analysis["outline"]

#         validation_agent = ValidationAgent(headings, structure_data)
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

# Import all necessary custom agents
from agents.structure_agent import StructureAnalysisAgent
from agents.visual_agent import VisualAnalysisAgent
from agents.text_agent import TextAnalysisAgent
from agents.hierarchy_agent import HierarchyAnalysisAgent as HierarchyAgent
from agents.validation_agent import ValidationAgent
from agents.TitleClassifier import AdvancedTitleClassifier   
from utils.helpers import get_pdf_files, log

INPUT_DIR = "input"
OUTPUT_DIR = "output"

def get_all_elements_path(pdf_path):
    # Now: input/abc.pdf --> output/abc_all_elements_result.json
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    return os.path.join("output", f"{base}_all_elements_results.json")


import subprocess

def run_model_on_pdf(pdf_path):
    """
    Call model.py on a single PDF file.
    This will execute: python model.py pdf_path
    Adjust the command if your model.py requires different arguments.
    """
    try:
        subprocess.run(
            ["python", "model.py", pdf_path],
            check=True  # This raises an error if the model fails
        )
    except subprocess.CalledProcessError as e:
        print(f"Model failed for {pdf_path}: {e}")


def extract_structure_for_all_pdfs(pdf_files):
    for file_path in pdf_files:
        filename = os.path.basename(file_path)
        try:
            start_time = time.time()
            log(f"🕐 Processing {filename}")

            all_elements_path = get_all_elements_path(file_path)

            if not os.path.exists(all_elements_path):
                log(f"❌ Missing all_elements_result.json for {filename} (expected at {all_elements_path})")
                continue

            structure_agent = StructureAnalysisAgent(all_elements_path, file_path)
            structure_data = structure_agent.extract_structure()
            

            # Classification step
            classifier = AdvancedTitleClassifier(structure_data,max_levels=4)
            classified_titles = classifier.classify()

            output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", "_classified.json"))
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(classified_titles, f, indent=2, ensure_ascii=False)

            end_time = time.time()
            duration = end_time - start_time
            log(f"✅ Done: {filename} in {duration:.2f} seconds")

        except Exception as e:
            log(f"❌ Error processing {filename}: {e}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_files = get_pdf_files(INPUT_DIR)

    log(f"📂 Found {len(pdf_files)} PDFs in input folder.")

    # STEP 1: Run model on all PDFs, one by one (SEQUENTIALLY)
    for pdf_path in pdf_files:
        run_model_on_pdf(pdf_path)

    # Confirm that all model outputs are present before proceeding
    missing = [f for f in pdf_files if not os.path.exists(get_all_elements_path(f))]
    if missing:
        log(f"❌ The following PDFs are missing model outputs: {[os.path.basename(f) for f in missing]}")
        return

    # STEP 2: Now run structure agent + rest of pipeline (SEQUENTIALLY)
    extract_structure_for_all_pdfs(pdf_files)

    log("🏁 All PDFs processed.")

if __name__ == "__main__":
    main()

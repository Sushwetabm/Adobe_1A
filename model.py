from paddleocr import LayoutDetection
from PIL import Image
import fitz  # PyMuPDF
import os
import json
from datetime import datetime
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import gc

# Keep your original CPU settings but optimize them
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'

# Single global model to avoid reloading
_model_instance = None

def get_shared_model():
    """Load model once and reuse - biggest speedup"""
    global _model_instance
    if _model_instance is None:
        print("🔧 Loading layout detection model...")
        _model_instance = LayoutDetection(model_name="PP-DocLayout-L")

    return _model_instance

def _init_worker():
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['FLAGS_use_mkldnn'] = '1'
    get_shared_model()


def process_single_image_optimized(img_path):
    """Your original function but with shared model"""
    model = get_shared_model()
    try:
        output = model.predict(img_path, batch_size=1)
        return img_path, output, True
    except Exception as e:
        print(f"❌ Error processing {img_path}: {e}")
        return img_path, [], False


class FastPDFProcessor:
    def __init__(self, max_workers=6):  # Conservative worker count
        self.layout_model = None
        self.max_workers = max_workers

    def _get_layout_model(self):
        """Keep your original model loading"""
        return get_shared_model()

    def convert_pdf_to_images_fast(self, pdf_path, output_dir="images", dpi=55):
        """Your original function with minor DPI optimization"""
        os.makedirs(output_dir, exist_ok=True)
        doc = fitz.open(pdf_path)
        image_paths = []

        print(f"📄 Converting {len(doc)} pages to images (DPI: {dpi})...")

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Slightly lower DPI for speed
            pix = page.get_pixmap(dpi=dpi)
            image_path = os.path.join(output_dir, f"page_{page_num+1}.png")
            pix.save(image_path)
            image_paths.append(image_path)
            pix = None

        return image_paths, doc

    def extract_text_from_coordinates(self, pdf_doc, page_num, bbox, dpi=55):
        """Modified to handle all element types better"""
        try:
            page = pdf_doc.load_page(page_num)
            page_rect = page.rect

            pix = page.get_pixmap(dpi=dpi)
            scale_x = page_rect.width / pix.width
            scale_y = page_rect.height / pix.height

            x1, y1, x2, y2 = bbox
            pdf_rect = fitz.Rect(
                x1 * scale_x, y1 * scale_y,
                x2 * scale_x, y2 * scale_y
            )

            # Try different extraction methods for better results
            text = page.get_text("text", clip=pdf_rect)

            # If no text found, try getting text blocks in the area
            if not text or not text.strip():
                text_blocks = page.get_text("blocks", clip=pdf_rect)
                if text_blocks:
                    text = " ".join([block[4] for block in text_blocks if len(block) > 4])

            return text.strip() if text else ""

        except Exception as e:
            print(f"⚠️ Text extraction error: {e}")
            return ""

    def process_layout_result_all_elements(self, det_result, pdf_doc, page_num, dpi=55):
        """MODIFIED: Extract text for ALL element types"""
        result = {
            "page_number": page_num + 1,
            "elements": [],
            "element_counts": {}
        }

        try:
            boxes = det_result.get('boxes', [])

            if boxes:
                sorted_boxes = sorted(
                    boxes,
                    key=lambda box: box.get('coordinate', [0, 0, 0, 0])[1]
                )

                for i, box in enumerate(sorted_boxes):
                    label = box.get('label', 'unknown').lower()
                    score = box.get('score', 0)
                    coordinate = box.get('coordinate', [0, 0, 0, 0])

                    result["element_counts"][label] = result["element_counts"].get(label, 0) + 1

                    # MODIFIED: Extract text for ALL elements, not just specific types
                    text_content = ""
                    try:
                        text_content = self.extract_text_from_coordinates(
                            pdf_doc, page_num, coordinate, dpi
                        )
                    except Exception as e:
                        print(f"⚠️ Failed to extract text for {label}: {e}")

                    element = {
                        "id": i + 1,
                        "type": label,
                        "confidence": round(float(score), 3),
                        "text": text_content,
                        "bbox": [float(x) for x in coordinate]  # Convert numpy types to Python float
                    }

                    result["elements"].append(element)

        except Exception as e:
            result["error"] = str(e)

        return result

    def process_layout_result_titles_only(self, det_result, pdf_doc, page_num, dpi=55):
        """Extract ONLY doc_title and paragraph_title elements"""
        result = {
            "page_number": page_num + 1,
            "elements": [],
            "element_counts": {}
        }

        try:
            boxes = det_result.get('boxes', [])

            if boxes:
                sorted_boxes = sorted(
                    boxes,
                    key=lambda box: box.get('coordinate', [0, 0, 0, 0])[1]
                )

                for i, box in enumerate(sorted_boxes):
                    label = box.get('label', 'unknown').lower()
                    score = box.get('score', 0)
                    coordinate = box.get('coordinate', [0, 0, 0, 0])

                    # ONLY process title elements
                    if label in ['doc_title', 'paragraph_title'] and score >= 0.6:
                        result["element_counts"][label] = result["element_counts"].get(label, 0) + 1

                        text_content = ""
                        try:
                            text_content = self.extract_text_from_coordinates(
                                pdf_doc, page_num, coordinate, dpi
                            )
                        except Exception as e:
                            print(f"⚠️ Failed to extract text for {label}: {e}")

                        element = {
                            "id": i + 1,
                            "type": label,
                            "confidence": round(float(score), 3),
                            "text": text_content,
                            "bbox": [float(x) for x in coordinate]  # Convert numpy types to Python float
                        }

                        result["elements"].append(element)

        except Exception as e:
            result["error"] = str(e)

        return result

    def process_images_simple_parallel(self, image_paths):
        """Simple parallel processing - just the AI inference step"""
        print(f"🚀 Processing {len(image_paths)} images with {self.max_workers} workers...")

        results = {}

        # Only parallelize the slowest part - AI inference
        with ProcessPoolExecutor(max_workers=self.max_workers, initializer=_init_worker) as executor:
            future_to_img = {
                executor.submit(process_single_image_optimized, img_path): img_path
                for img_path in image_paths
            }

            completed = 0
            for future in future_to_img:
                img_path, output, success = future.result()
                results[img_path] = output if success else []
                completed += 1
                print(f"✅ {completed}/{len(image_paths)}")

        return results

    def process_pdf_dual_output(self, pdf_path, output_dir="output", dpi=55):
        """MODIFIED: Create two JSON files - all elements and titles only"""
        print("⚡ Starting dual output processing...")
        start_time = datetime.now()

        # Step 1: Convert PDF to images (keep sequential - it's fast)
        image_paths, pdf_doc = self.convert_pdf_to_images_fast(pdf_path, dpi=dpi)
        os.makedirs(output_dir, exist_ok=True)

        # Step 2: Parallel AI processing (ONLY change from original)
        layout_results = self.process_images_simple_parallel(image_paths)

        # Step 3: Process results for BOTH outputs
        all_elements_results = []
        titles_only_results = []

        for idx, img_path in enumerate(image_paths):
            print(f"📝 Processing results for page {idx+1}...")

            layout_output = layout_results.get(img_path, [])

            # Process for ALL elements
            page_all_elements = []
            page_titles_only = []

            for det_result in layout_output:
                # Get all elements
                result_all = self.process_layout_result_all_elements(det_result, pdf_doc, idx, dpi)
                page_all_elements.append(result_all)

                # Get titles only
                result_titles = self.process_layout_result_titles_only(det_result, pdf_doc, idx, dpi)
                page_titles_only.append(result_titles)

            all_elements_results.extend(page_all_elements)
            titles_only_results.extend(page_titles_only)

            # Memory cleanup every few pages
            if idx % 3 == 0:
                gc.collect()

        # Create final results for ALL elements
        final_all_elements = {
            "document": pdf_path,
            "total_pages": len(image_paths),
            "processing_time": str(datetime.now() - start_time),
            "extraction_type": "all_elements",
            "dpi": dpi,
            "pages": all_elements_results
        }

        # Create final results for TITLES only
        final_titles_only = {
            "document": pdf_path,
            "total_pages": len(image_paths),
            "processing_time": str(datetime.now() - start_time),
            "extraction_type": "titles_only",
            "dpi": dpi,
            "pages": titles_only_results
        }

        # Save BOTH JSON files
        pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]

        all_elements_file = os.path.join(output_dir, f"{pdf_filename}_all_elements_results.json")
        titles_only_file = os.path.join(output_dir, f"{pdf_filename}_titles_only_results.json")

        with open(all_elements_file, "w", encoding="utf-8") as f:
            json.dump(final_all_elements, f, indent=2, ensure_ascii=False)

        with open(titles_only_file, "w", encoding="utf-8") as f:
            json.dump(final_titles_only, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved all elements to: {all_elements_file}")
        print(f"💾 Saved titles only to: {titles_only_file}")

        # Cleanup
        pdf_doc.close()

        for img_path in image_paths:
            try:
                os.remove(img_path)
            except:
                pass

        return final_all_elements, final_titles_only

    def get_titles_only_optimized(self, pdf_path, dpi=55):
        """Your original titles function with shared model"""
        print("🎯 Extracting titles only...")

        image_paths, pdf_doc = self.convert_pdf_to_images_fast(pdf_path, dpi=dpi)

        titles_result = {
            "document": pdf_path,
            "titles": []
        }

        # Use shared model for consistency
        model = self._get_layout_model()

        for idx, img_path in enumerate(image_paths):
            print(f"📖 Page {idx+1}...", end=" ")

            try:
                layout_output = model.predict(img_path, batch_size=1)
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

            for det_result in layout_output:
                boxes = det_result.get('boxes', [])

                for box in boxes:
                    label = box.get('label', '').lower()
                    if label in ['doc_title', 'paragraph_title']:
                        coordinate = box.get('coordinate', [0, 0, 0, 0])
                        text = self.extract_text_from_coordinates(pdf_doc, idx, coordinate, dpi)

                        if text and text.strip():
                            titles_result["titles"].append({
                                "page": idx + 1,
                                "type": label,
                                "text": text.strip(),
                                "confidence": round(box.get('score', 0), 3)
                            })

            print("✅")

        pdf_doc.close()

        # Clean up images
        for img_path in image_paths:
            try:
                os.remove(img_path)
            except:
                pass

        return titles_result


# At the end of your model.py file, replace the argument parsing section with:

if __name__ == "__main__":
    import argparse
    import time
    import glob
    mp.set_start_method("spawn", force=True)

    parser = argparse.ArgumentParser(description="Process a PDF to generate layout analysis JSONs.")
    
    # Make pdf_path optional and check environment variable
    parser.add_argument("pdf_path", nargs='?', help="Path to the PDF file to process.")
    parser.add_argument("--output_dir", default="output", help="Where to save results (default: output).")
    parser.add_argument("--dpi", type=int, default=55, help="Rendering DPI (default: 55).")
    parser.add_argument("--max_workers", type=int, default=6, help="Parallel workers (default: 6).")
    args = parser.parse_args()

    print("⚡ Dual Output PDF Processor")
    print("=" * 50)

    # Priority order: command line arg > environment variable > auto-search
    pdf_path = args.pdf_path or os.environ.get('PDF_PATH')
    
    if not pdf_path:
        # Look for PDFs in the current directory and input directory
        search_paths = ["*.pdf", "input/*.pdf", "*.PDF", "input/*.PDF"]
        found_pdfs = []
        
        for pattern in search_paths:
            found_pdfs.extend(glob.glob(pattern))
        
        if found_pdfs:
            pdf_path = found_pdfs[0]  # Use the first PDF found
            print(f"📁 No PDF specified, using: {pdf_path}")
        else:
            print("❌ No PDF file specified and none found.")
            print("Options:")
            print("1. Provide as argument: python model.py /path/to/file.pdf")
            print("2. Set environment variable: export PDF_PATH=/path/to/file.pdf")
            print("3. Place PDF file in current directory or 'input' folder")
            exit(1)

    # Check if the PDF file exists
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file '{pdf_path}' not found.")
        exit(1)

    processor = FastPDFProcessor(max_workers=args.max_workers)

    print(f"🚀 Processing: {pdf_path}")
    start = time.time()

    # Main processing call
    all_elements_results, titles_only_results = processor.process_pdf_dual_output(
        pdf_path, output_dir=args.output_dir, dpi=args.dpi
    )

    end = time.time()

    print(f"\n🏆 RESULTS:")
    print(f"⏱️  Total time: {end-start:.2f} seconds")
    print(f"📊 Pages processed: {all_elements_results['total_pages']}")
    print(f"🚀 Speed: {all_elements_results['total_pages']/(end-start):.2f} pages/sec")
    
    # Show improvement over sequential
    sequential_estimate = all_elements_results['total_pages'] * 4.5  # Rough estimate
    speedup = sequential_estimate / (end-start)
    print(f"📈 Estimated speedup: {speedup:.1f}x")

    # Display summary statistics
    print(f"\n📋 ALL ELEMENTS SUMMARY:")
    print("="*50)
    all_element_types = {}
    total_elements = 0
    
    for page in all_elements_results['pages']:
        total_elements += len(page['elements'])
        for element in page['elements']:
            elem_type = element['type']
            all_element_types[elem_type] = all_element_types.get(elem_type, 0) + 1

    print(f"📊 Total elements found: {total_elements}")
    for elem_type, count in sorted(all_element_types.items()):
        print(f"   • {elem_type}: {count}")

    print(f"\n🎯 TITLES ONLY SUMMARY:")
    print("="*50)
    title_count = 0
    for page in titles_only_results['pages']:
        title_count += len(page['elements'])
    
    print(f"📊 Total titles found: {title_count}")
    
    # Display sample titles
    print(f"\n📋 SAMPLE TITLES:")
    print("="*30)
    count = 0
    for page in titles_only_results['pages']:
        for element in page['elements']:
            if element['text'] and count < 5:  # Show first 5 titles
                print(f"📄 Page {page['page_number']} ({element['type']}): {element['text'][:80]}...")
                count += 1
            if count >= 5:
                break
        if count >= 5:
            break
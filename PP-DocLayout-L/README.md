---
license: apache-2.0
library_name: PaddleOCR
language:
- en
- zh
pipeline_tag: image-to-text
tags:
- OCR
- PaddlePaddle
- PaddleOCR
- layout_detection
---

# PP-DocLayout-L

## Introduction

A high-precision layout area localization model trained on a self-built dataset containing Chinese and English papers, magazines, contracts, books, exams, and research reports using RT-DETR-L. The layout detection model includes 23 common categories: document title, paragraph title, text, page number, abstract, table of contents, references, footnotes, header, footer, algorithm, formula, formula number, image, figure caption, table, table caption, seal, figure title, figure, header image, footer image, and aside text. The key metrics are as follow:

| Model| mAP(0.5) (%) | 
|  --- | --- | 
|PP-DocLayout-L |  90.4 | 

**Note**: the evaluation set of the above accuracy indicators is a self built layout area detection data set, including 500 document type images such as Chinese and English papers, newspapers, research papers and test papers.

## Quick Start

### Installation

1. PaddlePaddle

Please refer to the following commands to install PaddlePaddle using pip:

```bash
# for CUDA11.8
python -m pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# for CUDA12.6
python -m pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# for CPU
python -m pip install paddlepaddle==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

For details about PaddlePaddle installation, please refer to the [PaddlePaddle official website](https://www.paddlepaddle.org.cn/en/install/quick).

2. PaddleOCR

Install the latest version of the PaddleOCR inference package from PyPI:

```bash
python -m pip install paddleocr
```


### Model Usage

You can quickly experience the functionality with a single command:

```bash
paddleocr layout_detection \
    --model_name PP-DocLayout-L \
    -i https://cdn-uploads.huggingface.co/production/uploads/63d7b8ee07cd1aa3c49a2026/N5C68HPVAI-xQAWTxpbA6.jpeg
```

You can also integrate the model inference of the layout detection module into your project. Before running the following code, please download the sample image to your local machine.

```python
from paddleocr import LayoutDetection

model = LayoutDetection(model_name="PP-DocLayout-L")
output = model.predict("N5C68HPVAI-xQAWTxpbA6.jpeg", batch_size=1)
for res in output:
    res.print()
    res.save_to_img(save_path="./output/")
    res.save_to_json(save_path="./output/res.json")
```

After running, the obtained result is as follows:

```json
{'res': {'input_path': '/root/.paddlex/predict_input/N5C68HPVAI-xQAWTxpbA6.jpeg', 'page_index': None, 'boxes': [{'cls_id': 8, 'label': 'table', 'score': 0.9866371154785156, 'coordinate': [74.3101, 105.714195, 321.98795, 299.11014]}, {'cls_id': 2, 'label': 'text', 'score': 0.9859796166419983, 'coordinate': [34.659634, 349.9106, 358.33762, 611.34357]}, {'cls_id': 2, 'label': 'text', 'score': 0.9850561618804932, 'coordinate': [34.94621, 647.37744, 358.32578, 849.23584]}, {'cls_id': 8, 'label': 'table', 'score': 0.9850051403045654, 'coordinate': [438.06946, 105.37968, 662.88696, 313.88608]}, {'cls_id': 2, 'label': 'text', 'score': 0.9847787022590637, 'coordinate': [385.971, 497.0397, 710.95557, 697.68115]}, {'cls_id': 2, 'label': 'text', 'score': 0.980556845664978, 'coordinate': [385.79675, 345.93768, 710.07336, 459.1456]}, {'cls_id': 2, 'label': 'text', 'score': 0.9799885749816895, 'coordinate': [386.07678, 735.3819, 710.60815, 850.1992]}, {'cls_id': 9, 'label': 'table_title', 'score': 0.9376334547996521, 'coordinate': [35.275173, 19.85299, 358.9236, 77.812965]}, {'cls_id': 0, 'label': 'paragraph_title', 'score': 0.8755854964256287, 'coordinate': [386.63153, 476.6075, 699.78394, 490.1158]}, {'cls_id': 0, 'label': 'paragraph_title', 'score': 0.8617689609527588, 'coordinate': [387.2742, 715.95734, 524.38525, 729.20825]}, {'cls_id': 0, 'label': 'paragraph_title', 'score': 0.860828161239624, 'coordinate': [35.453644, 627.4963, 185.6373, 640.4026]}, {'cls_id': 0, 'label': 'paragraph_title', 'score': 0.857572615146637, 'coordinate': [35.33445, 330.80554, 141.46928, 344.407]}, {'cls_id': 9, 'label': 'table_title', 'score': 0.7964489459991455, 'coordinate': [385.9402, 19.755222, 711.51154, 75.00652]}, {'cls_id': 2, 'label': 'text', 'score': 0.5557674765586853, 'coordinate': [385.9402, 19.755222, 711.51154, 75.00652]}]}}
```

The visualized image is as follows:

![image/jpeg](https://cdn-uploads.huggingface.co/production/uploads/63d7b8ee07cd1aa3c49a2026/WaDEVTJUhRgHBZmI_bo5q.jpeg)

For details about usage command and descriptions of parameters, please refer to the [Document](https://paddlepaddle.github.io/PaddleOCR/latest/en/version3.x/module_usage/layout_detection.html#iii-quick-integration).

### Pipeline Usage

The ability of a single model is limited. But the pipeline consists of several models can provide more capacity to resolve difficult problems in real-world scenarios.

#### PP-StructureV3

Layout analysis is a technique used to extract structured information from document images. PP-StructureV3 includes the following six modules:
* Layout Detection Module
* General OCR Sub-pipeline
* Document Image Preprocessing Sub-pipeline （Optional）
* Table Recognition Sub-pipeline （Optional）
* Seal Recognition Sub-pipeline （Optional）
* Formula Recognition Sub-pipeline （Optional）

You can quickly experience the PP-StructureV3 pipeline with a single command.

```bash
paddleocr pp_structurev3 --layout_detection_model_name PP-DocLayout-L -i https://cdn-uploads.huggingface.co/production/uploads/63d7b8ee07cd1aa3c49a2026/KP10tiSZfAjMuwZUSLtRp.png
```

You can experience the inference of the pipeline with just a few lines of code. Taking the PP-StructureV3 pipeline as an example:

```python
from paddleocr import PPStructureV3

pipeline = PPStructureV3(layout_detection_model_name="PP-DocLayout-L")
# ocr = PPStructureV3(use_doc_orientation_classify=True) # Use use_doc_orientation_classify to enable/disable document orientation classification model
# ocr = PPStructureV3(use_doc_unwarping=True) # Use use_doc_unwarping to enable/disable document unwarping module
# ocr = PPStructureV3(use_textline_orientation=True) # Use use_textline_orientation to enable/disable textline orientation classification model
# ocr = PPStructureV3(device="gpu") # Use device to specify GPU for model inference
output = pipeline.predict("./KP10tiSZfAjMuwZUSLtRp.png")
for res in output:
    res.print() ## Print the structured prediction output
    res.save_to_json(save_path="output") ## Save the current image's structured result in JSON format
    res.save_to_markdown(save_path="output") ## Save the current image's result in Markdown format
```

The default model used in pipeline is `PP-DocLayout_plus-L`, so it is needed that specifing to `PP-DocLayout-L` by argument `layout_detection_model_name`. And you can also use the local model file by argument `layout_detection_model_dir`. 
For details about usage command and descriptions of parameters, please refer to the [Document](https://paddlepaddle.github.io/PaddleOCR/latest/en/version3.x/pipeline_usage/PP-StructureV3.html#2-quick-start).

## Links

[PaddleOCR Repo](https://github.com/paddlepaddle/paddleocr)

[PaddleOCR Documentation](https://paddlepaddle.github.io/PaddleOCR/latest/en/index.html)


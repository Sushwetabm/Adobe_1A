

##USING OCR
# ~260MB Slimmed Image with OCR
FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

# Install required system packages for PyMuPDF, Pillow, and OCR
RUN apt-get update && \
    apt-get install -y \
    libgl1 \
    libxrender1 \
    libsm6 \
    libxext6 \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    tesseract-ocr \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Entry point
CMD ["python", "extract_outline.py"]

# #1.8GB
# FROM --platform=linux/amd64 python:3.10

# WORKDIR /app

# # Install necessary system libraries and create symlink for libcrypt
# RUN apt-get update && \
#     apt-get install -y libgl1 libxrender1 libsm6 libxext6 libcrypt1 && \
#     ln -s /usr/lib/x86_64-linux-gnu/libcrypt.so.1 /usr/lib/x86_64-linux-gnu/libcrypt.so.2 && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# CMD ["python", "extract_outline.py"]



# GUARANTEED WORKING: Debian slim with proven PyMuPDF version
# FROM --platform=linux/amd64 python:3.9-slim AS builder

# # Install build essentials
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # Use older, stable PyMuPDF version that has reliable wheels
# RUN pip install --no-cache-dir --target=/packages \
#     --prefer-binary \
#     PyMuPDF==1.21.1 \
#     langdetect==1.0.9 \
#     regex==2022.10.31

# # Aggressive cleanup
# RUN find /packages -name "*.pyc" -delete && \
#     find /packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
#     find /packages -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true && \
#     find /packages -name "test*" -exec rm -rf {} + 2>/dev/null || true && \
#     find /packages -name "*.so" -exec strip {} \; 2>/dev/null || true

# COPY . /app

# # -------- Stage 2: Ultra-minimal runtime --------
# FROM --platform=linux/amd64 python:3.9-slim

# # Remove everything we don't need from Python slim
# RUN rm -rf /usr/lib/python*/ensurepip && \
#     rm -rf /usr/lib/python*/lib2to3 && \
#     rm -rf /usr/lib/python*/turtledemo && \
#     rm -rf /usr/lib/python*/tkinter && \
#     rm -rf /usr/lib/python*/idlelib && \
#     rm -rf /usr/share/man && \
#     rm -rf /usr/share/doc && \
#     rm -rf /var/lib/apt/lists/* && \
#     rm -rf /var/cache/apt/*

# WORKDIR /app

# # Copy packages and app
# COPY --from=builder /packages /usr/local/lib/python3.9/site-packages
# COPY --from=builder /app .

# # Create required directories
# RUN mkdir -p input output

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1
# ENV PYTHONOPTIMIZE=2

# # Verify installation
# RUN python -c "import fitz, langdetect, regex; print('All dependencies OK')"

# ENTRYPOINT ["python", "extract_outline.py"]
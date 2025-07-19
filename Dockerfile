
#1.8GB
# FROM --platform=linux/amd64 python:3.9

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



#524MB

# # -------- Stage 1: Builder --------
# FROM python:3.11-slim AS builder

# RUN apt-get update && apt-get install -y \
#     build-essential \
#     gcc \
#     g++ \
#     libffi-dev \
#     libxml2-dev \
#     libxslt-dev \
#     libjpeg-dev \
#     zlib1g-dev \
#     libtiff-dev \
#     libopenjp2-7-dev \
#     && apt-get clean

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# # -------- Stage 2: Runtime --------
# FROM python:3.11-slim AS runtime

# RUN apt-get update && apt-get install -y \
#     libxml2 \
#     libxslt1.1 \
#     libjpeg62-turbo \
#     zlib1g \
#     libtiff-dev \
#     libopenjp2-7 \
#     && apt-get clean

# WORKDIR /app

# COPY --from=builder /usr/local /usr/local
# COPY --from=builder /app /app

# ENTRYPOINT ["python", "app/main.py"]

#489mb
# # -------- Stage 1: Builder --------
# FROM python:3.11-slim AS builder

# # Install required system packages to build wheels
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     gcc \
#     g++ \
#     libffi-dev \
#     libxml2-dev \
#     libxslt-dev \
#     libjpeg-dev \
#     zlib1g-dev \
#     libtiff-dev \
#     libopenjp2-7-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# WORKDIR /app
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# # -------- Stage 2: Runtime --------
# FROM python:3.11-slim AS runtime

# # Install only the runtime libraries
# RUN apt-get update && apt-get install -y \
#     libxml2 \
#     libxslt1.1 \
#     libjpeg62-turbo \
#     zlib1g \
#     libtiff-dev \
#     libopenjp2-7 \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# WORKDIR /app

# # Copy installed Python libs and app from builder
# COPY --from=builder /usr/local /usr/local
# COPY --from=builder /app /app

# # Clean up potential cache
# RUN find /usr/local -type d -name '__pycache__' -exec rm -r {} + || true

# # Use non-root user (optional for security)
# # RUN useradd -m appuser && chown -R appuser /app
# # USER appuser

# ENTRYPOINT ["python", "extract_outline.py"]

#357mb
# # -------- Stage 1: Builder --------
# FROM python:3.11-slim AS builder

# # Install build dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     gcc \
#     g++ \
#     libffi-dev \
#     libxml2-dev \
#     libxslt-dev \
#     libjpeg-dev \
#     zlib1g-dev \
#     libtiff-dev \
#     libopenjp2-7-dev \
#     libfreetype6-dev \
#     liblcms2-dev \
#     libwebp-dev \
#     tcl8.6-dev \
#     tk8.6-dev \
#     python3-tk \
#     libharfbuzz-dev \
#     libfribidi-dev \
#     libxcb1-dev \
#     git \
#     && rm -rf /var/lib/apt/lists/*

# WORKDIR /app
# COPY requirements.txt ./

# # Build wheels and install to custom location
# RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
#     pip install --no-cache-dir --prefix=/install -r requirements.txt

# COPY . .

# # -------- Stage 2: Ultra-minimal runtime --------
# FROM debian:bookworm-slim AS runtime

# # Install ONLY essential runtime libraries
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     python3 \
#     python3-distutils \
#     libxml2 \
#     libxslt1.1 \
#     libjpeg62-turbo \
#     zlib1g \
#     libtiff6 \
#     libopenjp2-7 \
#     libfreetype6 \
#     liblcms2-2 \
#     libwebp7 \
#     libharfbuzz0b \
#     libfribidi0 \
#     libxcb1 \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/* \
#     && rm -rf /var/cache/apt/* \
#     && rm -rf /usr/share/doc/* \
#     && rm -rf /usr/share/man/* \
#     && rm -rf /usr/share/locale/* \
#     && rm -rf /usr/share/info/*

# WORKDIR /app

# # Create symlink for python
# RUN ln -s /usr/bin/python3 /usr/bin/python

# # Copy only the installed packages and binaries
# COPY --from=builder /install /usr/local

# # Copy ONLY essential application files (modify as needed)
# COPY --from=builder /app/extract_outline.py .
# # Add other essential files here:
# # COPY --from=builder /app/other_essential_file.py .

# # Ultra-aggressive cleanup
# RUN find /usr/local/lib/python3.11/site-packages -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && \
#     find /usr/local/lib/python3.11/site-packages -name "*.pyc" -delete && \
#     find /usr/local/lib/python3.11/site-packages -name "*.pyo" -delete && \
#     find /usr/local/lib/python3.11/site-packages -name "test*" -type d -exec rm -rf {} + 2>/dev/null || true && \
#     find /usr/local/lib/python3.11/site-packages -name "*test*.py" -delete 2>/dev/null || true && \
#     find /usr/local/lib/python3.11/site-packages -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true && \
#     find /usr/local/lib/python3.11/site-packages -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true && \
#     find /usr/local/lib/python3.11/site-packages -name "*.so" -exec strip {} \; 2>/dev/null || true && \
#     rm -rf /usr/local/lib/python3.11/site-packages/pip* && \
#     rm -rf /usr/local/lib/python3.11/site-packages/setuptools* && \
#     rm -rf /usr/local/lib/python3.11/site-packages/wheel* && \
#     rm -rf /usr/local/lib/python3.11/site-packages/pkg_resources* && \
#     rm -rf /tmp/* /var/tmp/* /root/.cache /root/.local && \
#     find /usr -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

# ENTRYPOINT ["python", "extract_outline.py"]

# GUARANTEED WORKING: Debian slim with proven PyMuPDF version
FROM --platform=linux/amd64 python:3.9-slim AS builder

# Install build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Use older, stable PyMuPDF version that has reliable wheels
RUN pip install --no-cache-dir --target=/packages \
    --prefer-binary \
    PyMuPDF==1.21.1 \
    langdetect==1.0.9 \
    regex==2022.10.31

# Aggressive cleanup
RUN find /packages -name "*.pyc" -delete && \
    find /packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /packages -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /packages -name "test*" -exec rm -rf {} + 2>/dev/null || true && \
    find /packages -name "*.so" -exec strip {} \; 2>/dev/null || true

COPY . /app

# -------- Stage 2: Ultra-minimal runtime --------
FROM --platform=linux/amd64 python:3.9-slim

# Remove everything we don't need from Python slim
RUN rm -rf /usr/lib/python*/ensurepip && \
    rm -rf /usr/lib/python*/lib2to3 && \
    rm -rf /usr/lib/python*/turtledemo && \
    rm -rf /usr/lib/python*/tkinter && \
    rm -rf /usr/lib/python*/idlelib && \
    rm -rf /usr/share/man && \
    rm -rf /usr/share/doc && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

WORKDIR /app

# Copy packages and app
COPY --from=builder /packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app .

# Create required directories
RUN mkdir -p input output

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=2

# Verify installation
RUN python -c "import fitz, langdetect, regex; print('All dependencies OK')"

ENTRYPOINT ["python", "extract_outline.py"]
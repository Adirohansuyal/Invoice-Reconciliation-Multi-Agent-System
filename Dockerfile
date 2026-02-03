# -------------------------------
# Base image
# -------------------------------
    FROM python:3.10-slim

    # -------------------------------
    # System dependencies (OCR + PDF)
    # -------------------------------
    RUN apt-get update && apt-get install -y \
        poppler-utils \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*
    
    # -------------------------------
    # Working directory
    # -------------------------------
    WORKDIR /app
    
    # -------------------------------
    # Install Python dependencies
    # -------------------------------
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # -------------------------------
    # Copy application code
    # -------------------------------
    COPY . .
    
    # -------------------------------
    # Streamlit config
    # -------------------------------
    ENV STREAMLIT_SERVER_PORT=8501
    ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
    
    # -------------------------------
    # Expose Streamlit port
    # -------------------------------
    EXPOSE 8501
    
    # -------------------------------
    # Run app
    # -------------------------------
    CMD ["streamlit", "run", "app.py"]
    

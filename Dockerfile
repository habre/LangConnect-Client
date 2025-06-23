FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    libxml2-dev \
    libxslt1-dev \
    libmagic-dev \
    poppler-utils \
    tesseract-ocr \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip
RUN pip install uv

# Copy requirements first for better layer caching
COPY pyproject.toml uv.lock ./

# Copy application code
COPY . .

# Install Python dependencies using uv
RUN uv sync --frozen

# Install additional dependencies with docx support
RUN uv pip install streamlit "unstructured[docx]"

# Expose ports for both API and Streamlit
# Note: The actual Streamlit port can be customized via STREAMLIT_PORT env var
EXPOSE 8080 8501 8765

# Default command runs the API server
# This can be overridden in docker-compose.yml for the streamlit service
CMD ["uv", "run", "uvicorn", "langconnect.server:APP", "--host", "0.0.0.0", "--port", "8080"]

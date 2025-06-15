# ---------- Stage 1: Builder ----------
FROM python:3.10-slim as ocr_builder

WORKDIR /app

# Install system dependencies for Python and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g newman newman-reporter-htmlextra && \
    apt-get purge -y --auto-remove curl gnupg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the full app source code
COPY . /app
RUN mkdir -p /app/reports

# ---------- Stage 2: Runtime ----------
FROM python:3.10-slim

WORKDIR /app

# Install required system libs and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g newman newman-reporter-htmlextra && \
    apt-get purge -y --auto-remove curl gnupg && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment and application
COPY --from=ocr_builder /venv /venv
COPY --from=ocr_builder /app /app

# Set venv in PATH
ENV PATH="/venv/bin:$PATH"

# Make sure reports directory exists
RUN mkdir -p /app/reports

# Entry point
CMD ["python", "./api_testing_script/main_runner.py"]

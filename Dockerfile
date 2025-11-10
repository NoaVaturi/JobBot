FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m -u 1000 jobbot

# Create data and logs directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R jobbot:jobbot /app

USER jobbot

# Default command - run the Flask app
CMD ["python", "app.py"]


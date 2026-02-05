FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY main.py .
COPY query.py .
COPY build_vectordb.py .

# Create directories
RUN mkdir -p /app/desktop /app/output

# Default command
CMD ["python", "main.py", "--help"]

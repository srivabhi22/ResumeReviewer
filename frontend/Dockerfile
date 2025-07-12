# Use a slim Python 3.9 image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code and supporting modules
COPY frontend/ ./frontend/
COPY src/ ./src/
COPY .env .env

# Expose Streamlit default port
EXPOSE 8501

# Command to run Streamlit frontend
CMD ["streamlit", "run", "frontend/main.py", "--server.port=8501", "--server.address=0.0.0.0"]

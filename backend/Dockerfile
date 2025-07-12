# Use a slim Python 3.9 image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and supporting modules
COPY backend/ ./backend/
COPY src/ ./src/
COPY .env .env

# Expose FastAPI port
EXPOSE 8000

# Command to run FastAPI backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

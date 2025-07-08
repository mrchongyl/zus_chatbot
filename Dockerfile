# Use official Python image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose only the Streamlit port (Cloud Run will route to $PORT)
EXPOSE 8501

# Start FastAPI in the background, Streamlit in the foreground (public)
CMD uvicorn api.main:app --host 0.0.0.0 --port 8000 & streamlit run zus_chatbot.py --server.port $PORT --server.address 0.0.0.0
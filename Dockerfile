FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

COPY . .

ENV STREAMLIT_SERVER_PORT=8502
EXPOSE 8502

CMD ["streamlit", "run", "web_app.py", "--server.port", "8502", "--server.headless", "true", "--server.fileWatcherType", "none"]


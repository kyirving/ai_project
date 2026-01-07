FROM python:3.11-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g; s/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && apt-get -o Acquire::Retries=3 update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

COPY . .

ENV STREAMLIT_SERVER_PORT=8502
EXPOSE 8502

CMD ["streamlit", "run", "web_app.py", "--server.port", "8502", "--server.headless", "true", "--server.fileWatcherType", "none"]

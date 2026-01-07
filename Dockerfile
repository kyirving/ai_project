FROM python:3.11-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive
RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list; \
    elif [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources; \
    else \
      printf '%s\n' \
        'deb http://mirrors.tuna.tsinghua.edu.cn/debian bookworm main contrib non-free non-free-firmware' \
        'deb http://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware' \
        'deb http://mirrors.tuna.tsinghua.edu.cn/debian bookworm-backports main contrib non-free non-free-firmware' \
        'deb http://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware' \
        > /etc/apt/sources.list; \
    fi; \
    apt-get -o Acquire::Retries=3 update; \
    apt-get install -y --no-install-recommends ffmpeg; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-base.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements-base.txt

COPY . .

ENV STREAMLIT_SERVER_PORT=8502
EXPOSE 8502

CMD ["streamlit", "run", "web_app.py", "--server.port", "8502", "--server.headless", "true", "--server.fileWatcherType", "none"]

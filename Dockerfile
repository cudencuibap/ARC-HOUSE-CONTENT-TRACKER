# Arc House Content Tracker - Docker image
FROM python:3.12-slim

# Khong ghi .pyc, output khong buffer (de thay log ngay)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ARC_DATA_DIR=/data \
    ARC_CONFIG_DIR=/config

# Node.js can thiet de sinh x-nonce chong bot (chay JS that cua site).
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY arc_tracker.py nonce_gen.js nonce_chunk.js ./

# Cac thu muc se duoc mount tu host
VOLUME ["/data", "/config"]

ENTRYPOINT ["python", "arc_tracker.py"]

FROM python:3.11-slim

# Playwright needs these system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-collector.txt ./
RUN pip install --no-cache-dir -r requirements-collector.txt

# Install Chromium for Playwright
RUN playwright install chromium && playwright install-deps chromium

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "collector/scheduler.py"]

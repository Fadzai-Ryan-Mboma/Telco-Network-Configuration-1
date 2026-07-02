FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl libpq-dev tini \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 \
    libxfixes3 libpango-1.0-0 libcairo2 \
    xvfb fluxbox x11vnc novnc websockify \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN playwright install chromium

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8510

# tini as PID 1 reaps zombie processes left behind when the Evaluation
# reconnect flow's Xvfb/Chromium subprocess tree is torn down — without a
# real init process, orphaned children reparent to PID 1 (this python
# process) and are never wait()ed on.
ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8510"]

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY miner/requirements.txt /app/src/miner/requirements.txt
RUN pip install --no-cache-dir -r /app/src/miner/requirements.txt

COPY shared /app/src/shared
COPY miner /app/src/miner

CMD ["python", "src/miner/main.py"]

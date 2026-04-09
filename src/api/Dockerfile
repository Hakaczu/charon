FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY api/requirements.txt /app/src/api/requirements.txt
RUN pip install --no-cache-dir -r /app/src/api/requirements.txt

COPY shared /app/src/shared
COPY api /app/src/api

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

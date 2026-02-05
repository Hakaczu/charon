FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY brain/requirements.txt /app/src/brain/requirements.txt
RUN pip install --no-cache-dir -r /app/src/brain/requirements.txt

COPY shared /app/src/shared
COPY brain /app/src/brain

CMD ["python", "src/brain/main.py"]

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY scripts /app/scripts

ENV PYTHONPATH=/app

# Default command can be overridden per service (api/miner/brain)
CMD ["uvicorn", "src.charon.api_main:app", "--host", "0.0.0.0", "--port", "8000"]

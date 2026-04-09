FROM python:3.12-slim

WORKDIR /app

COPY frontend/requirements.txt /app/src/frontend/requirements.txt
RUN pip install --no-cache-dir -r /app/src/frontend/requirements.txt

COPY frontend /app/src/frontend

# Streamlit uses .streamlit/config.toml, but we can rely on defaults or envs
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

CMD ["streamlit", "run", "src/frontend/main.py"]

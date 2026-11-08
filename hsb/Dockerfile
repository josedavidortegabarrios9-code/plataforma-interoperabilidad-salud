FROM python:3.11-slim

WORKDIR /workspace

# Solo instalar curl para diagnósticos si es necesario
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY hsb/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /workspace/

ENV PYTHONPATH=/workspace

EXPOSE 8000

CMD ["uvicorn", "hsb.main:app", "--host", "0.0.0.0", "--port", "8000"]

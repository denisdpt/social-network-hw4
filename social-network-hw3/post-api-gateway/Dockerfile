FROM python:3.10-slim

WORKDIR /app

COPY post-api-gateway/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY post-api-gateway /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]

FROM python:3.9

WORKDIR /app

COPY . /app
COPY grpc_stubs /app/grpc_stubs

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["python", "server.py"]
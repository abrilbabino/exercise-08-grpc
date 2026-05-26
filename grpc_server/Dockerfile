FROM python:3.14-slim
WORKDIR /app

COPY grpc_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos
COPY grpc_server/ ./grpc_server/
COPY proto/ ./proto/
COPY Makefile .

# Compilar proto usando el comando del Makefile
RUN apt-get update && apt-get install -y make && make proto

ENV PYTHONPATH=/app
EXPOSE 50051
CMD ["python", "grpc_server/server.py"]
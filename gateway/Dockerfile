FROM python:3.14-slim
WORKDIR /app

COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos
COPY gateway/ ./gateway/
COPY proto/ ./proto/
COPY Makefile .

# Compilar proto
RUN apt-get update && apt-get install -y make && make proto

ENV PYTHONPATH=/app
EXPOSE 8080
CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8080"]
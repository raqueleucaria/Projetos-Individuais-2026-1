FROM python:3.12-slim

WORKDIR /app

# Dependências primeiro (cache de camada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

ENV PYTHONPATH=/app/src
EXPOSE 8000

# Por padrão sobe a API; o serviço de scheduler sobrescreve o command no compose.
CMD ["uvicorn", "uda.api:app", "--host", "0.0.0.0", "--port", "8000"]

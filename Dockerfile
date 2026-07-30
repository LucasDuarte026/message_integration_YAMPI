FROM python:3.12-slim

# Evita que o Python grave arquivos .pyc no container
ENV PYTHONDONTWRITEBYTECODE=1
# Garante que os logs do Python sejam exibidos imediatamente no terminal do Docker
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências de sistema necessárias para compilar dependências, se houver
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências do Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação e arquivos de meta
COPY src/ /app/src/
COPY VERSION /app/

# Expõe a porta do servidor de Webhook
EXPOSE 5000

# O container executará o daemon em loop infinito a cada 5 minutos
CMD ["python", "src/daemon.py"]

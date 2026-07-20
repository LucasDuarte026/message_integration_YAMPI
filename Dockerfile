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

# Copia o código da aplicação
COPY src/ /app/src/

# Expõe a porta do servidor de Webhook
EXPOSE 5000

# Mantém o container vivo e ocioso para execuções manuais do main.py
CMD ["tail", "-f", "/dev/null"]

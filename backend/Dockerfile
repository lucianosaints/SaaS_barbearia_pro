# Usar uma imagem oficial Python leve
FROM python:3.11-slim

# Evita que o Python grave arquivos .pyc no disco e força o output para o console sem buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema necessárias (para PostgreSQL, bibliotecas C, etc)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia os requirements e instala as dependências do Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do backend para dentro do diretório de trabalho
COPY . /app/

# Coleta os arquivos estáticos (útil se usar whitenoise)
RUN python manage.py collectstatic --noinput

# Expõe a porta 8000
EXPOSE 8000

# Comando para rodar a aplicação via gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

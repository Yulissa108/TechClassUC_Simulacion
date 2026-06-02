FROM python:3.10-slim

# Instalamos librerías del sistema necesarias para que matplotlib dibuje las gráficas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpng-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponemos el puerto estándar
EXPOSE 10000

# Gunicorn arrancará tu app de forma ultra estable
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "app:app"]
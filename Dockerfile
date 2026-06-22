FROM python:3.11-slim

WORKDIR /app

# Installer GDAL et dépendances système
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Variables GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Api/ ./Api/
COPY pipeline/ ./pipeline/

EXPOSE 8000

CMD ["uvicorn", "Api.main:app", "--host", "0.0.0.0", "--port", "8000"]
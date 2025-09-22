FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps for geo stack (GDAL/PROJ/etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
    gdal-bin libgdal-dev \
    libgeos-dev \
    libproj-dev proj-data proj-bin \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . ./

EXPOSE 8000
CMD ["bash", "start.sh"]

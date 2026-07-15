FROM node:20-bookworm-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci \
    --fetch-retries=5 \
    --fetch-retry-mintimeout=2000 \
    --fetch-retry-maxtimeout=120000

COPY frontend ./
RUN npm run build


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    YAHAA_DATA_DIR=/app/data \
    TZ=Asia/Shanghai

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      curl \
      tzdata \
      fonts-dejavu-core \
      fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY bundled-fonts /app/app/bundled_fonts
COPY --from=frontend-build /app/app/static /app/app/static
RUN mkdir -p /app/data/fonts /app/data/input /app/data/output

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]

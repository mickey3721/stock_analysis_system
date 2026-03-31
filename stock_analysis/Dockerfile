FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装pysnowball及其依赖
RUN pip install --no-cache-dir pysnowball beautifulsoup4 requests

COPY . .

EXPOSE 8899

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8899"]

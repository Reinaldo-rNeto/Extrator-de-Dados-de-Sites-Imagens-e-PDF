FROM python:3.11-slim

# Impede que o Python grave arquivos .pyc e força envios rápidos pro log
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalação de utilitários do sistema Linux necessários para:
# 1. Chromium do Playwright (libnss3, libatk, etc)
# 2. Visão Computacional / OCR (tesseract-ocr, tesseract-ocr-por para o idioma Português)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    wget \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Configura o diretório de trabalho no container
WORKDIR /app

# Copia os requisitos primeiro (ajuda o docker a fazer cache das libs python)
COPY requirements.txt .

# Atualiza o PIP e instala os pacotes do requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Instala nativamente os navegadores do Playwright que o web_extractor vai usar (Chromium apenas)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copia todo o resto do código da aplicação pra dentro do container
COPY . .

# Expõe a porta padrão do Hugging Face Spaces (Obrigatório ser a 7860)
EXPOSE 7860

# Comando final que a máquina do Render/Hugging Face vai rodar
# O --server.address=0.0.0.0 garante que o site possa ser acessado pelo IP externo
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]

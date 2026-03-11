---
title: Extrator De Dados
emoji: 🦀
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

<div align="center">
  <h1>✨ Extrator de Dados IA Premium</h1>
  <p><strong>Transforme dados confusos de Sites, PDFs e Imagens em Tabelas Estruturadas via Inteligência Artificial!</strong></p>
</div>

---

## 🚀 Sobre o Projeto

O **Extrator de Dados IA Premium** é uma ferramenta robusta e ágil (em Python e Streamlit) projetada para automatizar o *Data Entry* de negócios. Ele une a flexibilidade de raspadores de arquitetura invisível (Web Scraping Avançado) com o modelo neural open-source mais potente da atualidade (Llama 3.3 70B via API da Groq).

Com uma interface moderna inspirada em *Glassmorphism*, extrair informações complexas (como Notas Fiscais ilegíveis, contratos massivos em PDF ou páginas de lojas dinâmicas) e converte-las para formatos organizados como `CSV` e `Excel` agora é uma tarefa de milissegundos.

## 🌟 Principais Funcionalidades

- **🕵🏻 Extração Web Universal (Playwright "Stealth")**: Capaz de contornar proteções básicas anti-bot, raspar dados desenhados com Javascript via **Auto-Scroll Mágico** e retornar apenas o texto limpo crucial da página. Além de um "Atalho Turbo" via regex para vídeos do YouTube devolvendo a legenda integralmente!
- **📄 Leitura Nativa de PDFs**: Upload veloz e leitura confiável de documentos paginados sem depender de conexões externas usando o `pdfplumber`.
- **📸 Visão Computacional OCR Avançada**: Integração limpa com o motor C++ Google Tesseract OCR para "ler" as informações e textos inseridos "dentro" de fotografias (png, jpg, jpeg).
- **🧠 Motor LLM Groq Ultra-Rápido**: Empregando LPU (Language Processing Units) ao invés do tradicional GPU, o Extrator processa blocos de mais de 25 mil caracteres ordenando a Llama 3 para aplicar filtros e gerar um retorno estritamente padronizado JSON (`List[Dict]`).
- **🗃️ Exportação Pronta**: Um clique converte todo o processamento massivo para o popular padrão corporativo (Planilha XLSX Premium do Excel ou banco CSV Simples).

## 🛠️ Tecnologias Utilizadas

- **Interface Gráfica & Cache:** [Streamlit](https://streamlit.io/) e `st.status()`
- **Inteligência Artificial & Motor Inferência:** `groq`, modelo `llama-3.3-70b-versatile`
- **Raspagem (Scraping):** `playwright` (Chromium Async), `beautifulsoup4`
- **Documentos & Imagens:** `pdfplumber`, `pytesseract` e `pillow` 
- **Estruturação Tabela:** `pandas` e `openpyxl`

## ⚙️ Instalação e Execução Local

### Pré-Requisitos no Windows/Linux/Mac
- **Python 3.10+** instalado
- **Tesseract OCR**: Se deseja utilizar o leitor de fotos "jpg/png", é obrigatório instalar a [versão C++ do Tesseract](https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe) oficial no Windows (e garantir que a pasta foi jogada no PATH do seu computador).
- Uma chave API gratuita da Groq Cloud.

### Passo 1: Clone este Repositório
```bash
git clone https://github.com/Reinaldo-rNeto/Extrator-de-Dados-de-Sites-Imagens-e-PDF.git
cd Extrator-de-Dados-de-Sites-Imagens-e-PDF
```

### Passo 2: Configuração de Ambiente
```bash
# Crie e ative um ambiente virtual
python -m venv venv
venv\Scripts\activate      # Se tiver no Windows
# source venv/bin/activate # Se tiver no Linux/Mac

# Instale os requerimentos e o navegador do Playwright
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

### Passo 3: Variáveis de Ambiente
Na pasta do projeto, crie um arquivo chamado `.env` e escreva exatamente isto:
```env
GROQ_API_KEY="gsk_sua_chave_groq_verdadeira_aqui"
```

### Passo 4: Executar a Mágica 🪄
```bash
streamlit run app.py
```

A interface abrirá no seu navegador preferido e já estará totalmente funcional!

## ☁️ Deploy no Render.com (Docker)

Esta aplicação foi polida com um `Dockerfile` especializado incluído na pasta raiz. O código já está desenhado para provisionar todas as dependências C++ do Ubuntu debaixo dos panos (NSS3, LibATK, e o Tesseract Português nativos para nuvem).

Basta fazer login gratuito em **Render.com** > **Novo Web Service** > Inserir a URL deste repositório > Setar Ambiente (Environment) para **Docker** e Lembrar de injetar sua Chave da `GROQ_API_KEY` na aba avançada (Environment Variables) antes de lançar o Deploy.

---

<div align="center">
  <sub>Construído com I.A para processar o mundo não-estruturado.</sub>
</div>

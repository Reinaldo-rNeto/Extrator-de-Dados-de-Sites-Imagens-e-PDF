import streamlit as st
import time
import sys
import asyncio
import traceback
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

# Correção vital para rodar Playwright em Threads do Streamlit no Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@st.cache_data(show_spinner=False, ttl=3600)
def extrair_html_cacheado(url: str) -> str:
    """
    Função auxiliar cacheada para não baixar a mesma URL várias vezes na mesma hora
    """
    # ==========================================
    # 🕸️ MODO PADRÃO: PLAYWRIGHT (Scraping Visual)
    # ==========================================
    try:
        with sync_playwright() as p:
            # ATUALIZAÇÃO ANTI-BOT: Mudando de Chromium para Firefox
            # O Firefox headless é nativamente menos rastreado por WAFs como Datadome e Cloudflare
            browser = p.firefox.launch(
                headless=True, 
                args=[
                    "--width=1920",
                    "--height=1080"
                ]
            )
            
            # Contexto "disfarçado" para evitar bloqueios de site que rejeitam robôs diretos
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
                }
            )
            
            page = context.new_page()
            
            # Injeta o disfarce ANTES da página carregar (Bypassa Cloudflare/Amazon/Shopee WAF)
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Aumentando limite de tempo (timeout robusto de 45s)
            page.set_default_timeout(45000)
            
            # Acessa a URL, wait_until 'commit' garante que assim que o html básico chegar, ele pare de esperar a eternidade
            try:
                page.goto(url, wait_until="commit", timeout=45000)
                time.sleep(3) # Dá um tempinho básico
            except Exception as e:
                print(f"Aviso de Timeout no carregamento completo: {e}")
            
            # Auto-Scroll Inteligente: Injeta JS para descer a página contínua (ex: Lojas Online)
            try:
                page.evaluate('''
                    async () => {
                        await new Promise((resolve) => {
                            let totalHeight = 0;
                            let distance = 500;
                            let scrolls = 0;
                            let maxScrolls = 8; // limite pra não travar no infinito
                            let timer = setInterval(() => {
                                let scrollHeight = document.body.scrollHeight;
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                scrolls++;
                                if (totalHeight >= scrollHeight || scrolls >= maxScrolls) {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 500); // 500ms entre scrolls pra carregar imagens
                        });
                    }
                ''')
                time.sleep(1) # Extra wait p/ dom processar novas tags
            except Exception as e:
                print(f"Aviso na rolagem JavaScript: {e}")
            # Captura todo o HTML no seu formato final processado

            html = page.content()
            browser.close()
            return html
    except Exception as e:
        tb = traceback.format_exc()
        raise Exception(f"Erro ao acessar {url}. Motivo técnico: {tb}")

class WebExtractor:
    """
    Classe responsável por extrair texto puro de sites e lojas virtuais.
    Ela "simula" um navegador real para carregar preços desenhados com Javascript.
    """
    def __init__(self):
        pass

    def extract_text(self, url: str) -> str:
        """
        Navega até a URL, rola a página um pouco, pega o HTML final e extrai só o texto bruto visível.
        """
        if not url.startswith("http"):
            url = "https://" + url

        texto_limpo = ""

        # ==========================================
        # 🚀 ATALHO TURBO: YOUTUBE
        # ==========================================
        if "youtube.com/watch" in url or "youtu.be/" in url:
            try:
                # Extrair o ID do vídeo usando Regex
                video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    print(f"[{url}] Detectado como Vídeo do YouTube. Baixando transcrição...")
                    # Baixa a transcrição em português ou falha graciosamente pra inglês
                    api = YouTubeTranscriptApi()
                    transcript_list = api.list(video_id)
                    
                    try:
                        transcript = transcript_list.find_transcript(['pt', 'pt-BR'])
                    except:
                        transcript = transcript_list.find_transcript(['en'])
                        
                    dados = transcript.fetch()
                    
                    texto_linhas = [f"--- Transcrição do Vídeo (ID: {video_id}) ---"]
                    for entry in dados:
                        if hasattr(entry, 'text'):
                            texto_linhas.append(entry.text)
                        elif isinstance(entry, dict) and 'text' in entry:
                            texto_linhas.append(entry['text'])
                    
                    texto_linhas.append("--- Fim da Transcrição ---")
                    return "\n".join(texto_linhas)
                else:
                    print("ID do YouTube não encontrado na URL. Tentando raspagem HTML padrão...")
            except Exception as e:
                print(f"Aviso: Não foi possível obter as legendas do YouTube ({e}). Caindo para Scraping Visual...")

        # ==========================================
        # 🕸️ MODO PADRÃO: PLAYWRIGHT (Scraping Visual)
        # ==========================================
        try:
            # Chama a função cacheada pelo Streamlit (Evita Playwright se já passamos por aqui recentemente)
            html = extrair_html_cacheado(url)

            # Processador HTML (Limpeza Profunda)
            soup = BeautifulSoup(html, "lxml")

            # 1. Destruir sumariamente tags de sujeira, menus escondidos e scripts para economizar os 25k caracteres
            tags_para_remover = [
                "script", "style", "noscript", "svg", "header", "footer", "nav", 
                "aside", "form", "button", "path", "meta", "link", "head", "iframe", "dialog"
            ]
            for invalid_tag in soup(tags_para_remover):
                invalid_tag.decompose()
            
            # 2. Truque de Mestre: Converter os links <a> em texto puro anotado inline
            # Assim não perdemos o href quando rodarmos o get_text final
            for a_tag in soup.find_all("a", href=True):
                txt = a_tag.get_text(strip=True)
                href = a_tag["href"]
                # Ignorar links inúteis ou vazios
                if txt and href and not href.startswith("javascript:"):
                    a_tag.string = f"{txt} [Link: {href}]"
            
            # 3. Extrair texto super limpo apenas do body (ignorando o DOM e as tags HTML)
            if soup.body:
                texto_limpo = soup.body.get_text(separator='\n', strip=True)
            else:
                texto_limpo = soup.get_text(separator='\n', strip=True)
            
            # 4. Compressão vertical extrema (remover múltiplas quebras de linhas)
            # Isso junta as linhas de um mesmo produto fazendo-o caber fácil no limite do LLM
            linhas = [linha.strip() for linha in texto_limpo.split('\n') if linha.strip()]
            texto_limpo = '\n'.join(linhas)
            
            # Retorna o suco condensado da informação
            return texto_limpo
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Erro ao tentar ler o site: {tb}")
            return f"Erro ao acessar {url}. Motivo técnico: {tb}"

if __name__ == "__main__":
    print("Módulo Web Extractor Inicializado.")

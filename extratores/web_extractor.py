import streamlit as st
import time
import sys
import asyncio
import traceback
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import os

# Correção vital para rodar Playwright em Threads do Streamlit no Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@st.cache_data(show_spinner=False, ttl=3600)
def extrair_html_cacheado(url: str) -> str:
    """
    Função auxiliar cacheada para não baixar a mesma URL várias vezes na mesma hora
    """
    # ==========================================
    try:
        html = ""
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
            
        # ==========================================
        # 🛡️ SISTEMA DE FALLBACK ANTI-BOT (ScrapingBee)
        # Se o Playwright foi pego pelo Datadome/Cloudflare (retornou Captcha, negative_traffic ou página em branco)
        # ==========================================
        html_low = html.lower()
        needs_fallback = (
            "negative_traffic" in html_low or 
            "captcha" in html_low or 
            "verifique se você é humano" in html_low or
            "403 forbidden" in html_low or
            "access denied" in html_low or
            len(html) < 5000 # Páginas de e-commerce sempre têm mais de 50k caracteres de código. Se for menor que 5k, fomos bloqueados silenciosamente.
        )
        
        if needs_fallback:
            print(f"⚠️ BLOQUEIO DETECTADO NO SITE (ou página muito curta): {url}. Acionando Proxies Premium (ScrapingBee)...")
            api_key = os.getenv("SCRAPINGBEE_API_KEY")
            
            if api_key:
                response = requests.get(
                    url="https://app.scrapingbee.com/api/v1/",
                    params={
                        "api_key": api_key,
                        "url": url,
                        "render_js": "true",
                        "premium_proxy": "true", # Essencial para Amazon/Mercado Livre
                    }
                )
                if response.status_code == 200:
                    print("✅ Falback ScrapingBee Vencedor!")
                    html = response.text
                else:
                    print(f"❌ ScrapingBee Falhou: {response.status_code} - {response.text}")
            else:
                print("❌ Chave SCRAPINGBEE_API_KEY não encontrada no .env. Fallback ignorado.")

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
                # Ignorar links inúteis ou relatórios javascript
                if txt and href and not href.startswith("javascript:"):
                    # URL REDUCTION OTIMIZATION: E-commerces (Amazon) usam links com 800+ caracteres de tracking. 
                    # Isso enche nossos 12.000 tokens muito rápido. Vamos arrancar as Queries!
                    clean_href = href.split('?')[0].split('/ref=')[0] 
                    a_tag.string = f"{txt} [Link: {clean_href}]"
            
            # 3. Extrair texto super limpo apenas do body (ignorando o DOM e as tags HTML)
            # MEGA OTIMIZAÇÃO: Tentar focar apenas no conteúdo principal pra evitar Cabeçalhos gigantes (que estouram os 12k chars)
            main_content = soup.find("main") or soup.find("div", id="search") or soup.find("div", role="main") or soup.find("div", id="root-app") or soup.body or soup
            
            # 4. Compressão Extrema (Smart Node Extraction)
            # Em vez de chamar get_text que engole spans com classes sujas, pegamos as strings com join
            linhas = []
            for text_node in main_content.stripped_strings:
                node_str = str(text_node).strip()
                # Ignorar ruídos muito curtos e coisas que poluem (|, -, >, "Em estoque")
                if len(node_str) > 2 and node_str.lower() not in ["mais opções de compra", "receba até", "frete grátis", "ver opções", "saber mais", "patrocinado", "prime", "em estoque"]:
                    linhas.append(node_str)
            
            # Unir tudo e remover blocos gigantes de espaços ou quebras para socar mais coisas em 12k chars
            texto_bruto = ' | '.join(linhas)
            # Limpa múltiplos pipes seguidos
            texto_limpo = re.sub(r'(\s*\|\s*){2,}', ' | ', texto_bruto)
            
            # Retorna o suco condensado da informação
            return texto_limpo
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Erro ao tentar ler o site: {tb}")
            return f"Erro ao acessar {url}. Motivo técnico: {tb}"

if __name__ == "__main__":
    print("Módulo Web Extractor Inicializado.")

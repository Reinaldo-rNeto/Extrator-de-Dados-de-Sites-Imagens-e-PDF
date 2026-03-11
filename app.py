import streamlit as st
import pandas as pd
import tempfile
import os

from motor_estruturador.engine import ExtractionEngine
from extratores.pdf_extractor import PDFExtractor
from extratores.web_extractor import WebExtractor
from extratores.image_extractor import ImageExtractor

import io

st.set_page_config(page_title="Extrator Universal Premium", page_icon="✨", layout="wide")

st.markdown("""
<style>
    /* Premium Dark Theme com Glassmorphism Dinamico */
    .stApp {
        background: linear-gradient(-45deg, #09090b, #18181b, #0f172a, #09090b);
        background-size: 400% 400%;
        animation: gradientBG 20s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    /* Estilizar cards e containeres como vidro */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    h1 {
        font-family: 'Inter', sans-serif;
        background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
    }
    h2, h3, p, label {
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif;
    }
    /* Botao principal magico */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        background-size: 200% auto;
        color: white !important;
        border: none;
        border-radius: 8px;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 1px;
        transition: 0.5s;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
    }
    .stButton>button:hover {
        background-position: right center; /* animacao do gradiente arrastando */
        color: #fff;
        text-decoration: none;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(236, 72, 153, 0.5);
    }
    .stTextInput fieldset, .stTextArea fieldset {
        border-radius: 10px !important;
        border-width: 1.5px !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        background: rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Sessão para armazenar os resultados
if 'resultados' not in st.session_state:
    st.session_state.resultados = []

# Botão Limpar Global
c_tit, c_btn = st.columns([4, 1])
with c_tit:
    st.title("✨ Extrator de Dados IA Premium")
    st.markdown("Extraia dados precisos e estruturados de arquivos e sites em milissegundos.")
with c_btn:
    st.write("") # Espaçamento
    if st.button("🗑️ Limpar Tudo", use_container_width=True):
        st.session_state.resultados = []
        st.rerun()

# Inicializa as classes
engine = ExtractionEngine()
pdf_extractor = PDFExtractor()
web_extractor = WebExtractor()
img_extractor = ImageExtractor()

# Layout da página
col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. Fonte de Dados")
    fonte_tipo = st.radio("Escolha o tipo de fonte:", ["📁 Arquivos Locais (PDF / Imagem)", "🌐 Página Web / Site"])
    
    arquivo_upload = None
    url_input = None
    
    pag_inicial = 1
    pag_final = None

    if fonte_tipo == "📁 Arquivos Locais (PDF / Imagem)":
        arquivo_upload = st.file_uploader("Selecione um Arquivo PDF ou Fotografia da sua máquina", type=["pdf", "png", "jpg", "jpeg"])
        
        if arquivo_upload and arquivo_upload.name.lower().endswith(".pdf"):
            st.markdown("**Intervalo de Páginas (Para PDFs ou Relatórios)**")
            cp1, cp2 = st.columns(2)
            pag_inicial = cp1.number_input("Página Inicial", min_value=1, value=1)
            pag_final_input = cp2.number_input("Página Final", min_value=1, value=3, help="A IA lê cerca de 3 a 5 páginas por vez devido ao limite de memória.")
            pag_final = pag_final_input
            
    else:
        url_input = st.text_input("Digite o link da página (Ex: https://lista.mercadolivre.com.br/...)")

    st.divider()
    
    st.header("2. O que extrair?")
    
    # Checkboxes Rápidos
    st.markdown("**Preenchimento Rápido (Opcional)**")
    c_check1, c_check2 = st.columns(2)
    
    pre_campos = []
    if c_check1.checkbox("🛒 Produtos E-commerce"):
        pre_campos.extend(["Nome do Produto", "Preço Original", "Preço com Desconto", "Marca", "Link da Imagem"])
    if c_check2.checkbox("📞 Contatos B2B"):
        pre_campos.extend(["Nome da Empresa", "Telefone", "E-mail", "Endereço", "Nome do Sócio"])
    if c_check1.checkbox("🧾 Notas Fiscais"):
        pre_campos.extend(["CNPJ Emissor", "Razão Social", "Valor Total", "Data de Emissão", "Chave de Acesso"])
        
    valor_preenchido = ", ".join(pre_campos) if pre_campos else ""
    
    campos_texto = st.text_area("Digite os campos personalizados que deseja extrair (separados por vírgula)", 
                                value=valor_preenchido,
                                placeholder="Ex: Nome da Empresa, CNPJ, Valor Total, Data de Vencimento")
    
    st.markdown("**Instruções Especiais (Mágico) ✨**")
    contexto_magico = st.text_input("Diga para a IA em qual aba/seção focar ou que regra seguir:",
                                    placeholder="Ex: Pegue só os celulares da 'aba de ofertas' com desconto...",
                                    help="Use este campo para conversar com a IA e direcionar a extração se a página for muito confusa.")
    
    extrair_btn = st.button("Iniciar Extração 🚀", type="primary", use_container_width=True)

with col2:
    st.header("3. Resultados")
    
    if extrair_btn:
        campos_lista = [c.strip() for c in campos_texto.split(",") if c.strip()]
        
        if not campos_lista:
            st.warning("Por favor, defina pelo menos um campo para extrair.")
        elif getattr(engine, 'api_key', None) == "coloque_sua_chave_groq_aqui":
            st.error("⚠️ ERRO: Chave da API do Groq ausente. Configure o arquivo `.env` com sua chave GROQ_API_KEY.")
        elif fonte_tipo == "📁 Arquivos Locais (PDF / Imagem)" and arquivo_upload is None:
             st.warning("Por favor, faça o upload de um arquivo PDF ou Imagem.")
        elif fonte_tipo == "🌐 Página Web / Site" and not url_input:
             st.warning("Por favor, digite ou cole a URL do site.")
        else:
            with st.status("Processo Mágico Iniciado...", expanded=True) as status:
                texto_bruto = ""
                
                if fonte_tipo == "📁 Arquivos Locais (PDF / Imagem)" and arquivo_upload is not None:
                    status.update(label="Lendo Arquivo Local... 📄", state="running")
                    try:
                        file_ext = os.path.splitext(arquivo_upload.name)[1].lower()
                        # Salva o arquivo temporariamente 
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                            tmp.write(arquivo_upload.getvalue())
                            tmp_path = tmp.name
                        
                        if file_ext == ".pdf":
                            texto_bruto = pdf_extractor.extract_text(tmp_path, start_page=pag_inicial, end_page=pag_final)
                        elif file_ext in [".png", ".jpg", ".jpeg"]:
                            texto_bruto = img_extractor.extract_text(tmp_path)
                            if texto_bruto == "erro_ocr_nao_instalado":
                                status.update(label="Erro no Reconhecimento Óptico ❌", state="error")
                                st.error("⚠️ **O 'Tesseract OCR' não está instalado neste Windows!**\n\n Para ler imagens, feche este programa e instale o pacote do Google OCR pelo link: [Baixar Instalador de OCR C++ (Oficial)](https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe). Avance até concluir e reinicie o Extrator para que ele detecte a nova visão computacional.")
                                texto_bruto = ""
                                
                        os.unlink(tmp_path)
                    except Exception as e:
                        status.update(label="Falha ao ler o Arquivo ❌", state="error")
                        st.error(f"Detalhe do erro: {e}")
                else:
                    status.update(label="Navegando Inviisivelmente pelo Site... 🌐", state="running")
                    try:
                        texto_bruto = web_extractor.extract_text(url_input)
                        if texto_bruto.startswith("Erro ao acessar"):
                            status.update(label="O robô foi bloqueado pelo site ❌", state="error")
                            st.error(f"Detalhe: {texto_bruto}")
                            texto_bruto = "" # Impede de enviar o erro pra IA
                    except Exception as e:
                        status.update(label="Falha gravíssima ao acessar site ❌", state="error")
                        st.error(f"Detalhe: {e}")
                # Mostra o texto bruto na tela para a gente debugar o "Anti-Bot"
                if texto_bruto:
                    with st.expander("🛠️ DEBUG: Texto capturado do site (Verifique se é captcha)"):
                        st.text_area("Primeiros 3000 caracteres:", value=texto_bruto[:3000], height=200)

                # Envia pro Cérebro
                if texto_bruto:
                    status.update(label="Enviando para o Motor Llama 3 Analisar... 🧠", state="running")
                    resultado, aviso_corte = engine.extract_structured_data(texto_bruto, campos_lista, custom_context=contexto_magico)
                    
                    if aviso_corte:
                        st.warning(f"⚠️ **Documento Gigante Detectado:** Parte do final do texto foi ignorado para não exceder o limite de memória do cérebro IA ({len(texto_bruto)} caracteres reduzidos para o limite máximo).")
                    
                    if isinstance(resultado, dict) and "erro" in resultado:
                        status.update(label="Falha na Inteligência Artificial ❌", state="error")
                        st.error(resultado["erro"])  # Mostra dentro
                        st.session_state.ui_erro = resultado["erro"] # Salva pra mostrar fora
                    else:
                        status.update(label="Montando Tabela de Resultados... 📊", state="running")
                        # O LLM agora é forçado a retornar no formato {"itens": [...]}
                        if isinstance(resultado, dict):
                            if "itens" in resultado and isinstance(resultado["itens"], list):
                                resultado = resultado["itens"]
                            else:
                                resultado = [resultado]
                        elif not isinstance(resultado, list):
                            resultado = []
                            
                        qtd_itens = len(resultado)
                        
                        for item in resultado:
                            item["Fonte"] = arquivo_upload.name if arquivo_upload else url_input
                            st.session_state.resultados.append(item)
                            
                        if qtd_itens > 0:
                            status.update(label=f"Concluído! {qtd_itens} itens extraídos ✨", state="complete")
                            st.success(f"{qtd_itens} itens extraídos da fonte com sucesso!")
                        else:
                            status.update(label="Busca Finalizada (Nenhum item válido) ⚠️", state="complete")
                            st.warning("A IA rodou, mas nenhum item válido foi encontrado correspondendo aos campos pesquisados no texto extraído.")
                else:
                    status.update(label="Conteúdo Invisível ou Bloqueado ❌", state="error")
                    st.error("O site retornou uma página completamente em branco ou todo o texto visual estava fortemente protegido/escondido. Verifique o link e tente novamente ou ajuste a configuração de bypass.")

    # Mostra um alerta de erro em CAIXA ALTA gigante fora do expansor se houver
    if getattr(st.session_state, 'ui_erro', None):
        st.error(f"🚨 **DETALHE DO ERRO:** {st.session_state.ui_erro}")
        st.session_state.ui_erro = None

    if st.session_state.resultados:
        df = pd.DataFrame(st.session_state.resultados)
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        
        c1, c2 = st.columns(2)
        
        with c1:
            # csv downloader
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Baixar Simples (CSV)",
                data=csv,
                file_name='dados_extraidos.csv',
                mime='text/csv',
                use_container_width=True
            )
            
        with c2:
            # excel Premium downloader
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Baixar Tabela (Planilha Excel)",
                data=excel_data,
                file_name='dados_premium_extrator.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type="primary",
                use_container_width=True
            )
    else:
         st.info("Nenhum dado extraído ainda. Configure na barra lateral e inicie.")

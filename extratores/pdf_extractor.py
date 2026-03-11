import pdfplumber
import os
import re

class PDFExtractor:
    """
    Classe responsável por extrair texto bruto de documentos PDF.
    """
    def __init__(self):
        pass

    def extract_text(self, file_path: str, start_page: int = 1, end_page: int | None = None) -> str:
        """
        Extrai todo o texto visível de um arquivo PDF preservando a estrutura da Tabela (layout=True).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        texto_completo = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                # Define limites seguros baseados no que o usuário pedir
                start_idx = max(0, start_page - 1)
                end_idx = min(total_pages, end_page) if end_page else total_pages
                
                # Extrai apenas as páginas selecionadas
                for page in pdf.pages[start_idx:end_idx]:
                    # O layout=True é ABSOLUTAMENTE VITAL para planilhas e relatórios financeiros
                    # Ele mantém os espaços e tabulações entre a "Descrição" e o "Valor" nas colunas.
                    texto_pagina = page.extract_text(layout=True)
                    if texto_pagina:
                        # Otimização de Memória: Troca grandes vácuos de espaço por apenas 3 espaços.
                        # Isso mantém o visual de colunas para a IA sem estourar o limite de Tokens (12k).
                        texto_pagina = re.sub(r' {4,}', '   ', texto_pagina)
                        texto_completo.append(texto_pagina)
            
            return "\n".join(texto_completo)
        except Exception as e:
            print(f"Erro ao ler PDF: {e}")
            return ""

# Teste simples (quando executado diretamente)
if __name__ == "__main__":
    print("Módulo PDF Extractor inicializado.")

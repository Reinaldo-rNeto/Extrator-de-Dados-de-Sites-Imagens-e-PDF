import pdfplumber
import os

class PDFExtractor:
    """
    Classe responsável por extrair texto bruto de documentos PDF.
    """
    def __init__(self):
        pass

    def extract_text(self, file_path: str) -> str:
        """
        Extrai todo o texto visível de um arquivo PDF.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        texto_completo = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    texto_pagina = page.extract_text()
                    if texto_pagina:
                        texto_completo.append(texto_pagina)
            
            return "\n".join(texto_completo)
        except Exception as e:
            print(f"Erro ao ler PDF: {e}")
            return ""

# Teste simples (quando executado diretamente)
if __name__ == "__main__":
    print("Módulo PDF Extractor inicializado.")

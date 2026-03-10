import pytesseract
from PIL import Image
import os
import sys

class ImageExtractor:
    """
    Extrator de texto para imagens e fotos renderizadas.
    Depende do Tesseract OCR instalado na máquina (Motor Visual do Google).
    """
    def __init__(self):
        # Local de instalação padrão no Windows
        self.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if sys.platform == "win32":
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

    def is_installed(self) -> bool:
        """Verifica se o usuário já instalou o Tesseract no Windows"""
        if sys.platform == "win32":
             return os.path.exists(self.tesseract_cmd)
        return True # Pressupõe nativo em Linux

    def extract_text(self, image_path: str) -> str:
        """Abre a imagem e tenta extrair os caracteres contidos nela."""
        if not self.is_installed():
            return "erro_ocr_nao_instalado"
            
        try:
            img = Image.open(image_path)
            # Lê o texto em Português e Inglês mesclado (linguagem padrão)
            texto = pytesseract.image_to_string(img, lang='por+eng')
            return texto.strip()
        except Exception as e:
            raise Exception(f"Falha ao processar Imagem via OCR: {e}")

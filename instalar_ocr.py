import os
import urllib.request
import subprocess
import sys

def download_and_install_tesseract():
    print("=== ASSISTENTE DE INSTALAÇÃO DO TESSERACT OCR ===")
    print("Este projeto precisa do Tesseract para ler imagens (OCR).")
    
    url = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
    installer_path = "tesseract_installer.exe"
    
    print(f"\n1. Baixando Motor OCR oficial ({url})...\nIsso pode demorar alguns segundos.")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req) as response, open(installer_path, 'wb') as out_file:
            out_file.write(response.read())
    except Exception as e:
        print(f"Erro no download: {e}")
        return

    print("Download Concluído!\n\n2. Iniciando Instalação Silenciosa...")
    try:
        # Modo silencioso para não incomodar o usuário
        subprocess.run([installer_path, "/SILENT"], check=True)
        print("\nSUCESSO! O Tesseract OCR foi instalado na sua máquina.")
        print("Você já pode voltar para o Extrator e extrair imagens!")
    except Exception as e:
        print(f"\nErro na instalação: {e}")
        print("Por favor, instale dando dois cliques no arquivo 'tesseract_installer.exe' manualmente.")
    
if __name__ == "__main__":
    download_and_install_tesseract()

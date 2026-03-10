from extratores.web_extractor import WebExtractor
from motor_estruturador.engine import ExtractionEngine
import json

url = "https://lista.mercadolivre.com.br/celular-samsung"
print(f"Lendo URL: {url}")
web_ext = WebExtractor()
texto = web_ext.extract_text(url)

print(f"Total de caracteres extraídos: {len(texto)}")

engine = ExtractionEngine()
campos = ["celulares samsung", "preço dos celulares"]

print("Enviando para o Llama 3...")
resultado = engine.extract_structured_data(texto, campos)

print("\n--- RESULTADO DA IA ---")
print(json.dumps(resultado, indent=2, ensure_ascii=False))

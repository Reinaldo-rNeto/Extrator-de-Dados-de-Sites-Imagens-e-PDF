from extratores.web_extractor import WebExtractor

extractor = WebExtractor()
url = "https://lista.mercadolivre.com.br/celular-samsung"
print(f"Lendo URL: {url}")
texto = extractor.extract_text(url)

print("--- TEXTO BRUTO OBTIDO ---")
# Imprime apenas os primeiros 2000 caracteres pra não travar o terminal
print(texto[:2000])
print("--------------------------")
print(f"Total de caracteres lidos: {len(texto)}")

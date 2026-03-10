import concurrent.futures
from extratores.web_extractor import WebExtractor
w = WebExtractor()

def run():
    print("Iniciando extração via Thread...")
    return w.extract_text('https://lista.mercadolivre.com.br/celular-samsung')

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(run)
    res = future.result()
    if res.startswith("Erro"):
        print("FALHA CAPTURADA:")
        print(res)
    else:
        print("SUCESSO NA THREAD!")

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class ExtractionEngine:
    """
    O 'Cérebro' do Extrator. Recebe um texto sujo e usa IA para extrair apenas o que o usuário quer.
    """
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key or self.api_key == "coloque_sua_chave_groq_aqui":
            print("AVISO: Chave da API do Groq não configurada.")
        else:
            self.client = Groq(api_key=self.api_key)
            # Llama 3.3 - 70B: O modelo mais poderoso e preciso de código aberto atual para essas tarefas
            self.model = "llama-3.3-70b-versatile"

    def extract_structured_data(self, source_text: str, target_fields: list[str], custom_context: str = "") -> tuple[dict|list, bool]:
        """
        Analisa o source_text e tenta encontrar os valores para os target_fields.
        Retorna um dicionário (JSON) extraído.
        """
        if not hasattr(self, 'client'):
             return {"erro": "API Key do Groq não configurada no arquivo .env"}, False

        # Aumentado para 25k caracteres para caber na cota Free da Groq (12000 Tokens/Min)
        MAX_CHARS = 25000
        foi_cortado = len(source_text) > MAX_CHARS
        text_preview = source_text[:MAX_CHARS] 

        prompt = f"""
        Você é um sistema especializado em extração de dados tabulares.
        Sua tarefa é analisar o seguinte texto-fonte (extraído de um PDF ou Site) e extrair fielmente as informações solicitadas.

        CAMPOS A EXTRAIR: {', '.join(target_fields)}
        
        INSTRUÇÕES DE FILTRO OU CONTEXTO DO USUÁRIO: {custom_context if custom_context else "Nenhuma (Extrair todos os itens correspondentes encontrados)."}

        REGRAS IMPORTANTES:
        1. Baseie-se APENAS no texto-fonte. Não invente informações! E obedeça estritamente às INSTRUÇÕES DE FILTRO acima.
        2. Se houver vários itens do mesmo tipo na página (ex: dezenas de produtos numa loja), a raiz do seu JSON DEVE conter uma única chave chamada "itens", contendo uma LISTA de objetos. (Exemplo: {{"itens": [{{"nome": "A", "preco": "10"}}, {{"nome": "B", "preco": "20"}}]}}).
        3. Se houver apenas um item, retorne da mesma forma na lista: {{"itens": [...]}}
        4. Se as informações não estiverem no texto, retorne {{"itens": []}} (lista vazia).
        5. Formato de resposta OBRIGATÓRIO: JSON perfeitamente válido contendo apenas o objeto {{"itens": [...]}}. Não escreva absolutamente NADA fora do JSON.

        TEXTO-FONTE:
        {text_preview}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                # Força o Llama a retornar um JSON estruturado em vez de conversa normal
                response_format={"type": "json_object"},
            )
            
            res_text = chat_completion.choices[0].message.content
            
            return json.loads(res_text.strip()), foi_cortado
            
        except json.JSONDecodeError:
            print(f"Erro ao converter a resposta da IA para JSON. Resposta bruta: {res_text}")
            return {"erro": "A IA não retornou um formato estruturado válido."}, foi_cortado
        except Exception as e:
            print(f"Erro na comunicação com a API: {e}")
            return {"erro": str(e)}, foi_cortado

if __name__ == "__main__":
    print("Motor Inicializado.")

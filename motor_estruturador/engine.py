import os
import json
from groq import Groq

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

        # Limite TÉCNICO estrito para cota Free da Groq (12k Tokens/Minuto)
        # Atenção: HTML de e-commerce é denso (poucos espaços). 1 char pode equivaler a quase 1 token.
        # Estamos travando em 12.000 chars para garantir matematicamente que nunca ultrapasse 12k Tokens.
        MAX_CHARS = 12000
        foi_cortado = len(source_text) > MAX_CHARS
        text_preview = source_text[:MAX_CHARS] 

        prompt = f"""
        Você é um sistema especializado em extração de dados tabulares.
        Sua tarefa é analisar o seguinte texto-fonte (extraído de um PDF ou Site) e extrair fielmente as informações solicitadas.

        CAMPOS A EXTRAIR: {', '.join(target_fields)}
        
        INSTRUÇÕES DE FILTRO OU CONTEXTO DO USUÁRIO: {custom_context if custom_context else "Nenhuma instrução específica."}

        REGRAS IMPORTANTES DE EXTRAÇÃO E FILTRAGEM:
        1. Baseie-se APENAS no texto-fonte. Não invente informações!
        2. ATENÇÃO AO FILTRO: Se o usuário pediu por um item específico nas "INSTRUÇÕES DE FILTRO" (exemplo: "apenas TV", "celular", "somente empresas de SP"), VOCÊ DEVE OBRIGATORIAMENTE FILTRAR E IGNORAR todos os outros itens da página que não sejam do tipo solicitado. Use inteligência para abstrair (uma "televisão" é uma "TV", "smartphone" é "celular").
        3. Se houver vários itens correspondentes na página, a raiz do seu JSON DEVE conter uma única chave chamada "itens", contendo uma LISTA de objetos. (Exemplo: {{"itens": [{{"nome": "A", "preco": "10", "link": "http..."}}, {{"nome": "B", "preco": "20"}}]}}).
        4. O formato de resposta OBRIGATÓRIO é um JSON perfeitamente válido contendo apenas o objeto {{"itens": [...]}}. 
        5. Lembre-se que o site extraído tem formatação rústica (os links aparecem assim: "[Link: http...]"). Extraia urls limpas!
        6. IMPORTANTE: Leia todo o texto-fonte passado até a última linha antes de dizer que não encontrou nada!
        7. Se as informações não estiverem no texto ou nenhum item passar no filtro do usuário apóes a LEITURA TOTAL, retorne estritamente {{"itens": []}} (lista vazia). Não escreva NADA fora do JSON bruto.

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

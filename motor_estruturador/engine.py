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
        2. ATENÇÃO AO FILTRO: Se o usuário pediu por um item específico nas "INSTRUÇÕES DE FILTRO" (exemplo: "apenas TV", "celular", "somente empresas de SP"), VOCÊ DEVE OBRIGATORIAMENTE FILTRAR E IGNORAR todos os outros itens.
        3. EXTRAÇÃO GRANULAR / TABELAS: Se o texto for um relatório financeiro, extrato ou tabela com múltiplas linhas (ex: Despesas, Receitas, Produtos), e o usuário pedir os itens, VOCÊ DEVE EXTRAIR CADA LINHA INDIVIDUALMENTE como um item separado do JSON. NÃO retorne apenas o "Total" geral a menos que solicitado. Queremos a lista completa de gastos/produtos!
        4. A raiz do seu JSON DEVE conter OBRIGATORIAMENTE uma única chave chamada "itens", contendo uma LISTA de objetos contendo os campos solicitados. (Exemplo: {{"itens": [{{"data": "...", "descricao": "...", "valor": "..."}}, {{"data": "...", "descricao": "..."}}]}}).
        5. O formato de resposta OBRIGATÓRIO é um JSON perfeitamente válido contendo apenas o objeto {{"itens": [...]}}. 
        6. Lembre-se que o site extraído tem formatação rústica (os links aparecem assim: "[Link: http...]"). Extraia urls limpas!
        7. IMPORTANTE: Leia todo o texto-fonte passado até a última linha antes de dizer que não encontrou nada!
        8. Se as informações não estiverem no texto ou nenhum item passar no filtro, retorne {{"itens": []}} (lista vazia). Não escreva NADA fora do JSON bruto.

        TEXTO-FONTE:
        {text_preview}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
            )
            res_text = chat_completion.choices[0].message.content
            return json.loads(res_text.strip()), foi_cortado
            
        except Exception as e:
            error_msg = str(e)
            # Se bater o limite diário do modelo 70B (Genius), faz Fallback Automático pro modelo 8B (Fast)
            if 'rate_limit_exceeded' in error_msg or '429' in error_msg:
                print("Limite do Llama 70B Atingido. Tentando Fallback para Llama 8B...")
                try:
                    fallback_completion = self.client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-8b-8192", # Modelo mais leve, possui cota diária separada
                        response_format={"type": "json_object"},
                    )
                    res_text = fallback_completion.choices[0].message.content
                    return json.loads(res_text.strip()), foi_cortado
                except json.JSONDecodeError:
                    return self._tenta_salvar_json_quebrado(res_text, foi_cortado)
                except Exception as fallback_e:
                    return {"erro": f"Cota de Inteligência Esgotada em todos os modelos. Detalhe: {fallback_e}"}, foi_cortado
            
            # Se for apenas um erro de JSON na primeira tentativa
            if 'json.decoder.JSONDecodeError' in str(type(e)) or 'Expecting value' in error_msg:
                return self._tenta_salvar_json_quebrado(res_text if 'res_text' in locals() else "", foi_cortado)
                
            print(f"Erro na comunicação com a API: {e}")
            return {"erro": str(e)}, foi_cortado

    def _tenta_salvar_json_quebrado(self, res_text: str, foi_cortado: bool):
        print(f"Erro de JSON. Salvando o que foi gerado. Resposta bruta: {res_text}")
        try:
            last_brace = res_text.rfind('}')
            if last_brace != -1:
                salvaged_text = res_text[:last_brace+1] + ']}'
                return json.loads(salvaged_text), True
        except:
            pass
        return {"erro": "A IA foi interrompida antes de terminar a lista. O arquivo é muito denso! Tente extrair apenas 1 ou 2 páginas por vez."}, foi_cortado

if __name__ == "__main__":
    print("Motor Inicializado.")

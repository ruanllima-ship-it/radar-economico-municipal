# afina_prompt.py
# O experimento de engenharia de prompt do TP5.
#
# Roda o MESMO municipio com dois prompts diferentes, um depois do outro,
# com o mesmo modelo e a mesma configuracao. A unica coisa que muda e o
# texto do prompt. Assim da para atribuir qualquer diferenca no resultado
# ao prompt, e nao ao acaso.
#
# Versao 1: entrega os numeros crus e pede que o modelo analise.
# Versao 2: entrega a analise pronta, feita pelo agente.py, e pede que o
#           modelo apenas redija.
#
# Rodar com o VS Code FECHADO, num terminal do Windows. O modelo precisa
# de uns 3 GB de memoria livre.

import os
import sys
import time
import subprocess

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

try:
    from deployment.agente import montar_analise, numero_br
    from deployment.diagnostico_llm import montar_pedido, regras_do_sistema, limpar_texto
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from deployment.agente import montar_analise, numero_br
    from deployment.diagnostico_llm import montar_pedido, regras_do_sistema, limpar_texto


nome_do_modelo = "Qwen/Qwen2.5-1.5B-Instruct"

# troque estes dois para testar outro municipio
codigo_do_teste = 1400704
ano_do_teste = 2021

pedacos_maximos = 260

pasta_deste_arquivo = os.path.dirname(os.path.abspath(__file__))
raiz_do_projeto = os.path.dirname(pasta_deste_arquivo)
caminho_indicadores = os.path.join(
    raiz_do_projeto, "data_acquisition", "cleaned_data", "indicadores_municipios.csv"
)


def memoria_livre_gb():
    comando = "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            capture_output=True,
            text=True,
            timeout=30,
        )
        texto = resultado.stdout.strip()
        if texto == "":
            return None
        return round(int(texto) / (1024 * 1024), 1)
    except Exception:
        return None


# ------------------------------------------------------------------
# A versao 1 do prompt, exatamente como foi usada no primeiro teste
# ------------------------------------------------------------------
regras_versao_1 = (
    "Você é um analista de dados econômicos municipais. Você escreve para "
    "prefeitos e vereadores de cidades pequenas, que não são técnicos.\n\n"
    "Regras que você deve seguir sempre:\n"
    "1. Use APENAS os números que estão na mensagem do usuário. Nunca calcule, "
    "nunca estime e nunca invente nenhum número.\n"
    "2. Se um dado não estiver na mensagem, diga que ele não está disponível, "
    "em vez de supor.\n"
    "3. Escreva em português do Brasil, em 3 parágrafos curtos, sem listas e "
    "sem títulos.\n"
    "4. Não use jargão. Explique o que cada indicador significa na prática.\n"
    "5. Não faça promessas nem garantias sobre o futuro."
)


def montar_pedido_versao_1(linha, mediana_ppc_estado, mediana_dep_estado, mediana_dep_brasil):
    return (
        "Faça o diagnóstico econômico deste município.\n\n"
        "MUNICÍPIO\n"
        "Nome: " + str(linha["municipio"]) + " (" + str(linha["uf"]) + ")\n"
        "Ano dos dados: " + str(ano_do_teste) + "\n"
        "População: " + numero_br(linha["populacao"], 0) + " habitantes\n\n"
        "RIQUEZA\n"
        "PIB: R$ " + numero_br(linha["pib"] / 1000, 1) + " milhões\n"
        "PIB por habitante: R$ " + numero_br(linha["pib_per_capita"], 0) + "\n"
        "PIB por habitante do Brasil: R$ " + numero_br(linha["pib_per_capita_brasil"], 0) + "\n"
        "PIB por habitante mediano do estado: R$ " + numero_br(mediana_ppc_estado, 0) + "\n"
        "Razão de riqueza (município dividido pelo Brasil): " + numero_br(linha["razao_riqueza"], 2) + "\n"
        "Posição no ranking nacional de PIB: " + numero_br(linha["posicao_pib"], 0) + " de 5.570\n\n"
        "DE ONDE VEM A ECONOMIA\n"
        "Agropecuária: " + numero_br(linha["part_agropecuaria"], 1) + "%\n"
        "Indústria: " + numero_br(linha["part_industria"], 1) + "%\n"
        "Serviços: " + numero_br(linha["part_servicos"], 1) + "%\n"
        "Administração pública: " + numero_br(linha["part_adm_publica"], 1) + "%\n"
        "Perfil predominante: " + str(linha["perfil"]) + "\n"
        "Índice de concentração setorial HHI, de 0 a 1: " + numero_br(linha["hhi"], 2) + "\n\n"
        "COMPARAÇÃO DA DEPENDÊNCIA DA ADMINISTRAÇÃO PÚBLICA\n"
        "Neste município: " + numero_br(linha["dependencia_adm"], 1) + "%\n"
        "Mediana dos municípios de " + str(linha["uf"]) + ": " + numero_br(mediana_dep_estado, 1) + "%\n"
        "Mediana dos municípios do Brasil: " + numero_br(mediana_dep_brasil, 1) + "%\n\n"
        "ESCREVA O DIAGNÓSTICO EM 3 PARÁGRAFOS:\n"
        "Parágrafo 1: como está a riqueza do município comparada ao estado e ao país.\n"
        "Parágrafo 2: de que a economia depende e o que isso significa na prática.\n"
        "Parágrafo 3: quais os riscos e o que o gestor deveria acompanhar."
    )


print()
print("=" * 74)
print("  EXPERIMENTO DE ENGENHARIA DE PROMPT")
print("=" * 74)
print()
print("Modelo:", nome_do_modelo, "em bfloat16")
print("Memoria livre antes de comecar:", memoria_livre_gb(), "GB")
print()

# ------------------------------------------------------------------
# Dados
# ------------------------------------------------------------------
indicadores = pd.read_csv(caminho_indicadores)
do_ano = indicadores[indicadores["ano"] == ano_do_teste]

achado = do_ano[do_ano["codigo"] == codigo_do_teste]
if len(achado) == 0:
    print("nao achei esse municipio nesse ano")
    sys.exit()
linha = achado.iloc[0]

do_estado = do_ano[do_ano["uf"] == linha["uf"]]
mediana_ppc_estado = do_estado["pib_per_capita"].median()
mediana_dep_estado = do_estado["dependencia_adm"].median()
mediana_dep_brasil = do_ano["dependencia_adm"].median()

analise = montar_analise(indicadores, codigo_do_teste, ano_do_teste)

print("Municipio:", analise["municipio"], "-", analise["estado"], "- ano", analise["ano"])
print()

# ------------------------------------------------------------------
# Modelo
# ------------------------------------------------------------------
print("Carregando o modelo...")
relogio = time.time()

tokenizador = AutoTokenizer.from_pretrained(nome_do_modelo)
try:
    modelo = AutoModelForCausalLM.from_pretrained(nome_do_modelo, dtype=torch.bfloat16)
except TypeError:
    modelo = AutoModelForCausalLM.from_pretrained(nome_do_modelo, torch_dtype=torch.bfloat16)
modelo.eval()

print("Carregou em", round(time.time() - relogio, 1), "segundos.")
print("Memoria livre depois de carregar:", memoria_livre_gb(), "GB")
print()


def gerar(regras, pedido):
    mensagens = [
        {"role": "system", "content": regras},
        {"role": "user", "content": pedido},
    ]
    texto_do_prompt = tokenizador.apply_chat_template(
        mensagens,
        tokenize=False,
        add_generation_prompt=True,
    )
    entrada = tokenizador(texto_do_prompt, return_tensors="pt")
    quantos_no_prompt = int(entrada["input_ids"].shape[1])

    relogio = time.time()
    with torch.no_grad():
        saida = modelo.generate(
            input_ids=entrada["input_ids"],
            attention_mask=entrada["attention_mask"],
            max_new_tokens=pedacos_maximos,
            do_sample=False,
        )
    demorou = time.time() - relogio

    so_a_resposta = saida[0][quantos_no_prompt:]
    texto = tokenizador.decode(so_a_resposta, skip_special_tokens=True)
    return texto, demorou, quantos_no_prompt, int(so_a_resposta.shape[0])


# ------------------------------------------------------------------
# Versao 1
# ------------------------------------------------------------------
print("=" * 74)
print("VERSAO 1 - entrega os numeros crus e pede que o modelo analise")
print("=" * 74)
print("Gerando. Aguarde.")

pedido_1 = montar_pedido_versao_1(linha, mediana_ppc_estado, mediana_dep_estado, mediana_dep_brasil)
texto_1, tempo_1, prompt_1, gerados_1 = gerar(regras_versao_1, pedido_1)

print("Pedacos do prompt:", prompt_1, "| gerados:", gerados_1, "| tempo:", round(tempo_1, 1), "s")
print()
print(texto_1.strip())
print()

# ------------------------------------------------------------------
# Versao 2
# ------------------------------------------------------------------
print("=" * 74)
print("VERSAO 2 - entrega a analise pronta e pede que o modelo so redija")
print("=" * 74)
print("Gerando. Aguarde.")

pedido_2 = montar_pedido(analise)
texto_2, tempo_2, prompt_2, gerados_2 = gerar(regras_do_sistema, pedido_2)

print("Pedacos do prompt:", prompt_2, "| gerados:", gerados_2, "| tempo:", round(tempo_2, 1), "s")
print()
print("--- como o modelo entregou (texto bruto) ---")
print(texto_2.strip())
print()
print("--- depois da limpeza feita pelo codigo ---")
print(limpar_texto(texto_2))
print()

print("=" * 74)
print("  RESUMO")
print("=" * 74)
print("Versao 1: prompt de", prompt_1, "pedacos, gerou", gerados_1, "em", round(tempo_1, 1), "s")
print("Versao 2: prompt de", prompt_2, "pedacos, gerou", gerados_2, "em", round(tempo_2, 1), "s")
print("Memoria livre no fim:", memoria_livre_gb(), "GB")
print()
print("  FIM. Copiar toda essa saida e mandar para analise.")
print("=" * 74)
print()
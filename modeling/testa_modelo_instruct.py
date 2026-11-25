# testa_modelo_instruct.py
# Teste do modelo que segue instrucao, para o agente de diagnostico do TP5.
#
# Esta versao mede os DOIS formatos de numero, um depois do outro:
#   bfloat16 - ocupa 3,1 GB, mas o processador desta maquina nao tem
#              instrucao nativa para ele, entao cada conta e emulada
#   float32  - ocupa 6,2 GB, mas roda nativo
#
# O prompt e exatamente o mesmo da primeira versao, de proposito: aqui eu
# quero medir velocidade, nao mexer na qualidade. O ajuste do prompt vem
# no proximo bloco, para dar para comparar o antes e o depois.
#
# IMPORTANTE: rodar com o VS Code FECHADO, num terminal do Windows.

import gc
import os
import sys
import time
import subprocess

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


nome_do_modelo = "Qwen/Qwen2.5-1.5B-Instruct"

pasta_deste_arquivo = os.path.dirname(os.path.abspath(__file__))
raiz_do_projeto = os.path.dirname(pasta_deste_arquivo)
caminho_indicadores = os.path.join(
    raiz_do_projeto, "data_acquisition", "cleaned_data", "indicadores_municipios.csv"
)

codigo_do_teste = 1400704
ano_do_teste = 2021
pedacos_para_gerar = 220


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


def formatar(valor, casas=0):
    if pd.isna(valor):
        return "sem dado"
    texto = f"{valor:,.{casas}f}"
    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")
    return texto


print()
print("=" * 72)
print("  TESTE DE VELOCIDADE: bfloat16 CONTRA float32")
print("=" * 72)
print()
print("Modelo:", nome_do_modelo)
print("Nucleos que o torch vai usar:", torch.get_num_threads())
print("Memoria livre antes de comecar:", memoria_livre_gb(), "GB")
print()


# ------------------------------------------------------------------
# 1) Dados reais do municipio
# ------------------------------------------------------------------
tabela = pd.read_csv(caminho_indicadores)
do_ano = tabela[tabela["ano"] == ano_do_teste]

linha = do_ano[do_ano["codigo"] == codigo_do_teste]
if len(linha) == 0:
    print("nao achei esse municipio nesse ano")
    sys.exit()
linha = linha.iloc[0]

do_estado = do_ano[do_ano["uf"] == linha["uf"]]
mediana_dep_estado = do_estado["dependencia_adm"].median()
mediana_dep_brasil = do_ano["dependencia_adm"].median()
mediana_ppc_estado = do_estado["pib_per_capita"].median()

print("Municipio do teste:", linha["municipio"], "(" + linha["uf"] + ")", "- ano", ano_do_teste)
print()


# ------------------------------------------------------------------
# 2) O prompt (identico ao da primeira versao)
# ------------------------------------------------------------------
regras = (
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

pedido = (
    "Faça o diagnóstico econômico deste município.\n\n"
    "MUNICÍPIO\n"
    "Nome: " + str(linha["municipio"]) + " (" + str(linha["uf"]) + ")\n"
    "Ano dos dados: " + str(ano_do_teste) + "\n"
    "População: " + formatar(linha["populacao"]) + " habitantes\n\n"
    "RIQUEZA\n"
    "PIB: R$ " + formatar(linha["pib"] / 1000, 1) + " milhões\n"
    "PIB por habitante: R$ " + formatar(linha["pib_per_capita"]) + "\n"
    "PIB por habitante do Brasil: R$ " + formatar(linha["pib_per_capita_brasil"]) + "\n"
    "PIB por habitante mediano do estado: R$ " + formatar(mediana_ppc_estado) + "\n"
    "Razão de riqueza (município dividido pelo Brasil): " + formatar(linha["razao_riqueza"], 2) + "\n"
    "Posição no ranking nacional de PIB: " + formatar(linha["posicao_pib"]) + " de 5.570\n\n"
    "DE ONDE VEM A ECONOMIA\n"
    "Agropecuária: " + formatar(linha["part_agropecuaria"], 1) + "%\n"
    "Indústria: " + formatar(linha["part_industria"], 1) + "%\n"
    "Serviços: " + formatar(linha["part_servicos"], 1) + "%\n"
    "Administração pública: " + formatar(linha["part_adm_publica"], 1) + "%\n"
    "Perfil predominante: " + str(linha["perfil"]) + "\n"
    "Índice de concentração setorial HHI, de 0 a 1: " + formatar(linha["hhi"], 2) + "\n\n"
    "COMPARAÇÃO DA DEPENDÊNCIA DA ADMINISTRAÇÃO PÚBLICA\n"
    "Neste município: " + formatar(linha["dependencia_adm"], 1) + "%\n"
    "Mediana dos municípios de " + str(linha["uf"]) + ": " + formatar(mediana_dep_estado, 1) + "%\n"
    "Mediana dos municípios do Brasil: " + formatar(mediana_dep_brasil, 1) + "%\n\n"
    "ESCREVA O DIAGNÓSTICO EM 3 PARÁGRAFOS:\n"
    "Parágrafo 1: como está a riqueza do município comparada ao estado e ao país.\n"
    "Parágrafo 2: de que a economia depende e o que isso significa na prática.\n"
    "Parágrafo 3: quais os riscos e o que o gestor deveria acompanhar."
)

mensagens = [
    {"role": "system", "content": regras},
    {"role": "user", "content": pedido},
]


# ------------------------------------------------------------------
# 3) A funcao que testa um formato
# ------------------------------------------------------------------
def testar(formato, rotulo):
    print("=" * 72)
    print("TESTANDO EM", rotulo)
    print("=" * 72)
    print("   Memoria livre antes:", memoria_livre_gb(), "GB")

    relogio = time.time()
    try:
        tokenizador = AutoTokenizer.from_pretrained(nome_do_modelo)
        try:
            modelo = AutoModelForCausalLM.from_pretrained(nome_do_modelo, dtype=formato)
        except TypeError:
            modelo = AutoModelForCausalLM.from_pretrained(nome_do_modelo, torch_dtype=formato)
    except Exception as erro:
        print("   NAO CARREGOU em", rotulo)
        print("   Erro:", str(erro)[:400])
        print()
        return

    modelo.eval()
    demorou_carregar = time.time() - relogio

    print("   Carregou em", round(demorou_carregar, 1), "segundos")
    print("   Memoria livre depois de carregar:", memoria_livre_gb(), "GB")

    texto_do_prompt = tokenizador.apply_chat_template(
        mensagens,
        tokenize=False,
        add_generation_prompt=True,
    )
    entrada = tokenizador(texto_do_prompt, return_tensors="pt")
    pedacos_do_prompt = int(entrada["input_ids"].shape[1])

    print("   Gerando", pedacos_para_gerar, "pedacos. Aguarde.")
    relogio = time.time()

    try:
        with torch.no_grad():
            saida = modelo.generate(
                input_ids=entrada["input_ids"],
                attention_mask=entrada["attention_mask"],
                max_new_tokens=pedacos_para_gerar,
                do_sample=False,
            )
    except Exception as erro:
        print("   NAO GEROU em", rotulo)
        print("   Erro:", str(erro)[:400])
        del modelo
        gc.collect()
        print()
        return

    demorou_gerar = time.time() - relogio

    so_a_resposta = saida[0][pedacos_do_prompt:]
    resposta = tokenizador.decode(so_a_resposta, skip_special_tokens=True)
    gerados = int(so_a_resposta.shape[0])

    print("   Pedacos do prompt:", pedacos_do_prompt)
    print("   Pedacos gerados:", gerados)
    print("   Tempo de geracao:", round(demorou_gerar, 1), "segundos")
    if demorou_gerar > 0:
        print("   VELOCIDADE:", round(gerados / demorou_gerar, 1), "pedacos por segundo")
    print()
    print("   ----- texto gerado em " + rotulo + " -----")
    print(resposta)
    print("   ----- fim do texto -----")
    print()

    # libera a memoria antes do proximo teste
    del modelo
    del tokenizador
    gc.collect()
    print("   Memoria livre depois de liberar:", memoria_livre_gb(), "GB")
    print()


# ------------------------------------------------------------------
# 4) Rodando os dois
# ------------------------------------------------------------------
testar(torch.bfloat16, "bfloat16 (3,1 GB)")
testar(torch.float32, "float32 (6,2 GB)")

print("=" * 72)
print("  FIM. Copiar toda essa saida e mandar para analise.")
print("=" * 72)
print()
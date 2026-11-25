# verifica_tp5.py
# Confere, arquivo por arquivo, se tudo o que o TP5 precisa esta no lugar.
#
# Rode da raiz do projeto:
#     py modeling/verifica_tp5.py
#
# Este programa so LE arquivos. Ele nao escreve, nao apaga e nao muda nada.
# No fim ele imprime um resumo dizendo o que esta certo e o que precisa de
# conserto.
#
# A API nao precisa estar ligada. O painel tambem nao.

import os
import sys


# o caminho da raiz sai do __file__, e nao da pasta de onde o comando foi
# dado. assim o programa funciona mesmo que alguem rode de outro lugar.
pasta_deste_arquivo = os.path.dirname(os.path.abspath(__file__))
raiz_do_projeto = os.path.dirname(pasta_deste_arquivo)

if raiz_do_projeto not in sys.path:
    sys.path.insert(0, raiz_do_projeto)


certos = []
problemas = []


def anotar(numero, nome, deu_certo, detalhe=""):
    """Guarda o resultado de um teste e imprime na hora."""
    if deu_certo is True:
        certos.append(nome)
        print("  [OK]    " + str(numero) + ". " + nome)
    else:
        problemas.append(nome)
        print("  [ERRO]  " + str(numero) + ". " + nome)
        if detalhe != "":
            print("          " + detalhe)


def ler_arquivo(caminho_relativo):
    """Devolve o conteudo do arquivo, ou None se ele nao existir."""
    caminho = os.path.join(raiz_do_projeto, caminho_relativo)
    if os.path.exists(caminho) is False:
        return None
    arquivo = open(caminho, encoding="utf-8")
    conteudo = arquivo.read()
    arquivo.close()
    return conteudo


print()
print("=" * 64)
print("VERIFICACAO DOS ARQUIVOS DO TP5")
print("Projeto:", raiz_do_projeto)
print("=" * 64)
print()

# ------------------------------------------------------------------
print("-- Os arquivos existem? --")

esperados = [
    "deployment/agente.py",
    "deployment/diagnostico_llm.py",
    "deployment/api.py",
    "deployment/respostas.py",
    "deployment/comum.py",
    "deployment/app.py",
    "deployment/modelo_llm.py",
    "deployment/paginas/diagnostico.py",
    "modeling/testa_agente.py",
    "modeling/afina_prompt.py",
    "modeling/testa_modelo_instruct.py",
]

numero = 0
for caminho in esperados:
    numero = numero + 1
    existe = os.path.exists(os.path.join(raiz_do_projeto, caminho))
    anotar(numero, "existe: " + caminho, existe, "arquivo nao encontrado")

print()

# ------------------------------------------------------------------
print("-- O agente (o que pensa) --")

numero = numero + 1
try:
    from deployment import agente
    anotar(numero, "agente.py importa sem erro", True)
    agente_ok = True
except Exception as erro:
    anotar(numero, "agente.py importa sem erro", False, str(erro))
    agente_ok = False

numero = numero + 1
texto_agente = ler_arquivo("deployment/agente.py")
if texto_agente is None:
    anotar(numero, "agente.py tem a correcao do arredondar(casas=0)", False, "arquivo nao encontrado")
else:
    tem_correcao = "if casas == 0:" in texto_agente
    anotar(numero, "agente.py tem a correcao do arredondar(casas=0)", tem_correcao,
           "falta o 'if casas == 0: return int(...)' dentro de arredondar()")

if agente_ok is True:
    numero = numero + 1
    try:
        import pandas as pd
        caminho_csv = os.path.join(raiz_do_projeto, "data_acquisition", "cleaned_data", "indicadores_municipios.csv")
        indicadores = pd.read_csv(caminho_csv)
        analise = agente.montar_analise(indicadores, 1400704, 2021)
        deu = analise is not None
        anotar(numero, "agente analisa Uiramuta em 2021", deu, "montar_analise devolveu None")
    except Exception as erro:
        analise = None
        anotar(numero, "agente analisa Uiramuta em 2021", False, str(erro))

    if analise is not None:
        numero = numero + 1
        populacao = analise["numeros"]["populacao"]
        e_inteiro = isinstance(populacao, int)
        anotar(numero, "populacao vem sem casa decimal", e_inteiro,
               "veio " + repr(populacao) + ", devia ser um numero inteiro")

        numero = numero + 1
        tem_tudo = len(analise["achados"]) > 0 and len(analise["acompanhar"]) > 0
        anotar(numero, "a analise traz achados e o que acompanhar", tem_tudo,
               "achados: " + str(len(analise["achados"])) + ", acompanhar: " + str(len(analise["acompanhar"])))

print()

# ------------------------------------------------------------------
print("-- O motor do modelo (o que escreve) --")

numero = numero + 1
texto_motor = ler_arquivo("deployment/diagnostico_llm.py")
if texto_motor is None:
    anotar(numero, "diagnostico_llm.py nao e a pagina trocada", False, "arquivo nao encontrado")
else:
    nao_e_pagina = "import streamlit" not in texto_motor
    anotar(numero, "diagnostico_llm.py nao e a pagina trocada", nao_e_pagina,
           "este arquivo esta com o conteudo da pagina do painel dentro dele")

numero = numero + 1
try:
    from deployment import diagnostico_llm
    anotar(numero, "diagnostico_llm.py importa sem erro", True)
    motor_ok = True
except Exception as erro:
    anotar(numero, "diagnostico_llm.py importa sem erro", False, str(erro))
    motor_ok = False

if motor_ok is True:
    numero = numero + 1
    valor = diagnostico_llm.pedacos_maximos
    anotar(numero, "pedacos_maximos esta em 480", valor == 480,
           "esta em " + str(valor) + "; com menos que isso o 3o paragrafo volta a ser cortado")

    numero = numero + 1
    sem_ponto = diagnostico_llm.cortar_na_ultima_frase("texto sem ponto final")
    anotar(numero, "a correcao do corte de frase esta aplicada", sem_ponto == "",
           "paragrafo sem nenhuma frase completa devia ser descartado")

    numero = numero + 1
    com_ponto = diagnostico_llm.cortar_na_ultima_frase("Primeira frase. Segunda pela metade")
    anotar(numero, "o corte preserva a parte completa", com_ponto == "Primeira frase.",
           "devolveu: " + repr(com_ponto))

    numero = numero + 1
    certo = diagnostico_llm.nome_do_modelo == "Qwen/Qwen2.5-1.5B-Instruct"
    anotar(numero, "o modelo do TP5 e o Qwen2.5-1.5B-Instruct", certo,
           "esta apontando para " + diagnostico_llm.nome_do_modelo)

    numero = numero + 1
    tem_regras = "9. " in diagnostico_llm.regras_do_sistema
    anotar(numero, "o prompt esta na versao 8 (9 regras)", tem_regras,
           "a regra 9 nao foi encontrada nas regras_do_sistema")

print()

# ------------------------------------------------------------------
print("-- Os Response Models --")

numero = numero + 1
try:
    from deployment.respostas import (
        TrajetoriaDoMunicipio,
        AnaliseDoMunicipio,
        RespostaDaAnalise,
        RespostaDoDiagnostico,
        RespostaDoModeloDeDiagnostico,
        RespostaSimples,
    )
    anotar(numero, "os 6 modelos novos do TP5 existem", True)
except Exception as erro:
    anotar(numero, "os 6 modelos novos do TP5 existem", False, str(erro))

print()

# ------------------------------------------------------------------
print("-- A API --")

numero = numero + 1
try:
    from deployment import api
    anotar(numero, "api.py importa sem erro", True)
    api_ok = True
except Exception as erro:
    anotar(numero, "api.py importa sem erro", False, str(erro))
    api_ok = False

if api_ok is True:
    numero = numero + 1
    anotar(numero, "a API esta na versao 3.0", api.app.version == "3.0",
           "esta na versao " + str(api.app.version))

    numero = numero + 1
    desenho = api.app.openapi()
    quantas = len(desenho["paths"])
    anotar(numero, "a API tem as 12 rotas", quantas == 12,
           "encontrei " + str(quantas) + " rotas")

    numero = numero + 1
    quantos = len(desenho["components"]["schemas"])
    anotar(numero, "a API tem os 25 schemas", quantos == 25,
           "encontrei " + str(quantos) + " schemas")

    numero = numero + 1
    rotas_novas = ["/analise/{codigo}", "/diagnostico", "/modelo_diagnostico", "/modelo_diagnostico/descarregar"]
    faltando = []
    for rota in rotas_novas:
        if rota not in desenho["paths"]:
            faltando.append(rota)
    anotar(numero, "as 4 rotas do agente existem", len(faltando) == 0,
           "faltam: " + ", ".join(faltando))

print()

# ------------------------------------------------------------------
print("-- O painel --")

numero = numero + 1
texto_comum = ler_arquivo("deployment/comum.py")
if texto_comum is None:
    anotar(numero, "comum.py converte o ano com int()", False, "arquivo nao encontrado")
else:
    anotar(numero, "comum.py converte o ano com int()", "ano = int(ano)" in texto_comum,
           "sem isso o POST /diagnostico quebra antes de sair do painel")

numero = numero + 1
if texto_comum is None:
    anotar(numero, "comum.py converte o codigo com int()", False, "arquivo nao encontrado")
else:
    tem = "int(codigo_da_opcao[municipio_escolhido])" in texto_comum
    anotar(numero, "comum.py converte o codigo com int()", tem, "mesmo motivo do ano")

numero = numero + 1
texto_pagina = ler_arquivo("deployment/paginas/diagnostico.py")
if texto_pagina is None:
    anotar(numero, "a pagina do diagnostico existe e tem conteudo", False, "arquivo nao encontrado")
else:
    e_pagina = "import streamlit" in texto_pagina and "Escrever o diagnóstico com a IA" in texto_pagina
    anotar(numero, "a pagina do diagnostico existe e tem conteudo", e_pagina,
           "o arquivo existe mas nao parece ser a pagina do painel")

numero = numero + 1
if texto_pagina is None:
    anotar(numero, "a pagina manda numeros comuns no POST", False, "arquivo nao encontrado")
else:
    tem = 'int(codigo_municipio)' in texto_pagina
    anotar(numero, "a pagina manda numeros comuns no POST", tem,
           "falta o int() na linha do corpo = {...}")

numero = numero + 1
texto_app = ler_arquivo("deployment/app.py")
if texto_app is None:
    anotar(numero, "a pagina esta pendurada no menu do painel", False, "arquivo nao encontrado")
else:
    tem = 'paginas/diagnostico.py' in texto_app
    anotar(numero, "a pagina esta pendurada no menu do painel", tem,
           "falta a linha st.Page('paginas/diagnostico.py', ...) no app.py")

numero = numero + 1
if texto_app is None:
    anotar(numero, "o painel tem 9 paginas", False, "arquivo nao encontrado")
else:
    quantas = texto_app.count("st.Page(")
    anotar(numero, "o painel tem 9 paginas", quantas == 9, "encontrei " + str(quantas))

print()

# ------------------------------------------------------------------
print("-- As bibliotecas --")

numero = numero + 1
try:
    import torch
    anotar(numero, "o PyTorch esta instalado", True)
except Exception as erro:
    anotar(numero, "o PyTorch esta instalado", False, str(erro))

numero = numero + 1
try:
    import transformers
    anotar(numero, "o Transformers esta instalado", True)
except Exception as erro:
    anotar(numero, "o Transformers esta instalado", False, str(erro))

numero = numero + 1
try:
    import streamlit
    anotar(numero, "o Streamlit esta instalado", True)
except Exception as erro:
    anotar(numero, "o Streamlit esta instalado", False, str(erro))

# ------------------------------------------------------------------
print()
print("=" * 64)
print("RESUMO:", len(certos), "certos,", len(problemas), "com problema")
print("=" * 64)

if len(problemas) == 0:
    print()
    print("Esta tudo no lugar. Pode ligar a API e o painel.")
else:
    print()
    print("Precisam de conserto:")
    for nome in problemas:
        print("  - " + nome)
    print()
    print("Mande esta lista inteira para o Claude.")
print()
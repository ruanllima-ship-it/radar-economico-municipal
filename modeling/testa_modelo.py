# testa_modelo.py
# Primeiro teste do modelo de linguagem do TP4, ainda fora da API.
# Ele baixa o modelo, carrega na memoria e resume uma noticia de verdade
# do proprio projeto, medindo quanto tempo cada etapa leva.
#
# Na primeira vez demora porque baixa quase 900 MB da internet.
# Nas proximas vezes o modelo ja fica guardado no cache da HuggingFace,
# dentro de C:\Users\ruanl\.cache\huggingface, fora da pasta do projeto.

import sys
import time
import subprocess

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


nome_do_modelo = "recogna-nlp/ptt5-base-summ"
caminho_das_noticias = "data/noticias_ibge.csv"


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
        kilobytes = int(texto)
        return round(kilobytes / (1024 * 1024), 1)
    except Exception:
        return None


print()
print("=" * 66)
print("  TESTE DO MODELO DE RESUMO EM PORTUGUES")
print("=" * 66)
print()

print("Modelo:", nome_do_modelo)
print("Nucleos que o torch vai usar:", torch.get_num_threads())
print("Memoria livre antes de comecar:", memoria_livre_gb(), "GB")
print()

# ------------------------------------------------------------------
# 1) Tokenizador
# ------------------------------------------------------------------
print("1) CARREGANDO O TOKENIZADOR")
print("   O tokenizador e quem transforma o texto em numeros.")
print("   Na primeira vez ele baixa alguns arquivos pequenos.")

relogio = time.time()

try:
    tokenizador = AutoTokenizer.from_pretrained(nome_do_modelo)
except Exception as erro:
    print("   NAO CARREGOU.")
    print("   Erro:", erro)
    sys.exit()

demorou = time.time() - relogio
print("   Carregou em", round(demorou, 1), "segundos.")
print()

# ------------------------------------------------------------------
# 2) Modelo
# ------------------------------------------------------------------
print("2) CARREGANDO O MODELO")
print("   Na primeira vez isso baixa cerca de 900 MB.")
print("   As barras de progresso que aparecerem sao do download.")

relogio = time.time()

try:
    modelo = AutoModelForSeq2SeqLM.from_pretrained(nome_do_modelo)
except Exception as erro:
    print("   NAO CARREGOU.")
    print("   Erro:", erro)
    sys.exit()

demorou = time.time() - relogio
print("   Carregou em", round(demorou, 1), "segundos.")

# avisa o modelo que e so para usar, nao para treinar
modelo.eval()

total_de_parametros = 0
for parametro in modelo.parameters():
    total_de_parametros = total_de_parametros + parametro.numel()

print("   Parametros do modelo:", total_de_parametros)
print("   Memoria livre depois de carregar:", memoria_livre_gb(), "GB")
print()

# ------------------------------------------------------------------
# 3) Uma noticia de verdade do projeto
# ------------------------------------------------------------------
print("3) LENDO UMA NOTICIA DO PROJETO")

tabela = pd.read_csv(caminho_das_noticias)

print("   Arquivo:", caminho_das_noticias)
print("   Linhas:", len(tabela))
print("   Colunas:", list(tabela.columns))

# descobre sozinho qual coluna guarda o texto longo da materia
primeira_linha = tabela.iloc[0]
coluna_do_texto = ""
maior_tamanho = 0

for coluna in tabela.columns:
    valor = primeira_linha[coluna]
    if isinstance(valor, str):
        if len(valor) > maior_tamanho:
            maior_tamanho = len(valor)
            coluna_do_texto = coluna

print("   Coluna de texto escolhida:", coluna_do_texto)

texto_da_noticia = primeira_linha[coluna_do_texto]
print("   Tamanho do texto:", len(texto_da_noticia), "caracteres")
print()
print("   COMECO DO TEXTO ORIGINAL:")
print("   " + texto_da_noticia[:400] + "...")
print()

# ------------------------------------------------------------------
# 4) Resumindo
# ------------------------------------------------------------------
print("4) RESUMINDO")
print("   O modelo le no maximo 512 pedacos por vez, entao o texto")
print("   e cortado nesse limite antes de entrar.")

entrada = tokenizador(
    texto_da_noticia,
    max_length=512,
    truncation=True,
    return_tensors="pt",
)

relogio = time.time()
resumo = ""

try:
    # no_grad economiza memoria: diz que nao vou treinar nada
    with torch.no_grad():
        saida = modelo.generate(
            entrada["input_ids"],
            max_length=256,
            min_length=40,
            num_beams=4,
            no_repeat_ngram_size=3,
            early_stopping=True,
        )
    resumo = tokenizador.decode(saida[0], skip_special_tokens=True)
    print("   Metodo usado: busca em feixe com 4 caminhos.")
except Exception as erro:
    print("   A busca em feixe nao funcionou.")
    print("   Erro:", erro)
    print("   Tentando de novo do jeito mais simples...")
    try:
        with torch.no_grad():
            saida = modelo.generate(
                entrada["input_ids"],
                max_length=256,
                min_length=40,
            )
        resumo = tokenizador.decode(saida[0], skip_special_tokens=True)
        print("   Metodo usado: geracao simples.")
    except Exception as outro_erro:
        print("   Tambem nao funcionou.")
        print("   Erro:", outro_erro)
        sys.exit()

demorou = time.time() - relogio

print("   Resumiu em", round(demorou, 1), "segundos.")
print("   Memoria livre no fim:", memoria_livre_gb(), "GB")
print()
print("   RESUMO GERADO PELO MODELO:")
print("   " + resumo)
print()

print("=" * 66)
print("  FIM. Copiar toda essa saida e mandar para analise.")
print("=" * 66)
print()
# afina_resumo.py
# Testa varias configuracoes de resumo no mesmo texto, para escolher a melhor.
# O modelo ja esta baixado, entao aqui ele so carrega do cache.

import sys
import time

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


nome_do_modelo = "recogna-nlp/ptt5-base-summ"
caminho_das_noticias = "data/noticias_ibge.csv"

# as quatro configuracoes que eu quero comparar
configuracoes = [
    {
        "nome": "A - como esta hoje",
        "limite_entrada": 512,
        "tamanho_maximo": 256,
        "tamanho_minimo": 40,
        "caminhos": 4,
        "peso_do_tamanho": 1.0,
    },
    {
        "nome": "B - sem piso minimo, resumo curto",
        "limite_entrada": 512,
        "tamanho_maximo": 160,
        "tamanho_minimo": 10,
        "caminhos": 5,
        "peso_do_tamanho": 1.0,
    },
    {
        "nome": "C - sem piso minimo, puxando para mais curto ainda",
        "limite_entrada": 512,
        "tamanho_maximo": 160,
        "tamanho_minimo": 10,
        "caminhos": 5,
        "peso_do_tamanho": 0.6,
    },
    {
        "nome": "D - lendo o dobro do texto de entrada",
        "limite_entrada": 1024,
        "tamanho_maximo": 160,
        "tamanho_minimo": 10,
        "caminhos": 5,
        "peso_do_tamanho": 1.0,
    },
]


def resumir(texto, configuracao):
    entrada = tokenizador(
        texto,
        max_length=configuracao["limite_entrada"],
        truncation=True,
        return_tensors="pt",
    )
    relogio = time.time()
    with torch.no_grad():
        saida = modelo.generate(
            entrada["input_ids"],
            max_length=configuracao["tamanho_maximo"],
            min_length=configuracao["tamanho_minimo"],
            num_beams=configuracao["caminhos"],
            length_penalty=configuracao["peso_do_tamanho"],
            no_repeat_ngram_size=3,
            early_stopping=True,
        )
    demorou = time.time() - relogio
    texto_resumido = tokenizador.decode(saida[0], skip_special_tokens=True)
    return texto_resumido, demorou


print()
print("=" * 70)
print("  COMPARANDO CONFIGURACOES DE RESUMO")
print("=" * 70)
print()

# ------------------------------------------------------------------
# Carregar (agora sem download, direto do cache)
# ------------------------------------------------------------------
print("CARREGANDO O MODELO DO CACHE (sem baixar nada)")

relogio = time.time()

try:
    tokenizador = AutoTokenizer.from_pretrained(nome_do_modelo)
    modelo = AutoModelForSeq2SeqLM.from_pretrained(nome_do_modelo)
except Exception as erro:
    print("   NAO CARREGOU.")
    print("   Erro:", erro)
    sys.exit()

modelo.eval()

demorou_carregar = time.time() - relogio
print("   Carregou em", round(demorou_carregar, 1), "segundos.")
print("   Esse e o tempo que a API vai levar no primeiro pedido.")
print()

# ------------------------------------------------------------------
# Ler as noticias
# ------------------------------------------------------------------
tabela = pd.read_csv(caminho_das_noticias)

# vou testar com duas materias diferentes, para nao decidir com uma so
indices_para_testar = [0, 7]

for indice in indices_para_testar:
    linha = tabela.iloc[indice]

    print("=" * 70)
    print("MATERIA", indice)
    print("=" * 70)
    print("Titulo:", linha["titulo"])
    print("Data:", linha["data"])
    print("Palavras no texto original:", linha["qtd_palavras"])
    print()
    print("RESUMO OFICIAL DO IBGE (para comparar):")
    print("   " + str(linha["resumo"]))
    print()

    texto_completo = linha["texto"]

    for configuracao in configuracoes:
        resumo_gerado, tempo = resumir(texto_completo, configuracao)
        print("-" * 70)
        print("CONFIGURACAO", configuracao["nome"])
        print("   Tempo:", round(tempo, 1), "segundos")
        print("   Palavras no resumo:", len(resumo_gerado.split()))
        print("   Texto:")
        print("   " + resumo_gerado)
        print()

    print()

print("=" * 70)
print("  FIM. Copiar toda essa saida e mandar para analise.")
print("=" * 70)
print()
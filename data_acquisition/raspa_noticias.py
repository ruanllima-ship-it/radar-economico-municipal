import os
from bs4 import BeautifulSoup
import pandas as pd

# o site do ibge tem protecao anti-robo (cloudflare) e devolve 403 pra scripts
# (ver espiar_pagina.py), entao as paginas foram salvas pelo navegador
# e aqui o beautiful soup extrai o conteudo delas
pasta_html = "data/html_ibge"


# funcao pra ler as etiquetas meta do html (titulo, data, resumo, link)
def pegar_meta(sopa, nome):
    tag = sopa.find("meta", attrs={"property": nome})
    if tag is None:
        tag = sopa.find("meta", attrs={"name": nome})
    if tag is None:
        return ""
    return tag.get("content", "")


noticias = []

lista_arquivos = os.listdir(pasta_html)
lista_arquivos.sort()

for nome_arquivo in lista_arquivos:

    if not nome_arquivo.endswith(".html") and not nome_arquivo.endswith(".htm"):
        continue

    print("lendo:", nome_arquivo)
    caminho = pasta_html + "/" + nome_arquivo
    arquivo = open(caminho, "r", encoding="utf-8", errors="ignore")
    html = arquivo.read()
    arquivo.close()

    sopa = BeautifulSoup(html, "html.parser")

    # se salvou a tela do cloudflare em vez da noticia, avisa e pula
    if sopa.title is not None and "Just a moment" in sopa.title.get_text():
        print("   esse arquivo e a tela de bloqueio, salve de novo pelo navegador")
        continue

    titulo = pegar_meta(sopa, "og:title")
    # o titulo vem com " | Agencia de Noticias" no final
    titulo = titulo.split(" | ")[0]

    if titulo == "":
        print("   nao achei titulo, pulando")
        continue

    data = pegar_meta(sopa, "article:published_time")
    data = data[0:10]

    resumo = pegar_meta(sopa, "og:description")
    link = pegar_meta(sopa, "og:url")

    # o texto da materia fica nas tags <p>
    # paragrafo muito curto costuma ser legenda ou menu, entao ignora
    paragrafos = []
    for tag_p in sopa.find_all("p"):
        texto_p = tag_p.get_text(" ", strip=True)
        # pula o aviso do site e a linha de autores, que nao sao noticia
        if "instabilidade no momento" in texto_p:
            continue
        if texto_p.startswith("Editoria"):
            continue
        if len(texto_p) >= 60 and "cookies" not in texto_p:
            paragrafos.append(texto_p)
    texto = " ".join(paragrafos)

    if "/releases/" in link:
        tipo = "release"
    else:
        tipo = "noticia"

    noticia = {
        "data": data,
        "tipo": tipo,
        "titulo": titulo,
        "resumo": resumo,
        "qtd_paragrafos": len(paragrafos),
        "qtd_palavras": len(texto.split()),
        "link": link,
        "texto": texto,
    }
    noticias.append(noticia)


if len(noticias) == 0:
    print("")
    print("nenhuma noticia lida, confira os arquivos da pasta", pasta_html)
else:
    # salvando em csv e em txt dentro da pasta data
    tabela = pd.DataFrame(noticias)
    tabela = tabela.sort_values("data")
    tabela.to_csv("data/noticias_ibge.csv", index=False)

    arquivo = open("data/noticias_ibge.txt", "w", encoding="utf-8")
    for indice, linha in tabela.iterrows():
        arquivo.write(linha["titulo"] + "\n")
        arquivo.write(linha["data"] + " | " + linha["link"] + "\n\n")
        arquivo.write(linha["texto"] + "\n")
        arquivo.write("\n" + "=" * 60 + "\n\n")
    arquivo.close()

    # resumo pra conferir
    print("")
    print("========== RESUMO ==========")
    print("noticias salvas:", len(tabela))
    print("")
    for indice, linha in tabela.iterrows():
        print(linha["data"], "|", linha["tipo"], "|", linha["qtd_paragrafos"], "par |", linha["qtd_palavras"], "palavras |", linha["titulo"])
    print("")
    print("comeco do texto da noticia mais recente:")
    print(tabela.iloc[-1]["texto"][0:400])
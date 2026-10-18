import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

# o site da agencia do ibge e montado por javascript e recusa acesso de
# script simples (erro 403, ver espiar_pagina.py). por isso aqui o selenium
# abre um chrome de verdade e navega pelas paginas, e o beautiful soup
# extrai o conteudo do html que o navegador montou

site = "https://agenciadenoticias.ibge.gov.br"
endereco_busca = site + "/busca-avancada.html?produto=9088"


# le as etiquetas meta do html
def pegar_meta(sopa, nome):
    tag = sopa.find("meta", attrs={"property": nome})
    if tag is None:
        tag = sopa.find("meta", attrs={"name": nome})
    if tag is None:
        return ""
    return tag.get("content", "")


# junta os paragrafos da materia
def pegar_paragrafos(sopa):
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
    return paragrafos


opcoes = webdriver.ChromeOptions()
opcoes.add_argument("--window-size=1280,900")

print("abrindo o chrome...")
navegador = webdriver.Chrome(options=opcoes)


# 1. abrindo a busca da agencia filtrada pelo pib dos municipios
print("abrindo a busca da agencia...")
navegador.get(endereco_busca)
time.sleep(15)

sopa_busca = BeautifulSoup(navegador.page_source, "html.parser")

lista = []
for item in sopa_busca.find_all("div", class_="lista-noticias__item"):

    tag_tipo = item.find("p", class_="tipo")
    if tag_tipo is None:
        continue
    tipo = tag_tipo.get_text(strip=True).upper()

    # a busca traz foto, audio e documento junto, queremos so texto
    if "NOT" not in tipo and "RELEASE" not in tipo:
        continue

    tag_link = item.find("a")
    link = tag_link.get("href")
    if link.startswith("/"):
        link = site + link

    # a mesma materia pode aparecer repetida na busca
    ja_tem = False
    for anotado in lista:
        if anotado["link"] == link:
            ja_tem = True
    if ja_tem:
        continue

    if "RELEASE" in tipo:
        tipo_curto = "release"
    else:
        tipo_curto = "noticia"

    lista.append({"link": link, "tipo": tipo_curto})

print("materias encontradas na busca:", len(lista))
print("")


# 2. entrando em cada materia e pegando o conteudo
noticias = []

for materia in lista:
    print("lendo:", materia["link"][-60:])
    navegador.get(materia["link"])
    time.sleep(3)

    sopa = BeautifulSoup(navegador.page_source, "html.parser")

    titulo = pegar_meta(sopa, "og:title")
    titulo = titulo.split(" | ")[0]

    if titulo == "":
        print("   nao achei titulo, pulando")
        continue

    data = pegar_meta(sopa, "article:published_time")
    data = data[0:10]

    resumo = pegar_meta(sopa, "og:description")

    paragrafos = pegar_paragrafos(sopa)
    texto = " ".join(paragrafos)

    noticia = {
        "data": data,
        "tipo": materia["tipo"],
        "titulo": titulo,
        "resumo": resumo,
        "qtd_paragrafos": len(paragrafos),
        "qtd_palavras": len(texto.split()),
        "link": materia["link"],
        "texto": texto,
    }
    noticias.append(noticia)

print("")
print("fechando o navegador...")
navegador.quit()


# 3. salvando em csv e txt dentro da pasta data
if len(noticias) == 0:
    print("nenhuma materia lida, confira se a busca abriu")
else:
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

    print("")
    print("========== RESUMO ==========")
    print("materias salvas:", len(tabela))
    print("")
    for indice, linha in tabela.iterrows():
        print(linha["data"], "|", linha["tipo"], "|", linha["qtd_palavras"], "palavras |", linha["titulo"][0:60])
    print("")
    print("total de palavras:", tabela["qtd_palavras"].sum())
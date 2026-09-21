import requests

cabecalho = {"User-Agent": "Mozilla/5.0 (projeto academico radar economico municipal)"}

# 1. a pagina do produto no site do ibge
endereco = "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html"
resposta = requests.get(endereco, headers=cabecalho, timeout=60)

print("========== PAGINA DO PRODUTO ==========")
print("status:", resposta.status_code)
print("tamanho do html:", len(resposta.text))
print("tem o titulo da secao de noticias?", "Releases" in resposta.text)
print("tem o endereco da agencia?", "agenciadenoticias" in resposta.text)
print("tem o numero da noticia de 2023 (45548)?", "45548" in resposta.text)
print("")

# salvando o html pra gente olhar por dentro
arquivo = open("data/pagina_produto_teste.html", "w", encoding="utf-8")
arquivo.write(resposta.text)
arquivo.close()


# 2. a pagina de busca da agencia, filtrada pelo pib dos municipios
endereco = "https://agenciadenoticias.ibge.gov.br/busca-avancada.html?produto=9088"
resposta = requests.get(endereco, headers=cabecalho, timeout=60)

print("========== BUSCA DA AGENCIA ==========")
print("status:", resposta.status_code)
print("tamanho do html:", len(resposta.text))
print("tem o numero da noticia de 2023 (45548)?", "45548" in resposta.text)
print("quantas vezes aparece /noticias/:", resposta.text.count("/noticias/"))
print("")

arquivo = open("data/pagina_busca_teste.html", "w", encoding="utf-8")
arquivo.write(resposta.text)
arquivo.close()

print("arquivos salvos na pasta data")
import requests

# 1. quais anos a tabela de estimativas tem
resposta = requests.get("https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos")
lista = resposta.json()
print("========== ANOS DA TABELA 6579 ==========")
for periodo in lista:
    print(periodo["id"], end="  ")
print("")
print("")

# 2. olhando a tabela 202 do censo
resposta = requests.get("https://servicodados.ibge.gov.br/api/v3/agregados/202/metadados")
dados = resposta.json()
print("========== TABELA 202 ==========")
print(dados["nome"])
print(dados["periodicidade"])
print("niveis:", dados["nivelTerritorial"])
for variavel in dados["variaveis"]:
    print("   variavel", variavel["id"], "|", variavel["nome"])
print("")

resposta = requests.get("https://servicodados.ibge.gov.br/api/v3/agregados/202/periodos")
lista = resposta.json()
print("anos da tabela 202:")
for periodo in lista:
    print(periodo["id"], end="  ")
print("")
print("")

# 3. teste com o rio de janeiro na tabela 202 em 2010
print("========== TESTE RIO 2010 NA TABELA 202 ==========")
resposta = requests.get("https://apisidra.ibge.gov.br/values/t/202/n6/3304557/v/93/p/2010")
linhas = resposta.json()
for linha in linhas:
    print(linha)
print("")

# 4. teste com o rio de janeiro na tabela 6579 em 2024
print("========== TESTE RIO 2024 NA TABELA 6579 ==========")
resposta = requests.get("https://apisidra.ibge.gov.br/values/t/6579/n6/3304557/v/9324/p/2024")
linhas = resposta.json()
for linha in linhas:
    print(linha)
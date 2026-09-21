import requests

# 1. perguntando para a API quais variaveis a tabela 5938 tem
endereco = "https://servicodados.ibge.gov.br/api/v3/agregados/5938/metadados"
resposta = requests.get(endereco)
dados = resposta.json()

print("========== NOME DA TABELA ==========")
print(dados["nome"])
print("")

print("========== PERIODO ==========")
print(dados["periodicidade"])
print("")

print("========== VARIAVEIS ==========")
for variavel in dados["variaveis"]:
    print(variavel["id"], "|", variavel["nome"], "|", variavel["unidade"])
print("")

# 2. perguntando quais anos existem
endereco = "https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos"
resposta = requests.get(endereco)
lista_anos = resposta.json()

print("========== ANOS DISPONIVEIS ==========")
for ano in lista_anos:
    print(ano["id"], end="  ")
print("")
print("")

# 3. testando um municipio so (Rio de Janeiro) em 2021 e 2023
# pra ver se os setores aparecem mesmo so ate 2021
endereco = "https://apisidra.ibge.gov.br/values/t/5938/n6/3304557/v/all/p/2021,2023"
resposta = requests.get(endereco)
linhas = resposta.json()

print("========== TESTE RIO DE JANEIRO ==========")
print(linhas[1]["D1N"])
contador = 0
for linha in linhas:
    if contador > 0:
        print(linha["D3N"], "|", linha["D2C"], "|", linha["D2N"], "|", linha["V"])
    contador = contador + 1
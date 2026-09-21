import requests

# pegando a lista de todas as tabelas do ibge
endereco = "https://servicodados.ibge.gov.br/api/v3/agregados"
resposta = requests.get(endereco)
pesquisas = resposta.json()

print("========== TABELAS DE POPULACAO ==========")
for pesquisa in pesquisas:
    nome_pesquisa = pesquisa["nome"]
    if "Estimativas de Popula" in nome_pesquisa or "Censo Demogr" in nome_pesquisa:
        for tabela in pesquisa["agregados"]:
            nome_tabela = tabela["nome"]
            if "opula" in nome_tabela and "residente" in nome_tabela:
                print(tabela["id"], "|", nome_pesquisa, "|", nome_tabela)
print("")


# olhando de perto a tabela das estimativas
def espiar(numero):
    endereco = "https://servicodados.ibge.gov.br/api/v3/agregados/" + numero + "/metadados"
    try:
        resposta = requests.get(endereco)
        dados = resposta.json()
        print("========== TABELA", numero, "==========")
        print(dados["nome"])
        print(dados["periodicidade"])
        for variavel in dados["variaveis"]:
            print("   variavel", variavel["id"], "|", variavel["nome"], "|", variavel["unidade"])
        print("")
    except Exception as erro:
        print("tabela", numero, "deu erro:", erro)
        print("")


espiar("6579")
espiar("4709")
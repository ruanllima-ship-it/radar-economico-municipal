import requests
import pandas as pd
import time


# funcao que baixa um endereco da api, tentando ate 3 vezes
def baixar(endereco):
    tentativa = 1
    while tentativa <= 3:
        try:
            resposta = requests.get(endereco, timeout=120)
            lista = resposta.json()
            tabela = pd.DataFrame(lista)
            # a primeira linha e o cabecalho
            tabela = tabela.drop(0)
            tabela = tabela[["D1C", "D1N", "D3N", "V"]]
            tabela.columns = ["codigo", "municipio", "ano", "populacao"]
            return tabela
        except Exception as erro:
            print("   deu problema na tentativa", tentativa, "-", erro)
            tentativa = tentativa + 1
            time.sleep(5)
    return None


# perguntando quais anos a tabela de estimativas tem de verdade
resposta = requests.get("https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos")
lista_periodos = resposta.json()
anos_estimativa = []
for periodo in lista_periodos:
    anos_estimativa.append(int(periodo["id"]))

print("anos que a tabela 6579 tem:", anos_estimativa)
print("")

pedacos = []
anos_sem_dado = []

# vai ate 2024 porque o 2024 serve pra calcular o 2023 depois
for ano in range(2010, 2025):

    if ano == 2010:
        print("baixando censo 2010")
        endereco = "https://apisidra.ibge.gov.br/values/t/202/n6/all/v/93/p/2010"
        fonte = "censo 2010"
    elif ano == 2022:
        print("baixando censo 2022")
        endereco = "https://apisidra.ibge.gov.br/values/t/4709/n6/all/v/93/p/2022"
        fonte = "censo 2022"
    elif ano in anos_estimativa:
        print("baixando estimativa", ano)
        endereco = "https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/" + str(ano)
        fonte = "estimativa"
    else:
        print("SEM FONTE para", ano)
        anos_sem_dado.append(ano)
        continue

    tabela = baixar(endereco)

    if tabela is None:
        print("   NAO CONSEGUIU", ano)
        anos_sem_dado.append(ano)
    else:
        tabela["fonte"] = fonte
        pedacos.append(tabela)

    time.sleep(1)


# juntando tudo
base = pd.concat(pedacos)
base.to_csv("data_acquisition/raw_data/populacao_municipios_2010_2024.csv", index=False)

print("")
print("========== RESUMO ==========")
print("total de linhas:", len(base))
print("")
print("linhas por ano e fonte:")
print(base.groupby(["ano", "fonte"]).size())
print("")
print("linhas sem numero (... ou -):")
sem_numero = base[(base["populacao"] == "...") | (base["populacao"] == "-")]
print(len(sem_numero))
print("")
print("anos sem populacao:", anos_sem_dado)
import requests
import pandas as pd

endereco = "https://apisidra.ibge.gov.br/values/t/5938/n6/all/v/37/p/2021"

resposta = requests.get(endereco)
lista = resposta.json()

tabela = pd.DataFrame(lista)
tabela = tabela.drop(0)

tabela = tabela[["D1C", "D1N", "V"]]
tabela.columns = ["codigo", "municipio", "pib_mil_reais"]

tabela["pib_mil_reais"] = pd.to_numeric(tabela["pib_mil_reais"], errors="coerce")

tabela.to_csv("data_acquisition/raw_data/pib_2021.csv", index=False)

amostra = tabela.head(20)
amostra.to_csv("data_acquisition/cleaned_data/amostra_pib.csv", index=False)

print("deu certo, salvou", len(tabela), "municipios")

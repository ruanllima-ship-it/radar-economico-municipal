import requests
import pandas as pd
import time

# codigos conferidos no espiar_sidra.py
variaveis = {
    "37": "pib",
    "498": "vab_total",
    "513": "vab_agropecuaria",
    "517": "vab_industria",
    "6575": "vab_servicos",
    "525": "vab_adm_publica",
}


# funcao que baixa um ano e uma variavel
# tenta ate 3 vezes se a api der problema
def baixar(ano, codigo_variavel):
    endereco = "https://apisidra.ibge.gov.br/values/t/5938/n6/all/v/" + codigo_variavel + "/p/" + str(ano)
    tentativa = 1
    while tentativa <= 3:
        try:
            resposta = requests.get(endereco, timeout=120)
            lista = resposta.json()
            tabela = pd.DataFrame(lista)
            # a primeira linha e o cabecalho, nao e dado
            tabela = tabela.drop(0)
            tabela = tabela[["D1C", "D1N", "D3N", "D2C", "V"]]
            tabela.columns = ["codigo", "municipio", "ano", "codigo_variavel", "valor"]
            return tabela
        except Exception as erro:
            print("   deu problema na tentativa", tentativa, "-", erro)
            tentativa = tentativa + 1
            time.sleep(5)
    return None


pedacos = []
falhas = []

for ano in range(2010, 2024):
    for codigo_variavel in variaveis:

        # 2022 e 2023 so tem pib, o resto vem vazio
        if ano >= 2022 and codigo_variavel != "37":
            continue

        nome_variavel = variaveis[codigo_variavel]
        print("baixando", ano, nome_variavel)

        tabela = baixar(ano, codigo_variavel)

        if tabela is None:
            print("   NAO CONSEGUIU:", ano, nome_variavel)
            falhas.append(str(ano) + " " + nome_variavel)
        else:
            tabela["variavel"] = nome_variavel
            pedacos.append(tabela)

        # pausa pra nao sobrecarregar o site do ibge
        time.sleep(1)


# juntando tudo numa tabela so
base = pd.concat(pedacos)
base.to_csv("data_acquisition/raw_data/pib_municipios_2010_2023.csv", index=False)

print("")
print("========== RESUMO ==========")
print("total de linhas:", len(base))
print("")
print("linhas por ano e variavel:")
contagem = base.groupby(["ano", "variavel"]).size()
print(contagem)
print("")
print("quantas linhas vieram com ... (sem dado):")
sem_dado = base[base["valor"] == "..."]
print(len(sem_dado))
print("")
if len(falhas) == 0:
    print("nenhuma falha, tudo baixado")
else:
    print("FALHAS:", falhas)
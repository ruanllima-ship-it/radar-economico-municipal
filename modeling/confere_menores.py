import pandas as pd

base = pd.read_csv("data_acquisition/cleaned_data/indicadores_municipios.csv")

# os 5 menores pib per capita de 2023, segundo a noticia do ibge:
# Manari (PE) 7.201,70 | Nina Rodrigues (MA) 7.701,32 | Matoes do Norte (MA) 7.722,89
# Cajapio (MA) 8.079,74 | Sao Joao Batista (MA) 8.246,12

ano_2023 = base[base["ano"] == 2023]
ano_2023 = ano_2023.sort_values("pib_per_capita")
menores = ano_2023.head(8)

print("========== 8 MENORES PIB PER CAPITA 2023 (nosso calculo) ==========")
for indice, linha in menores.iterrows():
    print(linha["municipio"], linha["uf"], "| pib mil R$", linha["pib"], "| populacao", linha["populacao"], "| per capita R$", round(linha["pib_per_capita"], 2))

print("")
print("========== MANARI NOS ULTIMOS ANOS ==========")
manari = base[(base["municipio"] == "Manari") & (base["uf"] == "PE")]
manari = manari[manari["ano"] >= 2019]
for indice, linha in manari.iterrows():
    print(linha["ano"], "| pib mil R$", linha["pib"], "| populacao", linha["populacao"], "| per capita R$", round(linha["pib_per_capita"], 2))
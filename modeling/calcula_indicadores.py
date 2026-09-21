import pandas as pd

# =========================================================
# 1. lendo os dados brutos
# =========================================================
print("lendo os arquivos brutos...")
pib_bruto = pd.read_csv("data_acquisition/raw_data/pib_municipios_2010_2023.csv")
pop_bruta = pd.read_csv("data_acquisition/raw_data/populacao_municipios_2010_2024.csv")

# os valores vem como texto e os sem dado vem como "..." ou "-"
pib_bruto["valor"] = pd.to_numeric(pib_bruto["valor"], errors="coerce")
pop_bruta["populacao"] = pd.to_numeric(pop_bruta["populacao"], errors="coerce")


# =========================================================
# 2. virando o pib de formato longo pra largo
# uma linha por municipio e ano, uma coluna por variavel
# =========================================================
base = pib_bruto.pivot(index=["codigo", "ano"], columns="variavel", values="valor")
base = base.reset_index()
base.columns.name = None


# =========================================================
# 3. nome limpo, uf, regiao e capital
# =========================================================

# o nome vem ora como "Rio de Janeiro (RJ)", ora como "Ariquemes - RO"
def limpa_nome(nome):
    nome = str(nome).strip()
    if nome.endswith(")") and len(nome) > 5 and nome[-5] == "(":
        return nome[:-5].strip()
    if len(nome) > 5 and nome[-5:-2] == " - ":
        return nome[:-5].strip()
    return nome


# pega o nome de 2023, que tem todos os municipios
nomes = pib_bruto[pib_bruto["ano"] == 2023][["codigo", "municipio"]]
nomes = nomes.drop_duplicates("codigo").copy()
lista_nomes = []
for nome in nomes["municipio"]:
    lista_nomes.append(limpa_nome(nome))
nomes["municipio"] = lista_nomes

base = base.merge(nomes, on="codigo", how="left")

# os 2 primeiros digitos do codigo sao a uf, o primeiro e a regiao
siglas_uf = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
}
nomes_regiao = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste"}

# codigos ibge das 27 capitais
capitais = [
    1100205, 1200401, 1302603, 1400100, 1501402, 1600303, 1721000,
    2111300, 2211001, 2304400, 2408102, 2507507, 2611606, 2704302, 2800308, 2927408,
    3106200, 3205309, 3304557, 3550308,
    4106902, 4205407, 4314902,
    5002704, 5103403, 5208707, 5300108,
]

lista_uf = []
lista_regiao = []
lista_capital = []
for codigo in base["codigo"]:
    lista_uf.append(siglas_uf[codigo // 100000])
    lista_regiao.append(nomes_regiao[codigo // 1000000])
    if codigo in capitais:
        lista_capital.append("sim")
    else:
        lista_capital.append("nao")

base["uf"] = lista_uf
base["regiao"] = lista_regiao
base["capital"] = lista_capital


# =========================================================
# 4. juntando a populacao
# =========================================================
pop = pop_bruta[["codigo", "ano", "populacao"]].copy()
pop = pop[pop["ano"] <= 2022]

# o ibge usa a populacao do censo 2022 tambem pro pib per capita de 2023
pop_2023 = pop[pop["ano"] == 2022].copy()
pop_2023["ano"] = 2023
pop = pd.concat([pop, pop_2023])

# conferindo codigos que estao na populacao mas nao no pib
codigos_pib = set(base["codigo"])
codigos_pop = set(pop["codigo"])
sobrando = codigos_pop - codigos_pib

print("")
print("========== MUNICIPIOS SO NA POPULACAO ==========")
for codigo in sobrando:
    linhas = pop_bruta[pop_bruta["codigo"] == codigo]
    print(codigo, "|", linhas.iloc[0]["municipio"], "| aparece em", len(linhas), "anos")

base = base.merge(pop, on=["codigo", "ano"], how="left")


# =========================================================
# 5. os sete indicadores
# =========================================================

# indicador 1: participacao no pib do brasil (%)
base["pib_brasil"] = base.groupby("ano")["pib"].transform("sum")
base["participacao_pib"] = base["pib"] / base["pib_brasil"] * 100

# indicador 2: pib per capita em reais (o pib vem em mil reais)
base["pib_per_capita"] = base["pib"] * 1000 / base["populacao"]

# indicador 3: razao de riqueza (acima de 1 = mais rico que a media do brasil)
soma_pib = base.groupby("ano")["pib"].sum()
soma_pop = base.groupby("ano")["populacao"].sum()
per_capita_brasil = soma_pib * 1000 / soma_pop
base["pib_per_capita_brasil"] = base["ano"].map(per_capita_brasil)
base["razao_riqueza"] = base["pib_per_capita"] / base["pib_per_capita_brasil"]

# indicador 4: curva de concentracao
# ordena do maior pro menor pib dentro de cada ano e vai somando
base = base.sort_values(["ano", "pib"], ascending=[True, False])
base["posicao_pib"] = base.groupby("ano").cumcount() + 1
base["participacao_acumulada"] = base.groupby("ano")["participacao_pib"].cumsum()

# participacao de cada setor no valor adicionado (so existe ate 2021)
fracao_agro = base["vab_agropecuaria"] / base["vab_total"]
fracao_industria = base["vab_industria"] / base["vab_total"]
fracao_servicos = base["vab_servicos"] / base["vab_total"]
fracao_adm = base["vab_adm_publica"] / base["vab_total"]

# indicador 5: diversificacao (hhi), vai de 0,25 (bem diversificado) a 1 (um setor so)
base["hhi"] = fracao_agro ** 2 + fracao_industria ** 2 + fracao_servicos ** 2 + fracao_adm ** 2

# indicador 6: dependencia da administracao publica (%)
base["dependencia_adm"] = fracao_adm * 100

# guardando as participacoes em % pra mostrar no app
base["part_agropecuaria"] = fracao_agro * 100
base["part_industria"] = fracao_industria * 100
base["part_servicos"] = fracao_servicos * 100
base["part_adm_publica"] = fracao_adm * 100

# indicador 7: perfil economico (setor com maior valor adicionado)
lista_perfil = []
for agro, industria, servicos, adm in zip(base["vab_agropecuaria"], base["vab_industria"], base["vab_servicos"], base["vab_adm_publica"]):
    if pd.isna(agro) or pd.isna(industria) or pd.isna(servicos) or pd.isna(adm):
        lista_perfil.append(None)
    else:
        maior = max(agro, industria, servicos, adm)
        if maior == agro:
            lista_perfil.append("Agropecuária")
        elif maior == industria:
            lista_perfil.append("Indústria")
        elif maior == servicos:
            lista_perfil.append("Serviços")
        else:
            lista_perfil.append("Administração pública")
base["perfil"] = lista_perfil


# =========================================================
# 6. resumo do brasil por ano
# =========================================================
linhas_resumo = []
for ano in sorted(base["ano"].unique()):
    do_ano = base[base["ano"] == ano]

    # quantos municipios precisa somar pra chegar em metade do pib
    antes_da_metade = do_ano[do_ano["participacao_acumulada"] < 50]
    municipios_metade = len(antes_da_metade) + 1

    capitais_do_ano = do_ano[do_ano["capital"] == "sim"]
    dez_maiores = do_ano[do_ano["posicao_pib"] <= 10]

    linha = {
        "ano": ano,
        "pib_brasil_mil_reais": do_ano["pib"].sum(),
        "populacao_brasil": do_ano["populacao"].sum(),
        "pib_per_capita_brasil": per_capita_brasil[ano],
        "municipios_metade_pib": municipios_metade,
        "participacao_capitais": capitais_do_ano["participacao_pib"].sum(),
        "participacao_10_maiores": dez_maiores["participacao_pib"].sum(),
    }
    linhas_resumo.append(linha)

resumo_brasil = pd.DataFrame(linhas_resumo)


# =========================================================
# 7. salvando
# =========================================================
colunas = [
    "codigo", "municipio", "uf", "regiao", "capital", "ano",
    "pib", "populacao", "participacao_pib", "pib_per_capita", "pib_per_capita_brasil",
    "razao_riqueza", "posicao_pib", "participacao_acumulada",
    "vab_total", "vab_agropecuaria", "vab_industria", "vab_servicos", "vab_adm_publica",
    "part_agropecuaria", "part_industria", "part_servicos", "part_adm_publica",
    "hhi", "dependencia_adm", "perfil",
]
base = base[colunas]
base = base.sort_values(["ano", "codigo"])
base = base.round(4)
base.to_csv("data_acquisition/cleaned_data/indicadores_municipios.csv", index=False)

resumo_brasil = resumo_brasil.round(4)
resumo_brasil.to_csv("data_acquisition/cleaned_data/resumo_brasil.csv", index=False)


# =========================================================
# 8. conferencia contra os numeros oficiais do ibge
# (noticia de 19/12/2025 sobre o pib dos municipios 2023)
# =========================================================
def mostra_municipio(nome, uf, ano):
    linha = base[(base["municipio"] == nome) & (base["uf"] == uf) & (base["ano"] == ano)]
    if len(linha) == 0:
        print("   nao achei", nome)
        return
    linha = linha.iloc[0]
    print("  ", nome, uf, ano, "| per capita R$", round(linha["pib_per_capita"], 2), "| razao", round(linha["razao_riqueza"], 2))


resumo_2022 = resumo_brasil[resumo_brasil["ano"] == 2022].iloc[0]
resumo_2023 = resumo_brasil[resumo_brasil["ano"] == 2023].iloc[0]

print("")
print("========== CONFERENCIA COM O IBGE ==========")
print("capitais achadas em 2023:", len(base[(base["capital"] == "sim") & (base["ano"] == 2023)]), "(tem que ser 27)")
print("capitais 2022:", round(resumo_2022["participacao_capitais"], 1), "% | ibge: 27,5%")
print("capitais 2023:", round(resumo_2023["participacao_capitais"], 1), "% | ibge: 28,3%")
print("10 maiores 2023:", round(resumo_2023["participacao_10_maiores"], 1), "% | ibge: 24,5%")
print("per capita brasil 2023: R$", round(resumo_2023["pib_per_capita_brasil"], 2), "| ibge: R$ 53,9 mil")
print("")
print("municipios (ibge: Saquarema R$ 722,4 mil | Brasilia R$ 129,8 mil e razao 2,41 | Manari R$ 7.201,70)")
mostra_municipio("Saquarema", "RJ", 2023)
mostra_municipio("Brasília", "DF", 2023)
mostra_municipio("Manari", "PE", 2023)

print("")
print("========== QUALIDADE DOS DADOS ==========")
print("linhas:", len(base), "| municipios:", base["codigo"].nunique(), "| anos:", base["ano"].min(), "a", base["ano"].max())
print("pib vazio:", base["pib"].isna().sum(), "| populacao vazia:", base["populacao"].isna().sum())
sem_pib_2010 = base[(base["ano"] == 2010) & (base["pib"].isna())]
print("municipios sem pib em 2010:", list(sem_pib_2010["municipio"] + " (" + sem_pib_2010["uf"] + ")"))

print("")
print("========== RESUMO DO BRASIL ==========")
print(resumo_brasil[["ano", "municipios_metade_pib", "participacao_capitais", "participacao_10_maiores"]])

print("")
print("perfis em 2021:")
print(base[base["ano"] == 2021]["perfil"].value_counts())
import time
import streamlit as st
import pandas as pd
from wordcloud import WordCloud

st.set_page_config(page_title="Radar Econômico Municipal", layout="wide")


# =========================================================
# funcoes de carregar dados (com cache)
# o @st.cache_data faz o arquivo ser lido uma vez so
# nos cliques seguintes o streamlit usa o que ja esta na memoria
# =========================================================
@st.cache_data
def carregar_indicadores():
    tabela = pd.read_csv("data_acquisition/cleaned_data/indicadores_municipios.csv")
    return tabela


@st.cache_data
def carregar_resumo():
    tabela = pd.read_csv("data_acquisition/cleaned_data/resumo_brasil.csv")
    return tabela


@st.cache_data
def carregar_noticias():
    tabela = pd.read_csv("data/noticias_ibge.csv")
    return tabela


@st.cache_data
def carregar_populacao_2024():
    tabela = pd.read_csv("data_acquisition/raw_data/populacao_municipios_2010_2024.csv")
    tabela = tabela[tabela["ano"] == 2024]
    tabela = tabela[["codigo", "populacao"]]
    tabela = tabela.rename(columns={"populacao": "populacao_estimada_2024"})
    return tabela


# palavras que nao dizem nada sobre o assunto e ficam fora da nuvem
palavras_fora = {
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "um", "uma", "uns", "umas",
    "o", "a", "os", "as", "e", "é", "que", "com", "por", "para", "pelo", "pela", "pelos", "pelas",
    "se", "ao", "aos", "à", "às", "mais", "menos", "como", "entre", "sobre", "também", "já",
    "foi", "foram", "ser", "são", "era", "eram", "está", "estão", "estava", "esse", "essa",
    "esses", "essas", "este", "esta", "estes", "estas", "isso", "isto", "seu", "sua", "seus",
    "suas", "ele", "ela", "eles", "elas", "não", "sim", "ou", "mas", "até", "após", "desde",
    "quando", "onde", "cada", "todos", "todas", "todo", "toda", "outro", "outra", "outros",
    "outras", "mesmo", "mesma", "ainda", "segundo", "parte", "apenas", "vez", "vezes", "cerca",
    "ter", "tem", "têm", "teve", "tinha", "tinham", "qual", "quais", "bem", "muito", "muita",
    "pode", "podem", "sendo", "sido", "há", "pois", "assim", "lhe", "sem", "sob", "nem",
    "contra", "durante", "enquanto", "porque", "ponto", "percentual", "p.p", "ano", "anos",
    "seguido", "seguida", "respectivamente", "caso", "maior", "menor", "maiores", "menores",
}


@st.cache_data
def gerar_nuvem(texto):
    nuvem = WordCloud(
        width=1000,
        height=450,
        background_color="white",
        colormap="viridis",
        stopwords=palavras_fora,
        collocations=False,
        min_word_length=3,
        max_words=100,
    )
    nuvem.generate(texto)
    return nuvem.to_array()


@st.cache_data
def contar_palavras(texto):
    contador = WordCloud(stopwords=palavras_fora, collocations=False, min_word_length=3)
    frequencias = contador.process_text(texto)
    tabela = pd.DataFrame({"palavra": list(frequencias.keys()), "vezes": list(frequencias.values())})
    tabela = tabela.sort_values("vezes", ascending=False)
    return tabela


# =========================================================
# funcoes pequenas de formatacao (numero no jeito brasileiro)
# =========================================================
def formata_numero(valor, casas=0):
    if pd.isna(valor):
        return "sem dado"
    texto = f"{valor:,.{casas}f}"
    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")
    return texto


def formata_pib(valor_mil_reais):
    # o pib vem em mil reais
    if pd.isna(valor_mil_reais):
        return "sem dado"
    if valor_mil_reais >= 1000000:
        return "R$ " + formata_numero(valor_mil_reais / 1000000, 1) + " bi"
    return "R$ " + formata_numero(valor_mil_reais / 1000, 1) + " mi"


# le o csv que o usuario subir, aceitando virgula ou ponto e virgula
def ler_csv_usuario(arquivo):
    try:
        tabela = pd.read_csv(arquivo)
    except UnicodeDecodeError:
        arquivo.seek(0)
        tabela = pd.read_csv(arquivo, encoding="latin-1")

    # se veio tudo numa coluna so, o separador era ponto e virgula (padrao do excel brasileiro)
    if len(tabela.columns) == 1:
        arquivo.seek(0)
        try:
            tabela = pd.read_csv(arquivo, sep=";", decimal=",")
        except UnicodeDecodeError:
            arquivo.seek(0)
            tabela = pd.read_csv(arquivo, sep=";", decimal=",", encoding="latin-1")
    return tabela


# =========================================================
# carregando tudo e medindo o tempo
# =========================================================
inicio = time.perf_counter()
indicadores = carregar_indicadores()
resumo = carregar_resumo()
noticias = carregar_noticias()
populacao_2024 = carregar_populacao_2024()
tempo_carga = time.perf_counter() - inicio


# =========================================================
# estado de sessao: coisas que o app lembra enquanto a pessoa navega
# =========================================================
if "comparacao" not in st.session_state:
    st.session_state["comparacao"] = []
if "dados_usuario" not in st.session_state:
    st.session_state["dados_usuario"] = None
if "nome_arquivo_usuario" not in st.session_state:
    st.session_state["nome_arquivo_usuario"] = ""
if "consultas" not in st.session_state:
    st.session_state["consultas"] = 0
if "ultimo_municipio" not in st.session_state:
    st.session_state["ultimo_municipio"] = None


# =========================================================
# barra lateral com os filtros
# =========================================================
st.sidebar.title("Filtros")

lista_anos = sorted(indicadores["ano"].unique(), reverse=True)
ano = st.sidebar.selectbox("Ano", lista_anos, key="filtro_ano")

lista_ufs = ["Brasil"] + sorted(indicadores["uf"].unique())
uf = st.sidebar.selectbox("Estado", lista_ufs, key="filtro_uf")

do_ano = indicadores[indicadores["ano"] == ano]
if uf == "Brasil":
    recorte = do_ano
else:
    recorte = do_ano[do_ano["uf"] == uf]

# lista de municipios no formato "Nome (UF)"
recorte_ordenado = recorte.sort_values("municipio")
opcoes_municipio = []
codigo_da_opcao = {}
for nome, sigla, codigo in zip(recorte_ordenado["municipio"], recorte_ordenado["uf"], recorte_ordenado["codigo"]):
    opcao = nome + " (" + sigla + ")"
    opcoes_municipio.append(opcao)
    codigo_da_opcao[opcao] = codigo

# comeca mostrando o municipio de maior pib do recorte
maior = recorte.sort_values("pib").iloc[-1]
opcao_maior = maior["municipio"] + " (" + maior["uf"] + ")"
indice_padrao = opcoes_municipio.index(opcao_maior)

municipio_escolhido = st.sidebar.selectbox("Município", opcoes_municipio, index=indice_padrao)
codigo = codigo_da_opcao[municipio_escolhido]

# contando quantos municipios diferentes a pessoa consultou nesta sessao
if st.session_state["ultimo_municipio"] != municipio_escolhido:
    st.session_state["consultas"] = st.session_state["consultas"] + 1
    st.session_state["ultimo_municipio"] = municipio_escolhido


# =========================================================
# cabecalho
# =========================================================
st.title("Radar Econômico Municipal")
st.write("Quanto da riqueza do Brasil está em poucas cidades, de que setor cada município vive e quem depende do dinheiro público. Escolha o ano, o estado e o município na barra à esquerda.")

aba_geral, aba_municipio, aba_ranking, aba_comparacao, aba_noticias, aba_dados = st.tabs(
    ["Visão geral", "Município", "Ranking", "Comparação", "Notícias do IBGE", "Seus dados"]
)


# =========================================================
# aba 1: visao geral do brasil
# =========================================================
with aba_geral:
    linha_resumo = resumo[resumo["ano"] == ano].iloc[0]
    linha_anterior = resumo[resumo["ano"] == ano - 1]

    # o ano vira texto so pro grafico nao mostrar "2,010"
    resumo_grafico = resumo.copy()
    resumo_grafico["ano"] = resumo_grafico["ano"].astype(str)

    st.subheader("O Brasil em " + str(ano))

    coluna1, coluna2, coluna3, coluna4 = st.columns(4)
    coluna1.metric("PIB do Brasil", formata_pib(linha_resumo["pib_brasil_mil_reais"]))
    coluna2.metric("PIB por habitante", "R$ " + formata_numero(linha_resumo["pib_per_capita_brasil"]))

    if len(linha_anterior) > 0:
        variacao_metade = int(linha_resumo["municipios_metade_pib"] - linha_anterior.iloc[0]["municipios_metade_pib"])
        variacao_capitais = round(linha_resumo["participacao_capitais"] - linha_anterior.iloc[0]["participacao_capitais"], 1)
        coluna3.metric("Municípios que somam metade do PIB", int(linha_resumo["municipios_metade_pib"]), variacao_metade)
        coluna4.metric("Peso das 27 capitais no PIB", formata_numero(linha_resumo["participacao_capitais"], 1) + "%", str(variacao_capitais) + " p.p.", delta_color="inverse")
    else:
        coluna3.metric("Municípios que somam metade do PIB", int(linha_resumo["municipios_metade_pib"]))
        coluna4.metric("Peso das 27 capitais no PIB", formata_numero(linha_resumo["participacao_capitais"], 1) + "%")

    st.write(
        "De 5.570 municípios, só " + str(int(linha_resumo["municipios_metade_pib"]))
        + " produzem metade de toda a riqueza do país. Quando esse número sobe, a economia está se espalhando pelo território. "
        "Ele subiu de 53 em 2010 para 87 em 2021 e voltou a cair em 2022 e 2023."
    )

    grafico1, grafico2 = st.columns(2)
    with grafico1:
        st.caption("Quantos municípios somam metade do PIB, por ano")
        st.line_chart(resumo_grafico, x="ano", y="municipios_metade_pib")
    with grafico2:
        st.caption("Peso das capitais no PIB do Brasil (%), por ano")
        st.line_chart(resumo_grafico, x="ano", y="participacao_capitais")

    st.subheader("De que setor vivem os municípios")
    if ano <= 2021:
        contagem_perfil = recorte["perfil"].value_counts()
        tabela_perfil = pd.DataFrame({"perfil": contagem_perfil.index, "municipios": contagem_perfil.values})
        st.bar_chart(tabela_perfil, x="perfil", y="municipios")
        if uf == "Brasil":
            local = "no Brasil"
        else:
            local = "em " + uf
        qtd_adm = len(recorte[recorte["perfil"] == "Administração pública"])
        st.write(
            "Em " + str(ano) + ", " + formata_numero(qtd_adm) + " municípios " + local
            + " tinham a administração pública (prefeitura, escolas e postos de saúde públicos) como a maior atividade econômica."
        )
    else:
        st.warning("O IBGE publicou os anos de 2022 e 2023 sem a divisão por setor. Essa divisão só volta com a nova série das Contas Nacionais, prevista para 2027. Escolha um ano até 2021 para ver os perfis.")


# =========================================================
# aba 2: o municipio escolhido
# =========================================================
with aba_municipio:
    linha = do_ano[do_ano["codigo"] == codigo].iloc[0]

    st.subheader(municipio_escolhido + " em " + str(ano))

    if pd.isna(linha["pib"]):
        st.info("O IBGE não tem PIB deste município em " + str(ano) + ". Ele foi criado depois desse ano. Escolha um ano a partir de 2013.")
    else:
        # media do estado (soma do pib dividida pela soma da populacao)
        do_estado = do_ano[do_ano["uf"] == linha["uf"]]
        per_capita_estado = do_estado["pib"].sum() * 1000 / do_estado["populacao"].sum()

        coluna1, coluna2, coluna3, coluna4 = st.columns(4)
        coluna1.metric("PIB", formata_pib(linha["pib"]))
        coluna2.metric("População", formata_numero(linha["populacao"]))
        coluna3.metric("PIB por habitante", "R$ " + formata_numero(linha["pib_per_capita"]))
        coluna4.metric("Razão de riqueza", formata_numero(linha["razao_riqueza"], 2), help="PIB por habitante do município dividido pelo do Brasil. Acima de 1, é mais rico que a média do país.")

        coluna5, coluna6, coluna7, coluna8 = st.columns(4)
        coluna5.metric("Participação no PIB do Brasil", formata_numero(linha["participacao_pib"], 3) + "%")
        coluna6.metric("Posição no ranking nacional", str(int(linha["posicao_pib"])) + "º de 5.570")
        coluna7.metric("PIB por habitante do estado", "R$ " + formata_numero(per_capita_estado))
        coluna8.metric("PIB por habitante do Brasil", "R$ " + formata_numero(linha["pib_per_capita_brasil"]))

        # aviso de distorcao (risco mapeado no tp1)
        if linha["razao_riqueza"] > 3:
            st.warning("Cuidado ao ler o PIB por habitante: ele é mais de 3 vezes a média do Brasil. Isso costuma acontecer em municípios com petróleo, mineração, refinarias ou grandes usinas, e essa riqueza não fica necessariamente com a população.")

        st.subheader("De que setor o município vive")
        if ano <= 2021:
            tabela_setores = pd.DataFrame({
                "setor": ["Agropecuária", "Indústria", "Serviços", "Administração pública"],
                "participacao": [linha["part_agropecuaria"], linha["part_industria"], linha["part_servicos"], linha["part_adm_publica"]],
            })

            grafico, textos = st.columns([2, 1])
            with grafico:
                st.caption("Participação de cada setor no valor adicionado (%)")
                st.bar_chart(tabela_setores, x="setor", y="participacao")
            with textos:
                st.metric("Perfil econômico", linha["perfil"])
                st.metric("Dependência da administração pública", formata_numero(linha["dependencia_adm"], 1) + "%")
                st.metric("Índice de concentração (HHI)", formata_numero(linha["hhi"], 3), help="Soma dos quadrados da participação de cada setor. Vai de 0,25 (os quatro setores do mesmo tamanho) até 1 (tudo num setor só).")

            # leitura simples dos numeros (criterio do projeto)
            if linha["hhi"] < 0.30:
                leitura_hhi = "tem a economia bem distribuída entre os setores"
            elif linha["hhi"] < 0.45:
                leitura_hhi = "tem a economia moderadamente concentrada"
            else:
                leitura_hhi = "tem a economia muito concentrada em um setor só, " + linha["perfil"]

            if linha["dependencia_adm"] >= 40:
                leitura_adm = "Mais de 40% do valor produzido vem do setor público, o que indica forte dependência de repasses."
            elif linha["dependencia_adm"] >= 25:
                leitura_adm = "O setor público tem peso relevante, entre 25% e 40% do valor produzido."
            else:
                leitura_adm = "O setor público pesa menos de 25% do valor produzido."

            st.write("Em " + str(ano) + ", " + municipio_escolhido + " " + leitura_hhi + ". " + leitura_adm)
        else:
            st.warning("O IBGE publicou os anos de 2022 e 2023 sem a divisão por setor. Escolha um ano até 2021 para ver de que setor o município vive.")

    st.subheader("PIB por habitante ao longo do tempo")
    historico = indicadores[indicadores["codigo"] == codigo][["ano", "pib_per_capita", "pib_per_capita_brasil"]]
    historico = historico.rename(columns={"pib_per_capita": "Município", "pib_per_capita_brasil": "Brasil"})
    historico["ano"] = historico["ano"].astype(str)
    st.line_chart(historico, x="ano", y=["Município", "Brasil"])
    st.caption("Valores em reais correntes, sem descontar a inflação.")

    # se a pessoa subiu dados na aba "Seus dados", mostra aqui tambem
    if st.session_state["dados_usuario"] is not None:
        dados_usuario = st.session_state["dados_usuario"]
        do_municipio = dados_usuario[dados_usuario["codigo"] == codigo]
        if len(do_municipio) > 0:
            st.subheader("Seus dados para este município")
            st.dataframe(do_municipio, hide_index=True)

    if st.button("Adicionar à comparação"):
        if codigo in st.session_state["comparacao"]:
            st.info(municipio_escolhido + " já está na comparação.")
        else:
            st.session_state["comparacao"].append(codigo)
            st.success(municipio_escolhido + " adicionado. Veja na aba Comparação.")


# =========================================================
# aba 3: ranking com download
# =========================================================
with aba_ranking:
    if uf == "Brasil":
        st.subheader("Ranking dos municípios do Brasil em " + str(ano))
    else:
        st.subheader("Ranking dos municípios de " + uf + " em " + str(ano))

    criterios = {
        "PIB": "pib",
        "PIB por habitante": "pib_per_capita",
        "Dependência da administração pública": "dependencia_adm",
        "Índice de concentração (HHI)": "hhi",
    }
    coluna_filtro1, coluna_filtro2 = st.columns(2)
    criterio = coluna_filtro1.selectbox("Ordenar por", list(criterios.keys()))
    quantidade = coluna_filtro2.slider("Quantos municípios mostrar", 10, 100, 20)

    coluna_ordem = criterios[criterio]
    if ano > 2021 and (coluna_ordem == "dependencia_adm" or coluna_ordem == "hhi"):
        st.warning("Esse critério só existe até 2021. Escolha outro ano ou ordene por PIB.")

    ranking = recorte.sort_values(coluna_ordem, ascending=False)
    ranking = ranking[["municipio", "uf", "pib", "populacao", "pib_per_capita", "razao_riqueza", "participacao_pib", "perfil", "dependencia_adm", "hhi"]]
    ranking = ranking.rename(columns={
        "municipio": "Município",
        "uf": "UF",
        "pib": "PIB (mil R$)",
        "populacao": "População",
        "pib_per_capita": "PIB por habitante (R$)",
        "razao_riqueza": "Razão de riqueza",
        "participacao_pib": "Participação no PIB do Brasil (%)",
        "perfil": "Perfil",
        "dependencia_adm": "Dependência adm. pública (%)",
        "hhi": "HHI",
    })

    # na tela: 2 casas decimais e sem as colunas de setor quando o ano nao tem
    ranking_tela = ranking.head(quantidade).round(2)
    if ano > 2021:
        ranking_tela = ranking_tela.drop(columns=["Perfil", "Dependência adm. pública (%)", "HHI"])
        st.caption("As colunas de setor só existem até 2021.")
    st.dataframe(ranking_tela, hide_index=True)

    arquivo_ranking = ranking.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar a tabela completa em CSV",
        data=arquivo_ranking,
        file_name="ranking_" + uf + "_" + str(ano) + ".csv",
        mime="text/csv",
    )

    # curva de concentracao do recorte
    st.subheader("Curva de concentração")
    curva = recorte[recorte["pib"].notna()].sort_values("pib", ascending=False).copy()
    curva["posicao"] = range(1, len(curva) + 1)
    curva["acumulado"] = curva["pib"].cumsum() / curva["pib"].sum() * 100
    municipios_metade_recorte = len(curva[curva["acumulado"] < 50]) + 1
    st.write(
        "Somando do maior para o menor, " + str(municipios_metade_recorte) + " de " + formata_numero(len(curva))
        + " municípios já chegam a metade do PIB do recorte escolhido."
    )
    st.caption("PIB acumulado (%) conforme se somam os municípios, do maior para o menor")
    st.line_chart(curva, x="posicao", y="acumulado")


# =========================================================
# aba 4: comparacao (lista guardada no estado de sessao)
# =========================================================
with aba_comparacao:
    st.subheader("Comparação entre municípios em " + str(ano))

    if len(st.session_state["comparacao"]) == 0:
        st.info("A lista está vazia. Na aba Município, clique em Adicionar à comparação. A lista fica guardada enquanto você troca de município, de ano ou de aba.")
    else:
        comparados = do_ano[do_ano["codigo"].isin(st.session_state["comparacao"])].copy()
        nomes_comparados = []
        for nome, sigla in zip(comparados["municipio"], comparados["uf"]):
            nomes_comparados.append(nome + " (" + sigla + ")")
        comparados["nome"] = nomes_comparados

        tabela_comparacao = comparados[["nome", "pib", "populacao", "pib_per_capita", "razao_riqueza", "perfil", "dependencia_adm", "hhi"]]
        tabela_comparacao = tabela_comparacao.rename(columns={
            "nome": "Município",
            "pib": "PIB (mil R$)",
            "populacao": "População",
            "pib_per_capita": "PIB por habitante (R$)",
            "razao_riqueza": "Razão de riqueza",
            "perfil": "Perfil",
            "dependencia_adm": "Dependência adm. pública (%)",
            "hhi": "HHI",
        })
        tabela_comparacao = tabela_comparacao.round(2)
        if ano > 2021:
            tabela_comparacao = tabela_comparacao.drop(columns=["Perfil", "Dependência adm. pública (%)", "HHI"])
            st.caption("As colunas de setor só existem até 2021. Troque o ano para vê-las.")
        st.dataframe(tabela_comparacao, hide_index=True)

        st.caption("PIB por habitante (R$)")
        st.bar_chart(comparados, x="nome", y="pib_per_capita")

        if st.button("Limpar a comparação"):
            st.session_state["comparacao"] = []
            st.rerun()


# =========================================================
# aba 5: noticias raspadas com beautiful soup
# =========================================================
with aba_noticias:
    st.subheader("O que o IBGE falou sobre o PIB dos Municípios")
    st.write("Notícias e releases da Agência de Notícias do IBGE sobre cada divulgação do PIB dos Municípios. O texto foi extraído das páginas com Beautiful Soup e salvo em data/noticias_ibge.csv e data/noticias_ibge.txt.")

    noticias["ano_publicacao"] = noticias["data"].str[0:4]
    lista_anos_noticias = ["Todas"] + sorted(noticias["ano_publicacao"].unique(), reverse=True)
    ano_noticia = st.selectbox("Notícias publicadas em", lista_anos_noticias)

    if ano_noticia == "Todas":
        noticias_escolhidas = noticias
    else:
        noticias_escolhidas = noticias[noticias["ano_publicacao"] == ano_noticia]

    coluna1, coluna2, coluna3, coluna4 = st.columns(4)
    coluna1.metric("Notícias", len(noticias_escolhidas))
    coluna2.metric("Palavras no total", formata_numero(noticias_escolhidas["qtd_palavras"].sum()))
    coluna3.metric("Média de palavras por notícia", formata_numero(noticias_escolhidas["qtd_palavras"].mean()))
    coluna4.metric("Período", noticias_escolhidas["data"].min()[0:4] + " a " + noticias_escolhidas["data"].max()[0:4])

    texto_junto = " ".join(noticias_escolhidas["texto"])

    st.subheader("Nuvem de palavras")
    st.image(gerar_nuvem(texto_junto))

    frequencias = contar_palavras(texto_junto)
    coluna_tabela, coluna_grafico = st.columns([1, 2])
    with coluna_tabela:
        st.caption("As 15 palavras que mais aparecem")
        st.dataframe(frequencias.head(15), hide_index=True)
    with coluna_grafico:
        st.caption("Tamanho de cada notícia (palavras)")
        tamanho = noticias_escolhidas[["data", "qtd_palavras"]]
        st.bar_chart(tamanho, x="data", y="qtd_palavras")

    st.subheader("As notícias")
    for indice, noticia in noticias_escolhidas.sort_values("data", ascending=False).iterrows():
        with st.expander(noticia["data"] + " | " + noticia["titulo"]):
            st.write(noticia["resumo"])
            st.write("Tipo: " + noticia["tipo"] + " | " + str(noticia["qtd_palavras"]) + " palavras")
            st.markdown("[Ler no site do IBGE](" + noticia["link"] + ")")

    st.caption("O site do IBGE bloqueia acesso automático (resposta 403), por isso as páginas foram salvas pelo navegador em data/html_ibge e processadas com Beautiful Soup.")


# =========================================================
# aba 6: upload e download de dados do usuario
# =========================================================
with aba_dados:
    st.subheader("Junte os seus dados aos do painel")
    st.write(
        "Suba um arquivo CSV com uma coluna chamada codigo (o código IBGE de 7 dígitos do município) "
        "e quantas colunas quiser com os seus dados, como orçamento, número de empregos ou nota do IDEB. "
        "O painel junta tudo pelo código e mostra ao lado dos indicadores do IBGE."
    )

    # modelo pronto pra pessoa baixar, preencher e subir de volta
    modelo = recorte[["codigo", "municipio", "uf"]].copy()
    modelo = modelo.merge(populacao_2024, on="codigo", how="left")
    modelo["seu_indicador"] = ""
    arquivo_modelo = modelo.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar modelo de CSV (" + uf + ")",
        data=arquivo_modelo,
        file_name="modelo_upload_" + uf + ".csv",
        mime="text/csv",
    )
    st.caption("O modelo já vem com a população estimada de 2024 como exemplo de dado extra. Preencha a coluna seu_indicador ou acrescente outras.")

    arquivo = st.file_uploader("Escolha o seu arquivo CSV", type=["csv"])

    if arquivo is not None:
        tabela_usuario = ler_csv_usuario(arquivo)
        if "codigo" not in tabela_usuario.columns:
            st.error("O arquivo precisa ter uma coluna chamada codigo, com o código IBGE de 7 dígitos. Colunas encontradas: " + ", ".join(tabela_usuario.columns))
        else:
            tabela_usuario["codigo"] = pd.to_numeric(tabela_usuario["codigo"], errors="coerce")
            tabela_usuario = tabela_usuario[tabela_usuario["codigo"].notna()]
            tabela_usuario["codigo"] = tabela_usuario["codigo"].astype(int)
            # guarda no estado de sessao pra nao perder ao trocar de aba ou de filtro
            st.session_state["dados_usuario"] = tabela_usuario
            st.session_state["nome_arquivo_usuario"] = arquivo.name

    if st.session_state["dados_usuario"] is not None:
        dados_usuario = st.session_state["dados_usuario"]
        st.success("Arquivo em uso: " + st.session_state["nome_arquivo_usuario"] + " (" + str(len(dados_usuario)) + " linhas). Ele continua carregado enquanto você navega.")

        # nao repete colunas que o painel ja tem
        colunas_usuario = []
        for coluna in dados_usuario.columns:
            if coluna not in ["municipio", "uf"]:
                colunas_usuario.append(coluna)

        juntos = do_ano[["codigo", "municipio", "uf", "pib", "populacao", "pib_per_capita", "perfil", "dependencia_adm"]]
        juntos = juntos.merge(dados_usuario[colunas_usuario], on="codigo", how="inner")

        nao_achados = len(dados_usuario) - len(juntos)
        st.write(str(len(juntos)) + " municípios encontrados na base do IBGE em " + str(ano) + ".")
        if nao_achados > 0:
            st.warning(str(nao_achados) + " linhas do arquivo não bateram com nenhum código IBGE. Confira se o código tem 7 dígitos.")

        st.dataframe(juntos, hide_index=True)

        # grafico cruzando uma coluna do usuario com o pib por habitante
        colunas_numericas = []
        for coluna in colunas_usuario:
            if coluna != "codigo" and pd.api.types.is_numeric_dtype(juntos[coluna]):
                if juntos[coluna].notna().sum() > 0:
                    colunas_numericas.append(coluna)

        if len(colunas_numericas) > 0:
            coluna_x = st.selectbox("Comparar qual coluna sua com o PIB por habitante?", colunas_numericas)
            st.scatter_chart(juntos, x=coluna_x, y="pib_per_capita")
        else:
            st.info("Nenhuma coluna numérica preenchida no seu arquivo para montar o gráfico.")

        arquivo_juntos = juntos.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Baixar seus dados junto com os do IBGE",
            data=arquivo_juntos,
            file_name="seus_dados_com_ibge_" + str(ano) + ".csv",
            mime="text/csv",
        )

        if st.button("Remover meus dados"):
            st.session_state["dados_usuario"] = None
            st.session_state["nome_arquivo_usuario"] = ""
            st.rerun()


# =========================================================
# rodape da barra lateral
# fica no final do script pra ja mostrar os numeros depois dos cliques
# =========================================================
st.sidebar.divider()
st.sidebar.caption("Municípios consultados nesta sessão: " + str(st.session_state["consultas"]))
st.sidebar.caption("Na lista de comparação: " + str(len(st.session_state["comparacao"])))
st.sidebar.caption("Dados carregados em " + formata_numero(tempo_carga, 3) + " s (a partir do segundo clique, vêm do cache)")
st.sidebar.caption("Fonte: IBGE, PIB dos Municípios (tabela 5938), Estimativas de População e Censos 2010 e 2022.")
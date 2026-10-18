import time
import pandas as pd
import streamlit as st
from wordcloud import WordCloud

# este arquivo guarda o que todas as paginas usam: a leitura dos dados
# com cache, as funcoes de formatacao e os filtros da barra lateral.
# assim nao precisa repetir o mesmo codigo em cada pagina


# =========================================================
# leitura dos dados (com cache)
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
# estado de sessao: o que o app lembra enquanto a pessoa navega
# =========================================================
def preparar_sessao():
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
    if "endereco_api" not in st.session_state:
        st.session_state["endereco_api"] = "http://127.0.0.1:8000"


# =========================================================
# filtros da barra lateral
# ficam no app.py, antes de abrir a pagina, pra valerem em todas elas
# =========================================================
def desenhar_filtros():
    inicio = time.perf_counter()
    indicadores = carregar_indicadores()
    tempo_carga = time.perf_counter() - inicio

    st.sidebar.divider()
    st.sidebar.title("Filtros")

    # ano
    lista_anos = sorted(indicadores["ano"].unique(), reverse=True)
    if "ano" not in st.session_state:
        st.session_state["ano"] = lista_anos[0]
    posicao = lista_anos.index(st.session_state["ano"])
    ano = st.sidebar.selectbox("Ano", lista_anos, index=posicao)
    st.session_state["ano"] = ano

    # estado
    lista_ufs = ["Brasil"] + sorted(indicadores["uf"].unique())
    if "uf" not in st.session_state:
        st.session_state["uf"] = "Brasil"
    if st.session_state["uf"] not in lista_ufs:
        st.session_state["uf"] = "Brasil"
    posicao = lista_ufs.index(st.session_state["uf"])
    uf = st.sidebar.selectbox("Estado", lista_ufs, index=posicao)
    st.session_state["uf"] = uf

    do_ano = indicadores[indicadores["ano"] == ano]
    if uf == "Brasil":
        recorte = do_ano
    else:
        recorte = do_ano[do_ano["uf"] == uf]

    # municipio, no formato "Nome (UF)"
    recorte_ordenado = recorte.sort_values("municipio")
    opcoes_municipio = []
    codigo_da_opcao = {}
    for nome, sigla, codigo in zip(recorte_ordenado["municipio"], recorte_ordenado["uf"], recorte_ordenado["codigo"]):
        opcao = nome + " (" + sigla + ")"
        opcoes_municipio.append(opcao)
        codigo_da_opcao[opcao] = codigo

    # se o municipio guardado nao existe no recorte, volta pro de maior pib
    if st.session_state.get("municipio") in opcoes_municipio:
        posicao = opcoes_municipio.index(st.session_state["municipio"])
    else:
        maior = recorte.sort_values("pib").iloc[-1]
        opcao_maior = maior["municipio"] + " (" + maior["uf"] + ")"
        posicao = opcoes_municipio.index(opcao_maior)

    municipio_escolhido = st.sidebar.selectbox("Município", opcoes_municipio, index=posicao)
    st.session_state["municipio"] = municipio_escolhido
    st.session_state["codigo"] = codigo_da_opcao[municipio_escolhido]

    # contando quantos municipios diferentes a pessoa consultou nesta sessao
    if st.session_state["ultimo_municipio"] != municipio_escolhido:
        st.session_state["consultas"] = st.session_state["consultas"] + 1
        st.session_state["ultimo_municipio"] = municipio_escolhido

    st.sidebar.divider()
    st.sidebar.caption("Municípios consultados nesta sessão: " + str(st.session_state["consultas"]))
    st.sidebar.caption("Na lista de comparação: " + str(len(st.session_state["comparacao"])))
    st.sidebar.caption("Dados carregados em " + formata_numero(tempo_carga, 3) + " s (a partir do segundo clique, vêm do cache)")
    st.sidebar.caption("Fonte: IBGE, PIB dos Municípios (tabela 5938), Estimativas de População e Censos 2010 e 2022.")


# devolve os recortes que as paginas usam, ja filtrados
def pegar_recortes():
    indicadores = carregar_indicadores()
    ano = st.session_state["ano"]
    uf = st.session_state["uf"]

    do_ano = indicadores[indicadores["ano"] == ano]
    if uf == "Brasil":
        recorte = do_ano
    else:
        recorte = do_ano[do_ano["uf"] == uf]

    return indicadores, do_ano, recorte
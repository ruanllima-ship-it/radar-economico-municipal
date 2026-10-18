import streamlit as st
import comum

noticias = comum.carregar_noticias()

st.title("Notícias do IBGE")
st.subheader("O que o IBGE falou sobre o PIB dos Municípios")
st.write("Notícias e releases da Agência de Notícias do IBGE sobre cada divulgação do PIB dos Municípios. As páginas foram abertas com Selenium e o texto extraído com Beautiful Soup, e o resultado está salvo em data/noticias_ibge.csv e data/noticias_ibge.txt.")

noticias["ano_publicacao"] = noticias["data"].str[0:4]
lista_anos_noticias = ["Todas"] + sorted(noticias["ano_publicacao"].unique(), reverse=True)
ano_noticia = st.selectbox("Notícias publicadas em", lista_anos_noticias)

if ano_noticia == "Todas":
    noticias_escolhidas = noticias
else:
    noticias_escolhidas = noticias[noticias["ano_publicacao"] == ano_noticia]

coluna1, coluna2, coluna3, coluna4 = st.columns(4)
coluna1.metric("Matérias", len(noticias_escolhidas))
coluna2.metric("Palavras no total", comum.formata_numero(noticias_escolhidas["qtd_palavras"].sum()))
coluna3.metric("Média de palavras por matéria", comum.formata_numero(noticias_escolhidas["qtd_palavras"].mean()))
coluna4.metric("Período", noticias_escolhidas["data"].min()[0:4] + " a " + noticias_escolhidas["data"].max()[0:4])

texto_junto = " ".join(noticias_escolhidas["texto"])

st.subheader("Nuvem de palavras")
st.image(comum.gerar_nuvem(texto_junto))

frequencias = comum.contar_palavras(texto_junto)
coluna_tabela, coluna_grafico = st.columns([1, 2])
with coluna_tabela:
    st.caption("As 15 palavras que mais aparecem")
    st.dataframe(frequencias.head(15), hide_index=True)
with coluna_grafico:
    st.caption("Tamanho de cada matéria (palavras)")
    tamanho = noticias_escolhidas[["data", "qtd_palavras"]]
    st.bar_chart(tamanho, x="data", y="qtd_palavras")

st.subheader("As matérias")
for indice, noticia in noticias_escolhidas.sort_values("data", ascending=False).iterrows():
    with st.expander(noticia["data"] + " | " + noticia["titulo"]):
        st.write(noticia["resumo"])
        st.write("Tipo: " + noticia["tipo"] + " | " + str(noticia["qtd_palavras"]) + " palavras")
        st.markdown("[Ler no site do IBGE](" + noticia["link"] + ")")

st.caption("O site do IBGE recusa acesso automatizado por script simples (resposta 403) e monta a busca por JavaScript, por isso a coleta usa o Selenium para abrir as páginas em um navegador de verdade.")
import streamlit as st
import comum

st.set_page_config(page_title="Radar Econômico Municipal", layout="wide")

# =========================================================
# menu de navegacao: cada pagina e um arquivo dentro de paginas/
# =========================================================
paginas = [
    st.Page("paginas/visao_geral.py", title="Visão geral", icon=":material/public:", default=True),
    st.Page("paginas/municipio.py", title="Município", icon=":material/location_city:"),
    st.Page("paginas/ranking.py", title="Ranking", icon=":material/leaderboard:"),
    st.Page("paginas/comparacao.py", title="Comparação", icon=":material/compare_arrows:"),
    st.Page("paginas/noticias.py", title="Notícias do IBGE", icon=":material/newspaper:"),
    st.Page("paginas/seus_dados.py", title="Seus dados", icon=":material/upload_file:"),
    st.Page("paginas/consulta_api.py", title="Consulta pela API", icon=":material/api:"),
]

navegacao = st.navigation(paginas)

# prepara o estado de sessao e desenha os filtros antes de abrir a pagina,
# assim os filtros valem para todas elas
comum.preparar_sessao()
comum.desenhar_filtros()

navegacao.run()
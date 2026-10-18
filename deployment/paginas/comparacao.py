import streamlit as st
import comum

indicadores, do_ano, recorte = comum.pegar_recortes()
ano = st.session_state["ano"]

st.title("Comparação")
st.subheader("Comparação entre municípios em " + str(ano))

if len(st.session_state["comparacao"]) == 0:
    st.info("A lista está vazia. Na página Município, clique em Adicionar à comparação. A lista fica guardada enquanto você troca de página, de município ou de ano.")
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
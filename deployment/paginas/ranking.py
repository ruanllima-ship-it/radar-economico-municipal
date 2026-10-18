import streamlit as st
import comum

indicadores, do_ano, recorte = comum.pegar_recortes()
ano = st.session_state["ano"]
uf = st.session_state["uf"]

st.title("Ranking")

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
    "Somando do maior para o menor, " + str(municipios_metade_recorte) + " de " + comum.formata_numero(len(curva))
    + " municípios já chegam a metade do PIB do recorte escolhido."
)
st.caption("PIB acumulado (%) conforme se somam os municípios, do maior para o menor")
st.line_chart(curva, x="posicao", y="acumulado")
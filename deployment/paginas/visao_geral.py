import pandas as pd
import streamlit as st
import comum

indicadores, do_ano, recorte = comum.pegar_recortes()
resumo = comum.carregar_resumo()
ano = st.session_state["ano"]
uf = st.session_state["uf"]

st.title("Radar Econômico Municipal")
st.write("Quanto da riqueza do Brasil está em poucas cidades, de que setor cada município vive e quem depende do dinheiro público. Escolha o ano, o estado e o município na barra à esquerda, e use o menu para trocar de página.")

linha_resumo = resumo[resumo["ano"] == ano].iloc[0]
linha_anterior = resumo[resumo["ano"] == ano - 1]

# o ano vira texto so pro grafico nao mostrar "2,010"
resumo_grafico = resumo.copy()
resumo_grafico["ano"] = resumo_grafico["ano"].astype(str)

st.subheader("O Brasil em " + str(ano))

coluna1, coluna2, coluna3, coluna4 = st.columns(4)
coluna1.metric("PIB do Brasil", comum.formata_pib(linha_resumo["pib_brasil_mil_reais"]))
coluna2.metric("PIB por habitante", "R$ " + comum.formata_numero(linha_resumo["pib_per_capita_brasil"]))

if len(linha_anterior) > 0:
    variacao_metade = int(linha_resumo["municipios_metade_pib"] - linha_anterior.iloc[0]["municipios_metade_pib"])
    variacao_capitais = round(linha_resumo["participacao_capitais"] - linha_anterior.iloc[0]["participacao_capitais"], 1)
    coluna3.metric("Municípios que somam metade do PIB", int(linha_resumo["municipios_metade_pib"]), variacao_metade)
    coluna4.metric("Peso das 27 capitais no PIB", comum.formata_numero(linha_resumo["participacao_capitais"], 1) + "%", str(variacao_capitais) + " p.p.", delta_color="inverse")
else:
    coluna3.metric("Municípios que somam metade do PIB", int(linha_resumo["municipios_metade_pib"]))
    coluna4.metric("Peso das 27 capitais no PIB", comum.formata_numero(linha_resumo["participacao_capitais"], 1) + "%")

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
        "Em " + str(ano) + ", " + comum.formata_numero(qtd_adm) + " municípios " + local
        + " tinham a administração pública (prefeitura, escolas e postos de saúde públicos) como a maior atividade econômica."
    )
else:
    st.warning("O IBGE publicou os anos de 2022 e 2023 sem a divisão por setor. Essa divisão só volta com a nova série das Contas Nacionais, prevista para 2027. Escolha um ano até 2021 para ver os perfis.")
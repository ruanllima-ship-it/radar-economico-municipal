import pandas as pd
import streamlit as st
import comum

indicadores, do_ano, recorte = comum.pegar_recortes()
populacao_2024 = comum.carregar_populacao_2024()
ano = st.session_state["ano"]
uf = st.session_state["uf"]

st.title("Seus dados")
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
    tabela_usuario = comum.ler_csv_usuario(arquivo)
    if "codigo" not in tabela_usuario.columns:
        st.error("O arquivo precisa ter uma coluna chamada codigo, com o código IBGE de 7 dígitos. Colunas encontradas: " + ", ".join(tabela_usuario.columns))
    else:
        tabela_usuario["codigo"] = pd.to_numeric(tabela_usuario["codigo"], errors="coerce")
        tabela_usuario = tabela_usuario[tabela_usuario["codigo"].notna()]
        tabela_usuario["codigo"] = tabela_usuario["codigo"].astype(int)
        # guarda no estado de sessao pra nao perder ao trocar de pagina ou de filtro
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
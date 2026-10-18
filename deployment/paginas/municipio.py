import pandas as pd
import streamlit as st
import comum

indicadores, do_ano, recorte = comum.pegar_recortes()
ano = st.session_state["ano"]
codigo = st.session_state["codigo"]
municipio_escolhido = st.session_state["municipio"]

st.title("Município")

linha = do_ano[do_ano["codigo"] == codigo].iloc[0]
st.subheader(municipio_escolhido + " em " + str(ano))

if pd.isna(linha["pib"]):
    st.info("O IBGE não tem PIB deste município em " + str(ano) + ". Ele foi criado depois desse ano. Escolha um ano a partir de 2013.")
else:
    # media do estado (soma do pib dividida pela soma da populacao)
    do_estado = do_ano[do_ano["uf"] == linha["uf"]]
    per_capita_estado = do_estado["pib"].sum() * 1000 / do_estado["populacao"].sum()

    coluna1, coluna2, coluna3, coluna4 = st.columns(4)
    coluna1.metric("PIB", comum.formata_pib(linha["pib"]))
    coluna2.metric("População", comum.formata_numero(linha["populacao"]))
    coluna3.metric("PIB por habitante", "R$ " + comum.formata_numero(linha["pib_per_capita"]))
    coluna4.metric("Razão de riqueza", comum.formata_numero(linha["razao_riqueza"], 2), help="PIB por habitante do município dividido pelo do Brasil. Acima de 1, é mais rico que a média do país.")

    coluna5, coluna6, coluna7, coluna8 = st.columns(4)
    coluna5.metric("Participação no PIB do Brasil", comum.formata_numero(linha["participacao_pib"], 3) + "%")
    coluna6.metric("Posição no ranking nacional", str(int(linha["posicao_pib"])) + "º de 5.570")
    coluna7.metric("PIB por habitante do estado", "R$ " + comum.formata_numero(per_capita_estado))
    coluna8.metric("PIB por habitante do Brasil", "R$ " + comum.formata_numero(linha["pib_per_capita_brasil"]))

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
            st.metric("Dependência da administração pública", comum.formata_numero(linha["dependencia_adm"], 1) + "%")
            st.metric("Índice de concentração (HHI)", comum.formata_numero(linha["hhi"], 3), help="Soma dos quadrados da participação de cada setor. Vai de 0,25 (os quatro setores do mesmo tamanho) até 1 (tudo num setor só).")

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

# se a pessoa subiu dados na pagina "Seus dados", mostra aqui tambem
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
        st.success(municipio_escolhido + " adicionado. Veja na página Comparação.")
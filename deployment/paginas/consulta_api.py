import pandas as pd
import requests
import streamlit as st
import comum

# esta pagina nao le os arquivos csv: ela pergunta tudo para a api do
# projeto (deployment/api.py), que precisa estar ligada em outro terminal

st.title("Consulta pela API")
st.write(
    "As outras páginas leem os arquivos de dados direto do disco. Esta aqui é diferente: "
    "ela conversa com a API do projeto, feita com FastAPI, exatamente como um sistema de fora faria. "
    "Para funcionar, a API precisa estar ligada em outro terminal."
)

st.code("py -m uvicorn deployment.api:app --reload", language="powershell")

endereco = st.text_input("Endereço da API", st.session_state["endereco_api"])
st.session_state["endereco_api"] = endereco


# funcao que pergunta para a api e devolve a resposta
def perguntar(caminho, metodo="GET", corpo=None):
    try:
        if metodo == "GET":
            resposta = requests.get(endereco + caminho, timeout=20)
        else:
            resposta = requests.post(endereco + caminho, json=corpo, timeout=20)
    except Exception:
        return None, "A API não respondeu. Confira se ela está ligada no endereço acima."

    if resposta.status_code != 200:
        try:
            detalhe = resposta.json().get("detail", "")
        except Exception:
            detalhe = ""
        return None, "A API respondeu com erro " + str(resposta.status_code) + ". " + str(detalhe)

    return resposta.json(), ""


# 1. conferindo se a api esta no ar
dados, erro = perguntar("/")

if erro != "":
    st.error(erro)
    st.info("Abra um segundo terminal no VS Code (botão + ao lado de powershell), ative o venv e rode o comando acima. Depois volte aqui e recarregue a página.")
    st.stop()

st.success("API no ar: " + dados["nome"] + " | " + comum.formata_numero(dados["municipios"]) + " municípios, anos de " + dados["anos"])

with st.expander("Rotas que esta API oferece"):
    for rota in dados["rotas"]:
        st.write("**" + rota + "** — " + dados["rotas"][rota])
    st.write("A documentação interativa fica em " + endereco + "/docs")

st.divider()

aba_municipio, aba_ranking, aba_comparar = st.tabs(["Consultar município (GET)", "Ranking (GET)", "Comparar (POST)"])


# 2. consulta de um municipio (GET)
with aba_municipio:
    st.write("Rota **GET /municipios/{codigo}**. Devolve os indicadores de um município pelo código IBGE.")
    codigo = st.number_input("Código IBGE de 7 dígitos", value=int(st.session_state["codigo"]), step=1)
    ano_consulta = st.number_input("Ano", value=int(st.session_state["ano"]), step=1)

    if st.button("Consultar na API", key="botao_municipio"):
        caminho = "/municipios/" + str(int(codigo)) + "?ano=" + str(int(ano_consulta))
        st.caption("Chamando: " + endereco + caminho)
        dados, erro = perguntar(caminho)
        if erro != "":
            st.error(erro)
        else:
            st.write("**" + dados["municipio"] + " (" + dados["uf"] + ")** — região " + dados["regiao"])
            tabela = pd.DataFrame(dados["dados"])
            st.dataframe(tabela, hide_index=True)
            with st.expander("Resposta crua da API (JSON)"):
                st.json(dados)


# 3. ranking (GET)
with aba_ranking:
    st.write("Rota **GET /ranking**. Devolve os municípios ordenados pelo critério escolhido.")
    criterios = {
        "PIB": "pib",
        "PIB por habitante": "pib_per_capita",
        "Dependência da administração pública": "dependencia_adm",
        "Índice de concentração (HHI)": "hhi",
    }
    coluna1, coluna2, coluna3 = st.columns(3)
    criterio = coluna1.selectbox("Critério", list(criterios.keys()))
    ano_ranking = coluna2.number_input("Ano do ranking", value=int(st.session_state["ano"]), step=1)
    limite = coluna3.slider("Quantos municípios", 5, 50, 10)

    uf_escolhida = st.session_state["uf"]

    if st.button("Consultar na API", key="botao_ranking"):
        caminho = "/ranking?ano=" + str(int(ano_ranking)) + "&criterio=" + criterios[criterio] + "&limite=" + str(limite)
        if uf_escolhida != "Brasil":
            caminho = caminho + "&uf=" + uf_escolhida
        st.caption("Chamando: " + endereco + caminho)
        dados, erro = perguntar(caminho)
        if erro != "":
            st.error(erro)
        else:
            tabela = pd.DataFrame(dados["dados"])
            st.dataframe(tabela, hide_index=True)


# 4. comparacao (POST)
with aba_comparar:
    st.write("Rota **POST /comparar**. Diferente das outras, esta envia dados para a API: uma lista de códigos de município.")

    if len(st.session_state["comparacao"]) == 0:
        st.info("A lista de comparação está vazia. Vá na página Município e clique em Adicionar à comparação.")
    else:
        st.write("Vai enviar estes códigos: " + str(st.session_state["comparacao"]))
        corpo = {"codigos": st.session_state["comparacao"], "ano": int(st.session_state["ano"])}
        st.caption("Corpo do pedido:")
        st.json(corpo)

        if st.button("Enviar para a API", key="botao_comparar"):
            dados, erro = perguntar("/comparar", "POST", corpo)
            if erro != "":
                st.error(erro)
            else:
                st.write("Pedidos: " + str(dados["pedidos"]) + " | encontrados: " + str(dados["encontrados"]))
                if len(dados["nao_encontrados"]) > 0:
                    st.warning("Códigos não encontrados na base: " + str(dados["nao_encontrados"]))
                tabela = pd.DataFrame(dados["dados"])
                st.dataframe(tabela, hide_index=True)
import requests
import streamlit as st
import comum

# esta pagina usa o modelo de linguagem local do projeto. ela nao carrega o
# modelo por conta propria: ela pede o resumo para a API (deployment/api.py),
# que e quem tem o modelo na memoria. ou seja, o painel e a API continuam
# sendo dois programas separados, como no TP3.

st.title("Resumo com IA")

st.write(
    "As matérias do IBGE que o projeto coletou são longas, de mil a duas mil palavras cada. "
    "Esta página pede para um modelo de linguagem resumir o texto, e mostra o resultado ao "
    "lado do resumo que o próprio IBGE publicou, para você comparar os dois."
)

st.warning(
    "**Os resumos desta página são gerados por máquina.** O modelo é pequeno e roda "
    "localmente, então ele pode deixar informação importante de fora, mudar o tempo verbal "
    "ou escrever uma frase estranha. Confira sempre no texto original antes de usar qualquer "
    "número daqui. O link da matéria fica logo abaixo de cada resumo.",
    icon=":material/warning:",
)

endereco = st.text_input("Endereço da API", st.session_state["endereco_api"])
st.session_state["endereco_api"] = endereco


# funcao que conversa com a api. o tempo limite e grande de proposito:
# o primeiro pedido carrega o modelo e pode passar de 40 segundos.
def perguntar(caminho, metodo="GET", corpo=None):
    try:
        if metodo == "GET":
            resposta = requests.get(endereco + caminho, timeout=240)
        else:
            resposta = requests.post(endereco + caminho, json=corpo, timeout=240)
    except Exception:
        return None, "sem_api", "A API não respondeu. Confira se ela está ligada no endereço acima."

    if resposta.status_code == 200:
        return resposta.json(), "", ""

    try:
        detalhe = resposta.json().get("detail", "")
    except Exception:
        detalhe = ""

    return None, str(resposta.status_code), str(detalhe)


# mostra o erro do jeito certo para cada codigo http
def mostrar_erro(codigo, detalhe):
    if codigo == "503":
        st.error("**Modelo indisponível (503).** " + detalhe)
        st.info(
            "Isso acontece quando o PyTorch ou o Transformers não carregaram. "
            "Pare a API com Ctrl+C e ligue de novo para ela tentar outra vez."
        )
    elif codigo == "429":
        st.warning("**Modelo ocupado (429).** " + detalhe)
    elif codigo == "413":
        st.warning("**Texto grande demais (413).** " + detalhe)
    elif codigo == "400":
        st.warning("**Pedido inválido (400).** " + detalhe)
    elif codigo == "422":
        st.warning("**Formato do pedido inválido (422).** " + detalhe)
    else:
        st.error("A API respondeu com erro " + codigo + ". " + detalhe)


# mostra os dados tecnicos que a api devolve junto com o resumo
def mostrar_ficha(saida):
    coluna1, coluna2, coluna3, coluna4 = st.columns(4)
    coluna1.metric("Tempo da geração", str(saida["segundos"]) + " s")
    coluna2.metric("Rodou em", saida["dispositivo"].upper())
    coluna3.metric("Pedaços do texto", comum.formata_numero(saida["pedacos_do_texto"]))
    coluna4.metric("Pedaços lidos", comum.formata_numero(saida["pedacos_lidos"]))

    if saida["texto_cortado"] is True:
        st.caption(
            "O modelo lê no máximo " + str(saida["pedacos_lidos"]) + " pedaços por vez, e este "
            "texto tinha " + str(saida["pedacos_do_texto"]) + ". Ou seja, ele resumiu só o começo "
            "da matéria. Isso é uma limitação do modelo, não um erro."
        )
    else:
        st.caption("O texto coube inteiro dentro do limite do modelo, nada foi cortado.")


# 1. conferindo se a api esta no ar e como esta o modelo
situacao, codigo, detalhe = perguntar("/modelo")

if situacao is None:
    st.error(detalhe)
    st.info(
        "Abra um segundo terminal no VS Code (botão + ao lado de powershell), ative o venv e rode: "
        "py -m uvicorn deployment.api:app --reload . Depois volte aqui e recarregue a página."
    )
    st.stop()

if situacao["estado"] == "pronto":
    st.success(
        "Modelo carregado e pronto: " + situacao["modelo"] + " rodando em " +
        situacao["dispositivo"].upper() + ". Carregou em " +
        str(situacao["segundos_para_carregar"]) + " s e já gerou " +
        str(situacao["resumos_gerados"]) + " resumo(s) nesta sessão da API."
    )
elif situacao["estado"] == "falhou":
    st.error("O modelo não pôde ser carregado. " + situacao["mensagem_do_erro"])
    st.stop()
else:
    st.info(
        "O modelo ainda não foi carregado: " + situacao["modelo"] + ". Ele é carregado na "
        "primeira vez que alguém pede um resumo, e isso leva algumas dezenas de segundos. "
        "Depois disso, cada resumo sai em poucos segundos."
    )

st.divider()

aba_noticia, aba_livre = st.tabs(["Resumir uma matéria do IBGE", "Resumir o meu texto"])


# 2. resumindo uma das materias coletadas no TP3
with aba_noticia:
    noticias = comum.carregar_noticias()

    st.write(
        "São as " + str(len(noticias)) + " matérias coletadas com Selenium no TP3, "
        "somando " + comum.formata_numero(noticias["qtd_palavras"].sum()) + " palavras."
    )

    titulos = list(noticias["titulo"])
    titulo_escolhido = st.selectbox("Escolha a matéria", titulos)

    escolhida = noticias[noticias["titulo"] == titulo_escolhido].iloc[0]

    st.caption(
        "Publicada em " + str(escolhida["data"]) + " | " +
        comum.formata_numero(escolhida["qtd_palavras"]) + " palavras em " +
        str(escolhida["qtd_paragrafos"]) + " parágrafos"
    )

    with st.expander("Ver o texto original inteiro"):
        st.write(escolhida["texto"])

    if st.button("Gerar resumo com o modelo", key="botao_noticia"):
        corpo = {"texto": escolhida["texto"], "tipo_analise": "resumo"}

        with st.spinner("Pedindo o resumo para a API. Se for o primeiro, o modelo precisa carregar antes."):
            saida, codigo, detalhe = perguntar("/processar_texto", "POST", corpo)

        if saida is None:
            mostrar_erro(codigo, detalhe)
        else:
            st.subheader("Resumo gerado pelo modelo")
            st.info(saida["resultado"])

            resumo_do_ibge = str(escolhida["resumo"]).strip()
            st.subheader("Resumo publicado pelo IBGE")
            if resumo_do_ibge == "" or resumo_do_ibge == "nan":
                st.caption("Esta matéria não trazia resumo próprio.")
            else:
                st.write(resumo_do_ibge)

            st.write("[Abrir a matéria original no site do IBGE](" + str(escolhida["link"]) + ")")

            st.divider()
            mostrar_ficha(saida)


# 3. resumindo um texto que a pessoa colar
with aba_livre:
    st.write(
        "Cole qualquer texto em português aqui. O modelo foi treinado para resumir "
        "notícias, então funciona melhor com textos jornalísticos ou de relatório."
    )

    texto_colado = st.text_area("Texto para resumir", height=260)

    quantidade = len(texto_colado.strip())
    st.caption("Você digitou " + comum.formata_numero(quantidade) + " caracteres. O mínimo é 200 e o máximo é 50.000.")

    if st.button("Gerar resumo com o modelo", key="botao_livre"):
        if quantidade < 200:
            st.warning("Texto curto demais. Mande pelo menos 200 caracteres para valer a pena resumir.")
        else:
            corpo = {"texto": texto_colado, "tipo_analise": "resumo"}

            with st.spinner("Pedindo o resumo para a API. Se for o primeiro, o modelo precisa carregar antes."):
                saida, codigo, detalhe = perguntar("/processar_texto", "POST", corpo)

            if saida is None:
                mostrar_erro(codigo, detalhe)
            else:
                st.subheader("Resumo gerado pelo modelo")
                st.info(saida["resultado"])
                st.divider()
                mostrar_ficha(saida)


st.divider()
st.caption(
    "Modelo: recogna-nlp/ptt5-base-summ, um T5 de 223 milhões de parâmetros treinado para "
    "resumo em português, baixado da HuggingFace e executado localmente. Nenhum texto desta "
    "página sai da sua máquina."
)
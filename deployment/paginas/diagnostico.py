import pandas as pd
import requests
import streamlit as st
import comum

# Esta pagina mostra o agente de diagnostico municipal do TP5.
#
# A ordem da pagina nao e por acaso. Primeiro vem a analise, que e feita
# inteira em Python no arquivo deployment/agente.py: os numeros, a posicao
# do municipio na distribuicao nacional, os achados, os alertas e o que
# acompanhar. Essa parte aparece na hora e nao usa IA nenhuma.
#
# So depois, e so se a pessoa clicar no botao, o modelo de linguagem entra.
# A unica tarefa dele e transformar a analise em texto corrido. Ele nao
# calcula nada e nao decide nada.
#
# A pagina nao carrega modelo nenhum por conta propria: ela pede tudo para
# a API (deployment/api.py), que e quem tem o modelo na memoria.

st.title("Diagnóstico com IA")

st.write(
    "Esta página junta as duas metades do projeto. A primeira metade é a **análise**, "
    "feita por regras em Python: ela compara o município com a distribuição nacional "
    "daquele ano e aponta o que chama atenção. A segunda metade é o **diagnóstico**, "
    "em que um modelo de linguagem local transforma essa análise em texto corrido."
)

st.info(
    "**Quem faz o quê.** Todos os números e todas as conclusões desta página saem da "
    "análise em Python. O modelo de linguagem só escreve: ele recebe a análise pronta e "
    "tem ordem expressa de não calcular nada. Foi assim porque nos testes, quando ele "
    "calculava, ele errava — somava percentuais que não deviam ser somados e comparava "
    "PIB total com PIB por habitante.",
    icon=":material/balance:",
)

endereco = st.text_input("Endereço da API", st.session_state["endereco_api"])
st.session_state["endereco_api"] = endereco

# guarda os diagnosticos ja gerados nesta sessao. gerar leva quase um minuto,
# entao seria ruim perder o texto so porque a pagina recarregou.
if "diagnosticos_gerados" not in st.session_state:
    st.session_state["diagnosticos_gerados"] = {}


# conversa com a api. o tempo limite e grande de proposito: o primeiro
# pedido carrega o modelo e depois escreve, e isso pode passar de um minuto.
def perguntar(caminho, metodo="GET", corpo=None):
    # os tres except separados sao de proposito. no comeco eu tinha um
    # except Exception sozinho, que dizia "a API nao respondeu" para
    # qualquer problema. quando o erro de verdade foi dentro do painel, a
    # mensagem apontou para o lado errado e me custou tempo. agora cada
    # tipo de falha diz o que ela e.
    try:
        if metodo == "GET":
            resposta = requests.get(endereco + caminho, timeout=300)
        else:
            resposta = requests.post(endereco + caminho, json=corpo, timeout=300)
    except requests.exceptions.Timeout:
        return None, "demorou", "A API não respondeu dentro de 5 minutos."
    except requests.exceptions.RequestException:
        return None, "sem_api", "Não consegui falar com a API."
    except Exception as erro:
        return None, "erro_no_painel", str(erro)

    if resposta.status_code == 200:
        return resposta.json(), "", ""

    try:
        detalhe = resposta.json().get("detail", "")
    except Exception:
        detalhe = ""

    return None, str(resposta.status_code), str(detalhe)


# deixa so a primeira letra maiuscula, sem mexer no resto da frase.
# o .capitalize() do python nao serve aqui porque ele rebaixa o resto.
def com_maiuscula(texto):
    if texto == "":
        return texto
    return texto[0].upper() + texto[1:]


def mostrar_erro(codigo_do_erro, detalhe):
    if codigo_do_erro == "503":
        st.error("**Modelo indisponível (503).** " + detalhe)
        st.info(
            "Isso acontece quando o PyTorch ou o Transformers não carregaram. "
            "Pare a API com Ctrl+C e ligue de novo para ela tentar outra vez."
        )
    elif codigo_do_erro == "429":
        st.warning("**Modelo ocupado (429).** " + detalhe)
    elif codigo_do_erro == "404":
        st.warning("**Não encontrado (404).** " + detalhe)
    elif codigo_do_erro == "422":
        st.warning("**Formato do pedido inválido (422).** " + detalhe)
    elif codigo_do_erro == "sem_api":
        st.error("**A API não está respondendo.** " + detalhe)
        st.info(
            "Confira se a janela do PowerShell com o uvicorn ainda está aberta e se o "
            "endereço acima está certo."
        )
    elif codigo_do_erro == "demorou":
        st.error("**A API demorou demais para responder.** " + detalhe)
        st.info(
            "O modelo pode estar sem memória para trabalhar. Feche o navegador e os "
            "programas pesados e tente de novo."
        )
    elif codigo_do_erro == "erro_no_painel":
        # este caso nao e culpa da API: o pedido nem chegou a sair daqui.
        st.error("**O erro aconteceu aqui no painel, antes do pedido sair.**")
        st.code(detalhe, language=None)
    else:
        st.error("A API respondeu com erro " + codigo_do_erro + ". " + detalhe)


# =========================================================
# 1. a API esta no ar? e o modelo, como esta?
# =========================================================
situacao, codigo_do_erro, detalhe = perguntar("/modelo_diagnostico")

if situacao is None:
    st.error(detalhe)
    st.info(
        "Abra um segundo terminal no VS Code (botão + ao lado de powershell), ative o venv e rode: "
        "py -m uvicorn deployment.api:app . Depois volte aqui e recarregue a página."
    )
    st.stop()

if situacao["estado"] == "falhou":
    st.error("O modelo não pôde ser carregado. " + situacao["mensagem_do_erro"])
    st.info("A análise abaixo continua funcionando, porque ela não depende do modelo.")
elif situacao["estado"] == "pronto":
    st.success(
        "Modelo carregado e pronto: " + situacao["modelo"] + " rodando em " +
        situacao["dispositivo"].upper() + ". Carregou em " +
        str(situacao["segundos_para_carregar"]) + " s e já escreveu " +
        str(situacao["diagnosticos_gerados"]) + " diagnóstico(s) nesta sessão da API."
    )
else:
    st.caption(
        "O modelo ainda não está na memória. Ele é carregado na primeira vez que alguém "
        "pede um diagnóstico, e isso leva cerca de 10 segundos. A análise logo abaixo não "
        "espera por ele."
    )

st.divider()

# =========================================================
# 2. a analise, feita em Python, sem IA
# =========================================================
codigo_municipio = st.session_state["codigo"]
ano = st.session_state["ano"]

saida, codigo_do_erro, detalhe = perguntar("/analise/" + str(codigo_municipio) + "?ano=" + str(ano))

if saida is None:
    mostrar_erro(codigo_do_erro, detalhe)
    st.stop()

analise = saida["analise"]
numeros = analise["numeros"]
faixas = analise["faixas"]

# quando o municipio tem o mesmo nome do estado (Rio de Janeiro, Sao Paulo),
# escrever o nome duas vezes fica estranho. nesse caso vai so a sigla.
if analise["municipio"] == analise["estado"]:
    entre_parenteses = analise["uf"]
else:
    entre_parenteses = analise["estado"]

if analise["e_capital"] is True:
    linha_de_cima = analise["municipio"] + " (" + entre_parenteses + "), capital, " + str(analise["ano"])
else:
    linha_de_cima = analise["municipio"] + " (" + entre_parenteses + "), " + str(analise["ano"])

st.header(linha_de_cima)
st.caption("Região " + analise["regiao"] + " | Código IBGE " + str(analise["codigo"]) + " | Perfil econômico: " + analise["perfil"])

coluna1, coluna2, coluna3, coluna4 = st.columns(4)
coluna1.metric("População", comum.formata_numero(numeros["populacao"]))
coluna2.metric("PIB", comum.formata_pib(numeros["pib_mil_reais"]))
coluna3.metric("PIB por habitante", "R$ " + comum.formata_numero(numeros["pib_por_habitante"]))
coluna4.metric(
    "Posição no PIB nacional",
    str(numeros["posicao_no_ranking"]) + "º",
    help="Entre os " + comum.formata_numero(numeros["total_de_municipios"]) + " municípios com dado neste ano.",
)

# o cifrao vai escapado (R\$) porque o Streamlit le o que estiver entre dois
# cifroes como formula matematica. esta frase tem dois, e sem o escape o
# trecho do meio aparecia em italico de equacao.
st.caption(
    "Comparando: o PIB por habitante do Brasil neste ano foi de R\\$ " +
    comum.formata_numero(numeros["pib_por_habitante_brasil"]) +
    " e a mediana do estado foi de R\\$ " +
    comum.formata_numero(numeros["pib_por_habitante_mediano_estado"]) + "."
)

# as faixas, que sao percentis da distribuicao nacional calculados na hora
st.subheader("Onde este município se encontra no país")

if analise["tem_dados_setoriais"] is True:
    faixa1, faixa2, faixa3 = st.columns(3)
    with faixa1:
        st.caption("Riqueza por habitante")
        st.markdown("### " + com_maiuscula(faixas["riqueza"]))
    with faixa2:
        st.caption("Dependência do setor público")
        st.markdown("### " + com_maiuscula(faixas["dependencia_publica"]))
    with faixa3:
        st.caption("Concentração setorial")
        st.markdown("### " + com_maiuscula(faixas["concentracao_setorial"]))
else:
    st.caption("Riqueza por habitante")
    st.markdown("### " + com_maiuscula(faixas["riqueza"]))
    st.info(
        "O IBGE ainda não publicou a abertura por setor de " + str(analise["ano"]) + ", então a "
        "parte setorial da análise fica de fora neste ano. Para ver a análise completa, escolha "
        "2021 na barra lateral, que é o último ano com dados por setor.",
        icon=":material/info:",
    )

st.caption(
    "Estas faixas não são números que eu escolhi. Elas são os percentis 25, 50, 75 e 90 da "
    "distribuição nacional daquele ano, calculados na hora, com todos os municípios da base."
)

st.divider()

# =========================================================
# 3. os graficos
# =========================================================
st.subheader("Como a economia local se divide")

if analise["tem_dados_setoriais"] is True:
    grafico_setores = pd.DataFrame(
        {
            "setor": ["Agropecuária", "Indústria", "Serviços", "Administração pública"],
            "participacao": [
                numeros["participacao_agropecuaria"],
                numeros["participacao_industria"],
                numeros["participacao_servicos"],
                numeros["participacao_administracao_publica"],
            ],
        }
    )

    coluna_esquerda, coluna_direita = st.columns(2)

    with coluna_esquerda:
        st.caption("Participação de cada setor no valor adicionado (%)")
        st.bar_chart(grafico_setores, x="setor", y="participacao")

    with coluna_direita:
        grafico_dependencia = pd.DataFrame(
            {
                "comparacao": ["Este município", "Mediana do estado", "Mediana do Brasil"],
                "dependencia": [
                    numeros["dependencia_administracao_publica"],
                    numeros["dependencia_mediana_do_estado"],
                    numeros["dependencia_mediana_do_brasil"],
                ],
            }
        )
        st.caption("Dependência da administração pública, comparada (%)")
        st.bar_chart(grafico_dependencia, x="comparacao", y="dependencia")
else:
    st.caption("Sem abertura por setor neste ano.")

st.subheader("A trajetória ao longo dos anos")

indicadores = comum.carregar_indicadores()
historico = indicadores[indicadores["codigo"] == codigo_municipio]
historico = historico.sort_values("ano")

# o ano vira texto antes de entrar no grafico. como numero, o Streamlit
# aplica separador de milhar e o eixo sai escrito "2,010", "2,011".
anos_em_texto = []
riqueza_por_ano = []
for ano_da_linha, razao in zip(historico["ano"], historico["razao_riqueza"]):
    anos_em_texto.append(str(ano_da_linha))
    riqueza_por_ano.append(razao)

grafico_trajetoria = pd.DataFrame()
grafico_trajetoria["ano"] = anos_em_texto
grafico_trajetoria["Município"] = riqueza_por_ano
grafico_trajetoria["Brasil"] = 1.0

st.line_chart(grafico_trajetoria, x="ano", y=["Município", "Brasil"])
st.caption(
    "A linha do município é o PIB por habitante dele dividido pelo do Brasil. A linha do "
    "Brasil vale 1,00 por definição. Acima de 1,00 o município é mais rico que a média do "
    "país; abaixo de 1,00, mais pobre."
)

st.divider()

# =========================================================
# 4. o que a analise apurou
# =========================================================
st.subheader("O que a análise apurou")

aba_achados, aba_alertas, aba_acompanhar = st.tabs(
    [
        "Achados (" + str(len(analise["achados"])) + ")",
        "Alertas (" + str(len(analise["alertas"])) + ")",
        "O que acompanhar (" + str(len(analise["acompanhar"])) + ")",
    ]
)

with aba_achados:
    st.caption("Fatos apurados a partir dos indicadores, sem juízo de valor.")
    for frase in analise["achados"]:
        st.write("- " + frase)

with aba_alertas:
    if len(analise["alertas"]) == 0:
        st.success("Nenhuma regra de alerta foi disparada para este município neste ano.")
    else:
        st.caption("Pontos de atenção disparados pelas regras de decisão do agente.")
        for frase in analise["alertas"]:
            st.warning(frase)

with aba_acompanhar:
    st.caption("O que valeria a pena acompanhar nos próximos anos.")
    for frase in analise["acompanhar"]:
        st.write("- " + frase)

st.divider()

# =========================================================
# 5. o diagnostico escrito pelo modelo
# =========================================================
st.subheader("O diagnóstico escrito pela IA")

st.write(
    "Até aqui nada passou por modelo de linguagem. Clicando no botão abaixo, a análise que "
    "você acabou de ver é enviada para o modelo local, que a transforma em três parágrafos "
    "de texto corrido."
)

st.warning(
    "**O texto abaixo é escrito por máquina.** O modelo é pequeno e roda na CPU desta "
    "máquina. Ele pode repetir uma ideia ou escrever uma frase torta. Os números dele vêm "
    "todos da análise acima, então a conferência é direta: qualquer número do texto tem que "
    "estar também nas abas de achados e alertas.",
    icon=":material/warning:",
)

chave = str(codigo_municipio) + "_" + str(ano)

if st.button("Escrever o diagnóstico com a IA", type="primary"):
    # o int() garante que vao dois numeros comuns do Python para o json.
    # o comum.py ja converte, mas repetir aqui nao custa nada e deixa a
    # pagina de pe mesmo se alguem mexer no comum.py depois.
    corpo = {"codigo": int(codigo_municipio), "ano": int(ano)}

    with st.spinner("O modelo está escrevendo. Isso leva de 1 a 4 minutos, e na primeira vez ele ainda precisa carregar."):
        resultado, codigo_do_erro, detalhe = perguntar("/diagnostico", "POST", corpo)

    if resultado is None:
        mostrar_erro(codigo_do_erro, detalhe)
    else:
        st.session_state["diagnosticos_gerados"][chave] = resultado

# mostra o diagnostico deste municipio e deste ano, se ja tiver sido gerado
if chave in st.session_state["diagnosticos_gerados"]:
    resultado = st.session_state["diagnosticos_gerados"][chave]

    st.success(resultado["texto"])

    ficha1, ficha2, ficha3, ficha4 = st.columns(4)
    ficha1.metric("Tempo da escrita", comum.formata_numero(resultado["segundos"], 1) + " s")
    ficha2.metric("Rodou em", resultado["dispositivo"].upper())
    ficha3.metric("Pedaços do prompt", comum.formata_numero(resultado["pedacos_do_prompt"]))
    ficha4.metric("Pedaços escritos", comum.formata_numero(resultado["pedacos_gerados"]))

    with st.expander("Ver o prompt exato que foi enviado ao modelo"):
        st.caption(
            "Este é o texto completo que o modelo recebeu. Tudo o que ele escreveu tem que "
            "sair daqui: se aparecer no diagnóstico um número que não está neste prompt, o "
            "modelo inventou."
        )
        st.code(resultado["prompt_enviado"], language=None)

st.divider()
st.caption(
    "Modelo: Qwen/Qwen2.5-1.5B-Instruct, de 1,54 bilhão de parâmetros, baixado da HuggingFace "
    "e executado localmente em bfloat16. Análise: deployment/agente.py. Prompt: "
    "deployment/diagnostico_llm.py. O histórico das cinco versões do prompt está em "
    "modeling/engenharia_de_prompt.md. Nenhum dado desta página sai da sua máquina."
)
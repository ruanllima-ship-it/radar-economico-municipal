import os

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as ExcecaoHTTPdoStarlette

# o import de cima funciona quando a API e ligada da raiz do projeto, que e
# o jeito recomendado. o de baixo cobre quem rodar de dentro da pasta
# deployment, para a API nao deixar de subir so por causa da pasta de onde
# o comando foi dado.
try:
    from deployment import modelo_llm
    from deployment import agente
    from deployment import diagnostico_llm
    from deployment.respostas import (
        RespostaRaiz,
        RespostaMunicipio,
        RespostaRanking,
        RespostaBrasil,
        RespostaNoticias,
        RespostaComparacao,
        RespostaDoTextoProcessado,
        RespostaDoModelo,
        RespostaDaAnalise,
        RespostaDoDiagnostico,
        RespostaDoModeloDeDiagnostico,
        RespostaSimples,
        RespostaDeErro,
    )
except ImportError:
    import modelo_llm
    import agente
    import diagnostico_llm
    from respostas import (
        RespostaRaiz,
        RespostaMunicipio,
        RespostaRanking,
        RespostaBrasil,
        RespostaNoticias,
        RespostaComparacao,
        RespostaDoTextoProcessado,
        RespostaDoModelo,
        RespostaDaAnalise,
        RespostaDoDiagnostico,
        RespostaDoModeloDeDiagnostico,
        RespostaSimples,
        RespostaDeErro,
    )

# esta api entrega os indicadores do radar economico municipal para quem
# quiser consultar de fora, sem abrir o painel. o proprio app do streamlit
# usa ela na pagina "Consulta pela API"

app = FastAPI(
    title="API do Radar Econômico Municipal",
    description="Consulta dos indicadores de concentração econômica dos municípios brasileiros, calculados a partir do PIB dos Municípios do IBGE (tabela 5938 do SIDRA) e das notícias da Agência de Notícias do IBGE.",
    version="3.0",
)


# os caminhos sao montados a partir de __file__, e nao da pasta de onde o
# comando foi dado. assim a API acha os CSVs mesmo que seja ligada de outra
# pasta. a raiz do projeto e a pasta que contem esta pasta deployment.
pasta_deste_arquivo = os.path.dirname(os.path.abspath(__file__))
raiz_do_projeto = os.path.dirname(pasta_deste_arquivo)

caminho_indicadores = os.path.join(raiz_do_projeto, "data_acquisition", "cleaned_data", "indicadores_municipios.csv")
caminho_resumo = os.path.join(raiz_do_projeto, "data_acquisition", "cleaned_data", "resumo_brasil.csv")
caminho_noticias = os.path.join(raiz_do_projeto, "data", "noticias_ibge.csv")

# os arquivos sao lidos uma vez so, quando a api liga
indicadores = pd.read_csv(caminho_indicadores)
resumo = pd.read_csv(caminho_resumo)
noticias = pd.read_csv(caminho_noticias)


# formato do pedido da rota de comparacao
class PedidoComparacao(BaseModel):
    codigos: list[int]
    ano: int = 2023


# formato do pedido da rota que usa o modelo de linguagem
class PedidoDeTexto(BaseModel):
    texto: str = Field(min_length=1, description="Texto em portugues que sera analisado.")
    tipo_analise: str = Field("resumo", description="Hoje so existe resumo.")


# formato do pedido da rota do agente de diagnostico
class PedidoDeDiagnostico(BaseModel):
    codigo: int = Field(description="Codigo IBGE do municipio, com 7 digitos.")
    ano: int = Field(2021, description="2021 e o ultimo ano com dados por setor.")


# troca os vazios por None, porque o json nao aceita o NaN do pandas, e
# converte os numeros do numpy em numeros comuns do python, porque os
# Response Models do Pydantic nao reconhecem os tipos do numpy
def limpar(tabela):
    registros = tabela.to_dict(orient="records")
    limpos = []
    for registro in registros:
        novo = {}
        for chave in registro:
            valor = registro[chave]
            if pd.isna(valor):
                novo[chave] = None
            elif hasattr(valor, "item"):
                novo[chave] = valor.item()
            else:
                novo[chave] = valor
        limpos.append(novo)
    return limpos


# ------------------------------------------------------------------
# Tratamento global de erros
# ------------------------------------------------------------------
#
# Os dois tratadores abaixo valem para a API inteira. O primeiro garante
# que TODO erro previsto saia no mesmo formato, e traduz a mensagem padrao
# do FastAPI quando alguem chama uma rota que nao existe. O segundo e uma
# rede de seguranca: se algum erro que eu nao previ acontecer, o cliente
# recebe um JSON explicando, e nao uma pagina de erro do servidor.


@app.exception_handler(ExcecaoHTTPdoStarlette)
def tratar_erro_http(requisicao, excecao):
    """Deixa todo erro previsto no mesmo formato: {"detail": "..."}."""
    mensagem = excecao.detail

    if excecao.status_code == 404 and mensagem == "Not Found":
        mensagem = "Rota não encontrada. Veja as rotas disponíveis em / ou em /docs."

    if excecao.status_code == 405:
        mensagem = "Método HTTP errado para esta rota. Confira em /docs se ela é GET ou POST."

    return JSONResponse(status_code=excecao.status_code, content={"detail": mensagem})


@app.exception_handler(Exception)
def tratar_erro_inesperado(requisicao, excecao):
    """Rede de seguranca para qualquer erro que eu nao previ."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno inesperado na API. Detalhe: " + str(excecao)},
    )


@app.get("/", response_model=RespostaRaiz)
def raiz():
    """Mostra o que a API faz e quais rotas existem."""
    return {
        "nome": "API do Radar Econômico Municipal",
        "fonte": "IBGE - PIB dos Municípios (tabela 5938), Censos e Estimativas de População",
        "municipios": int(indicadores["codigo"].nunique()),
        "anos": str(indicadores["ano"].min()) + " a " + str(indicadores["ano"].max()),
        "rotas": {
            "GET /municipios/{codigo}": "indicadores de um município pelo código IBGE de 7 dígitos",
            "GET /ranking": "ranking de municípios, com filtros de ano, estado e critério",
            "GET /brasil": "resumo da concentração econômica do Brasil, ano a ano",
            "GET /noticias": "notícias do IBGE extraídas da web",
            "POST /comparar": "compara vários municípios de uma vez",
            "POST /processar_texto": "resume um texto em português com o modelo de linguagem local",
            "GET /modelo": "situação do modelo de linguagem que resume textos",
            "GET /analise/{codigo}": "análise econômica do município feita por regras, sem IA",
            "POST /diagnostico": "diagnóstico do município escrito pelo agente com IA local",
            "GET /modelo_diagnostico": "situação do modelo que escreve os diagnósticos",
            "GET /docs": "documentação interativa das rotas",
        },
    }


@app.get(
    "/municipios/{codigo}",
    response_model=RespostaMunicipio,
    responses={404: {"model": RespostaDeErro, "description": "Município ou ano não encontrado"}},
)
def consultar_municipio(codigo: int, ano: int = None):
    """Devolve os indicadores de um município. Sem o ano, devolve a série toda."""
    do_municipio = indicadores[indicadores["codigo"] == codigo]

    if len(do_municipio) == 0:
        raise HTTPException(status_code=404, detail="Município não encontrado. Use o código IBGE de 7 dígitos.")

    if ano is not None:
        do_municipio = do_municipio[do_municipio["ano"] == ano]
        if len(do_municipio) == 0:
            raise HTTPException(status_code=404, detail="Não existe dado desse município nesse ano.")

    primeira = do_municipio.iloc[0]
    return {
        "codigo": int(primeira["codigo"]),
        "municipio": primeira["municipio"],
        "uf": primeira["uf"],
        "regiao": primeira["regiao"],
        "capital": primeira["capital"],
        "anos_encontrados": len(do_municipio),
        "dados": limpar(do_municipio),
    }


@app.get(
    "/ranking",
    response_model=RespostaRanking,
    responses={
        400: {"model": RespostaDeErro, "description": "Critério inválido"},
        404: {"model": RespostaDeErro, "description": "Ano ou estado não encontrado"},
    },
)
def consultar_ranking(
    ano: int = 2023,
    uf: str = None,
    criterio: str = Query("pib", description="pib, pib_per_capita, dependencia_adm ou hhi"),
    limite: int = 20,
):
    """Devolve os municípios ordenados pelo critério escolhido."""
    permitidos = ["pib", "pib_per_capita", "dependencia_adm", "hhi", "participacao_pib", "razao_riqueza"]
    if criterio not in permitidos:
        raise HTTPException(status_code=400, detail="Critério inválido. Use um destes: " + ", ".join(permitidos))

    recorte = indicadores[indicadores["ano"] == ano]
    if len(recorte) == 0:
        raise HTTPException(status_code=404, detail="Ano não encontrado na base.")

    if uf is not None:
        recorte = recorte[recorte["uf"] == uf.upper()]
        if len(recorte) == 0:
            raise HTTPException(status_code=404, detail="Estado não encontrado. Use a sigla, como RJ.")

    if limite > 500:
        limite = 500

    recorte = recorte.sort_values(criterio, ascending=False)
    recorte = recorte.head(limite)
    colunas = ["codigo", "municipio", "uf", "ano", "pib", "populacao", "pib_per_capita", "razao_riqueza", "participacao_pib", "perfil", "dependencia_adm", "hhi"]

    return {
        "ano": ano,
        "uf": uf,
        "criterio": criterio,
        "quantidade": len(recorte),
        "dados": limpar(recorte[colunas]),
    }


@app.get(
    "/brasil",
    response_model=RespostaBrasil,
    responses={404: {"model": RespostaDeErro, "description": "Ano não encontrado"}},
)
def consultar_brasil(ano: int = None):
    """Devolve o resumo da concentração econômica do Brasil, ano a ano."""
    recorte = resumo
    if ano is not None:
        recorte = recorte[recorte["ano"] == ano]
        if len(recorte) == 0:
            raise HTTPException(status_code=404, detail="Ano não encontrado na base.")
    return {"quantidade": len(recorte), "dados": limpar(recorte)}


@app.get(
    "/noticias",
    response_model=RespostaNoticias,
    responses={404: {"model": RespostaDeErro, "description": "Nenhuma notícia nesse ano"}},
)
def consultar_noticias(ano: str = None, com_texto: bool = False):
    """Devolve as notícias do IBGE extraídas da web.

    Com com_texto=false o campo texto vem vazio, para a resposta não ficar
    enorme. O campo continua existindo, para o formato ser sempre o mesmo.
    """
    recorte = noticias.copy()
    if ano is not None:
        recorte = recorte[recorte["data"].str[0:4] == ano]
        if len(recorte) == 0:
            raise HTTPException(status_code=404, detail="Nenhuma notícia publicada nesse ano.")

    if com_texto is False:
        recorte = recorte.drop(columns=["texto"])

    return {
        "quantidade": len(recorte),
        "total_de_palavras": int(noticias["qtd_palavras"].sum()),
        "dados": limpar(recorte),
    }


@app.post(
    "/comparar",
    response_model=RespostaComparacao,
    responses={
        400: {"model": RespostaDeErro, "description": "Lista de códigos vazia ou grande demais"},
        404: {"model": RespostaDeErro, "description": "Ano não encontrado"},
    },
)
def comparar_municipios(pedido: PedidoComparacao):
    """Recebe uma lista de códigos IBGE e devolve os indicadores de todos no mesmo ano."""
    if len(pedido.codigos) == 0:
        raise HTTPException(status_code=400, detail="Mande pelo menos um código de município.")
    if len(pedido.codigos) > 50:
        raise HTTPException(status_code=400, detail="Máximo de 50 municípios por consulta.")

    recorte = indicadores[indicadores["ano"] == pedido.ano]
    if len(recorte) == 0:
        raise HTTPException(status_code=404, detail="Ano não encontrado na base.")

    encontrados = recorte[recorte["codigo"].isin(pedido.codigos)]

    # avisando quais codigos nao existem na base
    nao_encontrados = []
    for codigo in pedido.codigos:
        if codigo not in list(encontrados["codigo"]):
            nao_encontrados.append(codigo)

    colunas = ["codigo", "municipio", "uf", "ano", "pib", "populacao", "pib_per_capita", "razao_riqueza", "participacao_pib", "posicao_pib", "perfil", "dependencia_adm", "hhi"]

    return {
        "ano": pedido.ano,
        "pedidos": len(pedido.codigos),
        "encontrados": len(encontrados),
        "nao_encontrados": nao_encontrados,
        "dados": limpar(encontrados[colunas]),
    }


# ------------------------------------------------------------------
# Rotas do modelo de linguagem (TP4)
# ------------------------------------------------------------------


@app.get("/modelo", response_model=RespostaDoModelo)
def consultar_modelo():
    """Informa a situação do modelo de linguagem, sem carregá-lo."""
    return modelo_llm.situacao()


@app.post(
    "/processar_texto",
    response_model=RespostaDoTextoProcessado,
    responses={
        400: {"model": RespostaDeErro, "description": "Texto curto demais ou tipo de análise não suportado"},
        413: {"model": RespostaDeErro, "description": "Texto grande demais"},
        429: {"model": RespostaDeErro, "description": "O modelo já está gerando outro resumo"},
        500: {"model": RespostaDeErro, "description": "O modelo falhou durante a geração"},
        503: {"model": RespostaDeErro, "description": "O modelo de linguagem não pôde ser carregado"},
    },
)
def processar_texto(pedido: PedidoDeTexto):
    """Recebe um texto em português e devolve o resumo feito pelo modelo local.

    Na primeira chamada o modelo é carregado na memória, o que leva cerca de
    13 segundos. As chamadas seguintes respondem em poucos segundos.
    """
    analises_suportadas = ["resumo"]
    if pedido.tipo_analise not in analises_suportadas:
        raise HTTPException(
            status_code=400,
            detail="Tipo de análise não suportado. Por enquanto a API faz apenas: " + ", ".join(analises_suportadas),
        )

    texto = pedido.texto.strip()

    if len(texto) < 200:
        raise HTTPException(
            status_code=400,
            detail="Texto curto demais para resumir. Mande pelo menos 200 caracteres, você mandou " + str(len(texto)) + ".",
        )

    if len(texto) > 50000:
        raise HTTPException(
            status_code=413,
            detail="Texto grande demais. O limite é de 50.000 caracteres e você mandou " + str(len(texto)) + ".",
        )

    carregou = modelo_llm.carregar()
    if carregou is False:
        raise HTTPException(
            status_code=503,
            detail="O modelo de linguagem não está disponível no momento. " + modelo_llm.situacao()["mensagem_do_erro"],
        )

    try:
        saida = modelo_llm.resumir(texto)
    except modelo_llm.ModeloOcupado:
        raise HTTPException(
            status_code=429,
            detail="O modelo está ocupado gerando outro resumo. Espere alguns segundos e tente de novo.",
        )
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail="O modelo foi carregado mas falhou ao gerar o resumo. Detalhe: " + str(erro),
        )

    return {
        "tipo_analise": "resumo",
        "modelo": modelo_llm.nome_do_modelo,
        "dispositivo": modelo_llm.dispositivo,
        "caracteres_recebidos": len(texto),
        "pedacos_do_texto": saida["pedacos_do_texto"],
        "pedacos_lidos": saida["pedacos_lidos"],
        "texto_cortado": saida["texto_cortado"],
        "segundos": saida["segundos"],
        "resultado": saida["resumo"],
    }


# ------------------------------------------------------------------
# Rotas do agente de diagnostico municipal (TP5)
# ------------------------------------------------------------------
#
# Sao duas rotas de proposito. A GET /analise devolve a analise feita por
# regras em Python, na hora, sem tocar no modelo de linguagem. A POST
# /diagnostico devolve a mesma analise MAIS o texto escrito pelo modelo.
#
# Quem quiser so os numeros e os alertas nao precisa esperar o modelo nem
# gastar memoria com ele.


@app.get(
    "/analise/{codigo}",
    response_model=RespostaDaAnalise,
    responses={404: {"model": RespostaDeErro, "description": "Município ou ano não encontrado"}},
)
def consultar_analise(codigo: int, ano: int = 2021):
    """Devolve a análise econômica do município, feita por regras, sem IA.

    Responde na hora: não carrega modelo nenhum e não usa memória extra.
    """
    analise = agente.montar_analise(indicadores, codigo, ano)
    if analise is None:
        raise HTTPException(
            status_code=404,
            detail="Não encontrei esse município nesse ano. Use o código IBGE de 7 dígitos.",
        )
    return {"analise": analise}


@app.get("/modelo_diagnostico", response_model=RespostaDoModeloDeDiagnostico)
def consultar_modelo_diagnostico():
    """Informa a situação do modelo que escreve os diagnósticos, sem carregá-lo."""
    return diagnostico_llm.situacao()


@app.post("/modelo_diagnostico/descarregar", response_model=RespostaSimples)
def descarregar_modelo_diagnostico():
    """Tira o modelo de diagnóstico da memória.

    Existe porque o modelo ocupa cerca de 2,9 GB e a máquina de
    desenvolvimento tem 15,7 GB no total. Depois de gerar os diagnósticos,
    descarregar devolve essa memória sem precisar reiniciar a API.
    """
    diagnostico_llm.descarregar()
    return {"ok": True, "mensagem": "Modelo de diagnóstico retirado da memória."}


@app.post(
    "/diagnostico",
    response_model=RespostaDoDiagnostico,
    responses={
        404: {"model": RespostaDeErro, "description": "Município ou ano não encontrado"},
        429: {"model": RespostaDeErro, "description": "O modelo já está escrevendo outro diagnóstico"},
        500: {"model": RespostaDeErro, "description": "O modelo falhou ao escrever"},
        503: {"model": RespostaDeErro, "description": "O modelo de linguagem não pôde ser carregado"},
    },
)
def gerar_diagnostico_do_municipio(pedido: PedidoDeDiagnostico):
    """Devolve a análise do município e o diagnóstico escrito pelo modelo local.

    A primeira chamada carrega o modelo, o que leva cerca de 10 segundos.
    Escrever o texto leva de 40 a 60 segundos, porque o modelo roda em CPU.
    """
    analise = agente.montar_analise(indicadores, pedido.codigo, pedido.ano)
    if analise is None:
        raise HTTPException(
            status_code=404,
            detail="Não encontrei esse município nesse ano. Use o código IBGE de 7 dígitos.",
        )

    carregou = diagnostico_llm.carregar()
    if carregou is False:
        raise HTTPException(
            status_code=503,
            detail="O modelo de linguagem não está disponível no momento. "
            + diagnostico_llm.situacao()["mensagem_do_erro"],
        )

    try:
        saida = diagnostico_llm.gerar_diagnostico(analise)
    except diagnostico_llm.ModeloOcupado:
        raise HTTPException(
            status_code=429,
            detail="O modelo está ocupado escrevendo outro diagnóstico. Espere e tente de novo.",
        )
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail="O modelo foi carregado mas falhou ao escrever o diagnóstico. Detalhe: " + str(erro),
        )

    return {
        "analise": analise,
        "texto": saida["texto"],
        "modelo": diagnostico_llm.nome_do_modelo,
        "dispositivo": diagnostico_llm.dispositivo,
        "segundos": saida["segundos"],
        "pedacos_do_prompt": saida["pedacos_do_prompt"],
        "pedacos_gerados": saida["pedacos_gerados"],
        "prompt_enviado": saida["prompt_enviado"],
    }
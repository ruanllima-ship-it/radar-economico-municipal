import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# esta api entrega os indicadores do radar economico municipal para quem
# quiser consultar de fora, sem abrir o painel. o proprio app do streamlit
# usa ela na pagina "Consulta pela API"

app = FastAPI(
    title="API do Radar Econômico Municipal",
    description="Consulta dos indicadores de concentração econômica dos municípios brasileiros, calculados a partir do PIB dos Municípios do IBGE (tabela 5938 do SIDRA) e das notícias da Agência de Notícias do IBGE.",
    version="1.0",
)


# os arquivos sao lidos uma vez so, quando a api liga
indicadores = pd.read_csv("data_acquisition/cleaned_data/indicadores_municipios.csv")
resumo = pd.read_csv("data_acquisition/cleaned_data/resumo_brasil.csv")
noticias = pd.read_csv("data/noticias_ibge.csv")


# formato do pedido da rota de comparacao
class PedidoComparacao(BaseModel):
    codigos: list[int]
    ano: int = 2023


# troca os vazios por None, porque o json nao aceita o NaN do pandas
def limpar(tabela):
    registros = tabela.to_dict(orient="records")
    limpos = []
    for registro in registros:
        novo = {}
        for chave in registro:
            valor = registro[chave]
            if pd.isna(valor):
                novo[chave] = None
            else:
                novo[chave] = valor
        limpos.append(novo)
    return limpos


@app.get("/")
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
            "GET /docs": "documentação interativa das rotas",
        },
    }


@app.get("/municipios/{codigo}")
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


@app.get("/ranking")
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


@app.get("/brasil")
def consultar_brasil(ano: int = None):
    """Devolve o resumo da concentração econômica do Brasil, ano a ano."""
    recorte = resumo
    if ano is not None:
        recorte = recorte[recorte["ano"] == ano]
        if len(recorte) == 0:
            raise HTTPException(status_code=404, detail="Ano não encontrado na base.")
    return {"quantidade": len(recorte), "dados": limpar(recorte)}


@app.get("/noticias")
def consultar_noticias(ano: str = None, com_texto: bool = False):
    """Devolve as notícias do IBGE extraídas da web."""
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


@app.post("/comparar")
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
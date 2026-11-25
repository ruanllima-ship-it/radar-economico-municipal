# respostas.py
# Response Models da API do Radar Economico Municipal.
#
# Ate o TP3 as rotas devolviam dicionarios montados na mao, e o FastAPI
# aceitava qualquer coisa que saisse de la. Aqui eu declaro, em Pydantic,
# o formato exato de cada resposta. Com isso o FastAPI passa a conferir
# todo retorno antes de mandar para o cliente, e a documentacao em /docs
# passa a mostrar os campos e os tipos de cada rota.

from pydantic import BaseModel


# ------------------------------------------------------------------
# Linhas das tabelas
# ------------------------------------------------------------------


class LinhaDoMunicipio(BaseModel):
    """Um municipio em um ano, com todos os indicadores calculados.

    Os campos de VAB e os derivados dele ficam vazios nos anos de 2022 e
    2023, porque o IBGE ainda nao publicou a abertura por setor.
    """

    codigo: int
    municipio: str
    uf: str
    regiao: str
    capital: str
    ano: int
    pib: float | None = None
    populacao: float | None = None
    participacao_pib: float | None = None
    pib_per_capita: float | None = None
    pib_per_capita_brasil: float | None = None
    razao_riqueza: float | None = None
    posicao_pib: int | None = None
    participacao_acumulada: float | None = None
    vab_total: float | None = None
    vab_agropecuaria: float | None = None
    vab_industria: float | None = None
    vab_servicos: float | None = None
    vab_adm_publica: float | None = None
    part_agropecuaria: float | None = None
    part_industria: float | None = None
    part_servicos: float | None = None
    part_adm_publica: float | None = None
    hhi: float | None = None
    dependencia_adm: float | None = None
    perfil: str | None = None


class LinhaDoRanking(BaseModel):
    """Um municipio dentro de um ranking. E um recorte das colunas principais."""

    codigo: int
    municipio: str
    uf: str
    ano: int
    pib: float | None = None
    populacao: float | None = None
    pib_per_capita: float | None = None
    razao_riqueza: float | None = None
    participacao_pib: float | None = None
    perfil: str | None = None
    dependencia_adm: float | None = None
    hhi: float | None = None


class LinhaDaComparacao(BaseModel):
    """Um municipio dentro de uma comparacao. Igual ao ranking, mais a posicao no PIB."""

    codigo: int
    municipio: str
    uf: str
    ano: int
    pib: float | None = None
    populacao: float | None = None
    pib_per_capita: float | None = None
    razao_riqueza: float | None = None
    participacao_pib: float | None = None
    posicao_pib: int | None = None
    perfil: str | None = None
    dependencia_adm: float | None = None
    hhi: float | None = None


class LinhaDoBrasil(BaseModel):
    """O retrato da concentracao economica do pais inteiro em um ano."""

    ano: int
    pib_brasil_mil_reais: float | None = None
    populacao_brasil: float | None = None
    pib_per_capita_brasil: float | None = None
    municipios_metade_pib: int | None = None
    participacao_capitais: float | None = None
    participacao_10_maiores: float | None = None


class Noticia(BaseModel):
    """Uma materia da Agencia de Noticias do IBGE coletada com Selenium.

    O campo texto so vem preenchido quando a rota e chamada com
    com_texto=true. Nos outros casos ele vem vazio, mas continua existindo,
    para que o formato da resposta seja sempre o mesmo.
    """

    data: str
    tipo: str | None = None
    titulo: str
    resumo: str | None = None
    qtd_paragrafos: int | None = None
    qtd_palavras: int | None = None
    link: str
    texto: str | None = None


# ------------------------------------------------------------------
# Respostas completas de cada rota
# ------------------------------------------------------------------


class RespostaRaiz(BaseModel):
    """Cartao de visita da API: o que ela faz e quais rotas existem."""

    nome: str
    fonte: str
    municipios: int
    anos: str
    rotas: dict[str, str]


class RespostaMunicipio(BaseModel):
    """Resposta da rota GET /municipios/{codigo}."""

    codigo: int
    municipio: str
    uf: str
    regiao: str
    capital: str
    anos_encontrados: int
    dados: list[LinhaDoMunicipio]


class RespostaRanking(BaseModel):
    """Resposta da rota GET /ranking."""

    ano: int
    uf: str | None = None
    criterio: str
    quantidade: int
    dados: list[LinhaDoRanking]


class RespostaBrasil(BaseModel):
    """Resposta da rota GET /brasil."""

    quantidade: int
    dados: list[LinhaDoBrasil]


class RespostaNoticias(BaseModel):
    """Resposta da rota GET /noticias."""

    quantidade: int
    total_de_palavras: int
    dados: list[Noticia]


class RespostaComparacao(BaseModel):
    """Resposta da rota POST /comparar.

    O campo nao_encontrados traz os codigos que o cliente pediu mas que
    nao existem na base naquele ano, para ele saber o que faltou.
    """

    ano: int
    pedidos: int
    encontrados: int
    nao_encontrados: list[int]
    dados: list[LinhaDaComparacao]


class RespostaDeErro(BaseModel):
    """Formato de toda resposta de erro da API.

    O FastAPI devolve os erros dentro de uma chave chamada detail. Declarar
    isso aqui faz a documentacao em /docs mostrar o formato do erro junto
    com o formato do sucesso.
    """

    detail: str


# ------------------------------------------------------------------
# Respostas das rotas do modelo de linguagem (TP4)
# ------------------------------------------------------------------


class RespostaDoTextoProcessado(BaseModel):
    """Resposta da rota POST /processar_texto.

    Alem do resultado, a resposta diz qual analise foi feita, qual modelo
    gerou, em que dispositivo rodou e quanto do texto o modelo conseguiu
    ler de verdade. Esse ultimo ponto importa: o modelo le no maximo 512
    pedacos por vez, e o campo texto_cortado avisa quando o texto enviado
    era maior que isso.
    """

    tipo_analise: str
    modelo: str
    dispositivo: str
    caracteres_recebidos: int
    pedacos_do_texto: int
    pedacos_lidos: int
    texto_cortado: bool
    segundos: float
    resultado: str


class RespostaDoModelo(BaseModel):
    """Resposta da rota GET /modelo.

    Serve para saber se o modelo ja esta carregado sem precisar pedir um
    resumo. O estado pode ser nao_carregado, carregando, pronto ou falhou.
    """

    modelo: str
    estado: str
    dispositivo: str
    segundos_para_carregar: float
    resumos_gerados: int
    mensagem_do_erro: str
    limite_de_entrada: int

    # ------------------------------------------------------------------
# Respostas do agente de diagnostico municipal (TP5)
# ------------------------------------------------------------------


class TrajetoriaDoMunicipio(BaseModel):
    """Como a riqueza do municipio andou do primeiro ao ultimo ano da base."""

    primeiro_ano: int
    ultimo_ano: int
    razao_riqueza_no_inicio: float
    razao_riqueza_no_fim: float
    sentido: str
    variacao_percentual: float | None = None


class AnaliseDoMunicipio(BaseModel):
    """A analise feita pelo agente, em Python, sem modelo de linguagem.

    Este e o resultado do arquivo deployment/agente.py: os numeros do
    municipio, a posicao dele na distribuicao nacional do ano, os fatos
    apurados pelas regras de decisao, os alertas e o que acompanhar.
    """

    codigo: int
    municipio: str
    uf: str
    estado: str
    regiao: str
    e_capital: bool
    ano: int
    perfil: str
    tem_dados_setoriais: bool
    numeros: dict[str, int | float | None]
    faixas: dict[str, str]
    trajetoria: TrajetoriaDoMunicipio | None = None
    achados: list[str]
    alertas: list[str]
    acompanhar: list[str]


class RespostaDaAnalise(BaseModel):
    """Resposta da rota GET /analise/{codigo}.

    So a analise, sem passar pelo modelo de linguagem. Responde na hora,
    sem carregar nada na memoria.
    """

    analise: AnaliseDoMunicipio


class RespostaDoDiagnostico(BaseModel):
    """Resposta da rota POST /diagnostico.

    Traz a analise E o texto escrito pelo modelo a partir dela. O campo
    prompt_enviado devolve o prompt exato que foi usado, para quem quiser
    conferir que nenhum numero do texto saiu de fora dele.
    """

    analise: AnaliseDoMunicipio
    texto: str
    modelo: str
    dispositivo: str
    segundos: float
    pedacos_do_prompt: int
    pedacos_gerados: int
    prompt_enviado: str


class RespostaDoModeloDeDiagnostico(BaseModel):
    """Resposta da rota GET /modelo_diagnostico.

    Serve para saber se o modelo que escreve os diagnosticos ja esta
    carregado, sem carrega-lo. O estado pode ser nao_carregado,
    carregando, pronto ou falhou.
    """

    modelo: str
    estado: str
    dispositivo: str
    segundos_para_carregar: float
    diagnosticos_gerados: int
    mensagem_do_erro: str
    pedacos_maximos: int


class RespostaSimples(BaseModel):
    """Resposta curta para acoes que so confirmam que deram certo."""

    ok: bool
    mensagem: str
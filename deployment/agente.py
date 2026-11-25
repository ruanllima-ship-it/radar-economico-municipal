# agente.py
# O motor de analise do diagnostico municipal.
#
# Este arquivo NAO usa modelo de linguagem nenhum, e isso e de proposito.
# Toda a analise acontece aqui, em Python: ler os indicadores, comparar o
# municipio com o estado e com o pais, olhar a trajetoria ao longo dos anos
# e aplicar regras de decisao. O resultado e uma analise estruturada.
#
# O modelo de linguagem entra depois, no arquivo diagnostico_llm.py, e a
# unica tarefa dele e transformar esta analise em texto corrido. Ele nunca
# calcula nada, porque quando ele calcula, ele erra.
#
# As faixas de classificacao nao sao numeros que eu inventei. Elas sao os
# percentis da distribuicao nacional daquele ano, calculados na hora. Dizer
# que a dependencia e "muito alta" aqui significa que o municipio esta entre
# os 10% mais dependentes do Brasil naquele ano.

import pandas as pd


# o prompt precisa do nome do estado por extenso. quando recebe so a sigla,
# o modelo chuta o nome e erra (ele trocou RR por Rio Grande do Norte).
estados = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AM": "Amazonas",
    "AP": "Amapá",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso",
    "PA": "Pará",
    "PB": "Paraíba",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "PR": "Paraná",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RO": "Rondônia",
    "RR": "Roraima",
    "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina",
    "SE": "Sergipe",
    "SP": "São Paulo",
    "TO": "Tocantins",
}


def numero_br(valor, casas=1):
    """Escreve o numero no jeito brasileiro: 83,5 em vez de 83.5."""
    if valor is None or pd.isna(valor):
        return "sem dado"
    texto = f"{valor:,.{casas}f}"
    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")
    return texto


def arredondar(valor, casas=2):
    """Arredonda, e devolve None quando o dado nao existe.

    Com casas=0 devolve numero inteiro de verdade, e nao 11014.0. Isso
    importa porque esses valores sao contagens (habitantes, posicao no
    ranking) e aparecem na resposta da API.
    """
    if valor is None:
        return None
    if pd.isna(valor):
        return None
    if casas == 0:
        return int(round(float(valor)))
    return round(float(valor), casas)


def classificar_por_percentil(valor, serie, rotulos):
    """Diz em que faixa da distribuicao nacional um valor cai.

    Recebe os quatro rotulos na ordem: abaixo do percentil 25, ate a
    mediana, ate o percentil 75, ate o percentil 90, e acima dele.
    """
    if valor is None or pd.isna(valor):
        return "sem dado"

    p25 = serie.quantile(0.25)
    p50 = serie.quantile(0.50)
    p75 = serie.quantile(0.75)
    p90 = serie.quantile(0.90)

    if valor < p25:
        return rotulos[0]
    if valor < p50:
        return rotulos[1]
    if valor < p75:
        return rotulos[2]
    if valor < p90:
        return rotulos[3]
    return rotulos[4]


def olhar_trajetoria(indicadores, codigo):
    """Compara o primeiro e o ultimo ano do municipio na base."""
    do_municipio = indicadores[indicadores["codigo"] == codigo]
    do_municipio = do_municipio.sort_values("ano")

    if len(do_municipio) < 2:
        return None

    primeira = do_municipio.iloc[0]
    ultima = do_municipio.iloc[-1]

    inicio = arredondar(primeira["razao_riqueza"])
    fim = arredondar(ultima["razao_riqueza"])

    if inicio is None or fim is None:
        return None

    diferenca = fim - inicio

    # uma variacao de menos de 10% para cima ou para baixo eu trato como
    # estabilidade, para nao transformar ruido em tendencia
    if inicio > 0:
        variacao = diferenca / inicio
    else:
        variacao = 0

    if variacao > 0.10:
        sentido = "subiu"
    elif variacao < -0.10:
        sentido = "caiu"
    else:
        sentido = "ficou estável"

    return {
        "primeiro_ano": int(primeira["ano"]),
        "ultimo_ano": int(ultima["ano"]),
        "razao_riqueza_no_inicio": inicio,
        "razao_riqueza_no_fim": fim,
        "sentido": sentido,
        "variacao_percentual": arredondar(variacao * 100, 1),
    }


def montar_analise(indicadores, codigo, ano):
    """Monta a analise completa de um municipio num ano.

    Devolve None se o municipio ou o ano nao existirem na base.
    """
    do_ano = indicadores[indicadores["ano"] == ano]
    if len(do_ano) == 0:
        return None

    achado = do_ano[do_ano["codigo"] == codigo]
    if len(achado) == 0:
        return None
    linha = achado.iloc[0]

    sigla = str(linha["uf"])
    do_estado = do_ano[do_ano["uf"] == sigla]

    # os anos de 2022 e 2023 nao tem abertura por setor, porque o IBGE
    # ainda nao publicou. a analise segue, mas sem a parte setorial.
    tem_setores = not pd.isna(linha["dependencia_adm"])

    # ------------------------------------------------------------------
    # os numeros
    # ------------------------------------------------------------------
    numeros = {
        "populacao": arredondar(linha["populacao"], 0),
        "pib_mil_reais": arredondar(linha["pib"], 0),
        "pib_por_habitante": arredondar(linha["pib_per_capita"], 0),
        "pib_por_habitante_brasil": arredondar(linha["pib_per_capita_brasil"], 0),
        "pib_por_habitante_mediano_estado": arredondar(do_estado["pib_per_capita"].median(), 0),
        "razao_riqueza": arredondar(linha["razao_riqueza"]),
        "posicao_no_ranking": arredondar(linha["posicao_pib"], 0),
        "total_de_municipios": len(do_ano),
        "participacao_no_pib_nacional": arredondar(linha["participacao_pib"], 4),
    }

    if tem_setores:
        agro = arredondar(linha["part_agropecuaria"], 1)
        industria = arredondar(linha["part_industria"], 1)
        servicos = arredondar(linha["part_servicos"], 1)
        publica = arredondar(linha["part_adm_publica"], 1)

        # a soma do setor privado vai pronta para o prompt. assim o modelo
        # nao precisa somar nada, que e justamente o que ele faz errado.
        soma_privada = None
        if agro is not None and industria is not None and servicos is not None:
            soma_privada = round(agro + industria + servicos, 1)

        numeros["participacao_agropecuaria"] = agro
        numeros["participacao_industria"] = industria
        numeros["participacao_servicos"] = servicos
        numeros["participacao_administracao_publica"] = publica
        numeros["soma_dos_setores_privados"] = soma_privada
        numeros["indice_hhi"] = arredondar(linha["hhi"])
        numeros["dependencia_administracao_publica"] = arredondar(linha["dependencia_adm"], 1)
        numeros["dependencia_mediana_do_estado"] = arredondar(do_estado["dependencia_adm"].median(), 1)
        numeros["dependencia_mediana_do_brasil"] = arredondar(do_ano["dependencia_adm"].median(), 1)

    # ------------------------------------------------------------------
    # as faixas, comparadas com a distribuicao nacional do ano
    # ------------------------------------------------------------------
    faixas = {}

    faixas["riqueza"] = classificar_por_percentil(
        linha["razao_riqueza"],
        do_ano["razao_riqueza"],
        [
            "muito abaixo da mediana nacional",
            "abaixo da mediana nacional",
            "acima da mediana nacional",
            "bem acima da mediana nacional",
            "muito acima da mediana nacional",
        ],
    )

    if tem_setores:
        faixas["dependencia_publica"] = classificar_por_percentil(
            linha["dependencia_adm"],
            do_ano["dependencia_adm"],
            [
                "muito baixa",
                "baixa",
                "acima da mediana nacional",
                "alta",
                "muito alta",
            ],
        )
        faixas["concentracao_setorial"] = classificar_por_percentil(
            linha["hhi"],
            do_ano["hhi"],
            [
                "economia diversificada",
                "diversificação acima da média",
                "concentração acima da mediana nacional",
                "economia concentrada",
                "economia muito concentrada",
            ],
        )

    # ------------------------------------------------------------------
    # as regras de decisao: achados, alertas e o que acompanhar
    # ------------------------------------------------------------------
    achados = []
    alertas = []
    acompanhar = []

    razao = numeros["razao_riqueza"]
    if razao is not None:
        if razao < 1:
            quanto = round((1 - razao) * 100)
            achados.append(
                "O PIB por habitante do município é " + str(quanto)
                + "% menor que o do Brasil."
            )
        elif razao < 2:
            quanto = round((razao - 1) * 100)
            achados.append(
                "O PIB por habitante do município é " + str(quanto)
                + "% maior que o do Brasil."
            )
        else:
            # acima do dobro, porcentagem fica dificil de ler ("983% maior")
            achados.append(
                "O PIB por habitante do município é " + numero_br(razao, 1)
                + " vezes o do Brasil."
            )

    if tem_setores:
        dependencia = numeros["dependencia_administracao_publica"]
        mediana_brasil = numeros["dependencia_mediana_do_brasil"]

        if dependencia is not None and mediana_brasil is not None and mediana_brasil > 0:
            vezes = round(dependencia / mediana_brasil, 1)
            # a direcao da comparacao vai escrita por extenso, e nao deixada
            # para quem le deduzir. nos testes com Sao Paulo e Sorriso, o
            # modelo recebia "responde por 6,1% ... contra uma mediana nacional
            # de 26,8%" e escrevia "forte dependencia da administracao publica",
            # invertendo o sentido. com "menos que" e "mais que" escritos na
            # frase, nao sobra nada para ele interpretar.
            if dependencia < mediana_brasil:
                comparacao = "Isso é MENOS que a mediana nacional"
            elif dependencia > mediana_brasil:
                comparacao = "Isso é MAIS que a mediana nacional"
            else:
                comparacao = "Isso é igual à mediana nacional"

            achados.append(
                "A administração pública responde por " + numero_br(dependencia, 1)
                + "% da economia deste município. " + comparacao + ", que é de "
                + numero_br(mediana_brasil, 1) + "%."
            )
            if vezes >= 1.5:
                alertas.append(
                    "A dependência do setor público é " + numero_br(vezes, 1)
                    + " vezes a mediana nacional. Quando a maior parte da economia vem"
                    + " da administração pública, o município fica exposto a qualquer"
                    + " mudança no repasse de recursos."
                )
                acompanhar.append(
                    "A evolução dos repasses federais e estaduais, porque eles sustentam"
                    + " a maior parte da atividade econômica local."
                )

        privada = numeros["soma_dos_setores_privados"]
        if privada is not None:
            achados.append(
                "A agropecuária, a indústria e os serviços somados respondem por "
                + numero_br(privada, 1) + "% da economia deste município. Este número"
                + " é a soma dos três setores privados, e não a participação de um"
                + " setor sozinho."
            )
            if privada < 30:
                alertas.append(
                    "A atividade privada é pequena: " + numero_br(privada, 1)
                    + "% da economia. Isso costuma significar poucos empregos fora da"
                    + " prefeitura e pouca arrecadação própria."
                )
                acompanhar.append(
                    "A criação de empregos privados e a arrecadação própria do município."
                )

        setor = str(linha["perfil"])
        if faixas.get("concentracao_setorial", "").startswith("economia muito concentrada"):
            # servicos e a categoria mais ampla do IBGE: ela junta comercio,
            # transporte, saude, educacao privada, tecnologia e muito mais.
            # um municipio concentrado em servicos nao corre o mesmo risco
            # de um concentrado numa unica industria ou numa unica lavoura,
            # entao aqui eu registro o fato sem tratar como alerta.
            if setor == "Serviços":
                achados.append(
                    "A economia é concentrada em serviços, que no IBGE é a categoria"
                    + " mais ampla e reúne atividades muito diferentes entre si."
                )
            else:
                alertas.append(
                    "A economia é muito concentrada em um único setor (" + setor + ")."
                    + " Municípios assim sofrem mais quando esse setor passa por uma crise."
                )
                acompanhar.append(
                    "O surgimento de atividades em outros setores, que reduzem a"
                    + " dependência de " + setor.lower() + "."
                )

    # o percentil e uma informacao forte, mas ela nao pode ficar num rotulo
    # curto: na versao 3 do prompt o modelo leu "entre as 10% mais
    # concentradas" e escreveu "10% superior a media nacional". Numero so
    # entra em frase completa, que diga exatamente o que ele significa.
    if tem_setores:
        if faixas.get("dependencia_publica") == "muito alta":
            achados.append(
                "Em " + str(ano) + ", este município estava entre os 10% mais"
                + " dependentes da administração pública de todo o país."
            )
        if faixas.get("concentracao_setorial") == "economia muito concentrada":
            achados.append(
                "Em " + str(ano) + ", este município estava entre os 10% com a"
                + " economia mais concentrada em um único setor no país."
            )

    trajetoria = olhar_trajetoria(indicadores, codigo)
    if trajetoria is not None:
        achados.append(
            "Entre " + str(trajetoria["primeiro_ano"]) + " e " + str(trajetoria["ultimo_ano"])
            + ", a riqueza por habitante comparada à do Brasil " + trajetoria["sentido"]
            + " (de " + numero_br(trajetoria["razao_riqueza_no_inicio"], 2) + " para "
            + numero_br(trajetoria["razao_riqueza_no_fim"], 2) + ")."
        )
        if trajetoria["sentido"] == "caiu":
            alertas.append(
                "O município vem perdendo posição em relação ao resto do país ao longo"
                + " da série histórica."
            )

    if len(acompanhar) == 0:
        acompanhar.append(
            "A evolução do PIB por habitante em relação à média nacional, ano a ano."
        )

    # ------------------------------------------------------------------
    return {
        "codigo": int(linha["codigo"]),
        "municipio": str(linha["municipio"]),
        "uf": sigla,
        "estado": estados.get(sigla, sigla),
        "regiao": str(linha["regiao"]),
        "e_capital": str(linha["capital"]) == "sim",
        "ano": int(ano),
        "perfil": str(linha["perfil"]) if tem_setores else "sem dado",
        "tem_dados_setoriais": tem_setores,
        "numeros": numeros,
        "faixas": faixas,
        "trajetoria": trajetoria,
        "achados": achados,
        "alertas": alertas,
        "acompanhar": acompanhar,
    }
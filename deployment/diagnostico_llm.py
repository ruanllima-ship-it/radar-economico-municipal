# diagnostico_llm.py
# Transforma a analise do agente.py em texto corrido, usando o modelo local.
#
# A divisao de trabalho deste projeto esta aqui:
#   agente.py           -> pensa (le os dados, compara, aplica regras)
#   diagnostico_llm.py  -> escreve (so redige o que o agente ja concluiu)
#
# O modelo nunca recebe a tarefa de analisar. Ele recebe os achados prontos
# e a ordem de transformar em paragrafos. Essa escolha veio dos testes do
# bloco 1, em que o modelo, ao analisar sozinho, somou numeros que nao devia,
# confundiu PIB total com PIB por habitante e trocou Roraima por Rio Grande
# do Norte. Tirando a analise das maos dele, esses erros somem.
#
# O carregamento segue o mesmo padrao do modelo_llm.py do TP4: preguicoso,
# com import dentro da funcao e duas travas.

import re
import time
import threading


nome_do_modelo = "Qwen/Qwen2.5-1.5B-Instruct"

# medido no bloco 1: em bfloat16 ocupa cerca de 2,9 GB e gera 6,3 pedacos
# por segundo nesta maquina. float32 tem a mesma velocidade e o dobro do
# consumo, entao bfloat16 e a escolha.
#
# comecou em 260. a versao 4 do prompt ainda cortava o terceiro paragrafo no
# meio, entao subiu para 320. na primeira execucao pelo painel a geracao bateu
# exatamente em 320: a limpeza descartou o terceiro paragrafo incompleto e o
# leitor recebeu so dois. 480 da folga para os tres, e a regra 4 do prompt foi
# apertada de "2 a 4 frases" para "2 a 3" para o texto nao inchar junto.
pedacos_maximos = 480

tokenizador = None
modelo = None
dispositivo = "cpu"
estado = "nao_carregado"
mensagem_do_erro = ""
segundos_para_carregar = 0.0
diagnosticos_gerados = 0

trava = threading.Lock()
trava_de_uso = threading.Lock()


class ModeloOcupado(Exception):
    """Levantada quando o modelo ja esta escrevendo outro diagnostico."""

    pass


def carregar():
    """Carrega o modelo na memoria. Devolve True se deu certo."""
    global tokenizador, modelo, dispositivo
    global estado, mensagem_do_erro, segundos_para_carregar

    if estado == "pronto":
        return True
    if estado == "falhou":
        return False

    with trava:
        if estado == "pronto":
            return True
        if estado == "falhou":
            return False

        estado = "carregando"
        relogio = time.time()

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
        except Exception as erro:
            estado = "falhou"
            mensagem_do_erro = "As bibliotecas torch e transformers nao estao instaladas. Detalhe: " + str(erro)
            return False

        try:
            tokenizador = AutoTokenizer.from_pretrained(nome_do_modelo)
            try:
                modelo = AutoModelForCausalLM.from_pretrained(nome_do_modelo, dtype=torch.bfloat16)
            except TypeError:
                modelo = AutoModelForCausalLM.from_pretrained(nome_do_modelo, torch_dtype=torch.bfloat16)
            modelo.eval()
        except Exception as erro:
            estado = "falhou"
            mensagem_do_erro = "Nao consegui carregar o modelo " + nome_do_modelo + ". Detalhe: " + str(erro)
            return False

        if torch.cuda.is_available():
            modelo = modelo.to("cuda")
            dispositivo = "cuda"
        else:
            dispositivo = "cpu"

        segundos_para_carregar = round(time.time() - relogio, 1)
        estado = "pronto"
        return True


def descarregar():
    """Tira o modelo da memoria. Util porque a maquina tem RAM apertada."""
    global tokenizador, modelo, estado, segundos_para_carregar

    import gc

    with trava:
        tokenizador = None
        modelo = None
        estado = "nao_carregado"
        segundos_para_carregar = 0.0
        gc.collect()
    return True


# ------------------------------------------------------------------
# O prompt
# ------------------------------------------------------------------
#
# Esta e a versao 8. As versoes 1 a 7 estao registradas em
# modeling/engenharia_de_prompt.md, cada uma com os defeitos que produziu e
# a correcao que gerou a versao seguinte.
#
# A regra 9 nasceu da primeira execucao pelo painel: o modelo abriu o segundo
# paragrafo com "No entanto" e emendou mais uma ma noticia. O conector
# prometia um contraste que os fatos nao tinham.
#
# A versao 6 mexeu no fim do pedido, e nao nas regras. A versao 5 entregou um
# paragrafo unico de 178 pedacos, parando sozinha bem antes do teto de 480.
# A ultima linha que ela lia era "Comece pela primeira frase, sem titulo", que
# nao falava de estrutura nenhuma. Como o fim do prompt e a parte que o modelo
# mais obedece, esse lugar passou a repetir a exigencia dos tres paragrafos.
#
# A versao 7 levou para o mesmo lugar a proibicao de apresentar um alerta como
# vantagem, depois que o modelo escreveu "ha tambem um ponto positivo" sobre
# estar entre os 10% mais dependentes do pais.
#
# A versao 8 veio dos testes com municipios ricos. Em Sao Paulo e Sorriso o
# aviso do fim do pedido dizia que a analise "nao apurou nenhum ponto
# favoravel", o que e falso para quem tem riqueza acima da media, e empurrava
# o modelo a inventar problema. Agora o aviso so diz que alerta e risco. E
# entrou a proibicao de tirar conclusao propria, depois que o modelo deduziu
# que 2,8% de administracao publica significa "gestao com poucos recursos".

regras_do_sistema = (
    "Você é um analista que escreve diagnósticos econômicos de municípios "
    "brasileiros para prefeitos e vereadores, que não são técnicos.\n\n"
    "A análise já foi feita e está pronta na mensagem do usuário. Sua única "
    "tarefa é transformá-la em texto corrido. Você não analisa, você redige.\n\n"
    "Regras obrigatórias:\n"
    "1. Use somente os fatos e os números que estão na mensagem do usuário. "
    "Não acrescente nenhum número novo.\n"
    "2. Nunca some, divida, calcule ou estime nada. Todas as contas já foram "
    "feitas e os resultados já estão na mensagem.\n"
    "3. Não escreva título, cabeçalho, lista, marcador ou numeração. Comece "
    "direto pela primeira frase do primeiro parágrafo.\n"
    "4. Escreva 3 parágrafos, nem mais nem menos. Cada parágrafo deve ter de "
    "2 a 3 frases. Separe os parágrafos com uma linha em branco.\n"
    "5. Escreva em português do Brasil, em linguagem simples. Explique o que "
    "cada indicador significa na prática.\n"
    "6. Não faça previsões nem promessas sobre o futuro.\n"
    "7. Não anuncie avaliações que não estejam nos fatos. Em especial, não "
    "escreva que existem sinais positivos, pontos favoráveis ou melhoras se "
    "os fatos listados não trouxerem nenhum.\n"
    "8. Termine o terceiro parágrafo com uma frase completa e pare de escrever.\n"
    "9. Só use expressões de contraste, como 'no entanto', 'por outro lado', "
    "'em compensação' ou 'apesar disso', quando o que vier depois delas for "
    "realmente oposto ao que veio antes. Quando os fatos apontarem todos para "
    "o mesmo lado, encadeie com 'além disso', 'somado a isso' ou comece a "
    "frase direto."
)


# as chaves das faixas sao nomes de variavel. no prompt elas viram texto
# legivel, porque o modelo le isso como portugues, nao como codigo.
rotulos_das_faixas = {
    "riqueza": "Riqueza por habitante",
    "dependencia_publica": "Dependência da administração pública",
    "concentracao_setorial": "Concentração setorial",
}


def montar_pedido(analise):
    """Monta a mensagem do usuario a partir da analise ja pronta."""
    linhas = []

    linhas.append("Escreva o diagnóstico econômico deste município.")
    linhas.append("")
    linhas.append("MUNICÍPIO")
    linhas.append("Nome: " + analise["municipio"])
    linhas.append("Estado: " + analise["estado"])
    linhas.append("Região: " + analise["regiao"])
    linhas.append("Ano dos dados: " + str(analise["ano"]))
    if analise["tem_dados_setoriais"] is True:
        linhas.append("Setor que mais pesa na economia: " + analise["perfil"])
    else:
        linhas.append(
            "Observação: o IBGE ainda não publicou a divisão por setor deste ano, "
            "então não há informação sobre de qual setor a economia depende."
        )
    linhas.append("")

    linhas.append("COMO O MUNICÍPIO SE COMPARA COM O RESTO DO PAÍS")
    for chave in analise["faixas"]:
        rotulo = rotulos_das_faixas.get(chave, chave)
        linhas.append("- " + rotulo + ": " + analise["faixas"][chave])
    linhas.append("")

    linhas.append("FATOS JÁ APURADOS (use estes, não calcule outros)")
    for texto in analise["achados"]:
        linhas.append("- " + texto)
    linhas.append("")

    if len(analise["alertas"]) > 0:
        linhas.append("PONTOS DE ATENÇÃO JÁ IDENTIFICADOS")
        for texto in analise["alertas"]:
            linhas.append("- " + texto)
        linhas.append("")

    linhas.append("O QUE O GESTOR DEVE ACOMPANHAR")
    for texto in analise["acompanhar"]:
        linhas.append("- " + texto)
    linhas.append("")

    linhas.append("COMO ORGANIZAR OS 3 PARÁGRAFOS")
    linhas.append("Parágrafo 1: a situação da riqueza do município comparada à do país.")
    linhas.append("Parágrafo 2: de que a economia local depende e o que isso significa no dia a dia.")
    linhas.append("Parágrafo 3: os riscos e o que o gestor deve acompanhar.")
    linhas.append("")
    # esta e a ultima coisa que o modelo le antes de comecar a escrever, e por
    # isso e a instrucao que ele mais obedece. na versao 5 este lugar estava
    # gasto com "Comece pela primeira frase, sem titulo", que nao dizia nada
    # sobre estrutura, e o modelo entregou um paragrafo unico. aqui a exigencia
    # dos tres paragrafos e repetida no ponto de maior peso.
    linhas.append("Escreva agora os três parágrafos, um depois do outro, separados por uma")
    linhas.append("linha em branco. Não junte tudo em um parágrafo só. Não escreva título.")

    # o aviso abaixo e montado a partir dos dados, e nao fixo no prompt.
    if len(analise["alertas"]) > 0:
        linhas.append("Atenção: os pontos de atenção acima são riscos. Não os apresente como")
        linhas.append("vantagens e não invente pontos positivos que não estejam nas listas.")
    else:
        linhas.append("Atenção: nenhum ponto de atenção foi disparado para este município.")
        linhas.append("Não invente riscos, problemas ou alertas que não estejam nas listas.")

    linhas.append("Não tire conclusões próprias a partir dos números. Se um fato diz que algo")
    linhas.append("é baixo, escreva que é baixo; não deduza o que isso causa. Escreva somente")
    linhas.append("em português do Brasil, sem nenhuma palavra em outro idioma.")

    return "\n".join(linhas)


def cortar_na_ultima_frase(texto):
    """Se o texto terminar no meio de uma frase, volta ate o ultimo ponto.

    A busca exige que o ponto venha seguido de espaco. Isso evita cortar em
    "3.758", onde o ponto e separador de milhar e nao fim de frase.

    Quando o trecho nao tem nenhuma frase completa dentro dele, devolve
    vazio. Isso acontece quando a geracao acaba no meio do primeiro periodo
    do paragrafo, e nesse caso o paragrafo inteiro tem que ser descartado:
    e melhor entregar dois paragrafos completos do que tres com um pedaco
    solto no fim.
    """
    texto = texto.strip()
    if texto == "":
        return texto
    if texto[-1] in ".!?":
        return texto

    finais = list(re.finditer(r"[.!?](?=\s)", texto))
    if len(finais) == 0:
        return ""

    ultimo = finais[-1]
    return texto[: ultimo.end()].strip()


def limpar_texto(texto):
    """Garante no codigo o que o prompt pede, mas nem sempre consegue.

    Faz quatro coisas: tira ideogramas, tira titulo e marcadores, fica so
    com os 3 primeiros paragrafos, e corta qualquer frase incompleta no fim.
    O modelo nao sabe parar sozinho, entao quem para e o codigo.
    """
    # o Qwen e um modelo chines e, de vez em quando, deixa escapar um ideograma
    # no meio da frase em portugues (no teste de Sorriso saiu "desenvolvimento
    # 长远 do municipio"). a regra do prompt pede portugues, mas regra de prompt
    # nao e garantia: aqui o caractere e removido no codigo.
    texto = re.sub(r"[\u3000-\u9fff\uff00-\uffef]+", "", texto)
    texto = re.sub(r"  +", " ", texto)

    texto = texto.strip()
    linhas = texto.split("\n")
    paragrafos = []

    for linha in linhas:
        corte = linha.strip()
        if corte == "":
            continue
        # tira marcadores de lista no comeco da linha
        corte = re.sub(r"^[-*•]\s+", "", corte)
        corte = re.sub(r"^\d+[\.\)]\s+", "", corte)
        # titulo: linha curta, sem ponto final, logo no comeco do texto
        if len(paragrafos) == 0:
            if len(corte) < 70 and corte.endswith(".") is False:
                continue
            if corte.lower().startswith("diagnóstico econômico"):
                continue
            if corte.lower().startswith("diagnostico economico"):
                continue
        paragrafos.append(corte)

    # o prompt pede 3 paragrafos; se vier mais, fico com os 3 primeiros
    paragrafos = paragrafos[0:3]

    # o ultimo paragrafo e o que costuma vir cortado no meio
    if len(paragrafos) > 0:
        paragrafos[-1] = cortar_na_ultima_frase(paragrafos[-1])
        if paragrafos[-1] == "":
            paragrafos = paragrafos[0:-1]

    return "\n\n".join(paragrafos)


def gerar_diagnostico(analise):
    """Porteiro: garante que so um diagnostico e escrito por vez."""
    conseguiu = trava_de_uso.acquire(blocking=False)
    if conseguiu is False:
        raise ModeloOcupado("Ja existe um diagnostico sendo escrito neste momento.")

    try:
        return escrever(analise)
    finally:
        trava_de_uso.release()


def escrever(analise):
    """Chama o modelo. So e chamada por gerar_diagnostico()."""
    global diagnosticos_gerados

    import torch

    pedido = montar_pedido(analise)

    mensagens = [
        {"role": "system", "content": regras_do_sistema},
        {"role": "user", "content": pedido},
    ]

    texto_do_prompt = tokenizador.apply_chat_template(
        mensagens,
        tokenize=False,
        add_generation_prompt=True,
    )

    entrada = tokenizador(texto_do_prompt, return_tensors="pt")
    identificadores = entrada["input_ids"]
    atencao = entrada["attention_mask"]

    if dispositivo == "cuda":
        identificadores = identificadores.to("cuda")
        atencao = atencao.to("cuda")

    pedacos_do_prompt = int(identificadores.shape[1])
    relogio = time.time()

    # do_sample=False deixa a geracao deterministica: o mesmo municipio no
    # mesmo ano sempre produz o mesmo texto. num trabalho sobre dados
    # economicos isso vale mais do que variedade de redacao.
    with torch.no_grad():
        saida = modelo.generate(
            input_ids=identificadores,
            attention_mask=atencao,
            max_new_tokens=pedacos_maximos,
            do_sample=False,
        )

    demorou = round(time.time() - relogio, 2)

    so_a_resposta = saida[0][pedacos_do_prompt:]
    bruto = tokenizador.decode(so_a_resposta, skip_special_tokens=True)
    texto = limpar_texto(bruto)

    diagnosticos_gerados = diagnosticos_gerados + 1

    return {
        "texto": texto,
        "texto_bruto": bruto.strip(),
        "segundos": demorou,
        "pedacos_do_prompt": pedacos_do_prompt,
        "pedacos_gerados": int(so_a_resposta.shape[0]),
        "prompt_enviado": pedido,
    }


def situacao():
    """Informa como esta o modelo agora, sem carregar nada."""
    return {
        "modelo": nome_do_modelo,
        "estado": estado,
        "dispositivo": dispositivo,
        "segundos_para_carregar": segundos_para_carregar,
        "diagnosticos_gerados": diagnosticos_gerados,
        "mensagem_do_erro": mensagem_do_erro,
        "pedacos_maximos": pedacos_maximos,
    }
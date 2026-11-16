# modelo_llm.py
# Carrega o modelo de linguagem local e gera os resumos.
#
# Quatro decisoes importantes estao neste arquivo:
#
# 1) O modelo NAO e carregado quando a API liga. Ele so e carregado na
#    primeira vez que alguem pede um resumo. Isso se chama carregamento
#    preguicoso. Carregar leva uns 13 segundos, e nao faz sentido atrasar
#    a subida da API inteira por causa de uma rota.
#
# 2) O import do torch e do transformers acontece dentro da funcao, e nao
#    no topo do arquivo. Assim, se essas bibliotecas nao estiverem
#    instaladas, a API continua subindo e as outras rotas continuam
#    funcionando. So a rota do modelo responde 503.
#
# 3) Existe uma trava de carregamento (Lock). O FastAPI atende varios
#    pedidos ao mesmo tempo, em threads diferentes. Sem a trava, dois
#    pedidos simultaneos carregariam o modelo duas vezes e gastariam o
#    dobro de memoria.
#
# 4) Existe uma segunda trava, a de uso. So um resumo e gerado por vez.
#    Se chegar outro pedido enquanto o modelo esta gerando, a API avisa
#    com 429 em vez de deixar os dois pedidos lentos disputando a CPU.

import time
import threading


nome_do_modelo = "recogna-nlp/ptt5-base-summ"

# configuracao B, escolhida no experimento do arquivo modeling/afina_resumo.py
limite_de_entrada = 512
tamanho_maximo = 160
tamanho_minimo = 10
caminhos = 5
repeticao_proibida = 3
peso_do_tamanho = 1.0

# estado do modelo, guardado aqui no proprio modulo
tokenizador = None
modelo = None
dispositivo = "cpu"
estado = "nao_carregado"
mensagem_do_erro = ""
segundos_para_carregar = 0.0
resumos_gerados = 0

trava = threading.Lock()
trava_de_uso = threading.Lock()


class ModeloOcupado(Exception):
    """Levantada quando o modelo ja esta gerando outro resumo."""

    pass


def carregar():
    """Carrega o modelo na memoria. Devolve True se deu certo."""
    global tokenizador, modelo, dispositivo
    global estado, mensagem_do_erro, segundos_para_carregar

    if estado == "pronto":
        return True

    # se ja falhou uma vez, nao adianta tentar de novo a cada pedido.
    # para tentar outra vez, e preciso reiniciar a API.
    if estado == "falhou":
        return False

    with trava:
        # outro pedido pode ter carregado enquanto este esperava a trava
        if estado == "pronto":
            return True
        if estado == "falhou":
            return False

        estado = "carregando"
        relogio = time.time()

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        except Exception as erro:
            estado = "falhou"
            mensagem_do_erro = "As bibliotecas torch e transformers nao estao instaladas. Detalhe: " + str(erro)
            return False

        try:
            tokenizador = AutoTokenizer.from_pretrained(nome_do_modelo)
            modelo = AutoModelForSeq2SeqLM.from_pretrained(nome_do_modelo)
            modelo.eval()
        except Exception as erro:
            estado = "falhou"
            mensagem_do_erro = "Nao consegui carregar o modelo " + nome_do_modelo + ". Detalhe: " + str(erro)
            return False

        # se existir placa de video disponivel, usa. senao, usa a CPU.
        if torch.cuda.is_available():
            modelo = modelo.to("cuda")
            dispositivo = "cuda"
        else:
            dispositivo = "cpu"

        segundos_para_carregar = round(time.time() - relogio, 1)
        estado = "pronto"
        return True


def contar_pedacos(texto):
    """Conta em quantos pedacos o modelo divide o texto, sem cortar nada."""
    sem_corte = tokenizador(texto, truncation=False)
    return len(sem_corte["input_ids"])


def resumir(texto):
    """Porteiro da geracao: garante que so um resumo roda por vez."""
    # se ja tem outro resumo rodando, avisa agora em vez de entrar na fila
    # e deixar os dois pedidos lentos disputando a mesma CPU.
    conseguiu = trava_de_uso.acquire(blocking=False)
    if conseguiu is False:
        raise ModeloOcupado("Ja existe um resumo sendo gerado neste momento.")

    try:
        return gerar(texto)
    finally:
        trava_de_uso.release()


def gerar(texto):
    """Faz a geracao em si. So e chamada por resumir(), com a trava de uso."""
    global resumos_gerados

    import torch

    total_de_pedacos = contar_pedacos(texto)

    entrada = tokenizador(
        texto,
        max_length=limite_de_entrada,
        truncation=True,
        return_tensors="pt",
    )
    identificadores = entrada["input_ids"]

    if dispositivo == "cuda":
        identificadores = identificadores.to("cuda")

    relogio = time.time()

    # no_grad economiza memoria: avisa que nao vou treinar nada
    with torch.no_grad():
        saida = modelo.generate(
            identificadores,
            max_length=tamanho_maximo,
            min_length=tamanho_minimo,
            num_beams=caminhos,
            no_repeat_ngram_size=repeticao_proibida,
            early_stopping=True,
            length_penalty=peso_do_tamanho,
        )

    demorou = round(time.time() - relogio, 2)
    texto_resumido = tokenizador.decode(saida[0], skip_special_tokens=True)

    resumos_gerados = resumos_gerados + 1

    pedacos_lidos = total_de_pedacos
    if pedacos_lidos > limite_de_entrada:
        pedacos_lidos = limite_de_entrada

    return {
        "resumo": texto_resumido,
        "segundos": demorou,
        "pedacos_do_texto": total_de_pedacos,
        "pedacos_lidos": pedacos_lidos,
        "texto_cortado": total_de_pedacos > limite_de_entrada,
    }


def situacao():
    """Informa como esta o modelo agora, sem carregar nada."""
    return {
        "modelo": nome_do_modelo,
        "estado": estado,
        "dispositivo": dispositivo,
        "segundos_para_carregar": segundos_para_carregar,
        "resumos_gerados": resumos_gerados,
        "mensagem_do_erro": mensagem_do_erro,
        "limite_de_entrada": limite_de_entrada,
    }
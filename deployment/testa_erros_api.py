# testa_erros_api.py
# Bateria de testes do tratamento de erros da API (rubrica 4 do TP4).
#
# Este script nao abre o navegador: ele conversa com a API igual a um
# sistema de fora faria, confere o codigo HTTP de cada situacao e imprime
# um relatorio no fim.
#
# A API precisa estar LIGADA em outro terminal antes de rodar isto:
#   py -m uvicorn deployment.api:app --reload

import time
import threading

import requests


endereco = "http://127.0.0.1:8000"

texto_valido = (
    "Excluindo a atividade de administração pública, a agropecuária respondia por "
    "mais da metade das economias em 1.135 dos 5.570 municípios brasileiros (20,4%) "
    "em 2014, 210 deles no Rio Grande do Sul e 144 no Paraná, o que indica a "
    "importância dessa atividade econômica no território nacional. No mesmo ano, "
    "652 municípios (11,7%) respondiam por metade do valor adicionado da "
    "agropecuária no país. O maior era em São Desidério, na Bahia, com R$ 1,7 bilhão."
)

acertos = 0
falhas = 0


def conferir(nome, caminho, esperado, metodo="GET", corpo=None):
    """Chama uma rota e confere se o codigo HTTP foi o esperado."""
    global acertos, falhas

    try:
        if metodo == "GET":
            resposta = requests.get(endereco + caminho, timeout=180)
        else:
            resposta = requests.post(endereco + caminho, json=corpo, timeout=180)
    except Exception as erro:
        print("FALHOU  " + nome)
        print("        a API nao respondeu:", erro)
        falhas = falhas + 1
        return None

    if resposta.status_code == esperado:
        print("OK      " + nome + "  ->  " + str(resposta.status_code))
        acertos = acertos + 1
    else:
        print("FALHOU  " + nome)
        print("        recebi " + str(resposta.status_code) + " e esperava " + str(esperado))
        falhas = falhas + 1

    try:
        conteudo = resposta.json()
    except Exception:
        return None

    if isinstance(conteudo, dict):
        if "detail" in conteudo:
            print("        mensagem: " + str(conteudo["detail"])[:140])

    return conteudo


print()
print("=" * 72)
print("  BATERIA DE TESTES DO TRATAMENTO DE ERROS DA API")
print("=" * 72)
print()

# ------------------------------------------------------------------
print("1) A API ESTA NO AR?")
print("-" * 72)

inicial = conferir("GET /  (cartao de visita)", "/", 200)
if inicial is None:
    print()
    print("A API nao respondeu. Ligue ela em outro terminal, a partir da raiz:")
    print("   py -m uvicorn deployment.api:app --reload")
    raise SystemExit

print()

# ------------------------------------------------------------------
print("2) ERROS DAS ROTAS DE DADOS")
print("-" * 72)

conferir("404 municipio inexistente", "/municipios/9999999", 404)
conferir("404 ano inexistente para o municipio", "/municipios/3304557?ano=1990", 404)
conferir("400 criterio de ranking invalido", "/ranking?criterio=banana", 400)
conferir("404 ano inexistente no ranking", "/ranking?ano=1500", 404)
conferir("404 estado inexistente", "/ranking?uf=ZZ", 404)
conferir("404 ano inexistente no brasil", "/brasil?ano=1800", 404)
conferir("404 ano sem noticia", "/noticias?ano=1999", 404)
conferir("400 lista de comparacao vazia", "/comparar", 400, "POST", {"codigos": [], "ano": 2023})
conferir("400 mais de 50 municipios", "/comparar", 400, "POST", {"codigos": list(range(1, 60)), "ano": 2023})

print()

# ------------------------------------------------------------------
print("3) ERROS GLOBAIS (valem para a API inteira)")
print("-" * 72)

conferir("404 rota que nao existe", "/rota_que_nao_existe", 404)
conferir("405 metodo errado (processar_texto e POST)", "/processar_texto", 405)

print()

# ------------------------------------------------------------------
print("4) VALIDACAO DA ENTRADA DA ROTA DO MODELO")
print("-" * 72)

conferir("400 texto curto demais", "/processar_texto", 400, "POST", {"texto": "oi"})
conferir("400 tipo de analise nao suportado", "/processar_texto", 400, "POST",
         {"texto": texto_valido, "tipo_analise": "sentimento"})
conferir("413 texto grande demais", "/processar_texto", 413, "POST", {"texto": "a" * 50001})
conferir("422 corpo sem o campo texto", "/processar_texto", 422, "POST", {"tipo_analise": "resumo"})
conferir("422 texto vazio", "/processar_texto", 422, "POST", {"texto": ""})

print()

# ------------------------------------------------------------------
print("5) O CAMINHO QUE DA CERTO")
print("-" * 72)
print("        A primeira chamada carrega o modelo. Pode levar uns 25 segundos.")

relogio = time.time()
saida = conferir("200 resumo gerado", "/processar_texto", 200, "POST", {"texto": texto_valido})
print("        o pedido inteiro levou " + str(round(time.time() - relogio, 1)) + " segundos")

if saida is not None:
    if "resultado" in saida:
        print("        modelo: " + str(saida["modelo"]) + " em " + str(saida["dispositivo"]))
        print("        geracao: " + str(saida["segundos"]) + " segundos")
        print("        resumo: " + str(saida["resultado"]))

print()
situacao = conferir("200 situacao do modelo", "/modelo", 200)
if situacao is not None:
    if "estado" in situacao:
        print("        estado: " + str(situacao["estado"]))
        print("        carregou em: " + str(situacao["segundos_para_carregar"]) + " segundos")
        print("        resumos ja gerados: " + str(situacao["resumos_gerados"]))

print()

# ------------------------------------------------------------------
print("6) SEGUNDA CHAMADA, COM O MODELO JA CARREGADO")
print("-" * 72)

relogio = time.time()
segunda = conferir("200 resumo gerado de novo", "/processar_texto", 200, "POST", {"texto": texto_valido})
print("        o pedido inteiro levou " + str(round(time.time() - relogio, 1)) + " segundos")
print("        (tem que ser bem mais rapido que o primeiro)")

print()

# ------------------------------------------------------------------
print("7) DOIS PEDIDOS AO MESMO TEMPO (tem que dar 429 em um deles)")
print("-" * 72)

codigos_recebidos = []


def pedir_resumo():
    try:
        resposta = requests.post(
            endereco + "/processar_texto",
            json={"texto": texto_valido},
            timeout=180,
        )
        codigos_recebidos.append(resposta.status_code)
    except Exception:
        codigos_recebidos.append(0)


primeira_thread = threading.Thread(target=pedir_resumo)
segunda_thread = threading.Thread(target=pedir_resumo)

primeira_thread.start()
time.sleep(0.5)
segunda_thread.start()

primeira_thread.join()
segunda_thread.join()

print("        codigos recebidos nos dois pedidos:", codigos_recebidos)

if 429 in codigos_recebidos:
    print("OK      429 o segundo pedido foi recusado por o modelo estar ocupado")
    acertos = acertos + 1
else:
    print("AVISO   nao veio 429. Pode ter acontecido de um pedido terminar")
    print("        antes do outro comecar. Nao e erro, so nao deu para testar.")

print()

# ------------------------------------------------------------------
print("=" * 72)
print("  RESULTADO: " + str(acertos) + " testes certos, " + str(falhas) + " falhas")
print("=" * 72)
print()
print("Codigos HTTP exercitados nesta bateria:")
print("  400  entrada invalida (texto curto, criterio errado, lista vazia)")
print("  404  recurso nao encontrado (municipio, ano, estado, rota)")
print("  405  metodo HTTP errado para a rota")
print("  413  texto maior que o limite de 50.000 caracteres")
print("  422  corpo do pedido fora do formato declarado (Pydantic)")
print("  429  modelo ocupado gerando outro resumo")
print("  503  modelo de linguagem nao disponivel (testavel desligando o torch)")
print()
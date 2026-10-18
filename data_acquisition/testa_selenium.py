import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# o selenium abre um chrome limpo, sem as extensoes do seu navegador
opcoes = webdriver.ChromeOptions()
opcoes.add_argument("--window-size=1280,900")

print("abrindo o chrome...")
navegador = webdriver.Chrome(options=opcoes)


def testar(nome, endereco, segundos):
    print("")
    print("==========", nome, "==========")
    navegador.get(endereco)
    print("esperando", segundos, "segundos a pagina carregar...")
    time.sleep(segundos)

    titulo = navegador.title
    html = navegador.page_source

    print("titulo:", titulo)
    print("tamanho do html:", len(html))

    if "Just a moment" in titulo or "Um momento" in titulo:
        print("RESULTADO: bloqueado pelo cloudflare")
    else:
        print("RESULTADO: a pagina abriu")

    # contando os links de noticia
    links = navegador.find_elements(By.TAG_NAME, "a")
    quantidade = 0
    for link in links:
        endereco_link = link.get_attribute("href")
        if endereco_link is None:
            continue
        if "/noticias/" in endereco_link or "/releases/" in endereco_link:
            quantidade = quantidade + 1
    print("links de noticia encontrados:", quantidade)

    # mostrando o comeco do texto pra conferir que nao e lixo
    corpo = navegador.find_element(By.TAG_NAME, "body")
    texto = corpo.text
    print("comeco do texto da pagina:")
    print(texto[0:300])

    # salvando pra conferir depois
    arquivo = open("data/teste_selenium_" + nome + ".html", "w", encoding="utf-8")
    arquivo.write(html)
    arquivo.close()


testar("produto", "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html", 15)
testar("agencia", "https://agenciadenoticias.ibge.gov.br/busca-avancada.html?produto=9088", 15)
testar("sidra", "https://sidra.ibge.gov.br/tabela/5938", 20)

print("")
print("fechando o navegador...")
navegador.quit()
print("pronto")
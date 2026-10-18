# Data Summary Report — Radar Econômico Municipal

Projeto de Bloco: Inteligência Artificial Aplicada — Ciência de Dados
Aluno: Ruan Luiz Fernandes da Silva Lima
Versão: TP3 (revisão da versão entregue no TP2)

## 1. Visão geral

O projeto usa quatro entradas de dados. Três vêm do IBGE e uma vem do próprio usuário. A base principal é o PIB dos Municípios, que traz o PIB e o valor adicionado por setor. A população vem das Estimativas de População e dos Censos 2010 e 2022, e é necessária porque o PIB per capita não está disponível na tabela do PIB dos Municípios. As notícias da Agência de Notícias do IBGE são a fonte de texto do painel. Por fim, o usuário pode enviar um CSV próprio, que é juntado aos indicadores pelo código do município.

Todas as fontes são coletadas por script, sem nenhuma etapa manual. No TP2 ainda restava um passo manual na coleta das notícias; ele foi eliminado no TP3 com o uso do Selenium.

A etapa de entendimento dos dados foi feita consultando os metadados da própria API antes de escrever a coleta, com os scripts espiar_sidra.py, espiar_populacao.py e espiar_populacao_2.py, e o comportamento dos sites foi diagnosticado com espiar_pagina.py e testa_selenium.py. Todos ficam no projeto como registro.

## 2. Fontes de dados

### 2.1 PIB dos Municípios (fonte principal)

A fonte é o IBGE, Sistema de Contas Nacionais, tabela 5938 do SIDRA, acessada pela API pública em https://apisidra.ibge.gov.br, sem cadastro nem chave. Os dados são anuais, por município, em milhares de reais correntes. A tabela vai de 2002 a 2023, e o projeto usa de 2010 a 2023.

As variáveis coletadas são o PIB a preços correntes (variável 37), o valor adicionado bruto total (498), da agropecuária (513), da indústria (517), dos serviços exceto administração pública (6575) e da administração, defesa, educação e saúde públicas e seguridade social (525). Para 2022 e 2023 só existe o PIB, porque o IBGE publicou esses anos sem a abertura por setor.

A coleta é feita pelo script data_acquisition/coleta_sidra.py, que pede um ano e uma variável por vez (74 pedidos), com até três tentativas em caso de falha. O resultado é data_acquisition/raw_data/pib_municipios_2010_2023.csv, com 412.180 linhas em formato longo. Cada combinação de ano e variável veio com exatamente 5.570 linhas.

O uso no projeto é o cálculo de todos os sete indicadores.

### 2.2 População (fonte complementar)

A população é necessária para o PIB per capita e a razão de riqueza. Como o IBGE publica população em tabelas diferentes conforme o ano, a coleta usa três fontes: o Censo 2010 para 2010 (tabela 202, variável 93), as Estimativas de População para 2011 a 2021 e para 2024 (tabela 6579, variável 9324) e o Censo 2022 para 2022 (tabela 4709, variável 93). A tabela de estimativas não tem 2007, 2010, 2022 nem 2023.

Para 2023, o projeto segue o próprio IBGE, que calculou o PIB per capita de 2022 e de 2023 com a população do Censo 2022. O ano de 2024 é usado apenas como exemplo de dado extra no modelo de upload do painel.

A coleta é feita por data_acquisition/coleta_populacao.py, que primeiro consulta quais anos a tabela de estimativas realmente tem. O resultado é data_acquisition/raw_data/populacao_municipios_2010_2024.csv, com 77.987 linhas.

### 2.3 Notícias da Agência de Notícias do IBGE (web scraping dinâmico)

São as notícias e releases oficiais publicados pelo IBGE a cada divulgação do PIB dos Municípios. **No TP3 essa coleta foi refeita e ampliada: passou de 10 para 15 matérias, publicadas entre dezembro de 2015 e dezembro de 2025, com 19.996 palavras no total.**

#### Por que foi preciso usar Selenium

No TP2, o acesso por script simples (biblioteca requests) recebeu resposta 403 dos sites do IBGE, diagnosticada com o script espiar_pagina.py: as páginas são protegidas por Cloudflare, que devolve uma tela de verificação a qualquer acesso automatizado sem navegador. Além disso, a página de busca da Agência monta a lista de resultados por JavaScript, o que impede a leitura apenas com requests e Beautiful Soup. Por isso, no TP2 as páginas foram salvas manualmente pelo navegador.

O teste registrado em data_acquisition/testa_selenium.py confirmou que o Selenium resolve os dois problemas: controlando um navegador Chrome real, o JavaScript do Cloudflare é executado normalmente e a página carrega, sem nenhuma tentativa de burlar a proteção, e o conteúdo montado por JavaScript fica disponível. As três páginas testadas (a página do produto no site do IBGE, a busca da Agência e a tabela 5938 no SIDRA) abriram sem bloqueio.

#### Como a coleta funciona hoje

O script data_acquisition/coleta_noticias_selenium.py faz a coleta em duas etapas. Primeiro o Selenium abre a busca avançada da Agência filtrada pelo produto PIB dos Municípios (busca-avancada.html?produto=9088) e o Beautiful Soup lê a lista de resultados, descartando os itens que são foto, áudio ou documento e ficando só com notícias e releases. Depois o Selenium navega até cada matéria e o Beautiful Soup extrai o título, a data de publicação, o resumo e o link das etiquetas meta (og:title, article:published_time, og:description, og:url) e o texto da matéria das tags de parágrafo, descartando trechos curtos, o aviso de instabilidade do site e a linha de autoria.

O resultado é salvo em dois formatos dentro de data/: noticias_ibge.csv, com uma linha por matéria e as colunas data, tipo, titulo, resumo, qtd_paragrafos, qtd_palavras, link e texto, e noticias_ibge.txt, com o texto corrido.

O script antigo, data_acquisition/raspa_noticias.py, foi mantido no projeto como registro do método usado no TP2, assim como as páginas salvas em data/html_ibge.

O uso no painel é a página Notícias do IBGE, com nuvem de palavras, tabela das palavras mais frequentes, estatísticas e a lista das matérias. A API também entrega esses dados pela rota GET /noticias.

### 2.4 Dados enviados pelo usuário

Na página Seus dados, o usuário pode enviar um CSV com uma coluna chamada codigo (código IBGE de 7 dígitos) e quantas colunas quiser. O painel aceita arquivos separados por vírgula ou por ponto e vírgula, com decimal em vírgula no padrão do Excel brasileiro, e com codificação UTF-8 ou Latin-1. Os dados ficam guardados no estado de sessão enquanto a pessoa navega entre as páginas, aparecem ao lado dos indicadores do IBGE, podem ser cruzados com o PIB per capita em um gráfico de dispersão e podem ser baixados já combinados.

## 3. Base tratada (saída do cálculo)

O script modeling/calcula_indicadores.py gera dois arquivos em data_acquisition/cleaned_data.

O arquivo indicadores_municipios.csv tem 77.980 linhas, uma por município e ano, de 2010 a 2023. As colunas de identificação são codigo, municipio, uf, regiao e capital. As colunas de valor são pib (mil reais), populacao, vab_total e o valor adicionado de cada setor. As colunas de indicador são participacao_pib, pib_per_capita, pib_per_capita_brasil, razao_riqueza, posicao_pib, participacao_acumulada, part_agropecuaria, part_industria, part_servicos, part_adm_publica, hhi, dependencia_adm e perfil.

O arquivo resumo_brasil.csv tem uma linha por ano, com o PIB e a população do Brasil, o PIB per capita nacional, a quantidade de municípios que somam metade do PIB, a participação das capitais e a participação dos 10 maiores municípios.

Esses dois arquivos são a única fonte lida pelo painel e pela API. Nenhuma das duas saídas consulta a internet em tempo de uso.

## 4. Tratamentos aplicados

A primeira linha do retorno da API é o cabeçalho e é descartada. Os valores chegam como texto e são convertidos para número, e os ausentes, que vêm como "..." ou "-", viram vazio. O PIB é transformado do formato longo para o largo, com uma coluna por variável. O nome do município chega em dois formatos, "Rio de Janeiro (RJ)" e "Ariquemes - RO", e a sigla é removida nos dois casos. A UF e a região não são tiradas do nome, e sim do código IBGE: os dois primeiros dígitos indicam a UF e o primeiro indica a região. As 27 capitais são marcadas pelo código. PIB e população são juntados pelo código e pelo ano. O PIB, que vem em milhares de reais, é multiplicado por mil no cálculo do per capita.

No texto das notícias, são descartados os parágrafos com menos de 60 caracteres (legendas e itens de menu), o aviso de instabilidade do site e a linha de autoria, que apareceriam em todas as matérias e distorceriam a nuvem de palavras.

## 5. Qualidade dos dados

A base tratada tem 15 valores de PIB vazios. São os 5 municípios criados em 2013 (Mojuí dos Campos, Pescaria Brava, Balneário Rincão, Pinto Bandeira e Paraíso das Águas), que não têm dado em 2010, 2011 e 2012. A população tem 10 valores vazios, ligados aos mesmos municípios. No total, os vazios representam cerca de 0,03% das linhas, abaixo da meta de 1%.

As Estimativas de População têm 5.571 municípios por ano, um a mais que o PIB. O município extra é Boa Esperança do Norte (MT), código 5101837, que ainda não tem PIB publicado e fica de fora na junção.

Na base de notícias, as 15 matérias têm entre 466 e 2.019 palavras, com média de 1.333. A busca da Agência devolveu 29 itens, dos quais 14 eram foto, áudio ou documento e foram descartados pelo filtro de tipo.

## 6. Validação contra os números oficiais

Os indicadores foram conferidos contra os números divulgados pelo IBGE na notícia de 19/12/2025 sobre o PIB dos Municípios 2023.

| Indicador | Calculado | Divulgado pelo IBGE |
|---|---|---|
| Participação das capitais em 2022 | 27,5% | 27,5% |
| Participação das capitais em 2023 | 28,3% | 28,3% |
| Participação dos 10 maiores municípios em 2023 | 24,5% | 24,5% |
| PIB per capita do Brasil em 2023 | R$ 53.886,67 | R$ 53,9 mil |
| PIB per capita de Saquarema (RJ) em 2023 | R$ 722.441,52 | R$ 722,4 mil |
| PIB per capita de Brasília (DF) em 2023 e razão | R$ 129.790,44 e 2,41 | R$ 129,8 mil e 2,41 |
| PIB per capita de Cajapió (MA) e São João Batista (MA) em 2023 | R$ 8.079,74 e R$ 8.246,12 | R$ 8.079,74 e R$ 8.246,12 |

Nina Rodrigues (MA) e Matões do Norte (MA) diferem em um ou dois centavos, por arredondamento, já que a API entrega o PIB em milhares de reais.

A única divergência relevante é Manari (PE). O IBGE divulga PIB per capita de R$ 7.201,70 em 2023, e o cálculo do projeto dá R$ 7.707,53. A população usada é a mesma do IBGE Cidades (23.763 habitantes no Censo 2022), então a diferença está no PIB: para chegar ao valor divulgado o PIB teria que ser de cerca de R$ 171 milhões, enquanto a tabela 5938 hoje informa R$ 183,2 milhões. A hipótese mais provável é uma revisão posterior dos dados, mas isso não foi confirmado. O projeto mantém o valor da tabela oficial, e com os dados atuais o menor PIB per capita de 2023 passa a ser Nina Rodrigues (MA).

## 7. Como os dados são servidos

A partir do TP3 os indicadores têm duas saídas.

O **painel em Streamlit** (deployment/app.py e a pasta deployment/paginas) lê os arquivos tratados direto do disco, usando cache para não reler a cada clique. São sete páginas: Visão geral, Município, Ranking, Comparação, Notícias do IBGE, Seus dados e Consulta pela API.

A **API em FastAPI** (deployment/api.py) lê os mesmos arquivos quando liga e os entrega em JSON por seis rotas: GET / com a descrição da própria API, GET /municipios/{codigo} com os indicadores de um município, GET /ranking com os municípios ordenados por um critério, GET /brasil com o resumo nacional por ano, GET /noticias com as matérias coletadas, e POST /comparar, que recebe uma lista de códigos de município e devolve os indicadores de todos. A documentação interativa fica em /docs, gerada automaticamente pelo FastAPI. A página Consulta pela API do painel consome essas rotas, demonstrando a integração de ponta a ponta.

## 8. Limitações

Os indicadores de composição setorial só existem até 2021, pela ausência de abertura setorial nas divulgações de 2022 e 2023. Os valores são correntes e não foram deflacionados, então comparações de valor entre anos devem ser feitas com cuidado; os indicadores de participação e de razão não são afetados, porque comparam valores do mesmo ano. O PIB per capita pode ser muito alto em municípios com petróleo, mineração ou refinarias sem que essa riqueza fique com a população, e o painel avisa quando a razão de riqueza passa de 3. A coleta das notícias depende do Chrome instalado e de internet, e leva cerca de dois minutos, por isso é executada sob demanda e nunca dentro da aplicação.

## 9. Organização dos arquivos

As bases numéricas seguem a estrutura do TDSP: os dados brutos ficam em data_acquisition/raw_data e os tratados em data_acquisition/cleaned_data. O conteúdo extraído da web fica em data/, como pede o enunciado, com os resultados da coleta em data/noticias_ibge.csv e data/noticias_ibge.txt e as páginas do método antigo em data/html_ibge. Os scripts de coleta ficam em data_acquisition, o cálculo em modeling, e o painel e a API em deployment.

## 10. Caminho para o uso de LLM

O conteúdo textual coletado (19.996 palavras em 15 matérias oficiais) e a base numérica tratada são as duas entradas previstas para as funcionalidades de IA generativa do TP4. O planejamento está em business_understanding/planejamento_llm.md.
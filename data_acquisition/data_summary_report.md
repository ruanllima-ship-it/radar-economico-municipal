# Data Summary Report — Radar Econômico Municipal

Projeto de Bloco: Inteligência Artificial Aplicada — Ciência de Dados
Aluno: Ruan Luiz Fernandes da Silva Lima
Versão: TP2 (evolução do rascunho entregue no TP1)

## 1. Visão geral

O projeto usa quatro entradas de dados. Três vêm do IBGE e uma vem do próprio usuário. A base principal é o PIB dos Municípios, que traz o PIB e o valor adicionado por setor. A população vem das Estimativas de População e dos Censos 2010 e 2022, e é necessária porque o PIB per capita não está disponível na tabela do PIB dos Municípios. As notícias da Agência de Notícias do IBGE são a fonte de texto do painel. Por fim, o usuário pode enviar um CSV próprio, que é juntado aos indicadores pelo código do município.

Todas as bases numéricas são coletadas por script, sem download manual. A etapa de entendimento dos dados foi feita consultando os metadados da própria API antes de escrever a coleta, com os scripts espiar_sidra.py, espiar_populacao.py e espiar_populacao_2.py, que ficam no projeto como registro.

## 2. Fontes de dados

### 2.1 PIB dos Municípios (fonte principal)

A fonte é o IBGE, Sistema de Contas Nacionais, tabela 5938 do SIDRA, acessada pela API pública em https://apisidra.ibge.gov.br, sem cadastro nem chave. Os dados são anuais, por município, em milhares de reais correntes. A tabela vai de 2002 a 2023, e o projeto usa de 2010 a 2023.

As variáveis coletadas são o PIB a preços correntes (variável 37), o valor adicionado bruto total (498), da agropecuária (513), da indústria (517), dos serviços exceto administração pública (6575) e da administração, defesa, educação e saúde públicas e seguridade social (525). Para 2022 e 2023 só existe o PIB, porque o IBGE publicou esses anos sem a abertura por setor.

A coleta é feita pelo script data_acquisition/coleta_sidra.py, que pede um ano e uma variável por vez (74 pedidos), com até três tentativas em caso de falha. O resultado é o arquivo data_acquisition/raw_data/pib_municipios_2010_2023.csv, com 412.180 linhas em formato longo (colunas codigo, municipio, ano, codigo_variavel, valor e variavel). Cada combinação de ano e variável veio com exatamente 5.570 linhas.

O uso no projeto é o cálculo de todos os sete indicadores: participação no PIB, PIB per capita, razão de riqueza, curva de concentração, HHI, dependência da administração pública e perfil econômico.

### 2.2 População (fonte complementar)

A população é necessária para o PIB per capita e a razão de riqueza. Como o IBGE publica população em tabelas diferentes conforme o ano, a coleta usa três fontes: o Censo 2010 para 2010 (tabela 202, variável 93, que devolve o total quando não se pede sexo nem situação do domicílio), as Estimativas de População para 2011 a 2021 e para 2024 (tabela 6579, variável 9324) e o Censo 2022 para 2022 (tabela 4709, variável 93). A tabela de estimativas não tem 2007, 2010, 2022 nem 2023.

Para 2023, o projeto segue o próprio IBGE, que calculou o PIB per capita de 2022 e de 2023 com a população do Censo 2022. Essa regra é aplicada no cálculo dos indicadores, não na base bruta. O ano de 2024 foi coletado e é usado apenas como exemplo de dado extra no modelo de upload do painel.

A coleta é feita pelo script data_acquisition/coleta_populacao.py, que primeiro consulta quais anos a tabela de estimativas realmente tem. O resultado é data_acquisition/raw_data/populacao_municipios_2010_2024.csv, com 77.987 linhas (colunas codigo, municipio, ano, populacao e fonte).

### 2.3 Notícias da Agência de Notícias do IBGE (fonte de texto, web scraping)

São as notícias e releases oficiais publicados pelo IBGE a cada divulgação do PIB dos Municípios, listados na seção "Notícias e Releases" da página oficial da pesquisa. Foram coletadas 10 matérias, publicadas entre dezembro de 2018 e dezembro de 2025, cobrindo os resultados de 2016 a 2023.

Os sites do IBGE têm proteção anti-robô (Cloudflare) e respondem com status 403 a pedidos feitos por script, o que foi confirmado pelo script data_acquisition/espiar_pagina.py. Para não burlar essa proteção, as páginas foram abertas e salvas pelo navegador na pasta data/html_ibge. O script data_acquisition/raspa_noticias.py usa Beautiful Soup para ler esses HTMLs e extrair o título, a data de publicação, o resumo e o link (das etiquetas meta og:title, article:published_time, og:description e og:url) e o texto da matéria (das tags de parágrafo, descartando trechos curtos, o aviso de instabilidade do site e a linha de autoria).

O resultado é salvo em dois formatos: data/noticias_ibge.csv, com uma linha por notícia e as colunas data, tipo, titulo, resumo, qtd_paragrafos, qtd_palavras, link e texto, e data/noticias_ibge.txt, com o texto corrido de todas as notícias. No total são 14.657 palavras, com média de 1.466 por notícia.

O uso no painel é a aba Notícias do IBGE, com nuvem de palavras, tabela das palavras mais frequentes, estatísticas de tamanho das matérias e a lista das notícias com link para o original.

### 2.4 Dados enviados pelo usuário

Na aba Seus dados, o usuário pode enviar um CSV com uma coluna chamada codigo (código IBGE de 7 dígitos) e quantas colunas quiser, como orçamento, número de empregos ou nota do IDEB. O painel aceita arquivos separados por vírgula ou por ponto e vírgula, com decimal em vírgula no padrão do Excel brasileiro, e com codificação UTF-8 ou Latin-1. Os dados ficam guardados no estado de sessão enquanto a pessoa navega, aparecem ao lado dos indicadores do IBGE, podem ser cruzados com o PIB per capita em um gráfico de dispersão e podem ser baixados junto com os dados do IBGE. O painel também oferece um modelo de CSV para download.

## 3. Base tratada (saída do cálculo)

O script modeling/calcula_indicadores.py gera dois arquivos em data_acquisition/cleaned_data.

O arquivo indicadores_municipios.csv tem 77.980 linhas, uma por município e ano, de 2010 a 2023. As colunas de identificação são codigo, municipio (sem a sigla da UF), uf, regiao e capital. As colunas de valor são pib (mil reais), populacao, vab_total e o valor adicionado de cada setor. As colunas de indicador são participacao_pib (%), pib_per_capita (reais), pib_per_capita_brasil, razao_riqueza, posicao_pib, participacao_acumulada (%), part_agropecuaria, part_industria, part_servicos e part_adm_publica (% do valor adicionado), hhi (de 0,25 a 1), dependencia_adm (%) e perfil.

O arquivo resumo_brasil.csv tem uma linha por ano, com o PIB e a população do Brasil, o PIB per capita nacional, a quantidade de municípios que somam metade do PIB, a participação das capitais e a participação dos 10 maiores municípios.

## 4. Tratamentos aplicados

A primeira linha do retorno da API é o cabeçalho e é descartada. Os valores chegam como texto e são convertidos para número, e os ausentes, que vêm como "..." ou "-", viram vazio. O PIB é transformado do formato longo para o largo, com uma coluna por variável. O nome do município chega em dois formatos, "Rio de Janeiro (RJ)" e "Ariquemes - RO", e a sigla é removida nos dois casos. A UF e a região não são tiradas do nome, e sim do código IBGE: os dois primeiros dígitos indicam a UF e o primeiro indica a região. As 27 capitais são marcadas pelo código. PIB e população são juntados pelo código e pelo ano. O PIB, que vem em milhares de reais, é multiplicado por mil no cálculo do per capita.

## 5. Qualidade dos dados

A base tratada tem 15 valores de PIB vazios. São os 5 municípios criados em 2013 (Mojuí dos Campos, Pescaria Brava, Balneário Rincão, Pinto Bandeira e Paraíso das Águas), que não têm dado em 2010, 2011 e 2012. Na base bruta isso aparece como 90 valores "..." (5 municípios, 3 anos, 6 variáveis). A população tem 10 valores vazios, ligados aos mesmos municípios nos anos anteriores à sua criação. No total, os vazios representam cerca de 0,03% das linhas, abaixo da meta de 1%.

As Estimativas de População têm 5.571 municípios por ano, um a mais que o PIB. O município extra é Boa Esperança do Norte (MT), código 5101837, que ainda não tem PIB publicado e fica de fora na junção.

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

A única divergência relevante é Manari (PE). O IBGE divulga PIB per capita de R$ 7.201,70 em 2023, e o cálculo do projeto dá R$ 7.707,53. A população usada é a mesma do IBGE Cidades (23.763 habitantes no Censo 2022), então a diferença está no PIB: para chegar a R$ 7.201,70 o PIB teria que ser de cerca de R$ 171 milhões, enquanto a tabela 5938 hoje informa R$ 183,2 milhões. A hipótese mais provável é uma revisão posterior dos dados (a página oficial lista uma nota técnica de junho de 2026, publicada depois da divulgação), mas isso não foi confirmado. O projeto mantém o valor da tabela oficial, e com os dados atuais o menor PIB per capita de 2023 passa a ser Nina Rodrigues (MA).

## 7. Limitações

Os indicadores de composição setorial só existem até 2021, pela ausência de abertura setorial nas divulgações de 2022 e 2023. Os valores são correntes e não foram deflacionados, então comparações de valor entre anos devem ser feitas com cuidado; os indicadores de participação e de razão não são afetados, porque comparam valores do mesmo ano. O PIB per capita pode ser muito alto em municípios com petróleo, mineração ou refinarias sem que essa riqueza fique com a população, e o painel avisa quando a razão de riqueza passa de 3. As notícias dependem de páginas salvas pelo navegador por causa do bloqueio a acesso automatizado, e novas notícias precisam ser salvas da mesma forma antes de rodar a raspagem.

## 8. Organização dos arquivos

As bases numéricas seguem a estrutura do TDSP: os dados brutos ficam em data_acquisition/raw_data e os tratados em data_acquisition/cleaned_data. O conteúdo extraído da web fica em data/, como pede o enunciado do TP2, com as páginas salvas em data/html_ibge e os resultados da raspagem em data/noticias_ibge.csv e data/noticias_ibge.txt. Os scripts de coleta e raspagem ficam em data_acquisition, o cálculo dos indicadores em modeling e o painel em deployment.
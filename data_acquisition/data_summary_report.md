# Data Summary Report — Radar Econômico Municipal

Projeto de Bloco: Inteligência Artificial Aplicada — Ciência de Dados
Aluno: Ruan Luiz Fernandes da Silva Lima
Versão: TP5 (revisão das versões entregues no TP2, TP3 e TP4)

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


---

# Atualização para o TP4 e o TP5

Versão: TP5 (revisão das versões entregues no TP2, TP3 e TP4)

As seções de 1 a 10 acima descrevem os dados como estavam ao final do TP3. Esta
parte registra como esses mesmos dados — os coletados por API e os coletados por
raspagem — passaram a alimentar as funcionalidades de inteligência artificial.

## 11. As duas entradas e os dois usos de IA

O projeto tem duas origens de dado, e cada uma alimenta uma funcionalidade de IA
diferente. Nenhuma das duas gerou coleta nova: os TPs 4 e 5 usam exatamente os
arquivos já descritos acima.

| Origem | Coletado com | Arquivo | Usado por |
|---|---|---|---|
| Texto das notícias do IBGE | Selenium + Beautiful Soup | `data/noticias_ibge.csv` (15 matérias, 19.996 palavras) | Resumo automático (TP4) |
| Indicadores municipais | API do SIDRA | `data_acquisition/cleaned_data/indicadores_municipios.csv` (77.980 linhas) | Agente de diagnóstico (TP5) |

Essa simetria não foi planejada no TP2, mas se mostrou útil: o dado de **texto**
alimenta a tarefa de texto, e o dado **numérico** alimenta a tarefa de análise.

## 12. O dado de raspagem no TP4: resumo automático

As 15 matérias coletadas com Selenium são a entrada da página **Resumo com IA**
e da rota `POST /processar_texto`.

O usuário escolhe uma das matérias já coletadas, ou cola um texto próprio, e o
modelo `recogna-nlp/ptt5-base-summ` devolve um resumo. O modelo lê no máximo 512
pedaços por vez, e a resposta da API informa quantos pedaços o texto tinha,
quantos foram lidos e se houve corte — o campo `texto_cortado` existe justamente
para que o usuário não receba um resumo parcial achando que é do texto inteiro.

As matérias têm entre 466 e 2.019 palavras, com média de 1.333. A maioria
ultrapassa o limite de 512 pedaços, e isso fica declarado na resposta.

A configuração de geração foi escolhida por experimento, registrado em
`modeling/afina_resumo.py`: foram comparadas duas configurações de busca em
feixe (`num_beams`), tamanho mínimo e máximo e penalidade de comprimento, e a
configuração B foi adotada.

## 13. O dado de API no TP5: análise e diagnóstico

A base tratada de 77.980 linhas é a entrada do agente. O caminho completo de um
diagnóstico é este:

1. O usuário escolhe município e ano na barra lateral do painel.
2. A página chama `GET /analise/{codigo}` na API do projeto.
3. A API chama `agente.montar_analise()`, que **lê o CSV tratado**, recorta o
   ano pedido, calcula os percentis 25, 50, 75 e 90 da distribuição nacional
   **daquele ano** e classifica o município nessas faixas.
4. As regras de decisão produzem três listas: achados, alertas e o que
   acompanhar.
5. A página mostra tudo isso na hora, com gráficos, sem IA nenhuma.
6. Se o usuário clicar no botão, a página chama `POST /diagnostico`, que refaz a
   análise e a entrega ao modelo `Qwen/Qwen2.5-1.5B-Instruct`, que escreve três
   parágrafos.

O ponto importante é o passo 3: **os percentis não são constantes gravadas no
código**. Eles são recalculados a cada consulta, a partir de todos os municípios
com dado naquele ano. Dizer que a dependência de um município é "muito alta"
significa que ele está entre os 10% mais dependentes do Brasil **naquele ano**,
e não que ele passou de um limite que eu escolhi.

### Quais colunas o agente usa

| Coluna do CSV | Para quê |
|---|---|
| `razao_riqueza` | faixa de riqueza, trajetória 2010–2023 e o achado principal |
| `dependencia_adm` | faixa de dependência pública e o alerta de repasses |
| `hhi` | faixa de concentração setorial |
| `perfil` | distinguir concentração em serviços de concentração industrial |
| `part_agropecuaria`, `part_industria`, `part_servicos`, `part_adm_publica` | gráfico de composição e soma dos setores privados |
| `pib`, `populacao`, `pib_per_capita`, `pib_per_capita_brasil` | números de cabeçalho |
| `posicao_pib` | posição no ranking nacional |
| `uf`, `regiao`, `capital`, `municipio` | identificação e nome do estado por extenso |

A soma dos setores privados é calculada no `agente.py` e entregue pronta ao
modelo. Isso é deliberado: nos primeiros testes o modelo somava os percentuais
por conta própria e errava, desobedecendo à ordem de não calcular. Tirando a
conta das mãos dele, o erro deixa de ser possível.

### A limitação de 2022 e 2023 no agente

Como o IBGE publicou 2022 e 2023 sem abertura setorial, o agente detecta a
ausência (`tem_dados_setoriais`) e faz a análise sem a parte setorial. O painel
avisa em caixa azul e sugere 2021. A API devolve `tem_dados_setoriais: false` e
um dicionário de faixas menor. O prompt enviado ao modelo também muda: em vez do
setor predominante, vai uma observação explicando que o dado não existe naquele
ano. Nenhuma das três camadas quebra.

## 14. Um defeito de dado descoberto no TP5

Os testes com municípios ricos revelaram um problema que não era do modelo nem
do prompt, mas da **frase que a análise escrevia**. O achado era:

> "A administração pública responde por 6,1% da economia local, contra uma
> mediana nacional de 26,8%."

Dois números no mesmo período, sem nenhuma palavra indicando a direção. Com
Uiramutã (83,5% contra 26,8%) o modelo acertava, porque a diferença é gritante.
Com Sorriso e São Paulo ele **inverteu**, escrevendo "forte dependência da
administração pública" sobre o município de menor dependência.

A correção foi no `agente.py`:

> "A administração pública responde por 6,1% da economia deste município.
> Isso é MENOS que a mediana nacional, que é de 26,8%."

O caso ficou registrado porque é uma lição sobre dado, e não sobre modelo:
**quando o dado sai da análise ambíguo, nenhuma instrução de prompt conserta.**
A mesma lógica levou a reescrever a frase dos setores privados, deixando
explícito que 92,7% é soma de três setores e não a participação de um.

## 15. Como os dados são servidos ao final do TP5

A **API em FastAPI** tem 12 rotas e 25 Response Models. As quatro novas do TP5
são: `GET /analise/{codigo}` (análise por regras, sem IA, resposta imediata),
`POST /diagnostico` (análise mais texto gerado), `GET /modelo_diagnostico`
(situação do modelo sem carregá-lo) e `POST /modelo_diagnostico/descarregar`
(libera os 2,9 GB da memória).

O **painel em Streamlit** tem 9 páginas: Visão geral, Município, Ranking,
Comparação, Notícias do IBGE, Resumo com IA, Diagnóstico com IA, Seus dados e
Consulta pela API.

Nenhuma das duas saídas consulta a internet em tempo de uso, e nenhum dado sai
da máquina em que o projeto roda.

## 16. Verificação automática do estado dos dados e do código

O arquivo `modeling/verifica_tp5.py` confere o projeto inteiro em 38 testes
automáticos: se os arquivos existem, se importam sem erro, se o agente consegue
analisar um município real do CSV, se os números de contagem vêm sem casa
decimal, se a API tem as rotas e os schemas esperados e se as bibliotecas estão
instaladas. Ele só lê, nunca escreve.

O arquivo foi escrito depois de um desligamento forçado da máquina ter
corrompido o ambiente, e passou a ser o primeiro comando rodado a cada sessão de
trabalho.

## 17. Limitações acrescentadas no TP5

Às limitações da seção 8 somam-se:

1. **A análise setorial não existe para 2022 e 2023**, e é ela que carrega os
   alertas mais relevantes. A análise desses anos fica reduzida à riqueza e à
   trajetória.
2. **O diagnóstico escrito leva de 3,5 a 5 minutos** na máquina de
   desenvolvimento, porque o modelo roda em CPU.
3. **O texto gerado tem deslizes de redação** conhecidos e documentados em
   `modeling/engenharia_de_prompt.md`. Nenhum deles afeta um número, e a
   conferência está disponível ao leitor pelo prompt devolvido junto.
4. **O agente analisa um município por vez.** Não há comparação entre
   municípios dentro do diagnóstico — para isso continua existindo a página de
   Comparação e a rota `POST /comparar`.
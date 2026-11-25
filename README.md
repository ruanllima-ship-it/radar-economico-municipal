# Radar Econômico Municipal

Painel interativo em Streamlit e API em FastAPI que mostram o quanto a riqueza do Brasil está concentrada em poucas cidades, de que setor cada município vive e quais dependem do setor público. Cobre os 5.570 municípios de 2010 a 2023, com dados oficiais do IBGE, e conta com dois modelos de linguagem rodando localmente: um que resume as matérias do IBGE coletadas da web e outro que escreve o diagnóstico econômico de um município a partir de uma análise feita em Python.

As 27 capitais responderam por 28,3% do PIB nacional em 2023, contra 27,5% em 2022 e 36,1% em 2002. O número de municípios necessários para somar metade do PIB do país subiu de 53 em 2010 para 87 em 2021 e voltou a cair para 84 em 2023. O dado é público, mas fica preso em tabelas técnicas. O projeto entrega essa informação já calculada e comparada, por duas portas: uma tela para quem não é técnico e uma API para quem quer os números dentro do próprio sistema.

## O painel: nove páginas com menu de navegação

- **Visão geral:** indicadores do Brasil no ano escolhido, evolução da concentração e quantos municípios vivem de cada setor.
- **Município:** PIB, população, PIB por habitante, razão de riqueza, posição no ranking, composição por setor, índice de concentração (HHI), dependência da administração pública e série histórica, comparados com o estado e o país.
- **Ranking:** ordenação por PIB, PIB por habitante, dependência do setor público ou HHI, com curva de concentração e download em CSV.
- **Comparação:** lista de municípios guardada no estado de sessão enquanto a pessoa navega.
- **Notícias do IBGE:** nuvem de palavras, palavras mais frequentes e estatísticas das 15 matérias oficiais coletadas da web.
- **Resumo com IA:** resume qualquer uma das 15 matérias, ou um texto colado pelo usuário, usando o modelo de linguagem local. Mostra o resumo gerado ao lado do resumo publicado pelo próprio IBGE, para comparação direta.
- **Diagnóstico com IA:** mostra a análise econômica do município feita por regras em Python — números, posição na distribuição nacional, gráficos e três abas com achados, alertas e o que acompanhar — tudo sem carregar modelo nenhum. Se a pessoa clicar no botão, um segundo modelo local transforma essa análise em três parágrafos de texto corrido, e o prompt enviado fica visível para conferência.
- **Seus dados:** upload de um CSV próprio (pelo código IBGE), que é juntado aos indicadores, cruzado em gráfico e pode ser baixado.
- **Consulta pela API:** consome a API do próprio projeto, demonstrando a integração de ponta a ponta.

Os filtros de ano, estado e município ficam na barra lateral e valem para todas as páginas. O painel usa `@st.cache_data` para ler os dados uma vez só e `st.session_state` para guardar a lista de comparação, os dados enviados pelo usuário e o contador da sessão.

## O agente de diagnóstico municipal

A funcionalidade central do TP5 é um agente que analisa um município e escreve um parecer. Ele é dividido em duas responsabilidades, em dois arquivos separados:

| Arquivo | Papel | Usa IA? |
|---|---|---|
| `deployment/agente.py` | **pensa** — classifica o município por percentil contra a distribuição nacional do ano e aplica regras de decisão, produzindo achados, alertas e o que acompanhar | não |
| `deployment/diagnostico_llm.py` | **escreve** — transforma a análise pronta em três parágrafos | sim |

A separação nasceu de um defeito medido. Quando o modelo recebia os números crus e a tarefa de analisar, ele somava percentuais que não podiam ser somados, comparava PIB total com PIB por habitante e chegou a dizer que Uiramutã fica no Rio Grande do Norte. Tirando a análise das mãos dele, esses erros deixaram de ser possíveis.

As faixas de classificação não são limites escolhidos à mão: são os percentis 25, 50, 75 e 90 da distribuição nacional **daquele ano**, recalculados a cada consulta. Dizer que um município tem dependência "muito alta" significa que ele está entre os 10% mais dependentes do Brasil naquele ano.

A evolução do prompt está registrada em [Engenharia de Prompt](modeling/engenharia_de_prompt.md), com as **oito versões**, o defeito que cada uma produziu, a correção que gerou a seguinte e as medições de cada execução.

## Os dois modelos de linguagem

| Uso | Modelo | Parâmetros | Memória |
|---|---|---|---|
| Resumo de texto (TP4) | `recogna-nlp/ptt5-base-summ` | 223 milhões | cerca de 1 GB |
| Diagnóstico municipal (TP5) | `Qwen/Qwen2.5-1.5B-Instruct` | 1,54 bilhão | cerca de 2,9 GB |

Os dois são baixados da HuggingFace e executados **inteiramente na máquina local**, com Transformers e PyTorch na versão de CPU. Não há chave de API, conta em serviço externo nem dependência de nuvem: depois do primeiro download, o projeto funciona sem internet e nenhum dado sai da máquina.

Nenhum dos dois é carregado quando a API liga. Cada um entra na memória na primeira vez que alguém pede o que ele faz. O resumo sai em 5 a 15 segundos; o diagnóstico leva de 3,5 a 5 minutos, porque o modelo é maior e roda em CPU. A rota `POST /modelo_diagnostico/descarregar` existe para liberar os 2,9 GB quando a máquina precisar.

A justificativa da escolha do primeiro modelo, com a comparação entre alternativas e o experimento dos parâmetros de geração, está em [Escolha e integração do modelo](modeling/escolha_do_modelo.md).

## A API: doze rotas em FastAPI

| Rota | O que faz |
|---|---|
| `GET /` | descreve a API e lista as rotas |
| `GET /municipios/{codigo}` | indicadores de um município pelo código IBGE, com ano opcional |
| `GET /ranking` | municípios ordenados por critério, com filtros de ano, estado e limite |
| `GET /brasil` | resumo da concentração econômica do Brasil, ano a ano |
| `GET /noticias` | matérias do IBGE coletadas da web |
| `POST /comparar` | recebe uma lista de códigos de município e devolve os indicadores de todos |
| `POST /processar_texto` | recebe um texto em português e devolve o resumo gerado pelo modelo local |
| `GET /modelo` | informa se o modelo de resumo já está carregado, sem carregá-lo |
| `GET /analise/{codigo}` | análise econômica do município feita por regras, **sem IA e com resposta imediata** |
| `POST /diagnostico` | a mesma análise mais o diagnóstico escrito pelo modelo local |
| `GET /modelo_diagnostico` | informa se o modelo de diagnóstico já está carregado, sem carregá-lo |
| `POST /modelo_diagnostico/descarregar` | tira o modelo de diagnóstico da memória |

A existência de `GET /analise` separada de `POST /diagnostico` é proposital: quem quiser só os insights não precisa esperar pelo modelo nem gastar memória com ele.

Todas as rotas usam **Response Models** em Pydantic, declarados em `deployment/respostas.py`, hoje 25 ao todo. Isso faz o FastAPI validar cada resposta antes de enviá-la e mostrar os campos e os tipos de cada rota na documentação interativa, que fica em `/docs`.

A resposta de `POST /diagnostico` inclui o campo `prompt_enviado`, com o texto exato que o modelo recebeu. Qualquer número do diagnóstico que não esteja ali foi inventado pelo modelo, e isso é verificável por qualquer pessoa.

### Tratamento de erros

| Código | Quando acontece |
|---|---|
| 400 | texto curto demais, tipo de análise não suportado, critério inválido, lista vazia |
| 404 | município, ano, estado ou notícia não encontrados, e rota inexistente |
| 405 | método HTTP errado para a rota |
| 413 | texto acima de 50.000 caracteres |
| 422 | corpo do pedido fora do formato declarado (validação do Pydantic) |
| 429 | modelo ocupado gerando outro resumo ou outro diagnóstico |
| 500 | falha na geração, ou qualquer erro imprevisto |
| 503 | modelo de linguagem não pôde ser carregado |

Dois tratadores globais garantem que todo erro saia no mesmo formato `{"detail": "..."}`, com mensagem em português, inclusive os erros que o código não previu. O script `deployment/testa_erros_api.py` exercita essas situações em 21 testes automáticos.

## Público-alvo

Gestores públicos municipais e estaduais de cidades pequenas e médias, que normalmente não têm equipe de dados na prefeitura, além de vereadores e conselhos municipais. Como público secundário estão jornalistas de economia, pesquisadores de desenvolvimento regional e empresas avaliando expansão. A API acrescenta um público técnico: desenvolvedores que queiram consumir os indicadores em outro sistema.

## ESG e ODS

Pilar Social, com apoio de Governança. Atende principalmente aos ODS 8 (trabalho decente e crescimento econômico, meta 8.2 de diversificação) e 10 (redução das desigualdades, meta 10.1), e de forma secundária aos ODS 11 (cidades e comunidades sustentáveis, meta 11.a) e 16 (instituições transparentes, meta 16.6).

O indicador que carrega o argumento social é a razão de riqueza. Uiramutã (RR) tem 0,31 e Paulínia (SP) tem 10,83: são 35 vezes de distância entre dois municípios do mesmo país. O enquadramento completo, incluindo uma seção sobre o que o projeto **não** mede, está no [Project Charter](business_understanding/project_charter.md), seção 17.

## Fontes de dados

- **PIB dos Municípios**, IBGE, tabela 5938 do SIDRA, pela API aberta (PIB e valor adicionado por setor, 2010 a 2023).
- **População**, IBGE: Censo 2010 (tabela 202), Estimativas de População (tabela 6579) e Censo 2022 (tabela 4709).
- **Notícias da Agência de Notícias do IBGE**: 15 matérias publicadas entre 2015 e 2025, com 19.996 palavras, coletadas com Selenium e Beautiful Soup.
- **CSV do usuário**, enviado pelo próprio painel.

Na divulgação de dezembro de 2025, o IBGE publicou 2022 e 2023 sem a abertura por setor. Por isso os indicadores de composição setorial vão até 2021, e o agente detecta a ausência e faz a análise sem a parte setorial nesses anos.

Os sites do IBGE respondem com erro 403 a pedidos de script simples e montam parte do conteúdo por JavaScript. Por isso a coleta das notícias usa o Selenium, que executa a página em um navegador real, sem burlar a proteção.

Os detalhes de cada fonte, dos tratamentos e da validação estão no [Data Summary Report](data_acquisition/data_summary_report.md). Escopo, objetivos e stakeholders estão no [Project Charter](business_understanding/project_charter.md). O planejamento da IA generativa está no [Planejamento de LLM](business_understanding/planejamento_llm.md).

## Organização do projeto (TDSP)

~~~
radar_economico_municipal/
├── README.md
├── requirements.txt
├── business_understanding/
│   ├── project_charter.md
│   └── planejamento_llm.md
├── data/                               conteúdo extraído da web
│   ├── html_ibge/                      páginas salvas no método do TP2
│   ├── noticias_ibge.csv
│   └── noticias_ibge.txt
├── data_acquisition/
│   ├── raw_data/                       bases do IBGE como vieram da API
│   ├── cleaned_data/                   base tratada com os indicadores
│   ├── espiar_*.py                     consultas aos metadados antes da coleta
│   ├── testa_selenium.py               diagnóstico do acesso aos sites do IBGE
│   ├── coleta_sidra.py                 coleta do PIB dos Municípios
│   ├── coleta_populacao.py             coleta da população
│   ├── coleta_noticias_selenium.py     coleta das notícias com Selenium
│   ├── raspa_noticias.py               método do TP2, mantido como registro
│   └── data_summary_report.md
├── modeling/
│   ├── calcula_indicadores.py          cálculo e validação dos sete indicadores
│   ├── confere_menores.py
│   ├── espiar_ambiente.py              verificação do hardware antes de escolher o modelo
│   ├── testa_instalacao.py             conferência do PyTorch e do Transformers
│   ├── testa_modelo.py                 primeiro teste do modelo de resumo
│   ├── afina_resumo.py                 experimento dos parâmetros de geração do resumo
│   ├── testa_modelo_instruct.py        teste do modelo de diagnóstico e bfloat16 x float32
│   ├── testa_agente.py                 sete casos de teste da análise por regras
│   ├── afina_prompt.py                 experimento comparando as versões do prompt
│   ├── verifica_tp5.py                 verificação do projeto inteiro em 38 testes
│   ├── escolha_do_modelo.md            justificativa do modelo de resumo
│   └── engenharia_de_prompt.md         as oito versões do prompt do agente
└── deployment/
    ├── app.py                          menu de navegação do painel
    ├── comum.py                        funções compartilhadas pelas páginas
    ├── api.py                          API em FastAPI, 12 rotas e tratamento de erros
    ├── respostas.py                    os 25 Response Models
    ├── modelo_llm.py                   modelo de resumo (TP4)
    ├── agente.py                       análise por regras, sem IA (TP5)
    ├── diagnostico_llm.py              modelo de diagnóstico (TP5)
    ├── testa_erros_api.py              bateria de 21 testes do tratamento de erros
    └── paginas/                        as nove páginas do painel
~~~

## Como rodar

Criar e ativar o ambiente virtual. Depois instalar o PyTorch na versão de CPU, que precisa de um índice próprio:

~~~
py -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
~~~

Sem o `--index-url`, o pip baixa a versão com suporte a GPU, que tem quase 3 GB. Em seguida, instalar o restante:

~~~
pip install -r requirements.txt
~~~

Antes de qualquer coisa, vale conferir se o projeto está inteiro:

~~~
py modeling\verifica_tp5.py
~~~

Esse script faz 38 testes, só lê arquivos e nunca escreve.

Todos os comandos abaixo rodam a partir da pasta raiz do projeto.

Para abrir o painel:

~~~
streamlit run deployment\app.py
~~~

Para ligar a API (em outro terminal; é obrigatório para as páginas Resumo com IA, Diagnóstico com IA e Consulta pela API):

~~~
py -m uvicorn deployment.api:app
~~~

A API sobe em `http://127.0.0.1:8000` e a documentação fica em `http://127.0.0.1:8000/docs`.

O parâmetro `--reload` serve para desenvolvimento e **não deve ser usado para rodar o projeto**: ele reinicia a API a cada arquivo salvo, o que derruba um diagnóstico em andamento, e mantém um processo Python a mais na memória.

Na primeira vez que cada funcionalidade de IA for usada, o modelo correspondente é baixado da HuggingFace (892 MB para o resumo, 3,09 GB para o diagnóstico) e guardado no cache local, em `C:\Users\<usuario>\.cache\huggingface`. Esse download acontece uma vez só.

Para rodar a bateria de testes do tratamento de erros, com a API ligada em outro terminal:

~~~
py deployment\testa_erros_api.py
~~~

Para testar a análise por regras, sem precisar da API nem do modelo:

~~~
py modeling\testa_agente.py
~~~

Para reconstruir toda a base do zero, rodar nesta ordem:

~~~
py data_acquisition\coleta_sidra.py
py data_acquisition\coleta_populacao.py
py data_acquisition\coleta_noticias_selenium.py
py modeling\calcula_indicadores.py
~~~

A coleta das notícias abre uma janela do Chrome e leva cerca de dois minutos.

## Autor

Ruan Luiz Fernandes da Silva Lima — Ciência de Dados, Projeto de Bloco: Inteligência Artificial Aplicada.

Este trabalho foi realizado com o auxílio da ferramenta de inteligência artificial generativa Claude Opus 5, da Anthropic.
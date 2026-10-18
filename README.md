# Radar Econômico Municipal

Painel interativo em Streamlit e API em FastAPI que mostram o quanto a riqueza do Brasil está concentrada em poucas cidades, de que setor cada município vive e quais dependem do setor público. Cobre os 5.570 municípios de 2010 a 2023, com dados oficiais do IBGE.

As 27 capitais responderam por 28,3% do PIB nacional em 2023, contra 27,5% em 2022 e 36,1% em 2002. O número de municípios necessários para somar metade do PIB do país subiu de 53 em 2010 para 87 em 2021 e voltou a cair para 84 em 2023. O dado é público, mas fica preso em tabelas técnicas. O projeto entrega essa informação já calculada e comparada, por duas portas: uma tela para quem não é técnico e uma API para quem quer os números dentro do próprio sistema.

## O painel: sete páginas com menu de navegação

- **Visão geral:** indicadores do Brasil no ano escolhido, evolução da concentração e quantos municípios vivem de cada setor.
- **Município:** PIB, população, PIB por habitante, razão de riqueza, posição no ranking, composição por setor, índice de concentração (HHI), dependência da administração pública e série histórica, comparados com o estado e o país.
- **Ranking:** ordenação por PIB, PIB por habitante, dependência do setor público ou HHI, com curva de concentração e download em CSV.
- **Comparação:** lista de municípios guardada no estado de sessão enquanto a pessoa navega.
- **Notícias do IBGE:** nuvem de palavras, palavras mais frequentes e estatísticas das 15 matérias oficiais coletadas da web.
- **Seus dados:** upload de um CSV próprio (pelo código IBGE), que é juntado aos indicadores, cruzado em gráfico e pode ser baixado.
- **Consulta pela API:** consome a API do próprio projeto, demonstrando a integração de ponta a ponta.

Os filtros de ano, estado e município ficam na barra lateral e valem para todas as páginas. O painel usa `@st.cache_data` para ler os dados uma vez só e `st.session_state` para guardar a lista de comparação, os dados enviados pelo usuário e o contador da sessão.

## A API: seis rotas em FastAPI

| Rota | O que faz |
|---|---|
| `GET /` | descreve a API e lista as rotas |
| `GET /municipios/{codigo}` | indicadores de um município pelo código IBGE, com ano opcional |
| `GET /ranking` | municípios ordenados por critério, com filtros de ano, estado e limite |
| `GET /brasil` | resumo da concentração econômica do Brasil, ano a ano |
| `GET /noticias` | matérias do IBGE coletadas da web |
| `POST /comparar` | recebe uma lista de códigos de município e devolve os indicadores de todos |

A documentação interativa fica em `/docs`, gerada automaticamente pelo FastAPI.

## Público-alvo

Gestores públicos municipais e estaduais de cidades pequenas e médias, que normalmente não têm equipe de dados na prefeitura, além de vereadores e conselhos municipais. Como público secundário estão jornalistas de economia, pesquisadores de desenvolvimento regional e empresas avaliando expansão. A API acrescenta um público técnico: desenvolvedores que queiram consumir os indicadores em outro sistema.

## ESG e ODS

Pilar Social, com apoio de Governança. Atende principalmente aos ODS 8 (trabalho decente e crescimento econômico) e 10 (redução das desigualdades), e de forma secundária ao ODS 11 (cidades e comunidades sustentáveis, meta 11.a).

## Fontes de dados

- **PIB dos Municípios**, IBGE, tabela 5938 do SIDRA, pela API aberta (PIB e valor adicionado por setor, 2010 a 2023).
- **População**, IBGE: Censo 2010 (tabela 202), Estimativas de População (tabela 6579) e Censo 2022 (tabela 4709).
- **Notícias da Agência de Notícias do IBGE**: 15 matérias publicadas entre 2015 e 2025, com 19.996 palavras, coletadas com Selenium e Beautiful Soup.
- **CSV do usuário**, enviado pelo próprio painel.

Na divulgação de dezembro de 2025, o IBGE publicou 2022 e 2023 sem a abertura por setor. Por isso os indicadores de composição setorial vão até 2021.

Os sites do IBGE respondem com erro 403 a pedidos de script simples e montam parte do conteúdo por JavaScript. Por isso a coleta das notícias usa o Selenium, que executa a página em um navegador real, sem burlar a proteção.

Os detalhes de cada fonte, dos tratamentos e da validação estão no [Data Summary Report](data_acquisition/data_summary_report.md). Escopo, objetivos e stakeholders estão no [Project Charter](business_understanding/project_charter.md). O caminho previsto para a IA generativa está no [Planejamento de LLM](business_understanding/planejamento_llm.md).

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
│   └── confere_menores.py
└── deployment/
    ├── app.py                          menu de navegação do painel
    ├── comum.py                        funções compartilhadas pelas páginas
    ├── api.py                          API em FastAPI
    └── paginas/                        as sete páginas do painel
~~~

## Como rodar

Criar e ativar o ambiente virtual e instalar as dependências:

~~~
pip install -r requirements.txt
~~~

Todos os comandos abaixo rodam a partir da pasta raiz do projeto.

Para abrir o painel:

~~~
streamlit run deployment\app.py
~~~

Para ligar a API (em outro terminal, se quiser usar a página Consulta pela API):

~~~
py -m uvicorn deployment.api:app --reload
~~~

A API sobe em `http://127.0.0.1:8000` e a documentação fica em `http://127.0.0.1:8000/docs`.

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
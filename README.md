# Radar Econômico Municipal

Painel interativo em Streamlit que mostra o quanto a riqueza do Brasil está concentrada em poucas cidades, de que setor cada município vive e quais dependem do setor público. Cobre os 5.570 municípios de 2010 a 2023, com dados oficiais do IBGE.

As 27 capitais responderam por 28,3% do PIB nacional em 2023, contra 27,5% em 2022 e 36,1% em 2002. O número de municípios necessários para somar metade do PIB do país subiu de 53 em 2010 para 87 em 2021 e voltou a cair para 84 em 2023. O dado é público, mas fica preso em tabelas técnicas. O painel entrega essa informação já calculada e comparada para quem precisa decidir.

## O que o painel faz

- **Visão geral:** indicadores do Brasil no ano escolhido, evolução da concentração e quantos municípios vivem de cada setor.
- **Município:** PIB, população, PIB por habitante, razão de riqueza, posição no ranking, composição por setor, índice de concentração (HHI), dependência da administração pública e série histórica, comparados com o estado e o país.
- **Ranking:** ordenação por PIB, PIB por habitante, dependência do setor público ou HHI, com curva de concentração e download em CSV.
- **Comparação:** lista de municípios guardada no estado de sessão enquanto a pessoa navega.
- **Notícias do IBGE:** nuvem de palavras, palavras mais frequentes e estatísticas das notícias oficiais extraídas com Beautiful Soup.
- **Seus dados:** upload de um CSV próprio (pelo código IBGE), que é juntado aos indicadores, cruzado em gráfico e pode ser baixado.

O painel usa `@st.cache_data` para ler os dados uma vez só e `st.session_state` para guardar a lista de comparação e os dados enviados pelo usuário.

## Público-alvo

Gestores públicos municipais e estaduais de cidades pequenas e médias, que normalmente não têm equipe de dados na prefeitura, além de vereadores e conselhos municipais. Como público secundário estão jornalistas de economia, pesquisadores de desenvolvimento regional e empresas avaliando expansão.

## ESG e ODS

Pilar Social, com apoio de Governança. Atende principalmente aos ODS 8 (trabalho decente e crescimento econômico) e 10 (redução das desigualdades), e de forma secundária ao ODS 11 (cidades e comunidades sustentáveis, meta 11.a).

## Fontes de dados

- **PIB dos Municípios**, IBGE, tabela 5938 do SIDRA, pela API aberta (PIB e valor adicionado por setor, 2010 a 2023).
- **População**, IBGE: Censo 2010 (tabela 202), Estimativas de População (tabela 6579) e Censo 2022 (tabela 4709).
- **Notícias da Agência de Notícias do IBGE** sobre cada divulgação do PIB dos Municípios, extraídas com Beautiful Soup.
- **CSV do usuário**, enviado pelo próprio painel.

Na divulgação de dezembro de 2025, o IBGE publicou 2022 e 2023 sem a abertura por setor. Por isso os indicadores de composição setorial vão até 2021. Os detalhes de cada fonte, dos tratamentos e da validação estão no [Data Summary Report](data_acquisition/data_summary_report.md). Escopo, objetivos e stakeholders estão no [Project Charter](business_understanding/project_charter.md).

## Organização do projeto (TDSP)

~~~
radar_economico_municipal/
├── README.md
├── requirements.txt
├── business_understanding/
│   └── project_charter.md
├── data/                          conteúdo extraído da web
│   ├── html_ibge/                 páginas das notícias salvas pelo navegador
│   ├── noticias_ibge.csv
│   └── noticias_ibge.txt
├── data_acquisition/
│   ├── raw_data/                  bases do IBGE como vieram da API
│   ├── cleaned_data/              base tratada com os indicadores
│   ├── espiar_*.py                consultas aos metadados antes da coleta
│   ├── coleta_sidra.py            coleta do PIB dos Municípios
│   ├── coleta_populacao.py        coleta da população
│   ├── raspa_noticias.py          extração das notícias com Beautiful Soup
│   └── data_summary_report.md
├── modeling/
│   ├── calcula_indicadores.py     cálculo e validação dos sete indicadores
│   └── confere_menores.py
└── deployment/
    └── app.py                     painel em Streamlit
~~~

## Como rodar

Criar e ativar o ambiente virtual e instalar as dependências:

~~~
pip install -r requirements.txt
~~~

Para só abrir o painel, a partir da pasta raiz do projeto:

~~~
streamlit run deployment\app.py
~~~

Para reconstruir a base do zero, rodar nesta ordem, sempre da pasta raiz:

~~~
py data_acquisition\coleta_sidra.py
py data_acquisition\coleta_populacao.py
py data_acquisition\raspa_noticias.py
py modeling\calcula_indicadores.py
~~~

## Autor

Ruan Luiz Fernandes da Silva Lima — Ciência de Dados, Projeto de Bloco: Inteligência Artificial Aplicada.

Este trabalho foi realizado com o auxílio da ferramenta de inteligência artificial generativa Claude Opus 5, da Anthropic.
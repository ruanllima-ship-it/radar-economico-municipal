# Project Charter — Radar Econômico Municipal

Projeto de Bloco: Inteligência Artificial Aplicada — Ciência de Dados
Aluno: Ruan Luiz Fernandes da Silva Lima
Versão: TP2 (evolução do rascunho entregue no TP1)
Repositório: https://github.com/ruanllima-ship-it/radar-economico-municipal

## 1. Contexto e problema de negócio

A economia brasileira é muito concentrada no território. Poucas cidades produzem a maior parte da riqueza do país, enquanto milhares de municípios pequenos só têm atividade econômica relevante porque recebem repasse público. O IBGE mede essa concentração todos os anos: as 27 capitais responderam por 28,3% do PIB nacional em 2023, contra 27,5% em 2022 e 36,1% em 2002. O país vinha desconcentrando aos poucos, e esse movimento travou e voltou a se inverter em 2023.

O problema é de acesso. A informação é pública e oficial, mas fica em tabelas com dezenas de milhares de linhas, valores em milhares de reais e nomes de variável técnicos. Um prefeito de cidade pequena, um vereador ou um jornalista local que queira saber se o seu município é dependente, de qual setor ele vive e como ele se compara com os vizinhos teria que baixar os arquivos, limpar e calcular tudo na mão. Na prática ninguém faz isso, e a discussão sobre desenvolvimento regional acontece sem base numérica.

## 2. Objetivos

O objetivo geral é transformar a base bruta do PIB dos Municípios em um painel interativo onde qualquer pessoa escolhe o município e recebe os indicadores já calculados e comparados com a média do estado e do país.

Os objetivos específicos são: automatizar a coleta dos dados do IBGE por script, sem download manual das bases numéricas; calcular sete indicadores de concentração, riqueza e composição setorial para os 5.570 municípios; oferecer filtros de ano, estado e município com resposta rápida; contextualizar os números com o que o próprio IBGE publicou sobre cada divulgação; e permitir que o usuário junte os seus próprios dados aos do painel e baixe os resultados.

## 3. Metas e situação ao final do TP2

A meta de cobertura era ter os 5.570 municípios com pelo menos 10 anos de série a partir de 2010. Ela foi atingida: a base tratada tem 5.570 municípios e 14 anos (2010 a 2023), num total de 77.980 linhas.

A meta de confiabilidade era reconstruir a base do zero por script e terminar com menos de 1% de células nulas. Também foi atingida: as bases numéricas são coletadas pela API do IBGE com os scripts da pasta data_acquisition, e sobraram 15 valores de PIB e 10 de população vazios, cerca de 0,03% das linhas. Todos os vazios têm explicação documentada no Data Summary Report.

A meta de usabilidade era ter no mínimo três filtros funcionando e resposta abaixo de três segundos. O painel tem os filtros de ano, estado e município, além de filtros internos por aba. A primeira carga leva de 2 a 4 segundos e, a partir do segundo clique, os dados vêm do cache em cerca de 0,02 segundo.

Foi acrescentada no TP2 uma meta de validação: os indicadores calculados precisam bater com os números oficiais divulgados pelo IBGE. Ela foi cumprida para a participação das capitais em 2022 e 2023, a participação dos 10 maiores municípios, o PIB per capita do Brasil e os casos de Saquarema e Brasília, com diferenças apenas de arredondamento.

## 4. Indicadores entregues pela aplicação

São sete indicadores, todos obtidos por soma e divisão a partir das bases do IBGE: a participação de cada município no PIB nacional; o PIB per capita, calculado como PIB dividido pela população; a razão de riqueza, que divide o PIB per capita do município pelo do Brasil (acima de 1 indica município mais rico que a média); a curva de concentração, que ordena os municípios do maior para o menor PIB e mostra quantos deles somam metade da economia; o índice de diversificação econômica (HHI), soma dos quadrados da participação dos quatro setores no valor adicionado; o grau de dependência da administração pública, participação desse setor no valor adicionado; e o perfil econômico, dado pelo setor com maior valor adicionado.

## 5. Escopo

Estão dentro do escopo a coleta das bases do IBGE por API, a raspagem das notícias oficiais da Agência de Notícias do IBGE com Beautiful Soup, o tratamento e a validação dos dados, o cálculo dos sete indicadores, o painel em Streamlit com filtros, gráficos, ranking, comparação entre municípios, nuvem de palavras, upload e download de arquivos CSV, e a documentação do projeto.

Ficam fora do escopo qualquer modelo preditivo ou projeção de PIB futuro, dados de outros países, análise abaixo do nível de município (bairros ou setores censitários) e a correção dos números do IBGE. Quando um número oficial parece inconsistente, o projeto registra a divergência e mantém o dado da fonte.

## 6. Stakeholders

| Grupo | Quem | Papel e interesse |
|---|---|---|
| Usuário principal | Gestores públicos municipais e estaduais de cidades pequenas e médias | Entender a base econômica do território antes de desenhar políticas; normalmente não têm equipe de dados na prefeitura |
| Usuários | Vereadores e conselhos municipais | Embasar a discussão do orçamento com número oficial |
| Usuários secundários | Jornalistas de economia e imprensa regional | Produzir pauta local sem tratar planilha |
| Usuários secundários | Pesquisadores e estudantes de desenvolvimento regional | Ganhar tempo pulando a etapa de coleta e limpeza |
| Usuários secundários | Empresas avaliando expansão | Conhecer o perfil produtivo de uma região |
| Fornecedor de dados | IBGE | Não participa do projeto, mas define a disponibilidade, o formato e as limitações das bases |
| Avaliador | Professor da disciplina | Define os requisitos de cada entrega e avalia o resultado |
| Executor | Aluno responsável | Acumula todos os papéis do TDSP: gestão, engenharia de dados, análise e desenvolvimento |

A interface foi desenhada pensando no gestor municipal, o perfil menos técnico, por isso os textos do painel explicam cada número em linguagem simples.

## 7. Enquadramento ESG e ODS

O projeto se posiciona no pilar Social do ESG, por tratar da desigualdade de renda entre regiões, com apoio da Governança, porque dá transparência sobre como a economia de cada município é composta e quanto ela depende do setor público.

Atende principalmente ao ODS 8 (Trabalho decente e crescimento econômico), que pede crescimento sustentado com diversificação econômica, exatamente o que o índice HHI e o perfil econômico medem, e ao ODS 10 (Redução das desigualdades), meta 10.1, porque acompanhar a distância entre o PIB per capita dos municípios ricos e pobres ao longo da série é uma leitura direta desse objetivo. De forma secundária, atende ao ODS 11 (Cidades e comunidades sustentáveis), meta 11.a, sobre planejamento regional e relação econômica entre áreas urbanas e rurais.

## 8. Premissas e restrições

O projeto parte da premissa de que as bases do IBGE continuam públicas e gratuitas, que a API do SIDRA segue disponível e que o volume de dados cabe em arquivos CSV locais, sem necessidade de banco de dados.

A principal restrição vem da fonte: na divulgação de dezembro de 2025, o IBGE publicou 2022 e 2023 sem a abertura do valor adicionado por setor, que só volta após a nova série do Sistema de Contas Nacionais, prevista para 2027. Por isso os indicadores de composição setorial (HHI, dependência e perfil) vão até 2021, e o painel avisa o usuário quando ele escolhe um ano posterior. Os valores são correntes, sem deflacionamento, e o painel também avisa isso nos gráficos de série histórica.

## 9. Riscos e mitigações

| Risco | O que aconteceu | Mitigação adotada |
|---|---|---|
| Ausência de abertura setorial em 2022 e 2023 | Confirmado no dado real: todas as variáveis de setor vêm vazias nesses anos | Indicadores setoriais limitados a 2010–2021 e aviso no painel |
| PIB per capita distorcido em municípios com petróleo, mineração ou refinaria | Confirmado: Saquarema tem PIB per capita 13,4 vezes a média do Brasil | Aviso automático no painel quando a razão de riqueza passa de 3 |
| Indisponibilidade ou lentidão da API | Não ocorreu, mas a coleta completa faz 74 pedidos | Coleta ano a ano, com até 3 tentativas por pedido, e base bruta salva em disco |
| Bloqueio de acesso automatizado a sites | Ocorreu: os sites do IBGE respondem 403 (proteção Cloudflare) para scripts | As páginas de notícias foram salvas pelo navegador e processadas com Beautiful Soup, sem tentar burlar a proteção |
| Mudança de código ou criação de município na série | Ocorreu: 5 municípios criados em 2013 e 1 município novo só nas estimativas de população | Uso do código IBGE de 7 dígitos como chave em todas as junções |
| Comparar anos com valor corrente | Permanece | Aviso nos gráficos; deflacionamento pelo IPCA previsto para a próxima etapa |

## 10. Arquitetura da solução

A solução segue o fluxo coleta, tratamento, cálculo e apresentação. Scripts em Python consultam a API do SIDRA e salvam a base bruta em data_acquisition/raw_data. Um script de raspagem com Beautiful Soup extrai as notícias do IBGE e salva em data/. O script modeling/calcula_indicadores.py junta PIB e população, calcula os indicadores, confere contra os números oficiais e salva a base tratada em data_acquisition/cleaned_data. O painel em deployment/app.py lê apenas os arquivos tratados, usa cache para não reler os dados a cada clique e estado de sessão para guardar a lista de comparação e os dados enviados pelo usuário.

## 11. Organização e cronograma

O projeto segue o CRISP-DM como raciocínio analítico e o TDSP como estrutura de pastas e artefatos.

O TP1 cobriu o entendimento do negócio: problema, metas, indicadores, ODS, público-alvo, estrutura de pastas e um app demonstrativo. O TP2 cobriu o controle de versão com Git e GitHub, a coleta completa das bases do IBGE, a raspagem das notícias, o cálculo e a validação dos indicadores, o painel interativo com cache, estado de sessão, upload e download, e esta documentação. As próximas etapas previstas são o deflacionamento pelo IPCA, o mapa dos municípios com as malhas territoriais do IBGE, o diagnóstico em texto gerado sob demanda, a publicação do painel na internet e a fase de aceitação com usuários.
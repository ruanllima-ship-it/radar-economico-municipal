# Project Charter — Radar Econômico Municipal

Projeto de Bloco: Inteligência Artificial Aplicada — Ciência de Dados
Aluno: Ruan Luiz Fernandes da Silva Lima
Versão: TP3 (revisão da versão entregue no TP2)
Repositório: https://github.com/ruanllima-ship-it/radar-economico-municipal

## 1. Contexto e problema de negócio

A economia brasileira é muito concentrada no território. Poucas cidades produzem a maior parte da riqueza do país, enquanto milhares de municípios pequenos só têm atividade econômica relevante porque recebem repasse público. O IBGE mede essa concentração todos os anos: as 27 capitais responderam por 28,3% do PIB nacional em 2023, contra 27,5% em 2022 e 36,1% em 2002. O país vinha desconcentrando aos poucos, e esse movimento travou e voltou a se inverter em 2023.

O problema é de acesso. A informação é pública e oficial, mas fica em tabelas com dezenas de milhares de linhas, valores em milhares de reais e nomes de variável técnicos. Um prefeito de cidade pequena, um vereador ou um jornalista local que queira saber se o seu município é dependente, de qual setor ele vive e como ele se compara com os vizinhos teria que baixar os arquivos, limpar e calcular tudo na mão. Na prática ninguém faz isso, e a discussão sobre desenvolvimento regional acontece sem base numérica.

## 2. Reavaliação do problema no TP3

O TP3 trouxe duas ferramentas novas, Selenium e FastAPI, e cada uma mudou a leitura de uma parte do problema.

O Selenium resolveu uma limitação que tinha sido registrada como ressalva no TP2. Os sites do IBGE respondem com erro 403 a pedidos feitos por script e montam parte do conteúdo por JavaScript, o que obrigou, no TP2, a salvar as páginas de notícia manualmente pelo navegador. Com o Selenium, que controla um navegador de verdade, a coleta passou a ser inteiramente automática e a cobertura subiu de 10 para 15 matérias, agora começando em 2015. Isso reforça a meta de confiabilidade: toda a base do projeto, numérica e textual, pode ser reconstruída do zero sem download manual.

O FastAPI ampliou o entendimento de quem é o usuário do projeto. Até o TP2 o painel era a única porta de saída dos dados, e quem não abrisse o painel não tinha acesso a nada. Com a API, os indicadores calculados passam a ser consumíveis por outros programas. Isso acrescenta um público que não estava previsto no TP1: o desenvolvedor ou o analista de uma prefeitura, de um jornal ou de uma universidade que queira usar os números dentro do próprio sistema. O problema de negócio continua o mesmo, mas a solução deixou de ser só uma tela e passou a ser também uma fonte de dados.

## 3. Objetivos

O objetivo geral é transformar a base bruta do PIB dos Municípios em indicadores prontos, acessíveis tanto por um painel interativo quanto por uma API.

Os objetivos específicos são: automatizar por completo a coleta dos dados, numéricos e textuais, sem nenhuma etapa manual; calcular sete indicadores de concentração, riqueza e composição setorial para os 5.570 municípios; oferecer uma interface com múltiplas páginas e filtros, pensada para quem não é técnico; disponibilizar os mesmos indicadores por uma API documentada; contextualizar os números com o que o próprio IBGE publicou sobre cada divulgação; e permitir que o usuário junte os seus próprios dados aos do painel.

## 4. Metas e situação ao final do TP3

A meta de cobertura era ter os 5.570 municípios com pelo menos 10 anos de série a partir de 2010. Foi atingida no TP2 e mantida: a base tratada tem 5.570 municípios e 14 anos, de 2010 a 2023, num total de 77.980 linhas.

A meta de confiabilidade era reconstruir a base do zero por script, com menos de 1% de células nulas. Também foi atingida, e no TP3 ela ficou mais forte: a última etapa manual que restava, o salvamento das páginas de notícia, foi eliminada com o Selenium. Sobraram 15 valores de PIB e 10 de população vazios, cerca de 0,03% das linhas, todos com explicação documentada.

A meta de usabilidade era ter no mínimo três filtros e resposta abaixo de três segundos. Mantida e ampliada: os filtros de ano, estado e município agora valem para todas as páginas do aplicativo, e a primeira carga leva de 2 a 4 segundos, caindo para cerca de 0,02 segundo a partir do segundo clique por causa do cache.

A meta de validação, acrescentada no TP2, exigia que os indicadores batessem com os números oficiais do IBGE. Continua cumprida, com diferenças apenas de arredondamento.

Foi acrescentada no TP3 uma meta de interoperabilidade: os indicadores precisam estar disponíveis para consumo por outros programas, com documentação. Cumprida com a API em FastAPI, que tem seis rotas e documentação interativa gerada automaticamente.

## 5. Indicadores entregues pela aplicação

São sete indicadores, todos obtidos por soma e divisão a partir das bases do IBGE: a participação de cada município no PIB nacional; o PIB per capita, calculado como PIB dividido pela população; a razão de riqueza, que divide o PIB per capita do município pelo do Brasil (acima de 1 indica município mais rico que a média); a curva de concentração, que ordena os municípios do maior para o menor PIB e mostra quantos deles somam metade da economia; o índice de diversificação econômica (HHI), soma dos quadrados da participação dos quatro setores no valor adicionado; o grau de dependência da administração pública, participação desse setor no valor adicionado; e o perfil econômico, dado pelo setor com maior valor adicionado.

## 6. Escopo

Estão dentro do escopo a coleta das bases do IBGE por API, a coleta automatizada das notícias oficiais com Selenium e Beautiful Soup, o tratamento e a validação dos dados, o cálculo dos sete indicadores, o painel em Streamlit com múltiplas páginas, filtros, gráficos, ranking, comparação, nuvem de palavras, upload e download de CSV, a API em FastAPI com rotas de consulta e de envio, e a documentação do projeto.

Ficam fora do escopo qualquer modelo preditivo ou projeção de PIB futuro, dados de outros países, análise abaixo do nível de município e a correção dos números do IBGE. Quando um número oficial parece inconsistente, o projeto registra a divergência e mantém o dado da fonte. A publicação da aplicação e da API em servidor na internet também fica fora do escopo desta etapa: ambas rodam localmente, com a preparação de deploy já feita pelo requirements.txt e pelo repositório versionado.

## 7. Stakeholders

| Grupo | Quem | Papel e interesse |
|---|---|---|
| Usuário principal | Gestores públicos municipais e estaduais de cidades pequenas e médias | Entender a base econômica do território antes de desenhar políticas; normalmente não têm equipe de dados na prefeitura |
| Usuários | Vereadores e conselhos municipais | Embasar a discussão do orçamento com número oficial |
| Usuários secundários | Jornalistas de economia e imprensa regional | Produzir pauta local sem tratar planilha |
| Usuários secundários | Pesquisadores e estudantes de desenvolvimento regional | Ganhar tempo pulando a etapa de coleta e limpeza |
| Usuários secundários | Empresas avaliando expansão | Conhecer o perfil produtivo de uma região |
| Novo no TP3 | Desenvolvedores e analistas de sistemas de terceiros | Consumir os indicadores pela API para usar dentro de outro sistema, sem passar pela interface |
| Fornecedor de dados | IBGE | Não participa do projeto, mas define a disponibilidade, o formato e as limitações das bases |
| Avaliador | Professor da disciplina | Define os requisitos de cada entrega e avalia o resultado |
| Executor | Aluno responsável | Acumula todos os papéis do TDSP: gestão, engenharia de dados, análise e desenvolvimento |

A interface foi desenhada pensando no gestor municipal, o perfil menos técnico, por isso os textos do painel explicam cada número em linguagem simples. A API, por outro lado, foi desenhada para o público técnico, com nomes de campo diretos e documentação automática.

## 8. Enquadramento ESG e ODS

O projeto se posiciona no pilar Social do ESG, por tratar da desigualdade de renda entre regiões, com apoio da Governança, porque dá transparência sobre como a economia de cada município é composta e quanto ela depende do setor público. A API reforça o lado de Governança, já que torna os indicadores auditáveis e reutilizáveis por terceiros.

Atende principalmente ao ODS 8 (Trabalho decente e crescimento econômico), que pede crescimento sustentado com diversificação econômica, exatamente o que o índice HHI e o perfil econômico medem, e ao ODS 10 (Redução das desigualdades), meta 10.1, porque acompanhar a distância entre o PIB per capita dos municípios ricos e pobres ao longo da série é uma leitura direta desse objetivo. De forma secundária, atende ao ODS 11 (Cidades e comunidades sustentáveis), meta 11.a, sobre planejamento regional.

## 9. Premissas e restrições

O projeto parte da premissa de que as bases do IBGE continuam públicas e gratuitas, que a API do SIDRA segue disponível e que o volume de dados cabe em arquivos CSV locais, sem necessidade de banco de dados.

A principal restrição vem da fonte: na divulgação de dezembro de 2025, o IBGE publicou 2022 e 2023 sem a abertura do valor adicionado por setor, que só volta após a nova série do Sistema de Contas Nacionais, prevista para 2027. Por isso os indicadores de composição setorial vão até 2021, e o painel e a API avisam quando o ano escolhido é posterior. Os valores são correntes, sem deflacionamento, e o painel avisa isso nos gráficos de série histórica.

Uma restrição nova no TP3: a coleta das notícias com Selenium depende do navegador Chrome instalado na máquina e de conexão com a internet, e leva cerca de dois minutos, enquanto a leitura dos arquivos já salvos é instantânea. Por isso a coleta continua sendo um passo separado, executado sob demanda, e nunca dentro da aplicação.

## 10. Riscos e mitigações

| Risco | O que aconteceu | Mitigação adotada |
|---|---|---|
| Ausência de abertura setorial em 2022 e 2023 | Confirmado no dado real | Indicadores setoriais limitados a 2010–2021, com aviso no painel e na API |
| PIB per capita distorcido em municípios com petróleo ou mineração | Confirmado: Saquarema tem PIB per capita 13,4 vezes a média do Brasil | Aviso automático no painel quando a razão de riqueza passa de 3 |
| Bloqueio de acesso automatizado aos sites do IBGE | Ocorreu no TP2 (erro 403) e foi resolvido no TP3 | Coleta passou a usar Selenium, que executa o JavaScript do site em um navegador real, sem burlar a proteção |
| Mudança na estrutura das páginas do IBGE | Não ocorreu, mas é provável com o tempo | A extração usa etiquetas meta padronizadas (og:title, article:published_time) e classes estáveis da listagem; o script avisa quando não encontra o conteúdo esperado |
| API e painel precisarem rodar ao mesmo tempo | Ocorre por desenho | A página de consulta detecta se a API está no ar e orienta o usuário, em vez de quebrar |
| Mudança de código ou criação de município na série | Ocorreu: 5 municípios criados em 2013 | Uso do código IBGE de 7 dígitos como chave em todas as junções |
| Comparar anos com valor corrente | Permanece | Aviso nos gráficos; deflacionamento pelo IPCA previsto para a próxima etapa |

## 11. Arquitetura da solução

A solução tem quatro camadas. A **coleta** reúne os scripts que buscam os dados na origem: a API do SIDRA para PIB e população, e o Selenium com Beautiful Soup para as notícias. A **modelagem** junta PIB e população, calcula os sete indicadores, confere contra os números oficiais e salva a base tratada. A **entrega** tem duas saídas que leem a mesma base tratada: o painel em Streamlit, com sete páginas e menu de navegação, e a API em FastAPI, com seis rotas. A **integração** fecha o ciclo: a página "Consulta pela API" do painel não lê os arquivos, e sim chama a própria API do projeto, demonstrando o caminho completo que um sistema externo percorreria.

## 12. Organização e cronograma

O projeto segue o CRISP-DM como raciocínio analítico e o TDSP como estrutura de pastas e artefatos.

O TP1 cobriu o entendimento do negócio. O TP2 cobriu o controle de versão, a coleta completa das bases, a raspagem das notícias, o cálculo e a validação dos indicadores, o painel interativo e a documentação. O TP3 cobriu a automação da coleta com Selenium, a construção da API em FastAPI, a reorganização do painel em múltiplas páginas, a integração do painel com a API e a revisão desta documentação. O TP4 vai introduzir recursos de IA via LLM, conforme o planejamento descrito em business_understanding/planejamento_llm.md.
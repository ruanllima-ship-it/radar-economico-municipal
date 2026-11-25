# Project Charter — Radar Econômico Municipal

Projeto de Bloco: Inteligência Artificial Aplicada — Ciência de Dados
Aluno: Ruan Luiz Fernandes da Silva Lima
Versão: TP5 (revisão das versões entregues no TP2, TP3 e TP4)
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


---

# Atualização para o TP4 e o TP5

Versão: TP5 (revisão das versões entregues no TP2, TP3 e TP4)

As seções de 1 a 12 acima descrevem o projeto como ele estava ao final do TP3.
Esta parte registra o que mudou com a entrada da inteligência artificial
generativa, no TP4, e do agente de diagnóstico, no TP5.

## 13. Reavaliação do problema de negócio

O problema continua o mesmo desde o TP1: a informação sobre a economia dos
municípios é pública, mas inacessível para quem precisaria dela. O que mudou foi
o entendimento de **onde** a inacessibilidade mora.

Até o TP3, a resposta era "os dados estão em tabelas difíceis", e a solução foi
calcular indicadores e mostrá-los em gráficos. Os TPs 4 e 5 mostraram que isso
resolve metade do problema. Um prefeito de cidade pequena, olhando a página do
município, vê que a dependência da administração pública é de 83,5% e que o HHI
é alto — e continua sem saber **o que fazer com isso**. O número está na tela,
mas a leitura do número continua exigindo alguém que saiba lê-lo.

É essa segunda metade que a IA generativa resolve neste projeto. Ela não produz
dado novo e não calcula nada: ela traduz para português o que a análise já
concluiu.

## 14. O que foi construído no TP4 e no TP5

| Etapa | Funcionalidade | Modelo | Entrada |
|---|---|---|---|
| TP4 | Resumo automático de texto | `recogna-nlp/ptt5-base-summ` (222,9 milhões de parâmetros) | as 15 matérias do IBGE coletadas por Selenium (19.996 palavras) |
| TP5 | Agente de diagnóstico municipal | `Qwen/Qwen2.5-1.5B-Instruct` (1,54 bilhão de parâmetros) | a base tratada de 77.980 linhas, pela análise do `agente.py` |

Os dois modelos rodam **localmente**, baixados da HuggingFace, sem chave de API
e sem enviar nenhum dado para fora da máquina. Essa decisão foi tomada no TP5,
depois de considerar uma API online: com chave, o professor não conseguiria
executar o projeto, a chave não poderia ficar num repositório público, e o
projeto deixaria de ser reprodutível. O risco de exposição de chave já estava
registrado em `business_understanding/planejamento_llm.md` desde o TP3.

## 15. Como dados, IA e engenharia de prompt se encaixam no problema

As três coisas resolvem partes diferentes do mesmo problema, e a ordem importa.

**Os dados** — coletados por API do SIDRA e por raspagem com Selenium — dão a
base factual. Sem eles não há o que dizer. São 77.980 linhas de indicadores
calculados e 19.996 palavras de texto oficial do IBGE, tudo reconstruível do
zero por script.

**A análise em Python** — `deployment/agente.py` — transforma dado em conclusão.
Ela classifica o município por percentil contra a distribuição nacional **do
ano**, calculada na hora, e aplica regras de decisão que produzem três listas:
achados (fatos), alertas (riscos) e o que acompanhar. Esta camada não usa IA, e
é ela que carrega todo o juízo técnico do projeto.

**O modelo de linguagem** entra por último e com a menor responsabilidade
possível: transformar a análise pronta em três parágrafos que um vereador leia
sem intérprete. Ele tem ordem expressa de não calcular e não concluir nada.

**A engenharia de prompt** é o que torna essa divisão confiável na prática. As
oito versões documentadas em `modeling/engenharia_de_prompt.md` mostram que a
divisão sozinha não basta: mesmo proibido de analisar, o modelo tentava deduzir,
inventava pontos positivos e invertia comparações. Cada versão do prompt corrige
um desses desvios, e duas delas foram corrigidas **fora do prompt** — uma no
código de limpeza e outra na própria frase que a análise escreve.

O alinhamento com o problema de negócio é direto: o usuário-alvo é quem **não
tem equipe de dados**. Para ele, um parágrafo em português vale mais que um
gráfico, desde que o parágrafo seja verdadeiro. Todo o esforço de engenharia
deste TP é para garantir essa segunda parte.

## 16. A transparência como requisito de projeto

Entregar texto gerado por máquina a um gestor público cria uma obrigação: ele
precisa poder conferir. O projeto trata isso como requisito, não como aviso
legal.

1. **A análise aparece antes da IA.** A página mostra os números, as faixas, os
   gráficos e as três listas assim que abre, sem carregar modelo nenhum. O botão
   da IA fica abaixo de tudo isso.
2. **A rota `GET /analise/{codigo}` existe separada.** Quem quiser só os
   insights não precisa do modelo nem espera por ele.
3. **O prompt enviado é devolvido junto com o texto.** O campo `prompt_enviado`
   da API e o expander "Ver o prompt exato que foi enviado ao modelo" mostram o
   texto integral. Qualquer número do diagnóstico que não esteja ali foi
   inventado pelo modelo, e isso é verificável por qualquer pessoa.
4. **O painel avisa que o texto é escrito por máquina**, em destaque, acima do
   botão.

## 17. Enquadramento ESG e ODS (revisado no TP5)

O enquadramento da seção 8 continua válido e ganha uma camada com o agente.

### Pilar Social

O projeto mede e expõe a desigualdade econômica entre territórios. O indicador
central é a razão de riqueza, que divide o PIB por habitante do município pelo
do Brasil. Uiramutã (RR) tem 0,31; Paulínia (SP) tem 10,83. São **35 vezes de
distância** entre dois municípios do mesmo país, e o painel mostra isso em um
gráfico que qualquer pessoa entende.

O agente acrescenta a leitura dessa desigualdade em linguagem comum. Um
município com 83,5% da economia na administração pública não é apenas pobre: ele
é **frágil**, porque qualquer mudança no repasse federal muda a vida de todo
mundo ali. Essa é uma conclusão social, e agora ela sai escrita.

### Pilar Governança

Três decisões do projeto são de governança:

- **Reprodutibilidade.** Toda a base é reconstruível do zero por script, sem
  passo manual, e o `modeling/verifica_tp5.py` confere o estado do projeto em 38
  testes automáticos.
- **Auditabilidade do texto gerado.** O prompt vai junto com a resposta.
- **Dado local.** Nenhuma informação sai da máquina de quem roda o projeto.

### ODS atendidos

**ODS 8 — Trabalho decente e crescimento econômico.** A meta 8.2 pede
diversificação econômica. O índice HHI e o perfil econômico medem exatamente
isso, e o agente transforma a medição em alerta quando a concentração é alta —
com a ressalva, construída no TP5, de que concentração em serviços não é o mesmo
risco que concentração numa única indústria.

**ODS 10 — Redução das desigualdades.** A meta 10.1 trata do crescimento da
renda dos 40% mais pobres acima da média nacional. A razão de riqueza ao longo
de 14 anos é uma leitura territorial direta dessa meta: o painel mostra se o
município está se aproximando ou se afastando da média do país. Uiramutã saiu de
0,32 em 2010 para 0,34 em 2023 — praticamente parado. Sorriso (MT) saiu de 1,35
para 2,31. A desigualdade entre municípios não está se fechando sozinha.

**ODS 11 — Cidades e comunidades sustentáveis.** A meta 11.a trata do
planejamento regional integrado. A API existe para isso: os indicadores podem
ser consumidos por sistemas de prefeituras, consórcios e universidades sem
passar pela interface.

**ODS 16 — Paz, justiça e instituições eficazes.** A meta 16.6 pede instituições
transparentes. Dar a um vereador a base econômica do próprio município em
linguagem acessível, com a fonte e o prompt à vista, é contribuição direta a
essa meta.

### O que o projeto **não** faz

Honestidade sobre o alcance faz parte do enquadramento ESG. O projeto não mede
emprego, renda domiciliar, informalidade, pobreza nem impacto ambiental. Ele
mede concentração econômica a partir do PIB, e PIB alto não significa população
rica — Saquarema (RJ) tem PIB por habitante 13,4 vezes a média nacional por
causa do petróleo, sem que essa riqueza fique com os moradores. O painel avisa
isso quando a razão de riqueza passa de 3. Nenhuma conclusão sobre bem-estar
pode ser tirada só destes indicadores.

## 18. Metas acrescentadas no TP4 e no TP5

| Meta | Situação |
|---|---|
| Executar IA generativa localmente, sem chave e sem enviar dado para fora | Cumprida: dois modelos locais |
| O modelo nunca produzir número que não esteja na análise | Cumprida e verificável pelo `prompt_enviado` |
| A análise funcionar sem o modelo | Cumprida: `GET /analise` responde na hora |
| A aplicação subir mesmo sem o PyTorch instalado | Cumprida: imports dentro da função, rota responde 503 |
| Documentar a evolução do prompt com defeito e correção | Cumprida: 8 versões em `modeling/engenharia_de_prompt.md` |
| Testar o agente em perfis econômicos opostos | Cumprida: 4 municípios, de 0,31× a 10,83× a riqueza nacional |

## 19. Riscos acrescentados no TP4 e no TP5

| Risco | O que aconteceu | Mitigação adotada |
|---|---|---|
| Modelo inventar número | Ocorreu na versão 1 do prompt | Análise feita em Python; prompt proíbe calcular; `prompt_enviado` permite conferência |
| Modelo inverter uma conclusão | Ocorreu nas versões 6 e 8 | Direção da comparação escrita por extenso no `agente.py`; proibição no fim do pedido |
| Modelo escrever em outro idioma | Ocorreu: ideograma chinês no teste de Sorriso | Filtro no código, além da regra no prompt |
| Falta de memória para o modelo | Ocorreu: 0,7 GB livres derrubaram a velocidade para 2,2 pedaços/s | `bfloat16`; carga preguiçosa; rota `POST /modelo_diagnostico/descarregar` |
| Dois pedidos simultâneos ao modelo | Previsto | Duas travas: uma de carga e uma de uso, com resposta HTTP 429 |
| Texto gerado ser tomado como verdade oficial | Risco permanente | Aviso em destaque no painel; análise visível antes da IA; prompt à vista |

## 20. Arquitetura ao final do TP5

Cinco camadas:

1. **Coleta** — API do SIDRA (PIB e população) e Selenium com Beautiful Soup
   (notícias do IBGE).
2. **Modelagem** — junção, cálculo dos sete indicadores e validação contra os
   números oficiais.
3. **Análise** — `deployment/agente.py`, sem IA: percentis calculados na hora e
   regras de decisão que produzem achados, alertas e o que acompanhar.
4. **Geração de texto** — `deployment/modelo_llm.py` (resumo, TP4) e
   `deployment/diagnostico_llm.py` (diagnóstico, TP5), ambos locais e de carga
   preguiçosa.
5. **Entrega** — API em FastAPI com 12 rotas e 25 Response Models, e painel em
   Streamlit com 9 páginas. O painel consome a própria API nas páginas de IA.

## 21. Cronograma atualizado

O TP1 cobriu o entendimento do negócio. O TP2 cobriu versionamento, coleta,
cálculo, validação, painel e documentação. O TP3 cobriu a automação da coleta
com Selenium, a API em FastAPI e a integração painel–API. O TP4 introduziu o
primeiro modelo de linguagem local, com a funcionalidade de resumo de texto,
tratamento de erros em oito códigos HTTP e Response Models tipados. O TP5
construiu o agente de diagnóstico municipal: a análise por regras em Python, o
segundo modelo local para redação, quatro rotas novas na API, a página do painel
e as oito versões documentadas do prompt.
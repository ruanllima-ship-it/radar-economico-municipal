# Planejamento para o uso de IA generativa (LLM) — TP4

Projeto: Radar Econômico Municipal
Aluno: Ruan Luiz Fernandes da Silva Lima
Versão: TP3 (planejamento da etapa seguinte)

## 1. Por que um LLM faz sentido neste projeto

O painel entrega números corretos, validados contra o IBGE, mas entregar número não é a mesma coisa que entregar entendimento. O público principal do projeto é o gestor de uma cidade pequena, que muitas vezes não sabe ler um índice de concentração nem comparar a sua situação com a de outro município. Hoje o painel resolve isso com frases fixas, escritas por regra: se o HHI passa de um valor, mostra um texto; se a dependência da administração pública passa de outro, mostra outro texto. Funciona, mas é limitado, porque não combina os indicadores entre si nem leva em conta o histórico do município.

É exatamente nesse ponto que um LLM agrega. Ele lê os sete indicadores de um município, o histórico desde 2010 e o contexto das notícias oficiais, e escreve um diagnóstico em linguagem comum, ligando as informações. O dado continua vindo do IBGE; o LLM só traduz.

## 2. Os dados disponíveis para alimentar o LLM

O projeto chega ao TP4 com dois tipos de dado já coletados, tratados e validados.

O **dado numérico** está em data_acquisition/cleaned_data/indicadores_municipios.csv, com 77.980 linhas cobrindo 5.570 municípios de 2010 a 2023, e em resumo_brasil.csv, com o retrato nacional por ano. Cada município tem PIB, população, PIB per capita, razão de riqueza, posição no ranking, participação no PIB nacional, composição por setor, índice de concentração, dependência da administração pública e perfil econômico.

O **dado textual** está em data/noticias_ibge.csv, com 15 matérias oficiais da Agência de Notícias do IBGE, 19.996 palavras publicadas entre 2015 e 2025. Cada matéria tem título, data, resumo, link e texto completo.

Há ainda um terceiro tipo, eventual: o CSV que o próprio usuário sobe na página Seus dados, que pode trazer orçamento, emprego ou qualquer indicador local.

## 3. As quatro aplicações previstas

### 3.1 Geração de texto: diagnóstico do município

É a aplicação principal. Na página Município, um botão gera um diagnóstico em três ou quatro parágrafos sobre o município escolhido. O LLM recebe os indicadores daquele município, a média do estado e do Brasil, a posição no ranking e a série histórica, e escreve um texto que explica se o município é rico ou pobre em relação à média, de que setor ele vive, se essa dependência é um risco e o que mudou ao longo dos anos.

O ganho é direto para o público-alvo: substitui as frases fixas por uma leitura que combina os indicadores. Para controlar custo e tempo, o diagnóstico só é gerado quando o usuário clica, e o resultado fica guardado em cache por município e ano, como já é feito com a nuvem de palavras.

### 3.2 Resumo automático das notícias

As 15 matérias somam quase 20 mil palavras, e ninguém vai ler tudo. O LLM gera um resumo de cada matéria em três ou quatro linhas, e um resumo geral que mostra como o discurso do IBGE sobre concentração econômica mudou de 2015 para 2025. Isso aproveita o texto coletado com Selenium e Beautiful Soup, que hoje só alimenta a nuvem de palavras e as estatísticas.

### 3.3 Perguntas e respostas sobre os dados

Um campo de pergunta onde o usuário escreve em linguagem comum, como "quais municípios do Maranhão dependem mais da administração pública?" ou "o que o IBGE disse sobre o semiárido?". O sistema identifica se a pergunta é sobre número ou sobre texto, busca o trecho relevante na base ou nas notícias, e manda para o LLM junto com a pergunta, para que a resposta seja construída apenas sobre o material recuperado. Essa é a aplicação mais ambiciosa, e por isso fica como objetivo secundário.

### 3.4 Classificação de sentimento das notícias

Classificar cada matéria como otimista, neutra ou preocupada em relação à desconcentração econômica, e mostrar essa classificação ao longo do tempo. Essa é a aplicação com menor ganho real, porque notícias do IBGE são deliberadamente neutras e técnicas, e o resultado tenderia a ser "neutro" em quase tudo. Fica registrada como possibilidade, mas não é prioridade.

## 4. Prioridade e critério de escolha

A ordem de implementação prevista é: primeiro o diagnóstico do município, depois o resumo das notícias, depois perguntas e respostas, e a classificação de sentimento apenas se sobrar tempo. O critério é o ganho para o público-alvo: o diagnóstico resolve o problema central do projeto, que é traduzir número em entendimento para quem não é técnico.

## 5. O que já está pronto para receber o LLM

Algumas decisões tomadas no TP2 e no TP3 foram pensadas justamente para facilitar esta etapa.

A base tratada já está pronta e validada, então o LLM nunca vai precisar calcular nada: ele recebe números prontos e corretos, o que reduz muito o risco de resposta errada. O texto das notícias já está limpo, sem menu, aviso de site nem linha de autoria, e com a contagem de palavras por matéria, o que ajuda a dividir o conteúdo em pedaços do tamanho certo. A API em FastAPI já entrega qualquer recorte dos dados em JSON, formato que serve direto como contexto para um modelo, e uma rota nova de diagnóstico se encaixa na estrutura existente sem reescrever nada. O cache e o estado de sessão do Streamlit já estão implementados e funcionando, e vão ser reaproveitados para não repetir chamadas caras. O painel já está dividido em páginas, então uma página nova de diagnóstico entra no menu sem mexer nas outras.

## 6. Riscos previstos e como tratar

O risco mais sério é o modelo inventar número. A mitigação é nunca pedir que ele calcule ou lembre de qualquer valor: todos os números vão no texto enviado ao modelo, e a instrução vai exigir que ele use apenas esses valores e cite a fonte e o ano.

O segundo risco é o custo e o tempo de resposta, já que são 5.570 municípios e 14 anos. A mitigação é gerar só sob demanda, nunca em lote, e guardar em cache por município e ano.

O terceiro risco é a chave de acesso ao modelo vazar no repositório público. A mitigação é guardar a chave fora do código, em variável de ambiente ou no arquivo de segredos do Streamlit, com o caminho já incluído no .gitignore.

O quarto risco é o diagnóstico soar como conselho técnico definitivo sobre a economia de uma cidade. A mitigação é um aviso visível de que o texto é gerado automaticamente a partir dos dados do IBGE, serve como apoio à leitura e não substitui análise técnica.

---

## 7. O que foi efetivamente entregue no TP4, e o que mudou do plano

Esta seção foi escrita depois da implementação, para registrar a diferença entre o
que foi planejado aqui, no TP3, e o que foi entregue no TP4.

### A prioridade foi invertida, e por um motivo

O plano original, na seção 4, previa o diagnóstico do município como primeira
aplicação e o resumo das notícias como segunda. A ordem foi invertida: o resumo
automático foi implementado, e o diagnóstico ficou para a última etapa do projeto.

O motivo é uma restrição que só ficou clara quando o enunciado do TP4 foi divulgado:
o modelo precisa rodar **localmente**, baixado da HuggingFace. Isso muda tudo o que
estava suposto nesta seção, que foi escrita pensando em um modelo grande acessado por
uma API na nuvem.

Gerar um diagnóstico em três ou quatro parágrafos, combinando sete indicadores com
série histórica e comparação com o estado, é tarefa de modelo grande. O modelo que
cabe nesta máquina tem 223 milhões de parâmetros, e o experimento registrado em
`modeling/escolha_do_modelo.md` mostrou que ele inventa informação justamente quando
é forçado a escrever mais do que tem para dizer. Insistir no diagnóstico seria entregar
texto bonito e errado sobre a economia de municípios reais — exatamente o primeiro
risco listado na seção 6 deste documento.

O resumo, ao contrário, é a tarefa para a qual o modelo escolhido foi treinado, e
aproveita as 19.996 palavras coletadas com Selenium no TP3, que até então só
alimentavam a nuvem de palavras.

### O que foi entregue

A rota `POST /processar_texto` na API recebe um texto em português e devolve o resumo
gerado pelo modelo local, junto com o tipo de análise, o modelo usado, o dispositivo,
o tempo de geração e quanto do texto o modelo conseguiu ler. A rota `GET /modelo`
informa se o modelo já está carregado, sem carregá-lo.

No painel, a página **Resumo com IA** permite resumir qualquer uma das 15 matérias do
IBGE ou um texto colado pelo usuário, e mostra o resumo do modelo ao lado do resumo
publicado pelo próprio IBGE, para comparação direta.

### As mitigações de risco previstas na seção 6, uma a uma

O risco de **inventar número** foi tratado de duas formas. O modelo nunca calcula nada:
ele recebe um texto pronto e só resume. E a configuração de geração foi escolhida por
experimento, entre quatro alternativas, justamente pelo critério de não inventar
conteúdo — o registro está em `modeling/escolha_do_modelo.md`, seção 7.

O risco de **custo e tempo de resposta** foi tratado com carregamento preguiçoso: o
modelo só é carregado quando alguém pede um resumo, e o resumo só é gerado quando o
usuário clica no botão. Nunca em lote.

O risco de **vazamento de chave de API** deixou de existir. Como o modelo roda
localmente, não há chave, conta nem serviço externo. Depois do download inicial, o
projeto funciona sem internet.

O risco de o texto **soar como parecer técnico definitivo** foi tratado com um aviso
fixo e visível no alto da página, informando que os resumos são gerados por máquina e
que o texto original deve ser consultado antes de usar qualquer número. O link da
matéria original aparece ao lado de cada resumo.

### O que continua para a última etapa

As aplicações 3.1 (diagnóstico do município), 3.3 (perguntas e respostas) e 3.4
(classificação de sentimento) seguem previstas. A rota `/processar_texto` já nasceu
preparada para isso: ela recebe um campo `tipo_analise`, hoje com um único valor
aceito, e recusa os demais com HTTP 400. Acrescentar uma análise nova é acrescentar um
valor a essa lista, sem mudar o formato da resposta.
# Engenharia de Prompt — Agente de Diagnóstico Municipal

Projeto de Bloco: Inteligência Artificial Aplicada — Ciência de Dados
Aluno: Ruan Luiz Fernandes da Silva Lima
Versão: TP5
Repositório: https://github.com/ruanllima-ship-it/radar-economico-municipal

Este documento registra as oito versões do prompt do agente de diagnóstico, o
defeito que cada uma produziu e a correção que gerou a versão seguinte. O
prompt final está em `deployment/diagnostico_llm.py`.

## 1. O modelo escolhido e a configuração

| Item | Valor |
|---|---|
| Modelo | `Qwen/Qwen2.5-1.5B-Instruct` |
| Parâmetros | 1.543.714.304 |
| Origem | HuggingFace, baixado e executado localmente |
| Precisão | `torch.bfloat16` |
| Memória ocupada | cerca de 2,9 GB |
| Tempo de carga | cerca de 10 s (a partir do cache local) |
| Geração | `do_sample=False` (determinística) |
| Teto de geração | `max_new_tokens = 480` |

A escolha do `bfloat16` veio de um teste direto contra `float32`, registrado em
`modeling/testa_modelo_instruct.py`: as duas precisões deram exatamente a mesma
velocidade (6,3 pedaços por segundo) na máquina de desenvolvimento, e o
`bfloat16` usa metade da memória. Com `float32` sobravam 0,3 GB livres na
máquina, o que inviabilizava rodar o painel ao mesmo tempo.

O `do_sample=False` é uma decisão de projeto, não de desempenho: com ele, o
mesmo município no mesmo ano sempre produz o mesmo texto. Num trabalho sobre
dados econômicos, poder repetir o resultado vale mais do que variedade de
redação.

### Velocidade medida: dois números diferentes

| Condição | Velocidade | Tempo de um diagnóstico |
|---|---|---|
| Banco de testes isolado, máquina livre | 6,3 pedaços/s | cerca de 60 s |
| Uso real pelo painel (Chrome + Streamlit + API ligados) | 1,4 a 1,7 pedaços/s | 3,5 a 5 min |

A diferença é memória. A máquina tem 15,7 GB, e o modelo sozinho pede 2,9 GB.
Com o VS Code aberto (4,1 GB medidos) a geração fica quatro vezes mais lenta.
Os dois números ficam registrados porque medição controlada e uso real não são
a mesma coisa, e esconder o segundo seria desonesto.

## 2. A decisão que vem antes do prompt: divisão de trabalho

Nos primeiros testes o modelo recebia os números crus do município e a tarefa
de analisar. O resultado tinha erros graves de raciocínio, não de redação:

- comparou PIB total com PIB por habitante como se fossem a mesma grandeza;
- somou 6,1 + 1,6 = 7,7 por conta própria, desobedecendo a ordem de não calcular;
- disse que Uiramutã fica no **Rio Grande do Norte** (fica em Roraima);
- ignorou o dado mais forte do município (83,5% contra 26,8%).

A conclusão foi que o problema não era o prompt, era a tarefa. Um modelo de 1,5
bilhão de parâmetros não é confiável para analisar. A arquitetura foi então
dividida em dois arquivos:

| Arquivo | Papel | Usa LLM? |
|---|---|---|
| `deployment/agente.py` | **pensa** — lê os indicadores, classifica o município por percentil contra a distribuição nacional do ano, aplica regras de decisão e produz achados, alertas e o que acompanhar | não |
| `deployment/diagnostico_llm.py` | **escreve** — recebe a análise pronta e a transforma em três parágrafos de texto corrido | sim |

Essa separação é visível de fora do código: a API tem duas rotas, `GET /analise`
(instantânea, sem IA) e `POST /diagnostico` (a mesma análise mais o texto). E a
página do painel mostra a análise inteira antes de o botão da IA ser clicado.

Todo o ganho de confiabilidade das versões seguintes vem daqui. As oito versões
do prompt resolvem problemas de redação, não de análise.

## 3. As oito versões

### Versão 1 — números crus, sem regras

O prompt entregava os números do município e pedia um diagnóstico.

Seis defeitos: comparou grandezas diferentes; fez conta; escreveu título e
quatro parágrafos; o texto terminou no meio de uma palavra; errou o estado; e
ignorou o dado mais relevante.

### Versão 2 — regras explícitas e análise pronta

Entrou a divisão de trabalho e um conjunto de regras numeradas: use só os fatos
da mensagem, nunca calcule, sem título, três parágrafos, linguagem simples, sem
previsões.

Cinco dos seis defeitos sumiram. Sobraram o corte no meio da palavra e um
defeito novo: o texto escreveu **"No entanto, há também sinais positivos"** e
emendou só notícias ruins. Daí nasceu a regra 7, que proíbe anunciar avaliações
que não estejam nos fatos.

### Versão 3 — limite de palavras

Entrou um limite de 180 palavras para o texto não inchar.

O modelo obedeceu ao limite e **desobedeceu à contagem de parágrafos**: escreveu
um só. E inventou um número: leu o rótulo "entre as 10% mais concentradas" e
escreveu "sendo 10% superior à média nacional".

Correção: o limite de palavras saiu, e os percentis deixaram de ir como rótulo
curto. Passaram a ir como frase completa, dentro dos achados do `agente.py`:

> "Em 2021, este município estava entre os 10% mais dependentes da
> administração pública de todo o país."

### Versão 4 — percentis em frase completa

Voltaram os três parágrafos, sem número inventado, com o estado correto. Mas o
texto ainda terminava no meio de uma frase.

Aqui o defeito era **meu, no código**, e não do modelo. A função
`cortar_na_ultima_frase` devolvia o texto intacto quando o parágrafo não tinha
nenhum ponto final dentro dele — eu tinha testado o caso fácil e deixado o caso
difícil passar. A correção faz a função devolver vazio nesse caso, e o parágrafo
incompleto é descartado inteiro. Entregar dois parágrafos completos é melhor que
três com um pedaço solto.

### Versão 5 — regra de conectores e teto maior

Entrou a regra 9, sobre conectores de contraste, depois que o modelo abriu um
parágrafo com "No entanto" e emendou mais uma má notícia. O teto subiu de 320
para 480 pedaços e a regra 4 apertou de "2 a 4 frases" para "2 a 3".

A regra 9 funcionou: o texto passou a usar "Além disso". Mas o modelo entregou
**um parágrafo só**, parando por conta própria em 178 pedaços de 480.

### Versão 6 — a exigência de estrutura muda de lugar

A última linha que o modelo lia antes de escrever era "Comece pela primeira
frase, sem título" — uma instrução fraca ocupando a posição mais forte do
prompt. A exigência dos três parágrafos estava na regra 4, soterrada por mais
cinco regras.

A correção não mudou nenhuma regra. Mudou o **fim do pedido**:

> "Escreva agora os três parágrafos, um depois do outro, separados por uma
> linha em branco. Não junte tudo em um parágrafo só. Não escreva título."

Os três parágrafos voltaram. Mas, com três parágrafos para preencher, o modelo
escreveu que estar **entre os 10% mais dependentes da administração pública**
era "um ponto positivo" e "um fator importante para o desenvolvimento local".
Isso é pior do que errar um número: é inverter a conclusão.

### Versão 7 — a proibição desce para o mesmo lugar

A regra 7 já proibia isso desde a versão 2, e não bastou. A proibição passou
também para o fim do pedido, e **montada a partir dos dados do município**:

- município com alerta recebe a proibição de inventar ponto favorável;
- município sem alerta recebe a proibição de inventar risco.

O "ponto positivo" sumiu. Sobraram deslizes de redação: anunciou "dois aspectos
principais" e listou três, e escreveu "e a incentivar a diversificação".

### Versão 8 — a correção que não foi no prompt

Os testes com municípios **ricos** (São Paulo e Sorriso) expuseram um defeito
que Uiramutã escondia. Este era o achado entregue ao modelo:

> "A administração pública responde por 6,1% da economia local, contra uma
> mediana nacional de 26,8%."

Com dois números no mesmo período e nenhuma palavra dizendo a direção, o modelo
inverteu: escreveu "**forte dependência** da administração pública" sobre o
município de menor dependência dos três, e atribuiu os 26,8% ao estado. Em São
Paulo fez o mesmo, dizendo que os 7,3% eram da média nacional.

Quando a diferença é gritante (Uiramutã, 83,5% contra 26,8%) ele acerta; quando
é o contrário, inverte.

**A correção foi no `agente.py`, não no prompt.** A análise passou a escrever a
direção por extenso:

> "A administração pública responde por 6,1% da economia deste município.
> Isso é MENOS que a mediana nacional, que é de 26,8%."

E a frase dos setores privados passou a avisar que o número é soma de três
setores, depois que o modelo chamou 92,7% de "concentrada em serviços".

Entraram ainda, nesta versão:

- a proibição de tirar conclusões próprias, depois que o modelo deduziu que
  2,8% de administração pública significa "gestão com poucos recursos";
- a retirada da frase "a análise não apurou nenhum ponto favorável", que era
  **falsa** para municípios ricos e empurrava o modelo a inventar problema;
- um filtro no código que remove ideogramas, depois que o Qwen (modelo chinês)
  escreveu "desenvolvimento 长远 do município". Regra de prompt pede; filtro de
  código garante.

## 4. A tabela das execuções medidas

Todas em Uiramutã (RR), 2021, pelo painel.

| Versão | Mudança | Prompt | Escritos | Tempo | Parágrafos | Defeito restante |
|---|---|---|---|---|---|---|
| 4 | corte de frase corrigido no código | 1.006 | **320 (teto)** | 186,3 s | 2 | bateu no teto |
| 5 | regra 9; teto 480; frases 2 a 3 | 1.094 | 178 | 193,9 s | 1 | parágrafo único |
| 6 | fim do pedido exige 3 parágrafos | 1.128 | **480 (teto)** | 295,5 s | 3 | alerta virou "ponto positivo" |
| 7 | fim do pedido proíbe ponto favorável | 1.203 | 388 | 276,8 s | 3 | deslizes de redação |

A coluna **Escritos** é o indicador mais útil. Quando ela bate exatamente no
teto, a geração foi interrompida. Na versão 7 ela para em 388 de 480: o modelo
chegou ao fim por conta própria.

## 5. Testes com perfis econômicos diferentes

O agente foi testado em quatro municípios escolhidos por serem opostos entre si.

| Município | Riqueza | Perfil | Alertas | O que o caso testa |
|---|---|---|---|---|
| Uiramutã (RR) | 0,31× o Brasil | Administração pública | 3 | município pobre e dependente |
| São Paulo (SP) | 1,58× | Serviços | 1 | a ressalva de serviços e a perda de posição |
| Paulínia (SP) | 10,83× | Indústria | 1 | riqueza extrema e concentração industrial real |
| Sorriso (MT) | 3,12× | Serviços | **0** | município sem nenhum alerta |

Dois achados vieram desses testes:

**A ressalva de serviços.** A primeira versão do `agente.py` acusava São Paulo
de "economia perigosamente concentrada", porque serviços é a categoria com maior
HHI. Mas serviços, no IBGE, é a categoria mais ampla: reúne comércio,
transporte, saúde, educação privada e tecnologia. Um município concentrado em
serviços não corre o mesmo risco de um concentrado numa única indústria. A regra
foi corrigida para registrar o fato como **achado**, e não como alerta.

**A frase "983% maior".** Para Paulínia, cujo PIB por habitante é 10,8 vezes o
do Brasil, a redação em percentual ficava ilegível. A regra passou a escrever
"10,8 vezes o do Brasil" quando a razão é maior que 2.

## 6. Limites conhecidos desta solução

São limites de um modelo de 1,5 bilhão de parâmetros rodando em CPU, e ficam
registrados em vez de escondidos:

1. **O número de parágrafos varia entre 2 e 3** conforme quanta coisa a análise
   encontrou. Sorriso, com 4 achados e nenhum alerta, rende dois parágrafos.
2. **Deslizes de concordância e de contagem** aparecem de vez em quando
   ("dois aspectos principais" seguido de três itens).
3. **Hedges desnecessários**: o modelo escreve "cerca de 16,6%" sobre um número
   exato.
4. **Previsões brandas** escapam da regra 6 ("poderá mitigar seus riscos").
5. **Cada diagnóstico leva de 3,5 a 5 minutos** nesta máquina.

Nenhum desses limites afeta um dado. Todos os números que aparecem nos textos
gerados foram conferidos contra os achados da análise, e a página do painel
oferece a conferência ao leitor: o campo `prompt_enviado` da API e o expander
"Ver o prompt exato que foi enviado ao modelo" mostram o texto integral que o
modelo recebeu. Qualquer número do diagnóstico que não esteja ali foi inventado.

## 7. Conclusão: o que estas oito versões ensinaram

**Num modelo pequeno, a última linha do pedido pesa mais que uma regra no prompt
do sistema.** A exigência dos três parágrafos estava na regra 4 desde a versão 2
e era ignorada; repetida na última linha, passou a ser obedecida. A proibição de
inventar pontos positivos estava na regra 7 desde a versão 2 e era ignorada;
repetida na última linha, passou a ser obedecida. Em nenhum dos casos a regra do
sistema foi apagada — ela ganhou uma segunda aparição no ponto de maior peso.

**Nem todo defeito de texto se conserta no prompt.** A inversão da versão 8 era
ambiguidade do dado de entrada, e foi resolvida no `agente.py`. O corte da
versão 4 era bug do meu código de limpeza. O ideograma foi resolvido com um
filtro, porque regra de prompt não é garantia.

**Prompt pode ser dado, não só texto.** A partir da versão 7, o aviso final é
montado a partir da análise do próprio município. O prompt deixou de ser
constante e passou a depender do que o agente encontrou.
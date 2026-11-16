# Escolha e integração do modelo de linguagem (TP4)

Projeto: Radar Econômico Municipal
Aluno: Ruan Luiz Fernandes da Silva Lima

Este documento registra como o modelo de linguagem do projeto foi escolhido, como
ele foi instalado e integrado à API, e quais ajustes foram necessários para rodar
na máquina local. Todos os números aqui foram medidos nesta máquina, com os
scripts que estão no próprio repositório. Nenhum foi estimado.

---

## 1. O ambiente onde o modelo roda

Antes de escolher qualquer modelo era preciso saber o que a máquina aguentava.
Para isso foi escrito o script `modeling/espiar_ambiente.py`, que apenas lê e
informa a configuração real do computador. Esse método é o mesmo já usado no TP2
e no TP3, quando os scripts `espiar_*.py` conferiram as fontes de dados antes de
qualquer código depender delas.

| Item | Valor medido |
|---|---|
| Sistema | Windows 11 Home, build 26200 |
| Python | 3.14.9, 64 bits, dentro do venv do projeto |
| Processador | Intel de 13ª geração, 32 núcleos lógicos |
| Memória RAM | 15,7 GB |
| Disco livre | 444 GB, SSD NVMe |
| Placa de vídeo | Intel UHD integrada e NVIDIA GeForce RTX dedicada |

A conclusão foi que a máquina comporta um modelo pequeno ou médio rodando em CPU,
mas que a memória é o recurso apertado: no momento da medição havia apenas 1,8 GB
de RAM livre, com o sistema usando 89% do total. Isso foi tratado antes de
continuar, e a quantidade de memória livre passou a ser conferida a cada teste.

---

## 2. Por que o PyTorch foi instalado na versão sem GPU

A máquina tem uma placa NVIDIA dedicada, então seria possível rodar o modelo nela.
Mesmo assim foi instalada a versão do PyTorch só para CPU, por três motivos.

O primeiro é o tamanho: a versão com suporte a GPU é um download de quase 3 GB,
contra os 128 MB que a versão de CPU efetivamente baixou. O segundo é a
compatibilidade: a versão com GPU exige que a versão do CUDA instalada combine com
a do PyTorch, o que acrescenta um ponto de falha. O terceiro é que o Python desta
máquina é a versão 3.14, muito recente, e isso já era um risco de compatibilidade
por si só — empilhar o CUDA em cima dele aumentaria a chance de o projeto não rodar.

Com 32 núcleos lógicos disponíveis, o ganho de velocidade não compensava o risco.

Essa decisão não está escrita no código como uma limitação. O arquivo
`deployment/modelo_llm.py` chama `torch.cuda.is_available()` e usa a placa de vídeo
automaticamente caso ela esteja disponível. Trata-se de uma escolha de instalação,
não de uma restrição do programa.

---

## 3. Como o ambiente foi preparado, passo a passo

O ambiente virtual do projeto (`venv`) já existia desde o TP1. Sobre ele foram
executados, nesta ordem, dentro da pasta raiz do projeto e com o venv ativo:

```
py -m pip install torch --index-url https://download.pytorch.org/whl/cpu
py -m pip install transformers sentencepiece protobuf
py -m pip install --upgrade protobuf
```

O parâmetro `--index-url` do primeiro comando é o que faz o pip buscar a versão
enxuta, compilada apenas para CPU, em vez da versão padrão do PyPI. O terceiro
comando foi necessário por causa de um erro descrito na seção 5.

A instalação foi verificada pelo script `modeling/testa_instalacao.py`, que importa
cada biblioteca, executa uma soma de tensores para provar que o PyTorch realmente
funciona, informa se há GPU disponível, conta os núcleos que o torch vai usar e
mede a memória livre no momento.

---

## 4. Bibliotecas usadas e suas versões

| Biblioteca | Versão | Para que serve no projeto |
|---|---|---|
| torch | 2.15.0+cpu | Executa o modelo. A roda instalada é `cp314`, ou seja, compilada para o Python 3.14 |
| transformers | 5.22.2 | Baixa o modelo da HuggingFace e o carrega na memória |
| sentencepiece | 0.2.3 | Tokenizador do modelo, que transforma o texto em números |
| protobuf | 7.36.1 | Lê o arquivo do tokenizador, que é gravado nesse formato |
| fastapi | 0.143.3 | Já existia desde o TP3; é onde a rota nova foi criada |
| streamlit | 1.62.0 | Já existia desde o TP1; é onde a página nova foi criada |

O download do PyTorch para CPU teve 128,6 MB. As demais bibliotecas somaram cerca
de 25 MB.

---

## 5. Dois ajustes de compatibilidade que foram necessários

O primeiro apareceu antes mesmo de escrever qualquer código. A versão 5 do
Transformers removeu a `SummarizationPipeline`, que é o caminho mais comum ensinado
em tutoriais para tarefas de resumo. O projeto não foi afetado porque o modelo é
carregado diretamente com `AutoModelForSeq2SeqLM`, que continua existindo na versão
5. Essa decisão foi tomada antes da instalação, com base na documentação do próprio
modelo, e acabou evitando um retrabalho.

O segundo apareceu na primeira execução e quebrou o carregamento do tokenizador. A
biblioteca `sentencepiece` havia sido compilada esperando o `protobuf` na versão
7.36.1, mas o ambiente tinha a 7.36.0 instalada, e o protobuf recusa executar código
gerado por uma versão mais nova que a sua. A mensagem exata foi:

```
Detected incompatible Protobuf Gencode/Runtime versions when loading
sentencepiece_model.proto: gencode 7.36.1 runtime 7.36.0.
Runtime version cannot be older than the linked gencode version.
```

Ao falhar por esse motivo, o Transformers tentou um caminho alternativo, o extrator
TikToken, e pediu a instalação de uma biblioteca chamada `tiktoken`. Essa pista era
falsa: o arquivo do modelo é SentencePiece, e instalar o `tiktoken` não resolveria
nada. A correção correta foi atualizar o protobuf para a versão 7.36.1.

Há ainda um aviso que aparece a cada download e que não é erro: o cache da
HuggingFace usa atalhos de sistema de arquivos que o Windows não permite sem o modo
desenvolvedor ligado, e por isso ele guarda os arquivos de forma menos eficiente.
A única consequência é usar um pouco mais de disco, o que é irrelevante com 444 GB
livres.

---

## 6. A escolha do modelo

### 6.1 Os critérios

O enunciado pede que a escolha seja justificada por desempenho, custo computacional
local e acessibilidade local. A esses três critérios foi acrescentado um quarto, que
no caso deste projeto é eliminatório: **o modelo precisa funcionar em português do
Brasil**. Todo o conteúdo do projeto é em português — as matérias do IBGE, os nomes
dos municípios, os termos econômicos — e um modelo que resuma bem em inglês não
resolve nada aqui.

### 6.2 Os modelos considerados

| Modelo | Tamanho em disco | Observação |
|---|---|---|
| **recogna-nlp/ptt5-base-summ** | **892 MB** | T5 treinado especificamente para resumo em português do Brasil, por um grupo de pesquisa brasileiro. Distribuído em formato `safetensors`. **Escolhido.** |
| csebuetnlp/mT5_multilingual_XLSum | 2,33 GB | Resume em 43 idiomas, inclusive português. Quase três vezes maior, e distribuído apenas como `pytorch_model.bin`, sem `safetensors` |
| neuralmind/bert-base-portuguese-cased (BERTimbau) | — | Excelente em português, mas é um modelo só de codificação: serve para classificar texto, não para gerar resumo. Não atende à tarefa |

O BERTimbau foi descartado por arquitetura, não por tamanho: resumir exige um modelo
que gere texto novo, e o BERT não gera.

A disputa real foi entre os dois primeiros. O mT5 multilíngue é mais versátil, mas
essa versatilidade é justamente o que o deixa caro aqui: ele carrega o vocabulário
de 43 idiomas para resolver um problema que acontece inteiramente em um só. Em uma
máquina onde a memória livre chegou a 1,8 GB, carregar 2,33 GB em vez de 892 MB é a
diferença entre rodar e não rodar.

### 6.3 Desempenho

O modelo escolhido foi testado antes de entrar na API, pelo script
`modeling/testa_modelo.py`, sobre uma matéria real do próprio projeto. O primeiro
resumo gerado trouxe uma frase inventada, que dizia que "os sete municípios líderes
do ranking eram São Paulo e Rio de Janeiro" — anunciando sete e citando dois.

Em vez de aceitar o resultado ou trocar o modelo por tentativa, foi escrito o script
`modeling/afina_resumo.py`, que gera o resumo de duas matérias diferentes com quatro
configurações de parâmetros e imprime os resultados lado a lado. O resultado está na
seção 7.

Na qualidade final, com a configuração escolhida, o modelo produz resumos corretos.
No teste da bateria de erros, sobre um texto do IBGE com 1.328 caracteres, ele
devolveu:

> "Excluindo a atividade de administração pública, a agropecuária responde por mais
> da metade das economias em 1.135 dos 5.570 municípios brasileiros (20,4%) em 2014,
> 210 deles no Rio Grande do Sul e 144 no Paraná."

Todos os números conferem com o texto original. O único desvio é o tempo verbal, que
passou de "respondia" para "responde".

### 6.4 Custo computacional local

| Medida | Valor medido |
|---|---|
| Parâmetros | 222.903.552 |
| Tamanho em disco | 892 MB |
| Memória RAM ocupada quando carregado | cerca de 1,0 GB |
| Tempo para carregar, script isolado | 12,6 s |
| Tempo para carregar, dentro da API | 35,8 s |
| Geração de resumo, texto curto (282 tokens) | 4,9 s |
| Geração de resumo, matéria inteira (512 tokens) | 12 a 15 s |
| Segundo pedido completo à API | 5,8 s |
| Núcleos de CPU usados | 24 |

A diferença entre os 12,6 segundos do script isolado e os 35,8 segundos dentro da
API merece explicação, porque é uma medição honesta de um limite real desta máquina.
A API já mantém em memória os três arquivos de dados do projeto, entre eles os 77.980
registros de indicadores. Com menos memória livre, o Windows passa a usar o disco
como memória auxiliar, e o carregamento fica mais lento. Não é defeito do modelo nem
do código: é o custo de rodar tudo ao mesmo tempo em uma máquina de 15,7 GB.

O que importa na prática é que esse custo é pago **uma vez só**. Depois de carregado,
o modelo permanece na memória e cada novo resumo custa de 5 a 15 segundos, conforme o
tamanho do texto.

### 6.5 Acessibilidade local

O modelo é carregado com duas linhas, usando as classes automáticas do Transformers:

```python
tokenizador = AutoTokenizer.from_pretrained("recogna-nlp/ptt5-base-summ")
modelo = AutoModelForSeq2SeqLM.from_pretrained("recogna-nlp/ptt5-base-summ")
```

Não é necessária chave de API, conta em serviço nenhum, cartão de crédito nem
autenticação na HuggingFace. O download acontece uma vez e os arquivos ficam no cache
local, em `C:\Users\<usuario>\.cache\huggingface`, fora da pasta do projeto — por isso
o modelo não vai para o repositório e o `.gitignore` não precisou ser alterado.

Depois do primeiro download, **o projeto funciona sem internet**. Isso foi verificado
pela própria bateria de testes, que roda inteiramente contra `127.0.0.1`.

O formato `safetensors`, que o modelo escolhido usa e o mT5 do XLSum não usa, é mais
seguro de carregar, porque é um formato de dados puro, enquanto o `.bin` do PyTorch é
um arquivo que pode executar código ao ser aberto.

---

## 7. O experimento que definiu os parâmetros

O script `modeling/afina_resumo.py` comparou quatro configurações sobre as mesmas
duas matérias.

| Config. | O que mudava | Matéria 0 | Matéria 7 |
|---|---|---|---|
| A | `min_length=40` | **inventou** uma frase sem sentido | mais completa das quatro |
| B | `min_length=10`, `max_length=160` | correta, porém incompleta | correta |
| C | B com `length_penalty=0,6` | idêntica à B | idêntica à B |
| D | entrada de 1024 em vez de 512 | **atribuiu os 32,8% ao grupo errado** | correta, com repetição |

Três conclusões saíram daí.

A configuração A obrigava o modelo a gerar no mínimo 40 tokens, e foi exatamente na
matéria em que ele tinha pouco a dizer que ele inventou conteúdo para cumprir o
mínimo. O piso mínimo era a causa da invenção, não o acaso.

A configuração D cometeu um erro mais perigoso que o da A: o texto original dizia que
os sete maiores municípios somavam cerca de um quarto do PIB e que as 27 capitais
somavam 32,8%; o modelo manteve a estrutura da frase das capitais e trocou o sujeito
pelos sete municípios, inclusive mantendo o "somadas" no feminino, que concordava com
"as capitais". É um número certo atribuído ao grupo errado, escrito de forma fluente,
e passaria despercebido por um leitor apressado.

O `length_penalty` da configuração C não teve efeito nenhum, o que mostra que esse
parâmetro não era o gargalo.

A configuração **B** foi escolhida por ter sido a única que não inventou nenhuma
informação em nenhuma das duas matérias, e por se adaptar ao texto: na matéria com
menos conteúdo ela parou em 23 palavras, na mais densa foi até 59. O custo aceito é
que em um dos casos ela deixou de fora um dado relevante. Para um projeto sobre
indicadores econômicos, um resumo incompleto é um problema menor do que um número
atribuído ao grupo errado, e o leitor pode sempre abrir a matéria original pelo link
que a API devolve.

### Configuração oficial do projeto

```python
limite_de_entrada    = 512
max_length           = 160
min_length           = 10
num_beams            = 5
no_repeat_ngram_size = 3
early_stopping       = True
length_penalty       = 1.0
```

---

## 8. Como a integração local foi feita

O modelo não foi colocado dentro do `api.py`. Ele ficou em um arquivo próprio,
`deployment/modelo_llm.py`, que a API importa. Quatro decisões de projeto estão nesse
arquivo, e todas vieram de números medidos.

**O modelo não é carregado quando a API liga.** Ele é carregado na primeira vez que
alguém pede um resumo. Isso se chama carregamento preguiçoso. O motivo está na seção
6.4: carregar custa de 12 a 36 segundos, e não faria sentido a API inteira demorar
isso para subir por causa de uma rota entre oito. Quem só quer consultar o PIB de um
município não paga pelo modelo.

**O `import torch` fica dentro da função, não no topo do arquivo.** Isso é
contraintuitivo, mas é proposital. Se o import estivesse no topo e as bibliotecas não
estivessem instaladas, a API inteira quebraria ao subir e as outras sete rotas
morreriam junto. Do jeito que está, a API sobe normalmente, as rotas de dados
continuam funcionando, e apenas a rota do modelo responde HTTP 503 com uma mensagem
explicando o que falta instalar.

**Existe uma trava de carregamento.** O FastAPI atende vários pedidos ao mesmo tempo,
em threads diferentes. Sem a trava, dois pedidos simultâneos carregariam o modelo duas
vezes e ocupariam 2 GB em vez de 1 — o que, nesta máquina, derrubaria tudo.

**Existe uma segunda trava, a de uso.** Só um resumo é gerado por vez. Se chegar outro
pedido enquanto o modelo está gerando, a API responde HTTP 429 em vez de deixar os dois
pedidos disputando a mesma CPU e ficando lentos.

Além dessas quatro, duas medidas de economia de memória estão na geração em si: a
chamada acontece dentro de `with torch.no_grad()`, que avisa ao PyTorch que não haverá
treinamento e dispensa o armazenamento usado para isso, e o texto de entrada é cortado
em 512 tokens, que é o limite para o qual o modelo foi treinado.

---

## 9. Onde cada coisa está no repositório

| Arquivo | O que faz |
|---|---|
| `modeling/espiar_ambiente.py` | Verifica o hardware antes de escolher o modelo |
| `modeling/testa_instalacao.py` | Confere se torch e transformers instalaram e funcionam |
| `modeling/testa_modelo.py` | Baixa o modelo e resume uma matéria real, medindo tempos |
| `modeling/afina_resumo.py` | Compara as quatro configurações de parâmetros |
| `modeling/escolha_do_modelo.md` | Este documento |
| `deployment/modelo_llm.py` | Carrega o modelo e gera os resumos |
| `deployment/respostas.py` | Response Models de todas as rotas |
| `deployment/api.py` | A API, com as rotas e o tratamento de erros |
| `deployment/testa_erros_api.py` | Bateria de 21 testes do tratamento de erros |
| `deployment/paginas/resumo_llm.py` | A página do painel que usa o modelo |

---

## 10. Limitações conhecidas

O modelo lê no máximo 512 tokens por vez, o que equivale a mais ou menos os três
primeiros parágrafos de uma matéria. As matérias coletadas no TP3 têm de 1.000 a 2.000
palavras, então na maioria delas o resumo cobre apenas o começo do texto. A API informa
isso explicitamente, no campo `texto_cortado` da resposta, e a página do painel mostra
um aviso quando acontece. É uma limitação exposta, não escondida.

O modelo é pequeno e, como todo modelo de resumo, pode mudar o tempo verbal, deixar
informação de fora ou, em casos raros, reescrever uma frase de maneira imprecisa. Por
isso a página mostra sempre o resumo do modelo ao lado do resumo publicado pelo IBGE e
do link para a matéria original, além de um aviso fixo de que o texto é gerado por
máquina. Essa medida estava prevista desde o TP3, no arquivo
`business_understanding/planejamento_llm.md`, como mitigação do risco de o texto gerado
soar como parecer técnico definitivo.

Por fim, o desempenho depende da memória livre da máquina. Com o navegador aberto e
muitos programas rodando, o carregamento do modelo pode passar de 35 segundos. Com a
máquina mais livre, cai para cerca de 13.
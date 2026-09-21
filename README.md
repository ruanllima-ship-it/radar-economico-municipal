# Radar Econômico Municipal

Painel interativo em Streamlit que mostra o quanto a riqueza do Brasil está concentrada em poucas cidades, qual o perfil econômico de cada município e quais são economicamente frágeis por dependerem de um único setor ou de repasse público.

As 27 capitais responderam por 28,3% do PIB nacional em 2023, contra 27,5% em 2022 e 36,1% em 2002. O dado é público e oficial, mas fica preso em planilhas técnicas do IBGE com dezenas de milhares de linhas. A proposta do painel é entregar essa informação já calculada e comparada para quem precisa decidir.

## Público-alvo

Gestores públicos municipais e estaduais de cidades pequenas e médias, que normalmente não têm equipe de dados na prefeitura, além de vereadores e conselhos municipais. Como público secundário estão jornalistas de economia, pesquisadores de desenvolvimento regional e empresas avaliando expansão.

## Enquadramento ESG e ODS

Pilar Social, com apoio de Governança. Atende principalmente aos ODS 8 (trabalho decente e crescimento econômico) e ODS 10 (redução das desigualdades), e de forma secundária ao ODS 11 (cidades e comunidades sustentáveis, meta 11.a).

## Indicadores

O painel calcula sete indicadores a partir da base do IBGE: participação do município no PIB nacional, PIB per capita, razão entre o PIB per capita do município e o do Brasil, curva de concentração, índice de diversificação econômica, grau de dependência da administração pública e classificação do município pelo setor de maior valor adicionado.

## Fonte dos dados

A fonte principal é o PIB dos Municípios (PIB-Munic), do IBGE / Sistema de Contas Nacionais, tabela 5938 do SIDRA, acessada pela API aberta em https://apisidra.ibge.gov.br. Os valores são publicados em milhares de reais correntes. Entram como fontes complementares a API de Localidades do IBGE, as Estimativas de População, o IPCA e a Agência de Notícias do IBGE.

Na divulgação de dezembro de 2025, o IBGE publicou os anos de 2022 e 2023 sem a abertura do valor adicionado por atividade econômica. Por isso os indicadores de concentração e riqueza cobrem a série até 2023, enquanto os de composição setorial ficam entre 2010 e 2021.

## Organização do projeto

O projeto segue o ciclo de vida do TDSP, com as pastas separadas por estágio: business_understanding, data_acquisition, modeling, deployment e customer_acceptance.

## Como rodar

Criar e ativar o ambiente virtual, instalar as dependências com `pip install -r requirements.txt` e executar `streamlit run deployment\app.py` sempre a partir da pasta raiz do projeto.

## Autor

Ruan Luiz Fernandes da Silva Lima — Ciência de Dados, Projeto de Bloco: Inteligência Artificial Aplicada.
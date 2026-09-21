import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Radar Econômico Municipal")

st.subheader("O problema")
st.write("A economia brasileira é muito concentrada no território. As 27 capitais responderam por 28,3% de todo o PIB nacional em 2023, contra 27,5% em 2022 e 36,1% em 2002. No outro extremo, milhares de municípios pequenos só têm atividade econômica porque recebem repasse público.")
st.write("Esse dado é público e oficial, mas fica preso em planilhas técnicas do IBGE. Um gestor municipal que queira saber se a sua cidade é dependente e de qual setor ela vive teria que baixar o arquivo e calcular tudo na mão.")

st.subheader("Objetivo")
st.write("Montar um painel onde a pessoa escolhe o município e recebe os indicadores já calculados, comparados com a média do estado e do país. O projeto atende aos ODS 8 e 10 da Agenda 2030.")

st.subheader("Links úteis")
st.write("PIB dos Municípios, tabela 5938 do SIDRA: https://sidra.ibge.gov.br/tabela/5938")
st.write("Página da pesquisa no IBGE: https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/2036-np-produto-interno-bruto-dos-municipios.html")
st.write("API de Localidades do IBGE: https://servicodados.ibge.gov.br/api/v1/localidades/municipios")
st.write("Conecta Brasil: https://conectabrasil.org/home")
st.write("Observatório do Terceiro Setor: https://observatorio3setor.org.br")

st.subheader("Amostra dos dados")
st.write("Valores em milhares de reais correntes, ano de 2021.")

dados = pd.read_csv("data_acquisition/cleaned_data/amostra_pib.csv")
st.dataframe(dados)
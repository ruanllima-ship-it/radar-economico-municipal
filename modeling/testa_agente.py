# testa_agente.py
# Testa o motor de analise do agente, sem usar modelo de linguagem nenhum.
#
# A ideia e conferir se as regras de decisao fazem sentido em municipios
# bem diferentes entre si, antes de o modelo escrever qualquer texto. Se a
# analise estiver errada aqui, nenhum prompt conserta depois.

import os
import sys

import pandas as pd

# o import de cima funciona quando se roda da raiz do projeto. o de baixo
# cobre quem rodar de dentro de outra pasta.
try:
    from deployment.agente import montar_analise
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from deployment.agente import montar_analise


pasta_deste_arquivo = os.path.dirname(os.path.abspath(__file__))
raiz_do_projeto = os.path.dirname(pasta_deste_arquivo)
caminho_indicadores = os.path.join(
    raiz_do_projeto, "data_acquisition", "cleaned_data", "indicadores_municipios.csv"
)

# municipios escolhidos de proposito, um de cada perfil, para ver se as
# regras acendem e apagam nos lugares certos
casos = [
    (1400704, 2021, "Uiramutã (RR) - vive da administração pública"),
    (3550308, 2021, "São Paulo (SP) - a maior economia do país"),
    (3536505, 2021, "Paulínia (SP) - indústria, PIB por habitante altíssimo"),
    (5107925, 2021, "Sorriso (MT) - agropecuária forte"),
    (3304557, 2023, "Rio de Janeiro (RJ) - ano SEM dados por setor"),
    (9999999, 2021, "código que não existe - tem que devolver nada"),
    (3550308, 1990, "ano que não existe - tem que devolver nada"),
]


print()
print("=" * 74)
print("  TESTE DO MOTOR DE ANÁLISE DO AGENTE (sem modelo de linguagem)")
print("=" * 74)

indicadores = pd.read_csv(caminho_indicadores)
print()
print("Linhas na base:", len(indicadores))
print()

for codigo, ano, rotulo in casos:
    print("=" * 74)
    print(rotulo)
    print("=" * 74)

    analise = montar_analise(indicadores, codigo, ano)

    if analise is None:
        print("   nada encontrado (esse era o resultado esperado)")
        print()
        continue

    print("   Município:", analise["municipio"], "-", analise["estado"])
    print("   Ano:", analise["ano"], "| Perfil:", analise["perfil"])
    print("   Tem dados por setor:", analise["tem_dados_setoriais"])
    print()

    print("   FAIXAS (comparadas com a distribuição nacional do ano):")
    for chave in analise["faixas"]:
        print("      " + chave + ": " + analise["faixas"][chave])
    print()

    print("   ACHADOS:")
    for texto in analise["achados"]:
        print("      - " + texto)
    print()

    if len(analise["alertas"]) > 0:
        print("   ALERTAS:")
        for texto in analise["alertas"]:
            print("      ! " + texto)
        print()
    else:
        print("   ALERTAS: nenhum")
        print()

    print("   O QUE ACOMPANHAR:")
    for texto in analise["acompanhar"]:
        print("      > " + texto)
    print()

print("=" * 74)
print("  FIM. Copiar toda essa saída e mandar para análise.")
print("=" * 74)
print()
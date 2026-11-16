# espiar_ambiente.py
# Antes de escolher o modelo de linguagem do TP4, eu preciso saber o que a
# minha maquina aguenta. Esse script so olha e informa. Nao instala nada.

import sys
import os
import platform
import shutil
import subprocess

print()
print("=" * 62)
print("  CONFERINDO O AMBIENTE PARA O TP4 (modelo de linguagem local)")
print("=" * 62)
print()

# ------------------------------------------------------------------
# 1) Versao do Python
# ------------------------------------------------------------------
print("1) PYTHON")

versao = sys.version_info
versao_curta = str(versao.major) + "." + str(versao.minor) + "." + str(versao.micro)

print("   Versao:", versao_curta)
print("   Executavel:", sys.executable)

if sys.maxsize > 2 ** 32:
    print("   Arquitetura: 64 bits (certo, o PyTorch exige 64 bits)")
else:
    print("   Arquitetura: 32 bits (problema, o PyTorch nao roda em 32 bits)")

if versao.major == 3 and versao.minor >= 14:
    print("   Observacao: o Python 3.14 e muito novo. O PyTorch para essa")
    print("   versao vai ser testado no bloco 2.")

if versao.major == 3 and versao.minor <= 12:
    print("   Observacao: versao bem suportada pelo PyTorch, sem risco aqui.")

print()

# ------------------------------------------------------------------
# 2) Sistema e processador
# ------------------------------------------------------------------
print("2) SISTEMA")

print("   Sistema:", platform.system(), platform.release())
print("   Processador:", platform.processor())

nucleos = os.cpu_count()
print("   Nucleos de CPU:", nucleos)

if nucleos is None:
    print("   Avaliacao: nao consegui contar os nucleos.")
elif nucleos >= 8:
    print("   Avaliacao: bom, o resumo em CPU deve sair rapido.")
elif nucleos >= 4:
    print("   Avaliacao: da para rodar em CPU, com um pouco de paciencia.")
else:
    print("   Avaliacao: poucos nucleos, cada resumo vai demorar mais.")

print()

# ------------------------------------------------------------------
# 3) Memoria RAM
# ------------------------------------------------------------------
print("3) MEMORIA RAM")

comando = "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"
memoria_gb = None

try:
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-Command", comando],
        capture_output=True,
        text=True,
        timeout=30,
    )
    texto = resultado.stdout.strip()
    if texto != "":
        bytes_totais = int(texto)
        memoria_gb = bytes_totais / (1024 ** 3)
except Exception:
    print("   Nao consegui medir a RAM por aqui.")

if memoria_gb is None:
    print("   RAM total: nao medida. Vou ver no Gerenciador de Tarefas.")
else:
    print("   RAM total:", round(memoria_gb, 1), "GB")
    if memoria_gb >= 15:
        print("   Avaliacao: folgado para o modelo que eu pretendo usar.")
    elif memoria_gb >= 7:
        print("   Avaliacao: suficiente, mas e bom fechar o navegador nos testes.")
    else:
        print("   Avaliacao: apertado. Vou precisar de um modelo menor.")

print()

# ------------------------------------------------------------------
# 4) Espaco em disco
# ------------------------------------------------------------------
print("4) ESPACO EM DISCO")

pasta_atual = os.getcwd()
print("   Pasta de onde rodei:", pasta_atual)

uso = shutil.disk_usage(pasta_atual)
total_gb = uso.total / (1024 ** 3)
livre_gb = uso.free / (1024 ** 3)

print("   Disco total:", round(total_gb, 1), "GB")
print("   Disco livre:", round(livre_gb, 1), "GB")
print("   O modelo de resumo ocupa cerca de 0,9 GB.")
print("   O PyTorch ocupa mais ou menos 1,5 GB depois de instalado.")
print("   Somando com folga, eu preciso de uns 4 GB livres.")

if livre_gb >= 4:
    print("   Avaliacao: espaco suficiente.")
else:
    print("   Avaliacao: pouco espaco. Preciso liberar antes de continuar.")

print()

# ------------------------------------------------------------------
# 5) Bibliotecas
# ------------------------------------------------------------------
print("5) BIBLIOTECAS (so conferindo, nao instalando)")

try:
    import torch
    print("   torch: instalado, versao", torch.__version__)
except Exception:
    print("   torch: ainda nao instalado (esperado, e o bloco 2)")

try:
    import transformers
    print("   transformers: instalado, versao", transformers.__version__)
except Exception:
    print("   transformers: ainda nao instalado (esperado, e o bloco 2)")

try:
    import fastapi
    print("   fastapi: instalado, versao", fastapi.__version__)
except Exception:
    print("   fastapi: nao achei, mas deveria estar aqui desde o TP3")

try:
    import pandas
    print("   pandas: instalado, versao", pandas.__version__)
except Exception:
    print("   pandas: nao achei, mas deveria estar aqui desde o TP1")

try:
    import streamlit
    print("   streamlit: instalado, versao", streamlit.__version__)
except Exception:
    print("   streamlit: nao achei, mas deveria estar aqui desde o TP1")

print()
print("=" * 62)
print("  FIM. Copiar toda essa saida e mandar para analise.")
print("=" * 62)
print()
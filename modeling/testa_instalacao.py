# testa_instalacao.py
# Confere se o PyTorch e o Transformers instalaram mesmo e se funcionam.
# Esse script ainda nao baixa modelo nenhum. So testa as bibliotecas.

import sys
import subprocess

print()
print("=" * 62)
print("  TESTANDO A INSTALACAO DO PYTORCH E DO TRANSFORMERS")
print("=" * 62)
print()

# ------------------------------------------------------------------
# 1) PyTorch
# ------------------------------------------------------------------
print("1) PYTORCH")

try:
    import torch
    print("   Importou. Versao:", torch.__version__)
except Exception as erro:
    print("   NAO IMPORTOU.")
    print("   Erro:", erro)
    print()
    print("   Sem o torch nao da para continuar. Parando aqui.")
    sys.exit()

# conta simples, so para provar que a biblioteca funciona de verdade
primeiro = torch.tensor([1.0, 2.0, 3.0])
segundo = torch.tensor([10.0, 20.0, 30.0])
soma = primeiro + segundo
print("   Teste de conta (deve dar [11.0, 22.0, 33.0]):", soma.tolist())

if torch.cuda.is_available():
    nome_da_placa = torch.cuda.get_device_name(0)
    print("   GPU: disponivel para o PyTorch ->", nome_da_placa)
    print("   Observacao: instalei a versao de CPU, entao isso e um bonus.")
else:
    print("   GPU: nao disponivel para o PyTorch (esperado, instalei a versao CPU).")
    print("   O modelo vai rodar na CPU.")

print("   Nucleos que o torch vai usar:", torch.get_num_threads())
print()

# ------------------------------------------------------------------
# 2) Transformers
# ------------------------------------------------------------------
print("2) TRANSFORMERS")

try:
    import transformers
    print("   Importou. Versao:", transformers.__version__)
except Exception as erro:
    print("   NAO IMPORTOU.")
    print("   Erro:", erro)

print()

# ------------------------------------------------------------------
# 3) SentencePiece (o tokenizador do modelo depende dele)
# ------------------------------------------------------------------
print("3) SENTENCEPIECE")

try:
    import sentencepiece
    print("   Importou. Versao:", sentencepiece.__version__)
except Exception as erro:
    print("   NAO IMPORTOU.")
    print("   Erro:", erro)

print()

# ------------------------------------------------------------------
# 4) Protobuf
# ------------------------------------------------------------------
print("4) PROTOBUF")

try:
    import google.protobuf
    print("   Importou. Versao:", google.protobuf.__version__)
except Exception as erro:
    print("   NAO IMPORTOU.")
    print("   Erro:", erro)

print()

# ------------------------------------------------------------------
# 5) Memoria livre agora
# ------------------------------------------------------------------
print("5) MEMORIA LIVRE NESTE MOMENTO")

comando = "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"

try:
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-Command", comando],
        capture_output=True,
        text=True,
        timeout=30,
    )
    texto = resultado.stdout.strip()
    if texto != "":
        kilobytes_livres = int(texto)
        livre_gb = kilobytes_livres / (1024 * 1024)
        print("   RAM disponivel agora:", round(livre_gb, 1), "GB")
        if livre_gb >= 4:
            print("   Avaliacao: folgado para carregar o modelo no bloco 3.")
        elif livre_gb >= 2:
            print("   Avaliacao: da, mas no limite. Melhor fechar mais programas.")
        else:
            print("   Avaliacao: pouca memoria. Preciso fechar programas antes.")
except Exception:
    print("   Nao consegui medir a memoria livre.")

print()
print("=" * 62)
print("  FIM. Copiar toda essa saida e mandar para analise.")
print("=" * 62)
print()
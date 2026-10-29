from pathlib import Path


# Pasta principal dos dados da automação na rede
PASTA_DADOS = Path(r"X:\GEAP\Gerencia\TCE")

# Planilha que contém as unidades, usuários e senhas
ARQUIVO_UNIDADES = PASTA_DADOS / "RAD-planilha.xlsx"

# Pasta onde ficam os PDFs que serão anexados no TCENET
PASTA_ANEXOS = PASTA_DADOS / "Anexos"
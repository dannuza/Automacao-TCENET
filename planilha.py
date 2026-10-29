import openpyxl

from app.config import ARQUIVO_UNIDADES


def carregar_planilha():
    """
    Abre a planilha de unidades e retorna a planilha ativa.
    """

    if not ARQUIVO_UNIDADES.exists():
        raise FileNotFoundError(
            f"Planilha não encontrada: {ARQUIVO_UNIDADES}"
        )

    workbook = openpyxl.load_workbook(
        ARQUIVO_UNIDADES,
        read_only=True,
        data_only=True
    )

    planilha = workbook.active

    return workbook, planilha


def carregar_unidades():
    """
    Lê a planilha de unidades e retorna as siglas cadastradas.
    """

    workbook, planilha = carregar_planilha()

    try:
        cabecalhos = [
            celula.value
            for celula in next(planilha.iter_rows())
        ]

        indice_sigla = cabecalhos.index("Sigla")

        siglas = []

        for linha in planilha.iter_rows(
            min_row=2,
            values_only=True
        ):
            sigla = linha[indice_sigla]

            if sigla and str(sigla).strip():
                siglas.append(str(sigla).strip())

        return sorted(set(siglas))

    finally:
        workbook.close()


def buscar_unidade_por_sigla(sigla):
    """
    Busca na planilha a unidade correspondente à sigla informada.

    Retorna um dicionário contendo os dados da unidade.
    """

    if not sigla:
        return None

    workbook, planilha = carregar_planilha()

    try:
        cabecalhos = [
            celula.value
            for celula in next(planilha.iter_rows())
        ]

        indices = {
            cabecalho: indice
            for indice, cabecalho in enumerate(cabecalhos)
            if cabecalho is not None
        }

        if "Sigla" not in indices:
            raise ValueError(
                "A coluna 'Sigla' não foi encontrada na planilha."
            )

        indice_sigla = indices["Sigla"]

        for linha in planilha.iter_rows(
            min_row=2,
            values_only=True
        ):
            valor_sigla = linha[indice_sigla]

            if valor_sigla is None:
                continue

            if str(valor_sigla).strip().upper() == sigla.strip().upper():

                dados_unidade = {}

                for nome_coluna, indice in indices.items():
                    dados_unidade[nome_coluna] = linha[indice]

                return dados_unidade

        return None

    finally:
        workbook.close()
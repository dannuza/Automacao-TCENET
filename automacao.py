import re
import unicodedata
import os
import glob

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Selenium_base import (
    iniciar_chrome,
    abrir_site,
    preencher,
    clicar,
    esperar_clicavel
)

from app.controle import (
    carregar_registros_por_edital,
    atualizar_status_planilha,
    consultar_status_planilha,
)

from selenium.common.exceptions import StaleElementReferenceException

# ============================================================
# CONFIGURAÇÕES
# ============================================================

URL_TCENET = "https://tcenet.tce.go.gov.br/"


# ============================================================
# ABRIR O TCENET
# ============================================================

def abrir_tcenet():
    """
    Inicia o Chrome e acessa o TCENET.
    """

    driver = iniciar_chrome()

    abrir_site(
        driver,
        URL_TCENET
    )

    return driver


# ============================================================
# ABRIR O MÓDULO GRAD
# ============================================================

def abrir_grad(driver):
    """
    Abre o módulo GRAD - Registro de Admissões.
    """

    clicar(
        driver,
        (
            "css selector",
            'button[alt="Grad - Registro de Admissões"]'
        )
    )


# ============================================================
# LOGIN E NAVEGAÇÃO ATÉ A PESQUISA DE ADMISSÕES
# ============================================================

def fazer_login(driver, usuario, senha):
    """
    Realiza o login e navega até:
    Cadastro > Manter Admissão > Pesquisar.
    """

    preencher(
        driver,
        ("id", "txtUsuario"),
        usuario
    )

    preencher(
        driver,
        ("id", "txtSenha"),
        senha
    )

    clicar(
        driver,
        ("id", "btnEntrar")
    )

    abrir_grad(driver)

    menu_cadastro = esperar_clicavel(
        driver,
        (
            "xpath",
            "//a[contains(normalize-space(.), 'Cadastro')]"
        )
    )

    menu_cadastro.click()

    botao_manter_admissao = esperar_clicavel(
        driver,
        (
            "xpath",
            "//a[normalize-space()='Manter Admissão']"
        )
    )

    botao_manter_admissao.click()

    botao_pesquisar = esperar_clicavel(
        driver,
        (
            "xpath",
            "//input[@value='Pesquisar']"
        )
    )

    botao_pesquisar.click()



# ============================================================
# NORMALIZAÇÃO DOS TEXTOS — VERSÃO CORRIGIDA
# ============================================================

def normalizar_texto(texto):
    """
    Normaliza textos para comparação:
    - Remove acentos;
    - Ignora maiúsculas/minúsculas;
    - Padroniza hífens e pontuação;
    - Remove espaços duplicados.
    """

    if texto is None:
        return ""

    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(r"[^A-Z0-9]+", " ", texto)
    return " ".join(texto.split())


def normalizar_cargo(valor):
    """
    Normaliza cargos sem depender de uma lista de concursos.
    Também ignora sufixos de carga horária, quando existentes.
    """

    texto = normalizar_texto(valor)

    texto = re.sub(
        r"\s+(?:20|30|40)\s*(?:HRS?|HORAS?)$",
        "",
        texto
    )

    return texto.strip()


def cargo_equivalente(cargo_planilha, cargo_site):
    """
    Compara cargos sem confundir nomes diferentes.

    Ignora acentos e pontuação.
    Tolera complementos separados por vírgula ou entre
    parênteses no nome apresentado pelo site.
    Não aceita correspondências parciais arbitrárias.
    """

    def preparar(valor):
        texto = str(valor or "").strip()

        # Remove complemento final entre parênteses.
        texto = re.sub(r"\s*\([^)]*\)\s*$", "", texto)

        # Remove observação posterior à vírgula.
        texto = texto.split(",", 1)[0]

        return normalizar_cargo(texto)

    esperado = preparar(cargo_planilha)
    encontrado = preparar(cargo_site)

    return bool(esperado) and esperado == encontrado


def normalizar_especialidade(valor):
    """
    Uniformiza especialidades de professores sem exigir
    cadastro manual de cada disciplina.

    Exemplos:
    PROFESSOR - EDUCACAO FISICA
    PROFESSOR DE EDUCAÇÃO FÍSICA

    Ambas ficam:
    PROFESSOR EDUCACAO FISICA
    """

    texto = normalizar_texto(valor)

    # Uniformiza PROFESSOR DE DISCIPLINA e PROFESSOR DISCIPLINA.
    texto = re.sub(r"^PROFESSOR\s+DE\s+", "PROFESSOR ", texto)

    # Uniformiza singular/plural de algumas denominações.
    equivalencias = {
        "PROFESSOR ARTES": "PROFESSOR ARTE",
        "PROFESSOR CIENCIAS BIOLOGIA":
            "PROFESSOR CIENCIA BIOLOGIA",
    }

    return equivalencias.get(texto, texto)


def normalizar_regiao(valor):
    """
    Compara cidades e regiões ignorando acentos,
    pontuação e espaços.

    Exemplo:
    ACREUNA = ACREÚNA
    """

    texto = normalizar_texto(valor)

    # Mantém a equivalência já utilizada para Aparecida.
    texto = re.sub(r"\bAPARECIDA\b", "AP", texto)

    return " ".join(texto.split())



# ============================================================
# PÁGINA 5 — SELECIONAR O EDITAL
# ============================================================

def selecionar_edital(driver, edital):
    """
    Localiza o edital na terceira coluna da tabela
    da Página 5 e clica no botão da primeira coluna.
    """

    def normalizar_edital(valor):
        valor = str(valor or "").strip()

        if "/" not in valor:
            return valor

        numero, ano = valor.split("/", 1)

        numero = numero.strip()
        ano = ano.strip()

        if numero.isdigit():
            numero = str(int(numero))

        return f"{numero}/{ano}"

    edital_busca = normalizar_edital(edital)

    print("\n" + "=" * 60)
    print("PÁGINA 5 — SELEÇÃO DO EDITAL")
    print("=" * 60)
    print(f"Edital informado: {edital}")

    tabela = esperar_clicavel(
        driver,
        (
            "id",
            "ctl00_ContentPlaceHolder1_gridEditais"
        )
    )

    linhas = tabela.find_elements(
        "xpath",
        ".//tr"
    )

    for numero_linha, linha in enumerate(
        linhas,
        start=1
    ):

        celulas = linha.find_elements(
            "xpath",
            "./td"
        )

        if len(celulas) < 3:
            continue

        edital_tabela = celulas[2].text.strip()

        if normalizar_edital(edital_tabela) == edital_busca:

            print(
                f"Edital encontrado na linha {numero_linha}: "
                f"{edital_tabela}"
            )

            botao = celulas[0].find_element(
                "xpath",
                ".//input[@type='image']"
            )

            botao.click()

            print("Edital selecionado com sucesso.")

            return

    raise ValueError(
        f"Edital '{edital}' não foi encontrado na Página 5."
    )



# ============================================================
# PÁGINA 6 — LOCALIZAR E SELECIONAR A LINHA
# ============================================================

def selecionar_linha_pagina6(
    driver,
    cargo="",
    especialidade="",
    regiao=""
):
    """
    Seleciona a linha da Página 6 comparando cargo,
    especialidade e região após normalização.
    """

    esperados = {
        "cargo": normalizar_cargo(cargo),
        "especialidade": normalizar_especialidade(especialidade),
        "regiao": normalizar_regiao(regiao),
    }

    campos_preenchidos = {
        nome: valor
        for nome, valor in esperados.items()
        if valor
    }

    print("\n" + "=" * 60)
    print("PÁGINA 6 — BUSCA AUTOMÁTICA")
    print("=" * 60)
    print(f"Cargo da planilha: {cargo}")
    print(f"Especialidade da planilha: {especialidade}")
    print(f"Região da planilha: {regiao}")
    print(f"Campos utilizados: {', '.join(campos_preenchidos)}")

    if not campos_preenchidos:
        raise ValueError(
            "Não há cargo, especialidade ou região "
            "preenchidos para realizar a busca."
        )

    tabela = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//table[contains(@id, 'grdEditalFinal')]"
            )
        )
    )

    linhas = tabela.find_elements(By.XPATH, ".//tr")

    print(f"Linhas carregadas na tabela: {len(linhas)}")
    print("Procurando correspondência...")

    for numero_linha, linha in enumerate(linhas, start=1):
        try:
            celulas = linha.find_elements(By.XPATH, "./td")

            if len(celulas) < 6:
                continue

            cargo_site = (
                celulas[3].get_attribute("textContent") or ""
            ).strip()

            especialidade_site = (
                celulas[4].get_attribute("textContent") or ""
            ).strip()

            regiao_site = (
                celulas[5].get_attribute("textContent") or ""
            ).strip()

            encontrados = {
                "cargo": normalizar_cargo(cargo_site),
                "especialidade": normalizar_especialidade(
                    especialidade_site
                ),
                "regiao": normalizar_regiao(regiao_site),
            }

            comparacoes = {}

            for campo, esperado in campos_preenchidos.items():
                if campo == "cargo":
                    comparacoes[campo] = cargo_equivalente(
                        cargo,
                        cargo_site
                    )
                else:
                    comparacoes[campo] = (
                        encontrados[campo] == esperado
                    )

            if not all(comparacoes.values()):
                continue

            print(f"\nCorrespondência encontrada na linha {numero_linha}.")
            print(f"Cargo no site: {cargo_site}")
            print(f"Especialidade no site: {especialidade_site}")
            print(f"Região no site: {regiao_site}")
            print(f"Resultado das comparações: {comparacoes}")

            botoes = celulas[0].find_elements(
                By.XPATH,
                (
                    ".//input[@type='image']"
                    " | .//button"
                    " | .//input[@type='submit']"
                )
            )

            if not botoes:
                raise ValueError(
                    f"A linha {numero_linha} corresponde aos dados, "
                    "mas não possui botão de seleção."
                )

            botoes[0].click()

            print("Linha selecionada com sucesso.")
            return

        except StaleElementReferenceException:
            # A tabela foi atualizada pelo site.
            # Interrompe em vez de clicar em uma linha desatualizada.
            raise RuntimeError(
                "A tabela da Página 6 foi atualizada durante a busca. "
                "A seleção foi interrompida por segurança."
            )

    print("\nNenhuma correspondência encontrada.")
    print("Valores normalizados usados na busca:")
    print(esperados)

    raise ValueError(
        "Nenhuma linha correspondente foi encontrada na Página 6. "
        "Consulte os valores normalizados impressos acima."
    )


# ============================================================
# PÁGINA 7 — ABRIR A PESQUISA DE APROVADOS
# ============================================================

def abrir_pesquisa_aprovados(driver):
    """
    Clica na lupa ao lado do campo Nome da Página 7
    e aguarda a tela Pesquisa de Aprovados.
    """

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    espera = WebDriverWait(driver, 20)

    botao_lupa = espera.until(
        EC.element_to_be_clickable(
            (
                By.ID,
                "ctl00_ContentPlaceHolder1_btnPesquisaAprovado"
            )
        )
    )

    botao_lupa.click()

    espera.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[contains(normalize-space(.), "
                "'Pesquisa de Aprovados')]"
            )
        )
    )

    print("Página 8 aberta: Pesquisa de Aprovados.")


# ============================================================
# PÁGINA 8 — PESQUISAR E SELECIONAR O CANDIDATO
# ============================================================

def pesquisar_aprovado(driver, registro):
    """
    Pesquisa o candidato pelo nome, confere o CPF e clica
    no nome para avançar.

    A tabela pode ser atualizada dinamicamente. Por isso,
    os elementos são localizados novamente durante a espera,
    evitando referências a elementos antigos.
    """

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        StaleElementReferenceException,
        TimeoutException
    )

    espera = WebDriverWait(driver, 20)

    nome = str(registro.get("NOME") or "").strip()

    cpf = re.sub(
        r"\D",
        "",
        str(registro.get("CPF") or "")
    ).zfill(11)

    if not nome:
        raise ValueError(
            "O nome do candidato não foi informado na planilha."
        )

    if len(cpf) != 11:
        raise ValueError(
            f"CPF inválido para o candidato {nome}: {cpf}"
        )

    print("\n" + "=" * 60)
    print("PÁGINA 8 — PESQUISA DO CANDIDATO")
    print("=" * 60)
    print(f"Nome pesquisado: {nome}")
    print(f"CPF para conferência: {cpf}")

    # --------------------------------------------------------
    # 1. PREENCHER O CAMPO DE PESQUISA
    # --------------------------------------------------------

    campo_pesquisa = espera.until(
        EC.visibility_of_element_located(
            (
                By.ID,
                "ctl00_ContentPlaceHolder1_UserControlPesquisa_txtPesquisa"
            )
        )
    )

    campo_pesquisa.clear()
    campo_pesquisa.send_keys(nome)

    # --------------------------------------------------------
    # 2. CLICAR EM PESQUISAR
    # --------------------------------------------------------

    botao_pesquisar = espera.until(
        EC.element_to_be_clickable(
            (
                By.ID,
                "ctl00_ContentPlaceHolder1_UserControlPesquisa_btnPesquisar"
            )
        )
    )

    botao_pesquisar.click()

    print("Pesquisa enviada. Aguardando os resultados...")

    # --------------------------------------------------------
    # 3. LOCALIZAR E CONFERIR O CANDIDATO
    # --------------------------------------------------------

    def localizar_e_clicar(navegador):

        try:
            celulas_nome = navegador.find_elements(
                By.CSS_SELECTOR,
                'td[nomecoluna="DESC_NOME_A"]'
            )

            for celula_nome in celulas_nome:

                nome_resultado = (
                    celula_nome.get_attribute("textContent") or ""
                ).strip()

                if nome_resultado.casefold() != nome.casefold():
                    continue

                linha = celula_nome.find_element(
                    By.XPATH,
                    "./ancestor::tr[1]"
                )

                celulas_cpf = linha.find_elements(
                    By.CSS_SELECTOR,
                    'td[nomecoluna="NUMR_CPF_A"]'
                )

                if not celulas_cpf:
                    continue

                cpf_resultado = re.sub(
                    r"\D",
                    "",
                    celulas_cpf[0].get_attribute("textContent") or ""
                )

                if cpf_resultado != cpf:
                    continue

                # Nome e CPF conferem. Clica no nome.
                celula_nome.click()

                print(
                    "Candidato localizado e conferido:\n"
                    f"Nome: {nome}\n"
                    f"CPF: {cpf}"
                )

                print(
                    "Nome selecionado. Avançando para a próxima página."
                )

                return True

            # A tabela ainda pode estar sendo atualizada.
            return False

        except StaleElementReferenceException:
            # A página atualizou os elementos.
            # Na próxima tentativa, a tabela será consultada novamente.
            return False

    # --------------------------------------------------------
    # 4. AGUARDAR A LOCALIZAÇÃO E O CLIQUE
    # --------------------------------------------------------

    try:
        espera.until(localizar_e_clicar)

    except TimeoutException as erro:
        raise TimeoutException(
            "Não foi possível localizar e selecionar o candidato "
            f"na Página 8 após 20 segundos.\n"
            f"Nome esperado: {nome}\n"
            f"CPF esperado: {cpf}\n"
            "Verifique se o candidato aparece nos resultados "
            "da pesquisa."
        ) from erro

# ============================================================
# PÁGINA 9 — PREENCHIMENTO DOS DADOS DA ADMISSÃO
# ============================================================

def preencher_pagina9(driver, registro):
    """
    Preenche os campos da Página 9 do TCENET.

    Regras:
    - Não altera campos preenchidos automaticamente.
    - Nacionalidade: BRASILEIRA.
    - Escolaridade: SUPERIOR.
    - Aptidão: APTO.
    - Quitação Eleitoral: Sim.
    - Declaração de Bens: Sim.
    - Quitação Militar: Sim para masculino e Não para feminino.
    - Documentação de Nomeação: correspondência exata com
      EDITAL DE RESULTADO FINAL.
    - Não clica no botão Gravar.
    - Interrompe se houver dados ausentes ou ambíguos.
    """

    from datetime import date, datetime

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import (
        WebDriverWait,
        Select
    )
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException,
        UnexpectedAlertPresentException
    )

    espera = WebDriverWait(driver, 20)

    # ========================================================
    # FUNÇÕES AUXILIARES
    # ========================================================

    def obter_valor(coluna):
        """Obtém e padroniza um valor da planilha."""

        valor = registro.get(coluna)

        if valor is None:
            return ""

        if isinstance(valor, (datetime, date)):
            return valor.strftime("%d/%m/%Y")

        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))

        return str(valor).strip()

    def preencher_campo(identificador, coluna):
        """
        Preenche um campo editável.
        Ignora campos somente leitura ou desabilitados.
        """

        valor = obter_valor(coluna)

        if not valor:
            return

        campo = espera.until(
            EC.visibility_of_element_located(
                (By.ID, identificador)
            )
        )

        if campo.get_attribute("readonly") is not None:
            print(f"Campo automático ignorado: {coluna}")
            return

        if campo.get_attribute("disabled") is not None:
            print(f"Campo desabilitado ignorado: {coluna}")
            return

        campo.clear()
        campo.send_keys(valor)

    def interpretar_sim_nao(valor, coluna):
        """
        Converte valores conhecidos para S ou N.
        Não aceita valores ambíguos.
        """

        texto = normalizar_texto(valor)

        valores_sim = {
            "S",
            "SIM",
            "1",
            "TRUE",
            "VERDADEIRO"
        }

        valores_nao = {
            "N",
            "NAO",
            "0",
            "FALSE",
            "FALSO"
        }

        if texto in valores_sim:
            return "S"

        if texto in valores_nao:
            return "N"

        raise ValueError(
            f"Valor não reconhecido na coluna '{coluna}': "
            f"'{valor}'. Esperado: Sim ou Não."
        )

    def aguardar_postback():
        """
        Aguarda o TCENET estar pronto e sem atualização
        assíncrona ASP.NET em andamento.
        """

        def pagina_pronta(navegador):
            return navegador.execute_script("""
                if (document.readyState !== 'complete') {
                    return false;
                }

                if (
                    window.Sys
                    && Sys.WebForms
                    && Sys.WebForms.PageRequestManager
                ) {
                    return !Sys.WebForms.PageRequestManager
                        .getInstance()
                        .get_isInAsyncPostBack();
                }

                return true;
            """)

        espera.until(pagina_pronta)

    def selecionar_radio(nome_grupo, valor, coluna):
        """
        Seleciona um botão de opção conforme o grupo.
        Se surgir uma confirmação inesperada, cancela
        a confirmação e interrompe a automação.
        """

        if nome_grupo == "rbDeficiente":
            mapa = {
                "S": "ctl00_ContentPlaceHolder1_rbDeficiente_0",
                "N": "ctl00_ContentPlaceHolder1_rbDeficiente_1"
            }

            valor_sn = interpretar_sim_nao(valor, coluna)

            print("\n--- DIAGNÓSTICO ACUMULA CARGO ---")

            elementos = driver.find_elements(
            By.XPATH,
            "//*[contains(@id, 'Acumulacao') or contains(@name, 'rbAcumulacao')]"
            )

            for elemento in elementos:
                print(
                    "TAG:", elemento.tag_name,
                    "| ID:", elemento.get_attribute("id"),
                    "| NAME:", elemento.get_attribute("name"),
                    "| TYPE:", elemento.get_attribute("type"),
                    "| VALUE:", elemento.get_attribute("value"),
                    "| TEXTO:", elemento.text
                )

            print("--- FIM DO DIAGNÓSTICO ---\n")

        elif nome_grupo == "rbSexo":
            texto = normalizar_texto(valor)

            if texto in {"M", "MASCULINO", "HOMEM"}:
                id_radio = "ctl00_ContentPlaceHolder1_rbSexo_0"

            elif texto in {"F", "FEMININO", "MULHER"}:
                id_radio = "ctl00_ContentPlaceHolder1_rbSexo_1"

            else:
                raise ValueError(
                    f"Sexo não reconhecido na coluna '{coluna}': "
                    f"'{valor}'."
                )

            radio = espera.until(
                EC.element_to_be_clickable(
                    (By.ID, id_radio)
                )
            )

            if not radio.is_selected():
                radio.click()
                verificar_confirmacao()
                aguardar_postback()

            return

        elif nome_grupo == "rbAcumulacao":
            mapa = {
                "S": "ctl00_ContentPlaceHolder1_rbAcumulacao_0",
                "N": "ctl00_ContentPlaceHolder1_rbAcumulacao_1"
            }

            valor_sn = interpretar_sim_nao(valor, coluna)

        elif nome_grupo == "rbQuitacaoEleitoral":
            mapa = {
                "S": "ctl00_ContentPlaceHolder1_rbQuitacaoEleitoral_0",
                "N": "ctl00_ContentPlaceHolder1_rbQuitacaoEleitoral_1"
            }

            valor_sn = interpretar_sim_nao(valor, coluna)

        elif nome_grupo == "rbDeclaracaoBens":
            mapa = {
                "S": "ctl00_ContentPlaceHolder1_rbDeclaracaoBens_0",
                "N": "ctl00_ContentPlaceHolder1_rbDeclaracaoBens_1"
            }

            valor_sn = interpretar_sim_nao(valor, coluna)

        elif nome_grupo == "rbServicoMilitar":
            mapa = {
                "S": "ctl00_ContentPlaceHolder1_rbServicoMilitar_0",
                "N": "ctl00_ContentPlaceHolder1_rbServicoMilitar_1"
            }

            valor_sn = interpretar_sim_nao(valor, coluna)

        elif nome_grupo == "rbSubJudice":
            mapa = {
                "S": "ctl00_ContentPlaceHolder1_rbSubJudice_0",
                "N": "ctl00_ContentPlaceHolder1_rbSubJudice_1"
            }

            valor_sn = interpretar_sim_nao(valor, coluna)

        elif nome_grupo == "rbNegro":
            mapa = {
                "S": "ctl00_ContentPlaceHolder1_rbNegro_0",
                "N": "ctl00_ContentPlaceHolder1_rbNegro_1"
            }

            valor_sn = interpretar_sim_nao(valor, coluna)

        else:
            raise ValueError(
                f"Grupo de opções não configurado: {nome_grupo}"
            )

        id_radio = mapa[valor_sn]

        radio = espera.until(
            EC.element_to_be_clickable(
                (By.ID, id_radio)
            )
        )

        if radio.is_selected():
            print(
                f"{coluna}: opção já estava selecionada."
            )
            return

        radio.click()

        verificar_confirmacao()
        aguardar_postback()

        print(f"{coluna}: {'Sim' if valor_sn == 'S' else 'Não'}")

    def verificar_confirmacao():
        """
        Não aceita automaticamente caixas de confirmação.
        Se aparecer um alerta JavaScript, cancela e interrompe.
        """

        try:
            alerta = WebDriverWait(driver, 1).until(
                EC.alert_is_present()
            )

        except TimeoutException:
            return

        mensagem = alerta.text

        # Dismiss equivale a cancelar a confirmação JavaScript.
        alerta.dismiss()

        raise RuntimeError(
            "O TCENET exibiu uma confirmação inesperada. "
            "A confirmação foi cancelada para evitar uma "
            "alteração automática. Mensagem: "
            f"{mensagem}"
        )

    def selecionar_opcao_por_texto(
        identificador,
        texto_desejado,
        descricao
    ):
        """
        Seleciona uma opção por correspondência exata
        após normalização e aguarda a atualização da página.
        """

        elemento = espera.until(
            EC.element_to_be_clickable(
                (By.ID, identificador)
            )
        )

        seletor = Select(elemento)
        texto_normalizado = normalizar_texto(texto_desejado)

        for opcao in seletor.options:
            if normalizar_texto(opcao.text) == texto_normalizado:
                valor_opcao = opcao.get_attribute("value")

                seletor.select_by_value(valor_opcao)

                print(
                    f"{descricao}: {opcao.text.strip()}"
                )

                verificar_confirmacao()
                aguardar_postback()
                return

        raise ValueError(
            f"A opção '{texto_desejado}' não foi encontrada "
            f"no campo '{descricao}'."
        )

    def selecionar_uf(estado):
        """Seleciona a UF pelo nome ou pela sigla."""

        estado_normalizado = normalizar_texto(estado)

        siglas = {
            "AC": "ACRE",
            "AL": "ALAGOAS",
            "AP": "AMAPA",
            "AM": "AMAZONAS",
            "BA": "BAHIA",
            "CE": "CEARA",
            "DF": "DISTRITO FEDERAL",
            "ES": "ESPIRITO SANTO",
            "GO": "GOIAS",
            "MA": "MARANHAO",
            "MT": "MATO GROSSO",
            "MS": "MATO GROSSO DO SUL",
            "MG": "MINAS GERAIS",
            "PA": "PARA",
            "PB": "PARAIBA",
            "PR": "PARANA",
            "PE": "PERNAMBUCO",
            "PI": "PIAUI",
            "RJ": "RIO DE JANEIRO",
            "RN": "RIO GRANDE DO NORTE",
            "RS": "RIO GRANDE DO SUL",
            "RO": "RONDONIA",
            "RR": "RORAIMA",
            "SC": "SANTA CATARINA",
            "SP": "SAO PAULO",
            "SE": "SERGIPE",
            "TO": "TOCANTINS",
        }

        nome_estado = siglas.get(
            estado_normalizado,
            estado_normalizado
        )

        elemento = espera.until(
            EC.element_to_be_clickable(
                (
                    By.ID,
                    "ctl00_ContentPlaceHolder1_dpUF"
                )
            )
        )

        seletor = Select(elemento)

        # Primeiro, procura correspondência exata pelo nome.
        for opcao in seletor.options:
            texto_opcao = normalizar_texto(opcao.text)

            if texto_opcao == nome_estado:
                seletor.select_by_value(
                    opcao.get_attribute("value")
                )

                print(f"UF selecionada: {opcao.text.strip()}")

                verificar_confirmacao()
                aguardar_postback()
                return

        # Se não encontrou o nome exato, tenta identificar a sigla
        # ou o nome do estado dentro do texto da opção.
        for opcao in seletor.options:
            texto_opcao = normalizar_texto(opcao.text)

            corresponde_nome = nome_estado in texto_opcao
            corresponde_sigla = (
                estado_normalizado in siglas
                and estado_normalizado in texto_opcao.split()
            )

            if corresponde_nome or corresponde_sigla:
                seletor.select_by_value(
                    opcao.get_attribute("value")
                )

                print(f"UF selecionada: {opcao.text.strip()}")

                verificar_confirmacao()
                aguardar_postback()
                return
  
        # Diagnóstico: mostra as opções disponíveis caso não encontre.
        opcoes_disponiveis = [
            opcao.text.strip()
            for opcao in seletor.options
        ]

        raise ValueError(
            f"Não foi encontrada a UF '{estado}' no TCENET. "
            f"Opções disponíveis: {opcoes_disponiveis}"
        )

        
    def aguardar_municipio_disponivel(cidade):
        """
        Aguarda o município desejado aparecer na lista.
        """

        cidade_normalizada = normalizar_texto(cidade)

        def municipio_carregado(navegador):
            elemento = navegador.find_element(
                By.ID,
                "ctl00_ContentPlaceHolder1_dpMunicipio"
            )

            seletor = Select(elemento)

            return any(
                normalizar_texto(opcao.text) == cidade_normalizada
                for opcao in seletor.options
            )

        espera.until(municipio_carregado)

        print(f"Município disponível: {cidade}")

    # ========================================================
    # ETAPA 1 — VALIDAR DADOS ESSENCIAIS
    # ========================================================

    obrigatorios = {
        "RG": "RG",
        "Órgão Expeditor": "ORGAO_EXPEDITOR",
        "PcD": "PCD",
        "Nome da Mãe": "NOME DA MÃE",
        "Sexo": "SEXO",
        "Data de Nascimento": "NASCIMENTO",
        "UF": "ESTADO"
    }

    ausentes = [
        nome_campo
        for nome_campo, coluna in obrigatorios.items()
        if not obter_valor(coluna)
    ]

    if ausentes:
        raise ValueError(
            "Preenchimento interrompido. Faltam dados "
            "essenciais na planilha: "
            + ", ".join(ausentes)
        )

    # Valida valores Sim/Não antes de interagir com o site.
    interpretar_sim_nao(
        obter_valor("PCD"),
        "PCD"
    )

    if obter_valor("ACUMULA CARGO"):
        interpretar_sim_nao(
            obter_valor("ACUMULA CARGO"),
            "ACUMULA CARGO"
        )

    if obter_valor("SUB JUDICE"):
        interpretar_sim_nao(
            obter_valor("SUB JUDICE"),
            "SUB JUDICE"
        )

    if obter_valor("NEGRO"):
        interpretar_sim_nao(
            obter_valor("NEGRO"),
            "NEGRO"
        )

    print("\n" + "=" * 60)
    print("PÁGINA 9 — PREENCHIMENTO DA ADMISSÃO")
    print("=" * 60)

    espera.until(
        EC.presence_of_element_located(
            (By.ID, "ctl00_ContentPlaceHolder1_txtNome")
        )
    )

    # ========================================================
    # ETAPA 2 — CONFIRMAR CAMPOS AUTOMÁTICOS
    # ========================================================

    campos_automaticos = [
        "ctl00_ContentPlaceHolder1_txtNome",
        "ctl00_ContentPlaceHolder1_txtCPF",
        "ctl00_ContentPlaceHolder1_txtOrgaoLotacao",
        "ctl00_ContentPlaceHolder1_txtDataNomeacao"
    ]

    for identificador in campos_automaticos:
        espera.until(
            EC.presence_of_element_located(
                (By.ID, identificador)
            )
        )

    print(
        "Campos automáticos identificados. "
        "A automação não tentará digitá-los."
    )

    # ========================================================
    # ETAPA 3 — DADOS PESSOAIS
    # ========================================================

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtRG",
        "RG"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtOrgExpedidor",
        "ORGAO_EXPEDITOR"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtNomeMae",
        "NOME DA MÃE"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtNomePai",
        "NOME DO PAI"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtFone",
        "TELEFONE"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtEndereco",
        "ENDEREÇO"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtBairro",
        "BAIRRO"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtCEP",
        "CEP"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtDataNascimento",
        "NASCIMENTO"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtEmail",
        "E-MAIL USUÁRIO EXTERNO"
    )

    preencher_campo(
        "ctl00_ContentPlaceHolder1_txtDataPosse",
        "DATA POSSE"
    )

    # ========================================================
    # ETAPA 4 — PcD E SEXO
    # ========================================================

    selecionar_radio(
        "rbDeficiente",
        obter_valor("PCD"),
        "PCD"
    )

    selecionar_radio(
        "rbSexo",
        obter_valor("SEXO"),
        "SEXO"
    )

    # ========================================================
    # ETAPA 5 — UF E MUNICÍPIO
    # ========================================================

    estado = obter_valor("ESTADO")
    cidade = obter_valor("CIDADE RESIDENCIA")

    selecionar_uf(estado)

    if cidade:
        aguardar_municipio_disponivel(cidade)

        selecionar_opcao_por_texto(
            "ctl00_ContentPlaceHolder1_dpMunicipio",
            cidade,
            "Município"
        )
    else:
        print(
            "Aviso: a coluna CIDADE RESIDENCIA está vazia."
        )

    # ========================================================
    # ETAPA 6 — NACIONALIDADE E ESCOLARIDADE
    # ========================================================

    selecionar_opcao_por_texto(
        "ctl00_ContentPlaceHolder1_dpNacionalidade",
        "BRASILEIRA",
        "Nacionalidade"
    )

    selecionar_opcao_por_texto(
        "ctl00_ContentPlaceHolder1_dpEscolaridade",
        "SUPERIOR",
        "Escolaridade"
    )

    # ========================================================
    # ETAPA 7 — ESTADO CIVIL, SE DISPONÍVEL
    # ========================================================

    estado_civil = obter_valor("ESTADO CIVIL")

    if estado_civil:
        selecionar_opcao_por_texto(
            "ctl00_ContentPlaceHolder1_dpEstadoCivil",
            estado_civil,
            "Estado Civil"
        )

    # ========================================================
    # ETAPA 8 — ACUMULAÇÃO DE CARGO
    # ========================================================

    acumulacao = obter_valor("ACUMULA CARGO")

    if acumulacao:
        print(
            "ACUMULA CARGO: mantendo a opção padrão do TCENET "
            "(Não), sem alterar o campo."
        )

    # ========================================================
    # ETAPA 9 — APTIDÃO, QUITAÇÕES E DECLARAÇÕES
    # ========================================================

    selecionar_opcao_por_texto(
        "ctl00_ContentPlaceHolder1_dpAptidao",
        "APTO",
        "Aptidão Física/Mental"
    )

    selecionar_radio(
        "rbQuitacaoEleitoral",
        "S",
        "Quitação Eleitoral"
    )

    selecionar_radio(
        "rbDeclaracaoBens",
        "S",
        "Declaração de Bens"
    )

    sexo_normalizado = normalizar_texto(
        obter_valor("SEXO")
    )

    if sexo_normalizado in {"M", "MASCULINO", "HOMEM"}:
        valor_militar = "S"

    elif sexo_normalizado in {"F", "FEMININO", "MULHER"}:
        valor_militar = "N"

    else:
        raise ValueError(
            "Não foi possível determinar a Quitação Militar "
            "a partir do sexo informado."
        )

    selecionar_radio(
        "rbServicoMilitar",
        valor_militar,
        "Quitação Militar"
    )

    # ========================================================
    # ETAPA 10 — SUB JUDICE E NEGRO
    # ========================================================

    sub_judice = obter_valor("SUB JUDICE")

    if sub_judice:
        selecionar_radio(
            "rbSubJudice",
            sub_judice,
            "SUB JUDICE"
        )

    negro = obter_valor("NEGRO")

    if negro:
        selecionar_radio(
            "rbNegro",
            negro,
            "NEGRO"
        )

    # ========================================================
    # ETAPA 11 — DOCUMENTAÇÃO DE NOMEAÇÃO
    # ========================================================

    edital = obter_valor("DOCUMENTO DE NOMEAÇÃO")

    if not edital:
        raise ValueError(
            "A coluna DOCUMENTO DE NOMEAÇÃO está vazia. "
            "Não é possível selecionar a documentação."
        )

    campo_documento = espera.until(
        EC.element_to_be_clickable(
            (
                By.ID,
                "ctl00_ContentPlaceHolder1_dpDocumentoNomeacao"
            )
        )
    )

    seletor_documento = Select(campo_documento)

    opcao_encontrada = False

    for opcao in seletor_documento.options:
        # A regra deste campo é igualdade exata,
        # sem normalização do texto.
        if opcao.text.strip() == edital.strip():
            seletor_documento.select_by_value(
                opcao.get_attribute("value")
            )

            opcao_encontrada = True
            break

    if not opcao_encontrada:
        raise ValueError(
            "Não foi encontrada uma opção de Documentação "
            "de Nomeação com texto exatamente igual a "
            f"'{edital}'. Nenhuma gravação foi realizada."
        )

    aguardar_postback()

    # ========================================================
    # ETAPA 12 — DATA DE NOMEAÇÃO AUTOMÁTICA
    # ========================================================

    def data_nomeacao_preenchida(navegador):
        campo = navegador.find_element(
            By.ID,
            "ctl00_ContentPlaceHolder1_txtDataNomeacao"
        )

        return bool(
            (campo.get_attribute("value") or "").strip()
        )

    espera.until(data_nomeacao_preenchida)

    print(
        "Documentação de Nomeação selecionada e "
        "Data de Nomeação preenchida pelo sistema."
    )

    
    
    
    
    # ========================================================
    # ETAPA 13 — NATURALIDADE, ACUMULAÇÃO E GRAVAR
    # ========================================================

    cidade_naturalidade = obter_valor("NATURALIDADE/CIDADE")
    estado_naturalidade = obter_valor("NATURALIDADE/ESTADO")

    if not cidade_naturalidade:
        raise ValueError(
            "A coluna NATURALIDADE/CIDADE está vazia na planilha. "
            "Gravação cancelada."
        )

    naturalidade = str(cidade_naturalidade).strip()

    print(f"Naturalidade — cidade: {naturalidade}")
    print(f"Naturalidade — estado: {estado_naturalidade or 'Não informado'}")

    # 1. Confirmar Acumulação = Não.
    radio_nao = espera.until(
        EC.presence_of_element_located(
            (By.ID, "ctl00_ContentPlaceHolder1_rbAcumulacao_1")
        )
    )

    if not radio_nao.is_selected():
        radio_nao.click()
        aguardar_postback()

        radio_nao = espera.until(
            EC.presence_of_element_located(
                (By.ID, "ctl00_ContentPlaceHolder1_rbAcumulacao_1")
            )
        )

    if not radio_nao.is_selected():
        raise RuntimeError(
            "Acumulação = Não não foi confirmada. Gravação cancelada."
        )

    print("Acumulação = Não confirmada.")

    
    # 2. Abrir a pesquisa de Naturalidade.
    botao_pesquisa = espera.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_ContentPlaceHolder1_btnPesquisaNaturalidade")
        )
    )
    botao_pesquisa.click()

    # DIAGNÓSTICO TEMPORÁRIO
    print("Janelas abertas após clicar na pesquisa:", driver.window_handles)
    print("Janela atual:", driver.current_window_handle)
    print("URL atual:", driver.current_url)

    # 3. Digitar a Naturalidade no campo da pesquisa.
    campo_pesquisa = espera.until(
        EC.visibility_of_element_located(
            (
                By.ID,
                "ctl00_ContentPlaceHolder1_UserControlPesquisa_txtPesquisa"
            )
        )
    )
    campo_pesquisa.clear()
    campo_pesquisa.send_keys(naturalidade)


    # 4. Executar a pesquisa.
    botao_pesquisar = espera.until(
        EC.element_to_be_clickable(
            (
                By.ID,
                "ctl00_ContentPlaceHolder1_UserControlPesquisa_btnPesquisar"
            )
        )
    )
    botao_pesquisar.click()

    print(f"Pesquisa enviada para Naturalidade: {naturalidade}")

    
    
    # 5. Selecionar o município pela cidade E pela UF

    cidade_procurada = str(cidade_naturalidade or "").strip().upper()
    uf_procurada = str(estado_naturalidade or "").strip().upper()

    # Aguarda a tabela de resultados da pesquisa
    espera.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "td[nomecoluna='nome_municipio_a']")
        )
    )

    
    
    # 5. Selecionar o município pela cidade E pela UF,
    # ignorando diferenças de acentuação.

    import unicodedata

    def normalizar_texto_naturalidade(valor):
        texto = str(valor or "").strip()
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(
            caractere for caractere in texto
            if not unicodedata.combining(caractere)
        )
        return " ".join(texto.upper().split())

    cidade_procurada = normalizar_texto(cidade_naturalidade)
    uf_procurada = normalizar_texto(estado_naturalidade)

    def municipio_encontrado(driver):
        celulas = driver.find_elements(
            By.CSS_SELECTOR,
            "td[nomecoluna='nome_municipio_a']"
        )

        for celula in celulas:
            try:
                nome = normalizar_texto(
                    celula.get_attribute("textContent")
                )

                linha = celula.find_element(
                    By.XPATH, "./ancestor::tr[1]"
                )

                celula_uf = linha.find_element(
                    By.CSS_SELECTOR,
                    "td[nomecoluna='desc_abreviac_a']"
                )

                uf = normalizar_texto(
                    celula_uf.get_attribute("textContent")
                )

                if nome == cidade_procurada and uf == uf_procurada:
                    return celula

            except StaleElementReferenceException:
                continue

        return False

    resultado = espera.until(municipio_encontrado)

    # Clica no resultado que corresponde à cidade E à UF.
    driver.execute_script(
        "arguments[0].click();", resultado
    )

    
    # DIAGNÓSTICO TEMPORÁRIO
    print("Janelas abertas após selecionar município:", driver.window_handles)
    print("Janela atual após seleção:", driver.current_window_handle)
    print("URL após seleção:", driver.current_url)


    
    
    # 6. Diagnosticar o campo Naturalidade após a seleção.

    campo_naturalidade = espera.until(
        EC.presence_of_element_located(
            (By.ID, "ctl00_ContentPlaceHolder1_txtNaturalidade")
        )
    )

    print(
        "Naturalidade — value:",
        repr(campo_naturalidade.get_attribute("value"))
    )
    print(
        "Naturalidade — atributo value:",
        repr(campo_naturalidade.get_dom_attribute("value"))
    )
    print(
        "Naturalidade — texto exibido:",
        repr(campo_naturalidade.get_attribute("textContent"))
    )
    print(
        "Naturalidade — HTML:",
        campo_naturalidade.get_attribute("outerHTML")
    )



    
    # 7. Clicar em Gravar.
    try:
        espera.until(
            EC.element_to_be_clickable(
                (By.ID, "ctl00_ContentPlaceHolder1_btnGravar")
            )
        ).click()

    except StaleElementReferenceException:
        espera.until(
            EC.element_to_be_clickable(
                (By.ID, "ctl00_ContentPlaceHolder1_btnGravar")
            )
        ).click()

    
    print("Clique em Gravar executado.")

    
    # O TCENET confirma a gravação por meio de um alerta.
    try:
        alerta = WebDriverWait(driver, 10).until(
            EC.alert_is_present()
        )

        # Ler a mensagem ANTES de aceitar o alerta.
        mensagem = alerta.text.strip()

        print(f"Mensagem do TCENET: {mensagem}")

        mensagem_normalizada = mensagem.casefold()

        if (
            "admissão alterada com sucesso" in mensagem_normalizada
            or "admissão cadastrada com sucesso" in mensagem_normalizada
        ):
            # Confirmar o alerta de sucesso.
            alerta.accept()

            print("Gravação confirmada pelo TCENET.")

        else:
            # Não aceitar uma mensagem desconhecida automaticamente.
            alerta.dismiss()

            raise RuntimeError(
                f"Mensagem inesperada após Gravar: {mensagem}"
            )

    except TimeoutException:
        raise RuntimeError(
            "O TCENET não apresentou a confirmação esperada "
            "após clicar em Gravar. Verifique a tela antes de continuar."
        )


# ============================================================
# ANEXOS — LOCALIZAR E IMPORTAR DOCUMENTO PELO CPF
# ============================================================


def anexar_documento(driver, registro):
    import os
    import glob
    import re
    from selenium.common.exceptions import TimeoutException

    espera = WebDriverWait(driver, 20)
    pasta_anexos = r"X:\GEAP\Gerencia\TCE\Anexos"

    # Identifica o PDF pelo CPF do candidato.
    cpf = re.sub(r"\D", "", str(registro.get("CPF") or ""))

    if not cpf:
        raise ValueError(
            "Não foi possível identificar o CPF do candidato "
            "para localizar o anexo."
        )

    if not os.path.isdir(pasta_anexos):
        raise FileNotFoundError(
            f"A pasta de anexos não foi encontrada: {pasta_anexos}"
        )

    arquivos = [
        caminho
        for caminho in glob.glob(os.path.join(pasta_anexos, "*"))
        if os.path.isfile(caminho)
        and os.path.basename(caminho).startswith(cpf)
        and caminho.lower().endswith(".pdf")
    ]

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum PDF iniciado pelo CPF {cpf} foi encontrado "
            f"em {pasta_anexos}"
        )

    if len(arquivos) > 1:
        raise RuntimeError(
            f"Foram encontrados vários PDFs para o CPF {cpf}. "
            "Verifique os arquivos antes de continuar:\n"
            + "\n".join(arquivos)
        )

    arquivo = os.path.abspath(arquivos[0])
    print(f"PDF localizado: {arquivo}")

    # 1. Abrir a tela de anexos.
    espera.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_ContentPlaceHolder1_btnAnexo")
        )
    ).click()

    print("Botão Anexos acionado.")

    # 2. Selecionar o arquivo PDF.
    campo_arquivo = espera.until(
        EC.presence_of_element_located(
            (By.ID, "ctl00_ContentPlaceHolder1_FileUplArquivo")
        )
    )
    campo_arquivo.send_keys(arquivo)

    print("PDF selecionado para importação.")

    # 3. Importar o documento.
    espera.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_ContentPlaceHolder1_btnImportar")
        )
    ).click()

    print("Botão Importar acionado.")

    # Se o TCENET apresentar um alerta após a importação,
    # aceita-o antes de continuar.
    try:
        alerta = WebDriverWait(driver, 3).until(
            EC.alert_is_present()
        )
        print(f"Mensagem após importação: {alerta.text}")
        alerta.accept()
    except TimeoutException:
        pass

    # 4. Retornar da tela de anexos para a Página 9.
    espera.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_ContentPlaceHolder1_Button1")
        )
    ).click()

    espera.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_ContentPlaceHolder1_btnRetornar")
        )
    )

    print("Retorno à Página 9 concluído.")

    # 5. Retornar da Página 9 para a tela anterior.
    driver.find_element(
        By.ID, "ctl00_ContentPlaceHolder1_btnRetornar"
    ).click()

    print("Segundo Retornar acionado.")




# ============================================================
# EXECUTAR A AUTOMAÇÃO
# ============================================================



def executar_automacao(dados_unidade, edital):
    """
    Processa os candidatos do edital e permite retomar o trabalho.

    PRONTO = OK / STATUS ANEXO = SIM:
        Candidato concluído; pula.

    PRONTO = OK / STATUS ANEXO diferente de SIM:
        Cadastro já gravado; tenta concluir o anexo.

    Outros status:
        Executa o fluxo completo de cadastro e anexo.
    """

    driver = abrir_tcenet()

    try:
        fazer_login(
            driver,
            dados_unidade["USER"],
            dados_unidade["SENHA"]
        )

        selecionar_edital(driver, edital)

        registros = carregar_registros_por_edital(edital)

        if not registros:
            raise ValueError(
                f"Nenhum registro encontrado para o edital '{edital}'."
            )

        total = len(registros)
        sucessos = 0
        falhas = 0
        pulados = 0

        print("\n" + "=" * 65)
        print("PROCESSAMENTO DE CANDIDATOS")
        print("=" * 65)
        print(f"Edital: {edital}")
        print(f"Total de candidatos: {total}")

        for indice, registro in enumerate(registros, start=1):
            nome = str(registro.get("NOME", "")).strip()
            cpf = str(registro.get("CPF", "")).strip()

            cargo = registro.get("CARGO/EMPREGO", "")
            especialidade = registro.get("ESPECIALIDADE", "")
            regiao = registro.get("REGIÃO", "")

            print("\n" + "=" * 65)
            print(f"CANDIDATO {indice} DE {total}")
            print("=" * 65)
            print(f"Nome: {nome}")
            print(f"CPF: {cpf}")

            try:
                # Confere o progresso salvo na planilha.
                pronto, status_anexo = consultar_status_planilha(
                    registro
                )

                # Caso 1: candidato já concluído.
                if pronto == "OK" and status_anexo == "SIM":
                    pulados += 1
                    print(
                        "Candidato já concluído "
                        "(cadastro e anexo). Pulando."
                    )
                    continue

                # Caso 2: cadastro salvo, mas anexo pendente.
                somente_anexo = pronto == "OK"

                if somente_anexo:
                    print(
                        "Cadastro já gravado. "
                        "Será tentado somente o anexo."
                    )

                print(f"Cargo/Emprego: {cargo}")
                print(f"Especialidade: {especialidade}")
                print(f"Região: {regiao}")

                # Página 6 — selecionar cargo, especialidade e região.
                selecionar_linha_pagina6(
                    driver,
                    cargo=cargo,
                    especialidade=especialidade,
                    regiao=regiao
                )

                # Página 7 — abrir pesquisa.
                abrir_pesquisa_aprovados(driver)

                # Página 8 — localizar e conferir nome e CPF.
                pesquisar_aprovado(driver, registro)

                if somente_anexo:
                    # Não preencher nem gravar novamente.
                    # Pressupõe que selecionar o candidato existente
                    # abra o registro na Página 9.
                    anexar_documento(driver, registro)

                    atualizar_status_planilha(
                        registro,
                        pronto="OK",
                        status_anexo="SIM"
                    )

                    sucessos += 1
                    print(
                        f"\nSUCESSO: {nome} — anexo concluído "
                        "em cadastro já existente."
                    )

                else:
                    # Fluxo normal para cadastro ainda não concluído.
                    preencher_pagina9(driver, registro)

                    # A gravação foi confirmada pelo TCENET.
                    # Salvar o progresso ANTES de anexar.
                    atualizar_status_planilha(
                        registro,
                        pronto="OK",
                        status_anexo="NÃO"
                    )

                    anexar_documento(driver, registro)

                    atualizar_status_planilha(
                        registro,
                        pronto="OK",
                        status_anexo="SIM"
                    )

                    sucessos += 1
                    print(
                        f"\nSUCESSO: {nome} — cadastro e anexo concluídos."
                    )

            except Exception as erro:
                falhas += 1

                print(f"\nFALHA: {nome} — CPF {cpf}")
                print(f"Erro: {type(erro).__name__}: {erro}")

                # Não apagar o progresso se o cadastro já foi gravado.
                try:
                    pronto_atual, anexo_atual = (
                        consultar_status_planilha(registro)
                    )

                    if pronto_atual != "OK":
                        atualizar_status_planilha(
                            registro,
                            pronto="NÃO",
                            status_anexo="NÃO"
                        )

                    elif anexo_atual != "SIM":
                        print(
                            "Cadastro permanece marcado como OK. "
                            "O anexo poderá ser tentado novamente."
                        )

                except Exception as erro_planilha:
                    print(
                        "ERRO AO CONSULTAR/ATUALIZAR STATUS: "
                        f"{erro_planilha}"
                    )

                # Tentar recuperar a Página 6 para o próximo candidato.
                if indice < total:
                    pagina6_recuperada = False

                    for tentativa in range(1, 4):
                        try:
                            driver.find_element(
                                "xpath",
                                "//table[contains(@id, 'grdEditalFinal')]"
                            )

                            pagina6_recuperada = True
                            break

                        except Exception:
                            try:
                                print(
                                    "Tentando recuperar a Página 6 "
                                    f"(tentativa {tentativa}/3)..."
                                )

                                driver.back()

                                WebDriverWait(driver, 10).until(
                                    lambda d: len(
                                        d.find_elements(
                                            "xpath",
                                            "//table[contains(@id, "
                                            "'grdEditalFinal')]"
                                        )
                                    ) > 0
                                )

                                pagina6_recuperada = True
                                break

                            except Exception:
                                continue

                    if not pagina6_recuperada:
                        raise RuntimeError(
                            f"O candidato {nome} falhou e não foi "
                            "possível recuperar a Página 6. "
                            "A automação foi interrompida por segurança."
                        ) from erro

                    print(
                        "Página 6 recuperada. "
                        "Continuando para o próximo candidato."
                    )

            finally:
                print(f"Progresso examinado: {indice}/{total}")

        print("\n" + "=" * 65)
        print("PROCESSAMENTO DA PLANILHA CONCLUÍDO")
        print(f"Total de candidatos: {total}")
        print(f"Concluídos nesta execução: {sucessos}")
        print(f"Já concluídos e pulados: {pulados}")
        print(f"Com falha nesta execução: {falhas}")
        print("=" * 65)

    finally:
        print("\nEncerrando o navegador...")
        driver.quit()
        print("Navegador encerrado.")
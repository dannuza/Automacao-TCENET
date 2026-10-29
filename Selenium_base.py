# ==================================================================================================
# selenium_base.py
# Base reutilizável para automações Selenium
# ==================================================================================================

from __future__ import annotations

import time
import logging
import traceback
import subprocess

from typing import Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common import exceptions
from selenium.common.exceptions import NoSuchElementException

# ==================================================================================================
# TIPOS
# ==================================================================================================

Locator = Tuple[str, str]


# ==================================================================================================
# CONFIGURAÇÕES PADRÃO
# ==================================================================================================

DEFAULT_TIMEOUT = 20
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 1

_logger_configurado = False


# ==================================================================================================
# LOG
# ==================================================================================================

def configurar_log(
    nome_arquivo: Optional[str] = None,
    nivel: int = logging.INFO
) -> None:
    """
    Configura o sistema de logs da automação.

    Se nome_arquivo não for informado, os logs serão enviados apenas para o console.
    """

    global _logger_configurado

    if _logger_configurado:
        return

    handlers = [logging.StreamHandler()]

    if nome_arquivo:
        caminho = Path(nome_arquivo)
        caminho.parent.mkdir(parents=True, exist_ok=True)

        handlers.append(
            logging.FileHandler(
                caminho,
                encoding="utf-8"
            )
        )

    logging.basicConfig(
        level=nivel,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=handlers
    )

    _logger_configurado = True


logger = logging.getLogger(__name__)


# ==================================================================================================
# CRIAÇÃO DO CHROME
# ==================================================================================================

def iniciar_chrome(
    download_path: str = None,
    headless: bool = False,
    implicit_wait: float = 3
) -> webdriver.Chrome:

    options = webdriver.ChromeOptions()

    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    options.add_experimental_option(
        "excludeSwitches",
        ["enable-logging"]
    )

    if headless:
        options.add_argument("--headless")

    if download_path:
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": download_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
        )

    service = Service(
        log_output=subprocess.DEVNULL
    )

    driver = webdriver.Chrome(
        options=options,
        service=service
    )

    global global_implicit_wait

    global_implicit_wait = implicit_wait

    driver.implicitly_wait(implicit_wait)

    return driver

    # ----------------------------------------------------------------------------------------------
    # Configurações gerais
    # ----------------------------------------------------------------------------------------------

    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # Evita mensagens desnecessárias do ChromeDriver.
    options.add_experimental_option(
        "excludeSwitches",
        ["enable-logging"]
    )

    # ----------------------------------------------------------------------------------------------
    # Headless
    # ----------------------------------------------------------------------------------------------

    if headless:
        options.add_argument("--headless=new")

    # ----------------------------------------------------------------------------------------------
    # Downloads
    # ----------------------------------------------------------------------------------------------

    if download_path:

        pasta_download = Path(download_path)
        pasta_download.mkdir(parents=True, exist_ok=True)

        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": str(
                    pasta_download.absolute()
                ),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
            }
        )

    # ----------------------------------------------------------------------------------------------
    # Criação do navegador
    # ----------------------------------------------------------------------------------------------

    try:

        driver = webdriver.Chrome(
            options=options,
            service=webdriver.ChromeService(
                log_output=subprocess.DEVNULL
            )
        )

        driver.implicitly_wait(implicit_wait)

        logger.info("Chrome iniciado com sucesso.")

        return driver

    except WebDriverException as erro:

        logger.exception(
            "Não foi possível iniciar o Chrome."
        )

        raise erro


# ==================================================================================================
# CRIAÇÃO DO FIREFOX
# ==================================================================================================

def iniciar_firefox(
    download_path: Optional[str] = None,
    headless: bool = False,
    implicit_wait: float = 0
) -> webdriver.Firefox:
    """
    Inicia o Firefox configurado para automação.
    """

    options = webdriver.FirefoxOptions()

    # ----------------------------------------------------------------------------------------------
    # Headless
    # ----------------------------------------------------------------------------------------------

    if headless:
        options.add_argument("--headless")

    # ----------------------------------------------------------------------------------------------
    # Downloads
    # ----------------------------------------------------------------------------------------------

    if download_path:

        pasta_download = Path(download_path)
        pasta_download.mkdir(parents=True, exist_ok=True)

        options.set_preference(
            "browser.download.folderList",
            2
        )

        options.set_preference(
            "browser.download.dir",
            str(pasta_download.absolute())
        )

        options.set_preference(
            "browser.download.manager.showWhenStarting",
            False
        )

        options.set_preference(
            "browser.helperApps.neverAsk.saveToDisk",
            "application/pdf"
        )

    # ----------------------------------------------------------------------------------------------
    # Criação
    # ----------------------------------------------------------------------------------------------

    try:

        driver = webdriver.Firefox(
            options=options
        )

        driver.maximize_window()

        driver.implicitly_wait(
            implicit_wait
        )

        logger.info("Firefox iniciado com sucesso.")

        return driver

    except WebDriverException as erro:

        logger.exception(
            "Não foi possível iniciar o Firefox."
        )

        raise erro


# ==================================================================================================
# ESPERAS
# ==================================================================================================

def esperar_presenca(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> WebElement:
    """
    Aguarda o elemento existir no DOM.
    """

    return WebDriverWait(
        driver,
        timeout
    ).until(
        EC.presence_of_element_located(locator)
    )


def esperar_visibilidade(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> WebElement:
    """
    Aguarda o elemento estar visível.
    """

    return WebDriverWait(
        driver,
        timeout
    ).until(
        EC.visibility_of_element_located(locator)
    )


def esperar_clicavel(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> WebElement:
    """
    Aguarda o elemento estar visível e clicável.
    """

    return WebDriverWait(
        driver,
        timeout
    ).until(
        EC.element_to_be_clickable(locator)
    )


def esperar_invisibilidade(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """
    Aguarda um elemento desaparecer.
    """

    return WebDriverWait(
        driver,
        timeout
    ).until(
        EC.invisibility_of_element_located(locator)
    )


def esperar_texto(
    driver: webdriver.Remote,
    locator: Locator,
    texto: str,
    timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """
    Aguarda determinado texto aparecer no elemento.
    """

    return WebDriverWait(
        driver,
        timeout
    ).until(
        EC.text_to_be_present_in_element(
            locator,
            texto
        )
    )


# ==================================================================================================
# LOCALIZAÇÃO
# ==================================================================================================

def encontrar(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT,
    visivel: bool = False
) -> WebElement:
    """
    Localiza um elemento.

    Args:
        visivel:
            Se True, aguarda o elemento ficar visível.
    """

    if visivel:

        return esperar_visibilidade(
            driver,
            locator,
            timeout
        )

    return esperar_presenca(
        driver,
        locator,
        timeout
    )


def encontrar_por_texto(
    driver: webdriver.Remote,
    texto: str,
    timeout: int = DEFAULT_TIMEOUT,
    exato: bool = False
) -> WebElement:
    """
    Localiza um elemento pelo texto.

    Evita depender de caminhos absolutos do HTML.
    """

    if exato:

        xpath = f"//*[normalize-space()={_xpath_string(texto)}]"

    else:

        xpath = (
            f"//*[contains("
            f"normalize-space(), "
            f"{_xpath_string(texto)}"
            f")]"
        )

    return esperar_presenca(
        driver,
        (By.XPATH, xpath),
        timeout
    )


def _xpath_string(texto: str) -> str:
    """
    Converte uma string Python para uma expressão XPath segura.

    Isso é importante quando o texto possui aspas.
    """

    if "'" not in texto:

        return f"'{texto}'"

    if '"' not in texto:

        return f'"{texto}"'

    partes = texto.split("'")

    return (
        "concat("
        + ", \"'\", ".join(
            f"'{parte}'"
            for parte in partes
        )
        + ")"
    )


# ==================================================================================================
# CLIQUE
# ==================================================================================================

def clicar(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT,
    tentativas: int = DEFAULT_RETRIES,
    intervalo: float = DEFAULT_RETRY_DELAY
) -> bool:
    """
    Localiza e clica em um elemento.

    Utiliza WebDriverWait antes do clique e tenta novamente
    caso o site esteja instável.
    """

    ultimo_erro = None

    for tentativa in range(1, tentativas + 1):

        try:

            elemento = esperar_clicavel(
                driver,
                locator,
                timeout
            )

            # Tenta trazer o elemento para a tela.
            driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center',
                    inline: 'center'
                });
                """,
                elemento
            )

            elemento.click()

            logger.info(
                "Clique realizado: %s",
                locator
            )

            return True

        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            StaleElementReferenceException,
            TimeoutException,
        ) as erro:

            ultimo_erro = erro

            logger.warning(
                "Falha no clique. Tentativa %s/%s: %s",
                tentativa,
                tentativas,
                locator
            )

            time.sleep(intervalo)

    logger.error(
        "Não foi possível clicar em %s.",
        locator
    )

    if ultimo_erro:
        raise ultimo_erro

    return False


def clicar_js(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """
    Realiza clique utilizando JavaScript.

    Deve ser utilizado somente quando o clique normal do Selenium
    não funcionar.
    """

    elemento = encontrar(
        driver,
        locator,
        timeout
    )

    driver.execute_script(
        "arguments[0].click();",
        elemento
    )

    logger.info(
        "Clique JavaScript realizado: %s",
        locator
    )

    return True


# ==================================================================================================
# CAMPOS DE TEXTO
# ==================================================================================================

def preencher(
    driver: webdriver.Remote,
    locator: Locator,
    valor: Union[str, int, float],
    timeout: int = DEFAULT_TIMEOUT,
    verificar: bool = True
) -> bool:
    """
    Limpa um campo e insere um valor.
    """

    elemento = esperar_visibilidade(
        driver,
        locator,
        timeout
    )

    valor = str(valor)

    elemento.clear()
    elemento.send_keys(valor)

    if verificar:

        valor_atual = elemento.get_attribute(
            "value"
        )

        if valor_atual != valor:

            raise RuntimeError(
                f"Valor não foi inserido corretamente em {locator}. "
                f"Esperado: {valor!r} | Atual: {valor_atual!r}"
            )

    logger.info(
        "Campo preenchido: %s",
        locator
    )

    return True


def limpar(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """
    Limpa um campo.
    """

    elemento = esperar_visibilidade(
        driver,
        locator,
        timeout
    )

    elemento.clear()

    return True


# ==================================================================================================
# SELECT
# ==================================================================================================

def selecionar(
    driver: webdriver.Remote,
    locator: Locator,
    texto: Optional[str] = None,
    valor: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """
    Seleciona uma opção de um <select> HTML.
    """

    elemento = esperar_visibilidade(
        driver,
        locator,
        timeout
    )

    campo = Select(elemento)

    if valor is not None:

        campo.select_by_value(valor)

        logger.info(
            "Select selecionado por value: %s",
            valor
        )

    elif texto is not None:

        campo.select_by_visible_text(texto)

        logger.info(
            "Select selecionado por texto: %s",
            texto
        )

    else:

        raise ValueError(
            "Informe texto ou valor para selecionar."
        )

    return True


def obter_opcao_selecionada(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> Optional[str]:
    """
    Retorna o texto da opção atualmente selecionada.
    """

    elemento = encontrar(
        driver,
        locator,
        timeout
    )

    campo = Select(elemento)

    try:

        return campo.first_selected_option.text

    except NoSuchElementException:

        return None


# ==================================================================================================
# TABELAS
# ==================================================================================================

def obter_linhas_tabela(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> list[list[str]]:
    """
    Extrai uma tabela HTML.

    Retorna:

        [
            ["João", "Analista", "Goiânia"],
            ["Maria", "Técnico", "Anápolis"]
        ]
    """

    tabela = encontrar(
        driver,
        locator,
        timeout
    )

    linhas = tabela.find_elements(
        By.CSS_SELECTOR,
        "tr"
    )

    resultado = []

    for linha in linhas:

        celulas = linha.find_elements(
            By.CSS_SELECTOR,
            "th, td"
        )

        valores = [
            celula.text.strip()
            for celula in celulas
        ]

        if valores:
            resultado.append(valores)

    logger.info(
        "Tabela extraída: %s linhas.",
        len(resultado)
    )

    return resultado


def obter_linhas_tabela_js(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> list[list[str]]:
    """
    Versão otimizada para tabelas grandes.
    """

    tabela = encontrar(
        driver,
        locator,
        timeout
    )

    return driver.execute_script(
        """
        return Array.from(
            arguments[0].querySelectorAll('tr')
        ).map(
            row => Array.from(
                row.querySelectorAll('th, td')
            ).map(
                cell => cell.innerText.trim()
            )
        );
        """,
        tabela
    )


# ==================================================================================================
# ENCONTRAR LINHA DE UMA TABELA
# ==================================================================================================

def encontrar_linha_por_texto(
    driver: webdriver.Remote,
    tabela_locator: Locator,
    texto: str,
    coluna: Optional[int] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Optional[WebElement]:
    """
    Procura uma linha de tabela que contenha determinado texto.

    Isso será MUITO importante para nosso projeto de concursos.

    Exemplo:

        encontrar_linha_por_texto(
            driver,
            tabela_locator,
            "2/2024"
        )

    """

    tabela = encontrar(
        driver,
        tabela_locator,
        timeout
    )

    linhas = tabela.find_elements(
        By.CSS_SELECTOR,
        "tbody tr"
    )

    # Algumas tabelas não possuem tbody.
    if not linhas:

        linhas = tabela.find_elements(
            By.CSS_SELECTOR,
            "tr"
        )

    for linha in linhas:

        celulas = linha.find_elements(
            By.CSS_SELECTOR,
            "td"
        )

        if coluna is not None:

            if coluna >= len(celulas):
                continue

            texto_celula = celulas[
                coluna
            ].text.strip()

            if texto_celula == texto:

                return linha

        else:

            texto_linha = linha.text.strip()

            if texto in texto_linha:

                return linha

    return None


# ==================================================================================================
# IFRAME
# ==================================================================================================

def entrar_iframe(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """
    Entra em um iframe.
    """

    WebDriverWait(
        driver,
        timeout
    ).until(
        EC.frame_to_be_available_and_switch_to_it(locator)
    )

    logger.info(
        "Entrou no iframe: %s",
        locator
    )

    return True


def sair_iframe(
    driver: webdriver.Remote
) -> None:
    """
    Retorna para o documento principal.
    """

    driver.switch_to.default_content()

    logger.info(
        "Retornou ao documento principal."
    )


# ==================================================================================================
# JANELAS / ABAS
# ==================================================================================================

def aguardar_nova_janela(
    driver: webdriver.Remote,
    quantidade_anterior: int,
    timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """
    Aguarda a abertura de uma nova aba/janela.
    """

    WebDriverWait(
        driver,
        timeout
    ).until(
        lambda d: len(d.window_handles) > quantidade_anterior
    )

    return True


def trocar_para_janela(
    driver: webdriver.Remote,
    indice: int = -1
) -> bool:
    """
    Troca para uma janela.

    indice = -1 significa a última janela aberta.
    """

    janelas = driver.window_handles

    if not janelas:

        raise RuntimeError(
            "Nenhuma janela encontrada."
        )

    driver.switch_to.window(
        janelas[indice]
    )

    logger.info(
        "Janela alterada para índice %s.",
        indice
    )

    return True


# ==================================================================================================
# ALERTAS
# ==================================================================================================

def alerta_presente(
    driver: webdriver.Remote
) -> bool:
    """
    Verifica se existe um alerta JavaScript.
    """

    try:

        driver.switch_to.alert

        return True

    except NoAlertPresentException:

        return False


def aceitar_alerta(
    driver: webdriver.Remote,
    timeout: int = 3
) -> Optional[str]:
    """
    Aguarda e aceita um alerta.

    Retorna o texto do alerta.
    """

    try:

        alerta = WebDriverWait(
            driver,
            timeout
        ).until(
            EC.alert_is_present()
        )

        texto = alerta.text

        alerta.accept()

        logger.info(
            "Alerta aceito: %s",
            texto
        )

        return texto

    except TimeoutException:

        return None


def recusar_alerta(
    driver: webdriver.Remote,
    timeout: int = 3
) -> Optional[str]:
    """
    Aguarda e recusa um alerta.

    Retorna o texto do alerta.
    """

    try:

        alerta = WebDriverWait(
            driver,
            timeout
        ).until(
            EC.alert_is_present()
        )

        texto = alerta.text

        alerta.dismiss()

        logger.info(
            "Alerta recusado: %s",
            texto
        )

        return texto

    except TimeoutException:

        return None


# ==================================================================================================
# NAVEGAÇÃO
# ==================================================================================================

def abrir_site(
    driver: webdriver.Remote,
    url: str,
    timeout: int = DEFAULT_TIMEOUT
) -> None:
    """
    Abre uma URL.
    """

    logger.info(
        "Abrindo site: %s",
        url
    )

    driver.get(url)

    WebDriverWait(
        driver,
        timeout
    ).until(
        lambda d: d.execute_script(
            "return document.readyState"
        ) == "complete"
    )

    logger.info(
        "Página carregada."
    )


# ==================================================================================================
# ESPERAR ELEMENTO DESAPARECER / FICAR OBSOLETO
# ==================================================================================================

def esperar_staleness(
    driver: webdriver.Remote,
    locator: Optional[Locator] = None,
    elemento: Optional[WebElement] = None,
    timeout: int = 5
) -> None:
    """
    Aguarda um elemento ficar obsoleto.

    Útil quando uma página atualiza uma tabela depois de uma pesquisa.
    """

    try:

        if elemento is None:

            if locator is None:

                raise ValueError(
                    "Informe locator ou elemento."
                )

            elemento = driver.find_element(
                *locator
            )

        WebDriverWait(
            driver,
            timeout
        ).until(
            EC.staleness_of(elemento)
        )

    except TimeoutException:

        pass

    except NoSuchElementException:

        pass


# ==================================================================================================
# SCROLL
# ==================================================================================================

def rolar_ate_elemento(
    driver: webdriver.Remote,
    locator: Locator,
    timeout: int = DEFAULT_TIMEOUT
) -> WebElement:
    """
    Rola a página até determinado elemento.
    """

    elemento = encontrar(
        driver,
        locator,
        timeout
    )

    driver.execute_script(
        """
        arguments[0].scrollIntoView({
            behavior: 'instant',
            block: 'center'
        });
        """,
        elemento
    )

    return elemento


# ==================================================================================================
# FECHAR
# ==================================================================================================

def fechar_navegador(
    driver: Optional[webdriver.Remote]
) -> None:
    """
    Fecha o navegador com segurança.
    """

    if driver is None:
        return

    try:

        driver.quit()

        logger.info(
            "Navegador encerrado."
        )

    except Exception:

        logger.exception(
            "Erro ao fechar o navegador."
        )


# ==================================================================================================
# EXECUÇÃO COM RETENTATIVA
# ==================================================================================================

def executar_com_retentativa(
    funcao: Callable,
    tentativas: int = DEFAULT_RETRIES,
    intervalo: float = DEFAULT_RETRY_DELAY,
    *args,
    **kwargs
):
    """
    Executa uma função novamente caso ocorra erro.

    Útil para operações que podem falhar momentaneamente
    por instabilidade do site.
    """

    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            return funcao(
                *args,
                **kwargs
            )

        except Exception as erro:

            ultimo_erro = erro

            logger.warning(
                "Erro na execução. "
                "Tentativa %s/%s.",
                tentativa,
                tentativas
            )

            if tentativa < tentativas:

                time.sleep(
                    intervalo
                )

    raise ultimo_erro


# ==================================================================================================
# TESTE RÁPIDO
# ==================================================================================================

if __name__ == "__main__":

    configurar_log(
        "logs/selenium.log"
    )

    driver = None

    try:

        driver = iniciar_chrome()

        abrir_site(
            driver,
            "https://www.google.com"
        )

        input(
            "\nNavegador aberto. "
            "Pressione ENTER para fechar..."
        )

    finally:

        fechar_navegador(
            driver
        )
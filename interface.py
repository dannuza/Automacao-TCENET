import tkinter as tk
from tkinter import ttk, messagebox

from app.planilha import carregar_unidades, buscar_unidade_por_sigla
from app.automacao import executar_automacao


class TelaPrincipal:
    def __init__(self, janela):
        self.janela = janela

        self.janela.title("Automação TCENET")
        self.janela.geometry("500x350")
        self.janela.resizable(False, False)

        # Dados da unidade selecionada
        self.dados_unidade = None

        # Navegador da automação
        self.driver = None

        # Edital selecionado
        self.edital_selecionado = None

        self.criar_interface()

    def criar_interface(self):
        titulo = ttk.Label(
            self.janela,
            text="AUTOMAÇÃO TCENET",
            font=("Arial", 20, "bold")
        )
        titulo.pack(pady=(30, 30))

        frame = ttk.Frame(self.janela)
        frame.pack(fill="x", padx=50)

        # Unidade
        ttk.Label(
            frame,
            text="Unidade"
        ).pack(anchor="w")

        self.unidade = ttk.Combobox(
            frame,
            state="readonly"
        )
        self.unidade.pack(fill="x", pady=(5, 20))

        # Edital
        ttk.Label(
            frame,
            text="Edital"
        ).pack(anchor="w")

        self.edital = ttk.Entry(frame)
        self.edital.pack(fill="x", pady=(5, 30))

        # Botão
        botao = ttk.Button(
            frame,
            text="CONTINUAR",
            command=self.continuar
        )
        botao.pack()

        self.carregar_unidades()

    def carregar_unidades(self):
        try:
            siglas = carregar_unidades()

            self.unidade["values"] = siglas

            if siglas:
                self.unidade.current(0)

        except Exception as erro:
            import traceback

            traceback.print_exc()

            messagebox.showerror(
                "Erro",
                f"Não foi possível carregar as unidades.\n\n{erro}"
            )

    def continuar(self):
        sigla = self.unidade.get().strip()
        edital = self.edital.get().strip()

        # Valida a unidade selecionada
        if not sigla:
            messagebox.showwarning(
                "Atenção",
                "Selecione uma unidade."
            )
            return

        # Valida o edital informado
        if not edital:
            messagebox.showwarning(
                "Atenção",
                "Digite o edital."
            )
            return

        try:
            # Busca os dados da unidade na planilha de acesso
            dados_unidade = buscar_unidade_por_sigla(sigla)

            if dados_unidade is None:
                messagebox.showerror(
                    "Erro",
                    f"A unidade '{sigla}' não foi encontrada na planilha."
                )
                return

            # Guarda os dados da unidade
            self.dados_unidade = dados_unidade

            # Guarda o edital selecionado
            self.edital_selecionado = edital

            # Executa a automação do TCENET
            self.driver = executar_automacao(
                self.dados_unidade,
                self.edital_selecionado
            )

        except Exception as erro:
            import traceback

            # Exibe o erro técnico no terminal
            traceback.print_exc()

            # Exibe uma mensagem na interface
            messagebox.showerror(
                "Erro na automação",
                f"A automação foi interrompida.\n\n{erro}"
            )


def iniciar_interface():
    janela = tk.Tk()

    TelaPrincipal(janela)

    janela.mainloop()
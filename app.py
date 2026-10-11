#!/usr/bin/env python3
import csv
import calendar
import os
import sys
import subprocess
import webbrowser
from datetime import datetime, timedelta
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

# Importações do Matplotlib para Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

PASTA_APP = os.path.dirname(os.path.abspath(__file__))

# Uma única família de fonte para toda a interface (a mais adequada a cada sistema)
if sys.platform.startswith("win"):
    FONTE_UI = "Segoe UI"
elif sys.platform == "darwin":
    FONTE_UI = "Helvetica Neue"
else:
    FONTE_UI = "DejaVu Sans"


def somar_meses(data_str, n_meses):
    """Soma n_meses a uma data no formato dd/mm/aaaa, ajustando o dia se o mês destino for mais curto."""
    dt = datetime.strptime(data_str, "%d/%m/%Y")
    mes_total = dt.month - 1 + n_meses
    ano = dt.year + mes_total // 12
    mes = mes_total % 12 + 1
    ultimo_dia_mes = calendar.monthrange(ano, mes)[1]
    dia = min(dt.day, ultimo_dia_mes)
    return dt.replace(year=ano, month=mes, day=dia).strftime("%d/%m/%Y")


def abrir_arquivo_externo(caminho):
    """Abre um arquivo (comprovante, PDF, etc) com o programa padrão do sistema operacional."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho)
        elif sys.platform == "darwin":
            subprocess.call(["open", caminho])
        else:
            subprocess.call(["xdg-open", caminho])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")

ARQUIVO_CSV = "contas.csv"


def formatar_moeda(valor):
    """Formata valor numérico para o padrão de moeda em Reais (R$ X.XXX,XX)"""
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")


class GerenciadorContasApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Contas")
        self.root.geometry("1100x850")
        self.root.minsize(1000, 600)

        # Ícone da janela/barra de tarefas (usa icone.png na mesma pasta do app.py)
        try:
            caminho_icone = os.path.join(PASTA_APP, "icone.png")
            self.icone_janela = tk.PhotoImage(file=caminho_icone)
            self.root.iconphoto(True, self.icone_janela)
        except Exception:
            pass

        # ---------------- PALETA E ESTILO GLOBAL ----------------
        self.COR_FUNDO = "#eef2f6"
        self.COR_PAINEL = "#ffffff"
        self.COR_BORDA = "#d7dee5"
        self.COR_TEXTO = "#1e293b"
        self.COR_TEXTO_SUAVE = "#64748b"
        self.COR_AZUL = "#2f80c4"
        self.COR_AZUL_CLARO = "#4da3d8"
        self.COR_VERDE = "#2f9e57"
        self.COR_AMBAR = "#e0900f"
        self.COR_VERMELHO = "#d64545"
        self.COR_ROXO = "#7d5fc4"
        self.COR_AZUL_ESCURO = "#2f6f9f"
        self.FONTE_BASE = (FONTE_UI, 9)
        self.FONTE_TITULO = (FONTE_UI, 13, "bold")
        self.FONTE_SECAO = (FONTE_UI, 10, "bold")
        self.FONTE_NEGRITO = (FONTE_UI, 9, "bold")
        self.FONTE_BOTAO = (FONTE_UI, 9, "bold")
        self.FONTE_PEQUENA = (FONTE_UI, 8)
        self.FONTE_PEQUENA_NEGRITO = (FONTE_UI, 8, "bold")

        self.root.configure(bg=self.COR_FUNDO)

        # Fonte padrão do Tk (vale também para os widgets ttk e para a lista dos Combobox)
        for nome_fonte in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
            try:
                tkfont.nametofont(nome_fonte).configure(family=FONTE_UI, size=9)
            except tk.TclError:
                pass

        # Fundo/cor padrão de qualquer widget clássico criado sem cor explícita
        # (inclui todos os diálogos, que antes ficavam com o cinza padrão do sistema)
        for classe in ("Frame", "Label", "Labelframe", "Toplevel", "Checkbutton"):
            self.root.option_add(f"*{classe}.Background", self.COR_FUNDO)
        self.root.option_add("*Checkbutton.activeBackground", self.COR_FUNDO)
        self.root.option_add("*Label.Foreground", self.COR_TEXTO)
        self.root.option_add("*Checkbutton.Foreground", self.COR_TEXTO)
        self.root.option_add("*Checkbutton.activeForeground", self.COR_TEXTO)
        self.root.option_add("*Checkbutton.highlightThickness", 0)

        # Configuração de Estilo
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("TFrame", background=self.COR_FUNDO)
        self.style.configure("TLabel", background=self.COR_FUNDO, foreground=self.COR_TEXTO, font=self.FONTE_BASE)
        self.style.configure(
            "TEntry",
            fieldbackground=self.COR_PAINEL,
            bordercolor=self.COR_BORDA,
            lightcolor=self.COR_BORDA,
            darkcolor=self.COR_BORDA,
            padding=4,
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=self.COR_PAINEL,
            background=self.COR_PAINEL,
            bordercolor=self.COR_BORDA,
            arrowcolor=self.COR_TEXTO_SUAVE,
            padding=4,
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.COR_PAINEL)],
            foreground=[("readonly", self.COR_TEXTO)],
        )
        self.style.configure(
            "Treeview",
            background=self.COR_PAINEL,
            fieldbackground=self.COR_PAINEL,
            foreground=self.COR_TEXTO,
            bordercolor=self.COR_BORDA,
            borderwidth=1,
            rowheight=26,
            font=self.FONTE_BASE,
        )
        self.style.configure(
            "Treeview.Heading",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=self.FONTE_NEGRITO,
            relief="flat",
            borderwidth=1,
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", self.COR_BORDA)],
        )
        self.style.map(
            "Treeview",
            background=[("selected", self.COR_AZUL_CLARO)],
            foreground=[("selected", "#ffffff")],
        )

        # Dados em memória
        self.contas = []
        self.caminho_arquivo_atual = os.path.abspath(ARQUIVO_CSV)
        self.carregar_dados()

        # Interface com Rolagem Geral Sem Barra Visível
        self.criar_interface_scrolavel()
        self.atualizar_tabela_e_cards()

    def carregar_dados(self):
        self.contas = []
        if os.path.exists(self.caminho_arquivo_atual):
            try:
                with open(self.caminho_arquivo_atual, "r", encoding="utf-8-sig", newline="") as f:
                    leitor = csv.DictReader(f, delimiter=";")
                    for row in leitor:
                        self.contas.append({
                            "id": int(row["id"]),
                            "data_lancamento": row.get("data_lancamento", ""),
                            "tipo": row.get("tipo", ""),
                            "descricao": row.get("descricao", ""),
                            "valor": float(row.get("valor", 0.0)),
                            "data_vencimento": row.get("data_vencimento", ""),
                            "forma_pagamento": row.get("forma_pagamento", ""),
                            "pago": row.get("pago", "Não"),
                            "comprovante": row.get("comprovante", ""),
                            "recorrencia": row.get("recorrencia", ""),
                            "data_pagamento": row.get("data_pagamento", ""),
                        })
            except Exception as e:
                messagebox.showerror(
                    "Erro", f"Falha ao carregar o arquivo CSV:\n{e}"
                )
                self.contas = []

    def salvar_dados(self):
        try:
            campos = [
                "id", "data_lancamento", "tipo", "descricao",
                "valor", "data_vencimento", "forma_pagamento", "pago",
                "comprovante", "recorrencia", "data_pagamento",
            ]
            with open(self.caminho_arquivo_atual, "w", encoding="utf-8-sig", newline="") as f:
                escritor = csv.DictWriter(f, fieldnames=campos, delimiter=";")
                escritor.writeheader()
                for c in self.contas:
                    escritor.writerow({campo: c.get(campo, "") for campo in campos})
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar no CSV:\n{e}")

    def calcular_status(self, conta):
        tipo = conta.get("tipo")
        pago = conta.get("pago", "Não")
        venc_str = conta.get("data_vencimento", "")

        if tipo == "Registro" or pago == "Sim":
            return "0", "Pago"

        if not venc_str:
            return "-", "Em Aberto"

        try:
            hoje = datetime.now().date()
            venc = datetime.strptime(venc_str, "%d/%m/%Y").date()
            dias = (venc - hoje).days

            if dias < 0:
                return str(dias), "Vencido"
            else:
                return str(dias), "Em Aberto"
        except ValueError:
            return "-", "Erro Data"

    # ---------------- COMPONENTES REUTILIZÁVEIS ----------------

    def _escurecer(self, widget, cor, fator=0.88):
        """Devolve a cor (qualquer formato aceito pelo Tk) um pouco mais escura, em #rrggbb."""
        try:
            r, g, b = [int(v / 256 * fator) for v in widget.winfo_rgb(cor)]
            return f"#{r:02x}{g:02x}{b:02x}"
        except tk.TclError:
            return cor

    def _ativar_hover(self, btn):
        """Padroniza um tk.Button: visual plano, cursor de mão e realce ao passar o mouse."""
        if getattr(btn, "_hover_ok", False):
            return
        btn._hover_ok = True
        normal = btn.cget("bg")
        hover = self._escurecer(btn, normal)
        btn.configure(
            relief="flat", bd=0, cursor="hand2",
            activebackground=hover, activeforeground=btn.cget("fg"),
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover) if str(btn.cget("state")) != "disabled" else None)
        btn.bind("<Leave>", lambda e: btn.configure(bg=normal))

    def _estilizar_botoes(self, raiz):
        """Aplica o padrão de botão a todos os tk.Button dentro de 'raiz' (usado nos diálogos)."""
        for filho in raiz.winfo_children():
            if isinstance(filho, tk.Button):
                self._ativar_hover(filho)
            self._estilizar_botoes(filho)

    def _botao(self, parent, texto, cor, comando, fg="white", **kw):
        opcoes = dict(font=self.FONTE_BOTAO, padx=12, pady=5)
        opcoes.update(kw)
        btn = tk.Button(parent, text=texto, bg=cor, fg=fg, command=comando, **opcoes)
        self._ativar_hover(btn)
        return btn

    def _rotulo(self, parent, texto, **kw):
        """Label que herda o fundo do contêiner (evita 'manchas' de cor diferente)."""
        opcoes = dict(bg=parent.cget("bg"), fg=self.COR_TEXTO, font=self.FONTE_BASE)
        opcoes.update(kw)
        return tk.Label(parent, text=texto, **opcoes)

    def _secao(self, parent, titulo):
        """Painel branco com borda e título; devolve o frame interno para receber o conteúdo."""
        caixa = tk.Frame(parent, bg=self.COR_PAINEL, highlightthickness=1,
                         highlightbackground=self.COR_BORDA, highlightcolor=self.COR_BORDA)
        caixa.pack(fill="x", padx=10, pady=5)
        tk.Label(
            caixa, text=titulo, font=self.FONTE_SECAO, bg=self.COR_PAINEL, fg=self.COR_TEXTO,
        ).pack(anchor="w", padx=14, pady=(10, 4))
        corpo = tk.Frame(caixa, bg=self.COR_PAINEL)
        corpo.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        return corpo

    def _criar_card(self, parent, titulo, cor_fundo, cor_texto, linha, coluna):
        """Card com título, resumo (quantidade - valor) e mini gráfico. Devolve (label, figura, canvas)."""
        card = tk.Frame(parent, bg=cor_fundo, highlightthickness=1,
                        highlightbackground=self.COR_BORDA, highlightcolor=self.COR_BORDA)
        card.grid(row=linha, column=coluna, sticky="nsew", padx=4, pady=4)

        cabecalho = tk.Frame(card, bg=cor_fundo)
        cabecalho.pack(fill="x", padx=12, pady=(8, 0))
        tk.Label(cabecalho, text=titulo, font=self.FONTE_NEGRITO, bg=cor_fundo, fg=cor_texto).pack(side="left")
        lbl_resumo = tk.Label(
            cabecalho, text="0 registro(s) - R$ 0,00", font=self.FONTE_NEGRITO, bg=cor_fundo, fg=cor_texto,
        )
        lbl_resumo.pack(side="right")

        figura = Figure(figsize=(4, 1.3), dpi=80)
        figura.patch.set_facecolor(cor_fundo)
        canvas = FigureCanvasTkAgg(figura, master=card)
        canvas.get_tk_widget().configure(bg=cor_fundo, highlightthickness=0)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=(0, 6))
        return lbl_resumo, figura, canvas

    # ---------------- ROLAGEM COM A RODA DO MOUSE ----------------

    def _on_roda(self, event):
        """Único tratador da roda do mouse. Decide quem rola conforme a janela sob o ponteiro:
        - janela principal: rola a página (exceto sobre a tabela, que tem rolagem própria);
        - diálogo com lista (importar/exportar): rola a lista, sem mexer na página de trás."""
        try:
            widget = event.widget
            janela = widget.winfo_toplevel()
        except (AttributeError, tk.TclError, KeyError):
            return

        if janela is self.root:
            if str(widget).startswith(str(self.tree)):
                return
            canvas = self.main_canvas
        else:
            canvas = getattr(janela, "canvas_rolagem", None)
            if canvas is None:
                return

        if event.num == 4:
            passos = -1
        elif event.num == 5:
            passos = 1
        elif sys.platform == "darwin":
            passos = -event.delta
        else:
            if not event.delta:
                return
            passos = -max(1, abs(event.delta) // 120) * (1 if event.delta > 0 else -1)
        canvas.yview_scroll(passos, "units")

    def _centralizar_dialogo(self, win, largura, altura):
        """Centraliza o diálogo sobre a janela principal, nunca menor que o conteúdo, e o torna modal."""
        win.transient(self.root)
        self._estilizar_botoes(win)
        win.update_idletasks()
        largura = max(largura, win.winfo_reqwidth())
        altura = max(altura, win.winfo_reqheight() + 12)
        x = self.root.winfo_x() + (self.root.winfo_width() - largura) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - altura) // 2
        win.geometry(f"{largura}x{altura}+{max(x, 0)}+{max(y, 0)}")
        win.grab_set()

    # ---------------- INTERFACE ----------------

    def criar_interface_scrolavel(self):
        """Contêiner principal com rolagem pela roda do mouse (sem barra visível)
        e barra de status fixa no rodapé com o arquivo ativo."""
        barra_status = tk.Frame(
            self.root, bg=self.COR_PAINEL, highlightthickness=1,
            highlightbackground=self.COR_BORDA, highlightcolor=self.COR_BORDA,
        )
        barra_status.pack(side="bottom", fill="x")
        tk.Label(
            barra_status, text="Arquivo ativo:", bg=self.COR_PAINEL,
            fg=self.COR_TEXTO_SUAVE, font=self.FONTE_PEQUENA_NEGRITO,
        ).pack(side="left", padx=(12, 4), pady=4)
        self.lbl_caminho_csv = tk.Label(
            barra_status, text=self.caminho_arquivo_atual, bg=self.COR_PAINEL,
            fg=self.COR_TEXTO, font=self.FONTE_PEQUENA, anchor="w",
        )
        self.lbl_caminho_csv.pack(side="left", fill="x", expand=True, pady=4)

        self.main_canvas = tk.Canvas(self.root, highlightthickness=0, bg=self.COR_FUNDO)

        self.scrollable_frame = tk.Frame(self.main_canvas, bg=self.COR_FUNDO)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            self.main_canvas.itemconfig(self.canvas_window, width=event.width)

        self.main_canvas.bind("<Configure>", _on_canvas_configure)
        self.main_canvas.pack(side="left", fill="both", expand=True)

        # Windows/macOS usam <MouseWheel>; Linux/X11 usa <Button-4>/<Button-5>.
        self.root.bind_all("<MouseWheel>", self._on_roda)
        self.root.bind_all("<Button-4>", self._on_roda)
        self.root.bind_all("<Button-5>", self._on_roda)

        self.criar_interface(self.scrollable_frame)

    def criar_interface(self, parent):
        # ---------------- BARRA SUPERIOR ----------------
        frame_top = tk.Frame(
            parent, bg=self.COR_PAINEL, padx=14, pady=10,
            highlightthickness=1, highlightbackground=self.COR_BORDA, highlightcolor=self.COR_BORDA,
        )
        frame_top.pack(fill="x")

        frame_esquerda = tk.Frame(frame_top, bg=self.COR_PAINEL)
        frame_esquerda.pack(side="left")
        tk.Label(
            frame_esquerda, text="Gerenciador de Contas",
            font=self.FONTE_TITULO, bg=self.COR_PAINEL, fg=self.COR_TEXTO,
        ).pack(anchor="w")
        tk.Label(
            frame_esquerda, text="V020926",
            font=self.FONTE_PEQUENA, bg=self.COR_PAINEL, fg=self.COR_TEXTO_SUAVE,
        ).pack(anchor="w")

        frame_botoes_top = tk.Frame(frame_top, bg=self.COR_PAINEL)
        frame_botoes_top.pack(side="right")
        self._botao(frame_botoes_top, "📥 Importar CSV", self.COR_AZUL, self.abrir_janela_importar).pack(side="left", padx=(0, 6))
        self._botao(frame_botoes_top, "📤 Exportar CSV", self.COR_AZUL_ESCURO, self.abrir_janela_exportar).pack(side="left")

        # ---------------- 4 CARDS / GRÁFICOS MINIATURA (GRADE 2x2) ----------------
        frame_cards = tk.Frame(parent, bg=self.COR_FUNDO, pady=6, padx=5)
        frame_cards.pack(fill="x", padx=10)
        frame_cards.grid_columnconfigure(0, weight=1, uniform="cards")
        frame_cards.grid_columnconfigure(1, weight=1, uniform="cards")

        self.lbl_card_pagar, self.fig_pagar, self.canvas_pagar = self._criar_card(
            frame_cards, "A Pagar (Próximos 30 Dias)", "#fbe9e9", "#b83232", 0, 0)
        self.lbl_card_receber, self.fig_receber, self.canvas_receber = self._criar_card(
            frame_cards, "A Receber (Próximos 30 Dias)", "#fdf3df", "#9a6200", 0, 1)
        self.lbl_card_quitados, self.fig_quitados, self.canvas_quitados = self._criar_card(
            frame_cards, "Quitados (Últimos 30 Dias)", "#e6f4ea", "#1f7a41", 1, 0)
        self.lbl_card_registros, self.fig_registros, self.canvas_registros = self._criar_card(
            frame_cards, "Registros no Ato (Últimos 30 Dias)", "#e7f0fb", "#2f6f9f", 1, 1)

        # ---------------- PAINEL DE GRÁFICOS INTERATIVO ----------------
        corpo_grafico = self._secao(parent, "Evolução Financeira (30 Dias / Período)")

        frame_ctrl_grafico = tk.Frame(corpo_grafico, bg=self.COR_PAINEL)
        frame_ctrl_grafico.pack(fill="x", pady=(0, 6))

        hoje = datetime.now()

        self._rotulo(frame_ctrl_grafico, "Mês:", font=self.FONTE_NEGRITO).pack(side="left", padx=(0, 4))
        self.combo_graf_mes = ttk.Combobox(
            frame_ctrl_grafico, values=[f"{i:02d}" for i in range(1, 13)],
            state="readonly", width=4,
        )
        self.combo_graf_mes.set(f"{hoje.month:02d}")
        self.combo_graf_mes.pack(side="left", padx=(0, 14))
        self.combo_graf_mes.bind("<<ComboboxSelected>>", lambda e: self.atualizar_graficos())

        self._rotulo(frame_ctrl_grafico, "Ano:", font=self.FONTE_NEGRITO).pack(side="left", padx=(0, 4))
        self.combo_graf_ano = ttk.Combobox(
            frame_ctrl_grafico, values=[str(y) for y in range(hoje.year - 2, hoje.year + 4)],
            state="readonly", width=6,
        )
        self.combo_graf_ano.set(str(hoje.year))
        self.combo_graf_ano.pack(side="left", padx=(0, 14))
        self.combo_graf_ano.bind("<<ComboboxSelected>>", lambda e: self.atualizar_graficos())

        self._rotulo(frame_ctrl_grafico, "Exibir Tipos:", font=self.FONTE_NEGRITO).pack(side="left", padx=(0, 4))
        self.combo_graf_tipo = ttk.Combobox(
            frame_ctrl_grafico, values=["Ambos", "Apenas A Pagar", "Apenas A Receber"],
            state="readonly", width=18,
        )
        self.combo_graf_tipo.set("Ambos")
        self.combo_graf_tipo.pack(side="left")
        self.combo_graf_tipo.bind("<<ComboboxSelected>>", lambda e: self.atualizar_graficos())

        self.figura = Figure(figsize=(9, 2.4), dpi=90)
        self.figura.patch.set_facecolor(self.COR_PAINEL)
        self.canvas_grafico = FigureCanvasTkAgg(self.figura, master=corpo_grafico)
        self.canvas_grafico.get_tk_widget().configure(bg=self.COR_PAINEL, highlightthickness=0)
        self.canvas_grafico.get_tk_widget().pack(fill="both", expand=True)

        # ---------------- FORMULÁRIO DE CADASTRO ----------------
        corpo_form = self._secao(parent, "Novo Lançamento")

        # Colunas de campo (1, 3, 5) com a mesma largura; colunas de rótulo (0, 2, 4) ajustam ao texto.
        for col in (1, 3, 5):
            corpo_form.grid_columnconfigure(col, weight=1, uniform="campo")

        def rotulo(texto, linha, coluna):
            self._rotulo(corpo_form, texto).grid(
                row=linha, column=coluna, sticky="w", padx=(0 if coluna == 0 else 18, 8), pady=4)

        # Linha 1: Data Lançamento, Tipo, Descrição
        rotulo("Data Lançamento:", 0, 0)
        self.ent_data_lancamento = ttk.Entry(corpo_form, width=12)
        self.ent_data_lancamento.grid(row=0, column=1, sticky="ew", pady=4)
        self.ent_data_lancamento.insert(0, datetime.now().strftime("%d/%m/%Y"))

        rotulo("Tipo:", 0, 2)
        self.combo_tipo = ttk.Combobox(
            corpo_form, values=["A Pagar", "A Receber", "Registro"], state="readonly", width=12,
        )
        self.combo_tipo.grid(row=0, column=3, sticky="ew", pady=4)
        self.combo_tipo.set("A Pagar")
        self.combo_tipo.bind("<<ComboboxSelected>>", self.ao_mudar_tipo)

        rotulo("Descrição:", 0, 4)
        self.ent_descricao = ttk.Entry(corpo_form, width=12)
        self.ent_descricao.grid(row=0, column=5, sticky="ew", pady=4)

        # Linha 2: Valor, Vencimento, Forma Pagamento
        rotulo("Valor (R$):", 1, 0)
        self.ent_valor = ttk.Entry(corpo_form, width=12)
        self.ent_valor.grid(row=1, column=1, sticky="ew", pady=4)

        rotulo("Vencimento:", 1, 2)
        self.ent_vencimento = ttk.Entry(corpo_form, width=12)
        self.ent_vencimento.grid(row=1, column=3, sticky="ew", pady=4)
        self.ent_vencimento.insert(0, datetime.now().strftime("%d/%m/%Y"))

        rotulo("Forma Pagamento:", 1, 4)
        self.combo_forma = ttk.Combobox(
            corpo_form,
            values=["Pix", "Boleto", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Transferência"],
            state="readonly", width=12,
        )
        self.combo_forma.grid(row=1, column=5, sticky="ew", pady=4)
        self.combo_forma.set("Pix")

        # Enter em qualquer campo de texto cadastra a conta
        for campo in (self.ent_data_lancamento, self.ent_descricao, self.ent_valor, self.ent_vencimento):
            campo.bind("<Return>", lambda e: self.adicionar_conta())

        # Linha 3: Comprovante + Recorrência mensal
        self.caminho_comprovante_novo = ""

        self._botao(
            corpo_form, "📎 Anexar Comprovante", self.COR_BORDA, self._selecionar_comprovante_novo,
            fg=self.COR_TEXTO, font=self.FONTE_PEQUENA_NEGRITO,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 4))

        self.lbl_comprovante_novo = self._rotulo(
            corpo_form, "Nenhum arquivo selecionado", font=self.FONTE_PEQUENA, fg=self.COR_TEXTO_SUAVE,
        )
        self.lbl_comprovante_novo.grid(row=2, column=2, columnspan=2, sticky="w", padx=(18, 0), pady=(8, 4))

        self.var_recorrente = tk.BooleanVar(value=False)
        tk.Checkbutton(
            corpo_form, text="🔁 Repetir mensalmente por:", variable=self.var_recorrente,
            font=self.FONTE_NEGRITO, bg=self.COR_PAINEL, activebackground=self.COR_PAINEL,
            fg=self.COR_TEXTO, activeforeground=self.COR_TEXTO, highlightthickness=0, bd=0,
            command=self._alternar_campo_recorrencia,
        ).grid(row=2, column=4, sticky="w", padx=(18, 0), pady=(8, 4))

        frame_meses = tk.Frame(corpo_form, bg=self.COR_PAINEL)
        frame_meses.grid(row=2, column=5, sticky="w", pady=(8, 4))
        self.spin_meses_recorrencia = tk.Spinbox(
            frame_meses, from_=2, to=60, width=4, state="disabled", font=self.FONTE_BASE,
        )
        self.spin_meses_recorrencia.pack(side="left")
        self._rotulo(frame_meses, "meses").pack(side="left", padx=(4, 0))

        # Botão de cadastrar, alinhado à direita em linha própria
        self._botao(
            corpo_form, "+ Cadastrar Conta", self.COR_VERDE, self.adicionar_conta, padx=20, pady=7,
        ).grid(row=3, column=0, columnspan=6, sticky="e", pady=(10, 0))

        # ---------------- CAIXA LOCALIZAR / FILTRAR (2 LINHAS) ----------------
        corpo_filtro = self._secao(parent, "Localizar / Filtrar")

        linha_busca = tk.Frame(corpo_filtro, bg=self.COR_PAINEL)
        linha_busca.pack(fill="x")

        self._rotulo(linha_busca, "🔍 Pesquisar:", font=self.FONTE_NEGRITO).pack(side="left", padx=(0, 6))
        self.ent_pesquisa = ttk.Entry(linha_busca)
        self.ent_pesquisa.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.ent_pesquisa.bind("<KeyRelease>", lambda event: self.atualizar_tabela_e_cards())

        self._botao(
            linha_busca, "🖨️ Relatório / Imprimir", self.COR_ROXO, self.abrir_janela_relatorio,
            font=self.FONTE_PEQUENA_NEGRITO,
        ).pack(side="right")
        self._botao(
            linha_busca, "📄 Exportar PDF", self.COR_AZUL, self.exportar_relatorio_pdf,
            font=self.FONTE_PEQUENA_NEGRITO,
        ).pack(side="right", padx=(0, 8))

        linha_filtros = tk.Frame(corpo_filtro, bg=self.COR_PAINEL)
        linha_filtros.pack(fill="x", pady=(8, 0))

        self._rotulo(linha_filtros, "Tipo/Status:", font=self.FONTE_NEGRITO).pack(side="left", padx=(0, 6))
        self.combo_filtro_tipo = ttk.Combobox(
            linha_filtros,
            values=[
                "Todos",
                "A Pagar - Em Aberto / Vencido",
                "A Pagar - Pago",
                "A Receber - Em Aberto / Vencido",
                "A Receber - Recebido",
                "Registro (No Ato)"
            ],
            state="readonly", width=30,
        )
        self.combo_filtro_tipo.set("Todos")
        self.combo_filtro_tipo.pack(side="left", padx=(0, 18))
        self.combo_filtro_tipo.bind("<<ComboboxSelected>>", lambda event: self.atualizar_tabela_e_cards())

        self._rotulo(linha_filtros, "Período:", font=self.FONTE_NEGRITO).pack(side="left", padx=(0, 6))
        self.combo_periodo = ttk.Combobox(
            linha_filtros,
            values=["Todos", "Hoje", "Próximos 7 dias", "Próximos 30 dias", "Este mês", "Mês passado"],
            state="readonly", width=18,
        )
        self.combo_periodo.set("Todos")
        self.combo_periodo.pack(side="left", padx=(0, 18))
        self.combo_periodo.bind("<<ComboboxSelected>>", lambda event: self.atualizar_tabela_e_cards())

        self._botao(
            linha_filtros, "✖ Limpar Filtros", self.COR_BORDA, self.limpar_busca,
            fg=self.COR_TEXTO, font=self.FONTE_PEQUENA_NEGRITO,
        ).pack(side="left")

        # ---------------- TABELA (ALTURA FIXA + BARRA DE ROLAGEM PRÓPRIA) ----------------
        frame_tabela = tk.Frame(parent, bg=self.COR_FUNDO)
        frame_tabela.pack(fill="both", expand=True, padx=10, pady=(5, 12))

        colunas = (
            "id", "data_lancamento", "tipo", "descricao", "valor", "vencimento",
            "forma", "anexo", "dias", "status", "opcao",
        )
        self.tree = ttk.Treeview(
            frame_tabela, columns=colunas, show="headings", selectmode="browse", height=12,
        )
        barra_tree = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=barra_tree.set)
        barra_tree.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # (título, largura, âncora do conteúdo, estica?) — só a Descrição estica com a janela;
        # o cabeçalho acompanha o alinhamento do conteúdo.
        definicao = {
            "id":              ("ID",            38, "center", False),
            "data_lancamento": ("Lançamento",   100, "center", False),
            "tipo":            ("Tipo",          95, "center", False),
            "descricao":       ("Descrição",    200, "w",      True),
            "valor":           ("Valor (R$)",   105, "e",      False),
            "vencimento":      ("Vencimento",   100, "center", False),
            "forma":           ("Forma Pagto",  115, "center", False),
            "anexo":           ("📎",            32, "center", False),
            "dias":            ("Dias P/ Vencer", 115, "center", False),
            "status":          ("Status",        80, "center", False),
            "opcao":           ("Ação",          50, "center", False),
        }
        for chave, (titulo, largura, ancora, estica) in definicao.items():
            self.tree.heading(chave, text=titulo, anchor=ancora)
            self.tree.column(chave, width=largura, minwidth=largura if not estica else 120,
                             anchor=ancora, stretch=estica)

        self.tree.tag_configure("tag_pago", background="#e6f4ea", foreground="#1f7a41")
        self.tree.tag_configure("tag_aberto", background="#fdf3df", foreground="#9a6200")
        self.tree.tag_configure("tag_vencido", background="#fbe9e9", foreground="#b83232")

        self.tree.bind("<Double-1>", self.abrir_janela_modificador)

    # ---------------- GRÁFICOS ----------------

    @staticmethod
    def _fmt_eixo_valor(v, _pos=None):
        """Valor compacto para o eixo Y: 850, 1,5k, 12k."""
        if abs(v) >= 1000:
            return f"{v / 1000:.1f}".replace(".", ",").rstrip("0").rstrip(",") + "k"
        return f"{v:.0f}"

    def _estilizar_eixos(self, ax, tamanho_fonte):
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.tick_params(axis="both", labelsize=tamanho_fonte, colors=self.COR_TEXTO_SUAVE, length=3)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(self.COR_BORDA)

    def _desenhar_mini_grafico(self, figura, canvas, lista_valores, cor_linha, bg_color, datas=None):
        """Mini gráfico de 30 dias. 'datas' (lista de date) vira o eixo X em dd/mm, uma marca a cada 7 dias."""
        figura.clear()
        ax = figura.add_subplot(111)
        ax.set_facecolor(bg_color)

        valores = list(lista_valores) if lista_valores else [0] * 30
        todos_zero = sum(valores) == 0
        x = list(range(len(valores)))

        ax.plot(x, valores, color=cor_linha, linewidth=1.6, marker="o", markersize=2.5)
        ax.fill_between(x, valores, color=cor_linha, alpha=0.15, linewidth=0)
        ax.set_xlim(-0.5, len(valores) - 0.5)

        if datas and len(datas) == len(valores):
            posicoes = list(range(0, len(datas), 7))
            if len(datas) - 1 - posicoes[-1] >= 3:
                posicoes.append(len(datas) - 1)
            ax.set_xticks(posicoes)
            ax.set_xticklabels([datas[i].strftime("%d/%m") for i in posicoes])

        self._estilizar_eixos(ax, 7)

        # Evita o eixo Y "autoescalar" para uma faixa decimal minúscula quando não há valores.
        if todos_zero:
            ax.set_ylim(0, 1)
            ax.set_yticks([0])
        else:
            ax.set_ylim(bottom=0)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
            ax.yaxis.set_major_formatter(FuncFormatter(self._fmt_eixo_valor))

        figura.tight_layout(pad=0.6)
        canvas.draw()

    def atualizar_graficos(self):
        self.figura.clear()

        mes_sel = int(self.combo_graf_mes.get())
        ano_sel = int(self.combo_graf_ano.get())
        tipo_filtro = self.combo_graf_tipo.get()

        dias_no_mes = calendar.monthrange(ano_sel, mes_sel)[1]

        dados_por_dia = {dia: {"A Pagar": 0.0, "A Receber": 0.0} for dia in range(1, dias_no_mes + 1)}

        for c in self.contas:
            data_str = c.get("data_vencimento", "")
            tipo = c.get("tipo", "")
            valor = c.get("valor", 0.0)

            try:
                dt_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
                if dt_obj.month == mes_sel and dt_obj.year == ano_sel:
                    if tipo in dados_por_dia[dt_obj.day]:
                        dados_por_dia[dt_obj.day][tipo] += valor
            except ValueError:
                continue

        ax = self.figura.add_subplot(111)
        ax.set_facecolor("#f8fafc")

        dias = list(range(1, dias_no_mes + 1))
        valores_pagar = [dados_por_dia[d]["A Pagar"] for d in dias]
        valores_receber = [dados_por_dia[d]["A Receber"] for d in dias]

        if tipo_filtro in ["Ambos", "Apenas A Pagar"]:
            ax.plot(dias, valores_pagar, marker="o", markersize=4, color="#d64545", linewidth=1.8, label="A Pagar")
            ax.fill_between(dias, valores_pagar, color="#d64545", alpha=0.10, linewidth=0)
        if tipo_filtro in ["Ambos", "Apenas A Receber"]:
            ax.plot(dias, valores_receber, marker="s", markersize=4, color="#2f9e57", linewidth=1.8, label="A Receber")
            ax.fill_between(dias, valores_receber, color="#2f9e57", alpha=0.10, linewidth=0)

        # Rótulos do eixo X de 5 em 5 dias (sempre incluindo o dia 1), em vez de todos os 28-31 dias
        marcas = [1] + list(range(5, dias_no_mes + 1, 5))
        if dias_no_mes - marcas[-1] >= 3:
            marcas.append(dias_no_mes)
        ax.set_xticks(marcas)
        ax.set_xticklabels([f"{d:02d}" for d in marcas])
        ax.set_xlim(0.5, dias_no_mes + 0.5)

        maior = max(valores_pagar + valores_receber + [0])
        if maior == 0:
            ax.set_ylim(0, 1)
        else:
            ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: "R$ " + self._fmt_eixo_valor(v)))

        ax.set_title(
            f"Vencimentos de {mes_sel:02d}/{ano_sel} - Período ({dias_no_mes} Dias)",
            fontsize=9, fontweight="bold", color=self.COR_TEXTO,
        )
        ax.set_xlabel("Dia do mês", fontsize=8, color=self.COR_TEXTO_SUAVE)
        self._estilizar_eixos(ax, 8)
        ax.legend(fontsize=8, loc="upper right", frameon=False)

        self.figura.tight_layout()
        self.canvas_grafico.draw()

    def limpar_busca(self):
        self.ent_pesquisa.delete(0, tk.END)
        self.combo_filtro_tipo.set("Todos")
        self.combo_periodo.set("Todos")
        self.atualizar_tabela_e_cards()

    def ao_mudar_tipo(self, event=None):
        tipo = self.combo_tipo.get()
        if tipo == "Registro":
            self.ent_vencimento.delete(0, tk.END)
            self.ent_vencimento.insert(0, datetime.now().strftime("%d/%m/%Y"))
            self.ent_vencimento.config(state="disabled")
        else:
            self.ent_vencimento.config(state="normal")

    def _selecionar_comprovante_novo(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar comprovante",
            filetypes=[("Documentos e Imagens", "*.pdf *.png *.jpg *.jpeg"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            self.caminho_comprovante_novo = caminho
            self.lbl_comprovante_novo.config(text=os.path.basename(caminho), fg=self.COR_VERDE)

    def _alternar_campo_recorrencia(self):
        self.spin_meses_recorrencia.config(
            state="normal" if self.var_recorrente.get() else "disabled"
        )

    def adicionar_conta(self):
        data_lanc = self.ent_data_lancamento.get().strip()
        tipo = self.combo_tipo.get()
        descricao = self.ent_descricao.get().strip()
        valor_str = self.ent_valor.get().strip().replace(",", ".")
        vencimento = self.ent_vencimento.get().strip()
        forma = self.combo_forma.get()

        if not descricao:
            messagebox.showwarning("Aviso", "Preencha a descrição da conta!")
            return

        try:
            valor = float(valor_str)
            if valor <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning(
                "Aviso", "Insira um valor numérico válido maior que zero!"
            )
            return

        pago = "Sim" if tipo == "Registro" else "Não"

        if tipo == "Registro":
            vencimento = datetime.now().strftime("%d/%m/%Y")

        repetir = self.var_recorrente.get() and tipo != "Registro"
        qtd_parcelas = 1
        if repetir:
            try:
                qtd_parcelas = max(2, int(self.spin_meses_recorrencia.get()))
            except ValueError:
                qtd_parcelas = 2
            if not vencimento:
                messagebox.showwarning("Aviso", "Informe o Vencimento para gerar a recorrência mensal!")
                return

        id_recorrencia = f"R{int(datetime.now().timestamp())}" if repetir else ""

        for parcela in range(qtd_parcelas):
            novo_id = (max((c["id"] for c in self.contas), default=0)) + 1
            try:
                venc_parcela = somar_meses(vencimento, parcela) if vencimento else vencimento
            except ValueError:
                venc_parcela = vencimento

            desc_parcela = f"{descricao} ({parcela + 1}/{qtd_parcelas})" if repetir else descricao

            nova_conta = {
                "id": novo_id,
                "data_lancamento": data_lanc if data_lanc else datetime.now().strftime("%d/%m/%Y"),
                "tipo": tipo,
                "descricao": desc_parcela,
                "valor": valor,
                "data_vencimento": venc_parcela,
                "forma_pagamento": forma,
                "pago": pago,
                "comprovante": self.caminho_comprovante_novo if parcela == 0 else "",
                "recorrencia": id_recorrencia,
            }
            self.contas.append(nova_conta)

        self.salvar_dados()
        self.atualizar_tabela_e_cards()

        self.ent_descricao.delete(0, tk.END)
        self.ent_valor.delete(0, tk.END)
        self.caminho_comprovante_novo = ""
        self.lbl_comprovante_novo.config(text="Nenhum arquivo selecionado", fg=self.COR_TEXTO_SUAVE)
        self.var_recorrente.set(False)
        self._alternar_campo_recorrencia()

        if repetir:
            messagebox.showinfo("Sucesso", f"{qtd_parcelas} lançamentos mensais gerados com sucesso!")
        else:
            messagebox.showinfo("Sucesso", "Lançamento adicionado com sucesso!")

    def _valida_filtro_tipo(self, conta, filtro_tipo, status_conta):
        tipo = conta.get("tipo", "")

        if filtro_tipo == "Todos":
            return True
        elif filtro_tipo == "A Pagar - Em Aberto / Vencido":
            return tipo == "A Pagar" and status_conta in ["Em Aberto", "Vencido"]
        elif filtro_tipo == "A Pagar - Pago":
            return tipo == "A Pagar" and status_conta == "Pago"
        elif filtro_tipo == "A Receber - Em Aberto / Vencido":
            return tipo == "A Receber" and status_conta in ["Em Aberto", "Vencido"]
        elif filtro_tipo == "A Receber - Recebido":
            return tipo == "A Receber" and status_conta == "Pago"
        elif filtro_tipo == "Registro (No Ato)":
            return tipo == "Registro"
        return True

    def _valida_filtro_periodo(self, data_referencia, filtro_periodo):
        if filtro_periodo == "Todos" or not filtro_periodo:
            return True
        if not data_referencia:
            return False

        hoje = datetime.now().date()

        if filtro_periodo == "Hoje":
            return data_referencia == hoje
        elif filtro_periodo == "Próximos 7 dias":
            return hoje <= data_referencia <= hoje + timedelta(days=7)
        elif filtro_periodo == "Próximos 30 dias":
            return hoje <= data_referencia <= hoje + timedelta(days=30)
        elif filtro_periodo == "Este mês":
            return data_referencia.month == hoje.month and data_referencia.year == hoje.year
        elif filtro_periodo == "Mês passado":
            mes_passado = hoje.month - 1 or 12
            ano_mes_passado = hoje.year if hoje.month > 1 else hoje.year - 1
            return data_referencia.month == mes_passado and data_referencia.year == ano_mes_passado
        return True

    def atualizar_tabela_e_cards(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        pagar_qtd, pagar_val = 0, 0.0
        receber_qtd, receber_val = 0, 0.0
        quitados_qtd, quitados_val = 0, 0.0
        registros_qtd, registros_val = 0, 0.0

        hoje = datetime.now().date()

        # Janela de 30 dias futuros para A Pagar e A Receber
        proximos_30_dias = [hoje + timedelta(days=i) for i in range(30)]
        map_pagar_30d = {dt: 0.0 for dt in proximos_30_dias}
        map_receber_30d = {dt: 0.0 for dt in proximos_30_dias}

        # Janela de 30 dias passados para Quitados e Registros no Ato
        ultimos_30_dias = [hoje - timedelta(days=i) for i in range(29, -1, -1)]
        map_quitados_30d = {dt: 0.0 for dt in ultimos_30_dias}
        map_registros_30d = {dt: 0.0 for dt in ultimos_30_dias}

        termo_busca = self.ent_pesquisa.get().strip().lower() if hasattr(self, 'ent_pesquisa') else ""
        filtro_tipo = self.combo_filtro_tipo.get() if hasattr(self, 'combo_filtro_tipo') else "Todos"
        filtro_periodo = self.combo_periodo.get() if hasattr(self, 'combo_periodo') else "Todos"

        for conta in self.contas:
            dias_vencer, status = self.calcular_status(conta)
            valor = conta["valor"]
            tipo = conta.get("tipo", "")

            venc_str = conta.get("data_vencimento", "")
            dt_venc = None
            try:
                dt_venc = datetime.strptime(venc_str, "%d/%m/%Y").date()
            except ValueError:
                pass

            lanc_str = conta.get("data_lancamento", "")
            dt_lanc = None
            try:
                dt_lanc = datetime.strptime(lanc_str, "%d/%m/%Y").date()
            except ValueError:
                pass

            pagto_str = conta.get("data_pagamento", "")
            dt_pagto = None
            try:
                dt_pagto = datetime.strptime(pagto_str, "%d/%m/%Y").date()
            except ValueError:
                pass

            if tipo == "Registro":
                if dt_lanc and dt_lanc in map_registros_30d:
                    registros_qtd += 1
                    registros_val += valor
                    map_registros_30d[dt_lanc] += valor
                tag = "tag_pago"
            elif status == "Pago":
                # Usa a data em que a conta foi de fato paga/recebida (não o vencimento).
                # Lançamentos antigos sem data_pagamento registrada caem no vencimento
                # ou lançamento, por compatibilidade com dados já existentes.
                dt_referencia_quitado = dt_pagto or dt_venc or dt_lanc
                if dt_referencia_quitado and dt_referencia_quitado in map_quitados_30d:
                    quitados_qtd += 1
                    quitados_val += valor
                    map_quitados_30d[dt_referencia_quitado] += valor
                tag = "tag_pago"
            elif tipo == "A Pagar":
                if dt_venc and dt_venc in map_pagar_30d:
                    pagar_qtd += 1
                    pagar_val += valor
                    map_pagar_30d[dt_venc] += valor
                tag = "tag_vencido" if status == "Vencido" else "tag_aberto"
            elif tipo == "A Receber":
                if dt_venc and dt_venc in map_receber_30d:
                    receber_qtd += 1
                    receber_val += valor
                    map_receber_30d[dt_venc] += valor
                tag = "tag_vencido" if status == "Vencido" else "tag_aberto"
            else:
                tag = "tag_aberto"

            data_lanc = conta.get("data_lancamento", "-")

            if not self._valida_filtro_tipo(conta, filtro_tipo, status):
                continue

            data_ref_periodo = dt_venc if tipo != "Registro" else dt_lanc
            if not self._valida_filtro_periodo(data_ref_periodo, filtro_periodo):
                continue

            if termo_busca:
                conteudo_linha = f"{conta['id']} {data_lanc} {conta['tipo']} {conta['descricao']} {valor:.2f} {conta['data_vencimento']} {conta['forma_pagamento']} {status}".lower()
                if termo_busca not in conteudo_linha:
                    continue

            self.tree.insert(
                "",
                "end",
                values=(
                    conta["id"],
                    data_lanc,
                    conta["tipo"],
                    conta["descricao"],
                    formatar_moeda(valor),
                    conta["data_vencimento"],
                    conta["forma_pagamento"],
                    "📎" if conta.get("comprovante") else "",
                    dias_vencer,
                    status,
                    " ⚙ ",
                ),
                tags=(tag,),
            )

        self.lbl_card_pagar.config(text=f"{pagar_qtd} registro(s) - {formatar_moeda(pagar_val)}")
        self._desenhar_mini_grafico(self.fig_pagar, self.canvas_pagar, list(map_pagar_30d.values()), "#d64545", "#fbe9e9", proximos_30_dias)

        self.lbl_card_receber.config(text=f"{receber_qtd} registro(s) - {formatar_moeda(receber_val)}")
        self._desenhar_mini_grafico(self.fig_receber, self.canvas_receber, list(map_receber_30d.values()), "#e0900f", "#fdf3df", proximos_30_dias)

        self.lbl_card_quitados.config(text=f"{quitados_qtd} registro(s) - {formatar_moeda(quitados_val)}")
        self._desenhar_mini_grafico(self.fig_quitados, self.canvas_quitados, list(map_quitados_30d.values()), "#2f9e57", "#e6f4ea", ultimos_30_dias)

        self.lbl_card_registros.config(text=f"{registros_qtd} registro(s) - {formatar_moeda(registros_val)}")
        self._desenhar_mini_grafico(self.fig_registros, self.canvas_registros, list(map_registros_30d.values()), "#4da3d8", "#e7f0fb", ultimos_30_dias)

        self.atualizar_graficos()

    def abrir_janela_modificador(self, event=None):
        selecionado = self.tree.selection()
        if not selecionado:
            return

        item = self.tree.item(selecionado)
        id_conta = item["values"][0]

        conta_obj = next((c for c in self.contas if c["id"] == id_conta), None)
        if not conta_obj:
            return

        descricao_conta = conta_obj.get("descricao", "")
        dias, status_atual = self.calcular_status(conta_obj)

        tem_comprovante = bool(conta_obj.get("comprovante"))

        win = tk.Toplevel(self.root)
        win.title("Janela de Ação")
        win.resizable(False, False)

        tk.Label(
            win,
            text=f"Ações para a Conta ID #{id_conta}",
            font=(FONTE_UI, 11, "bold"),
        ).pack(pady=(15, 5))

        tk.Label(
            win,
            text=f"Descrição: {descricao_conta}\nStatus Atual: {status_atual}",
            font=(FONTE_UI, 9),
            fg="#555",
            justify="center",
            wraplength=340
        ).pack(pady=(0, 15))

        btn_pago = tk.Button(
            win,
            text="🟢 Marcar como Pago / Recebido",
            bg="#2f9e57",
            fg="white",
            font=(FONTE_UI, 9, "bold"),
            pady=5,
            command=lambda: self.acao_marcar_pago(id_conta, win),
            cursor="hand2",
        )
        btn_pago.pack(fill="x", padx=30, pady=4)

        btn_editar = tk.Button(
            win,
            text="✏️ Editar Lançamento",
            bg="#b36b00",
            fg="white",
            font=(FONTE_UI, 9, "bold"),
            pady=5,
            command=lambda: self.abrir_janela_edicao(conta_obj, win),
            cursor="hand2",
        )
        btn_editar.pack(fill="x", padx=30, pady=4)

        btn_estornar = tk.Button(
            win,
            text="↩️ Estornar Lançamento",
            bg=self.COR_AZUL_ESCURO,
            fg="white",
            font=(FONTE_UI, 9, "bold"),
            pady=5,
            command=lambda: self.abrir_janela_estorno(conta_obj, win),
            cursor="hand2",
        )
        btn_estornar.pack(fill="x", padx=30, pady=4)

        if tem_comprovante:
            btn_comprovante = tk.Button(
                win,
                text="📎 Abrir Comprovante",
                bg=self.COR_AZUL_CLARO,
                fg="white",
                font=(FONTE_UI, 9, "bold"),
                pady=5,
                command=lambda: abrir_arquivo_externo(conta_obj["comprovante"]),
                cursor="hand2",
            )
            btn_comprovante.pack(fill="x", padx=30, pady=4)

        btn_excluir = tk.Button(
            win,
            text="🔴 Excluir Registro",
            bg="#d64545",
            fg="white",
            font=(FONTE_UI, 9, "bold"),
            pady=5,
            command=lambda: self.acao_excluir(id_conta, win),
            cursor="hand2",
        )
        btn_excluir.pack(fill="x", padx=30, pady=4)

        self._centralizar_dialogo(win, 380, 0)

    def acao_marcar_pago(self, id_conta, janela):
        for conta in self.contas:
            if conta["id"] == id_conta:
                conta["pago"] = "Sim"
                conta["data_pagamento"] = datetime.now().strftime("%d/%m/%Y")
                break

        self.salvar_dados()
        self.atualizar_tabela_e_cards()
        janela.destroy()
        messagebox.showinfo("Sucesso", "Status alterado para Pago/Recebido!")

    def abrir_janela_edicao(self, conta, janela_pai):
        win_edit = tk.Toplevel(self.root)
        win_edit.title(f"Editar Lançamento ID #{conta['id']}")
        win_edit.resizable(False, False)

        tk.Label(win_edit, text="Editar Dados do Lançamento", font=(FONTE_UI, 10, "bold")).pack(pady=10)

        frame_fields = tk.Frame(win_edit, padx=15)
        frame_fields.pack(fill="both", expand=True)

        tk.Label(frame_fields, text="Descrição:").grid(row=0, column=0, sticky="w", pady=4)
        ent_desc = ttk.Entry(frame_fields, width=28)
        ent_desc.insert(0, conta.get("descricao", ""))
        ent_desc.grid(row=0, column=1, pady=4)

        tk.Label(frame_fields, text="Valor (R$):").grid(row=1, column=0, sticky="w", pady=4)
        ent_val = ttk.Entry(frame_fields, width=28)
        ent_val.insert(0, str(conta.get("valor", 0.0)))
        ent_val.grid(row=1, column=1, pady=4)

        tk.Label(frame_fields, text="Vencimento:").grid(row=2, column=0, sticky="w", pady=4)
        ent_venc = ttk.Entry(frame_fields, width=28)
        ent_venc.insert(0, conta.get("data_vencimento", ""))
        ent_venc.grid(row=2, column=1, pady=4)

        tk.Label(frame_fields, text="Forma Pagto:").grid(row=3, column=0, sticky="w", pady=4)
        combo_forma_edit = ttk.Combobox(
            frame_fields,
            values=[
                "Pix",
                "Boleto",
                "Dinheiro",
                "Cartão de Crédito",
                "Cartão de Débito",
                "Transferência",
            ],
            state="readonly",
            width=25,
        )
        combo_forma_edit.set(conta.get("forma_pagamento", "Pix"))
        combo_forma_edit.grid(row=3, column=1, pady=4)

        tk.Label(frame_fields, text="Comprovante:").grid(row=4, column=0, sticky="w", pady=4)
        comprovante_atual = {"caminho": conta.get("comprovante", "")}
        nome_atual = os.path.basename(comprovante_atual["caminho"]) if comprovante_atual["caminho"] else "Nenhum"
        lbl_comprovante_edit = tk.Label(frame_fields, text=nome_atual, font=(FONTE_UI, 8), fg=self.COR_TEXTO_SUAVE)
        lbl_comprovante_edit.grid(row=4, column=1, sticky="w", pady=4)

        def selecionar_comprovante_edicao():
            caminho = filedialog.askopenfilename(
                title="Selecionar comprovante",
                filetypes=[("Documentos e Imagens", "*.pdf *.png *.jpg *.jpeg"), ("Todos os arquivos", "*.*")],
                parent=win_edit,
            )
            if caminho:
                comprovante_atual["caminho"] = caminho
                lbl_comprovante_edit.config(text=os.path.basename(caminho), fg=self.COR_VERDE)

        tk.Button(
            frame_fields, text="📎 Anexar/Trocar", font=(FONTE_UI, 8), relief="flat",
            bg=self.COR_BORDA, cursor="hand2", command=selecionar_comprovante_edicao,
        ).grid(row=4, column=1, sticky="e", pady=4)

        tk.Label(frame_fields, text="Motivo da Edição:\n(Salvo na Descrição)", font=(FONTE_UI, 8, "bold"), fg="#d64545").grid(row=5, column=0, sticky="w", pady=10)
        ent_nota = ttk.Entry(frame_fields, width=28)
        ent_nota.grid(row=5, column=1, pady=10)

        def salvar_edicao():
            nova_desc = ent_desc.get().strip()
            novo_val_str = ent_val.get().strip().replace(",", ".")
            novo_venc = ent_venc.get().strip()
            nova_forma = combo_forma_edit.get()
            nota = ent_nota.get().strip()

            if not nova_desc:
                messagebox.showwarning("Aviso", "Descrição não pode ficar vazia!", parent=win_edit)
                return

            if not nota:
                messagebox.showwarning("Aviso", "Por favor, informe o motivo/nota da edição!", parent=win_edit)
                return

            try:
                novo_val = float(novo_val_str)
                if novo_val <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showwarning("Aviso", "Insira um valor numérico válido!", parent=win_edit)
                return

            conta["descricao"] = f"{nova_desc} [Editado: {nota}]"
            conta["valor"] = novo_val
            conta["data_vencimento"] = novo_venc
            conta["forma_pagamento"] = nova_forma
            conta["comprovante"] = comprovante_atual["caminho"]

            self.salvar_dados()
            self.atualizar_tabela_e_cards()
            win_edit.destroy()
            janela_pai.destroy()
            messagebox.showinfo("Sucesso", "Lançamento editado com sucesso!")

        btn_salvar = tk.Button(
            win_edit,
            text="💾 Salvar Alterações",
            bg="#b36b00",
            fg="white",
            font=(FONTE_UI, 9, "bold"),
            command=salvar_edicao,
            cursor="hand2",
            pady=5
        )
        btn_salvar.pack(fill="x", padx=30, pady=15)

        self._centralizar_dialogo(win_edit, 400, 0)

    def abrir_janela_estorno(self, conta, janela_pai):
        win_estorno = tk.Toplevel(self.root)
        win_estorno.title(f"Estornar Lançamento ID #{conta['id']}")
        win_estorno.resizable(False, False)

        tk.Label(win_estorno, text="Confirmar Estorno", font=(FONTE_UI, 10, "bold"), fg=self.COR_AZUL_ESCURO).pack(pady=(15, 5))
        tk.Label(
            win_estorno,
            text="O estorno reverterá o status do lançamento para não pago/em aberto.",
            font=(FONTE_UI, 8),
            fg="#555",
            wraplength=340
        ).pack(pady=(0, 10))

        frame_nota = tk.Frame(win_estorno, padx=15)
        frame_nota.pack(fill="x")

        tk.Label(frame_nota, text="Motivo do Estorno:", font=(FONTE_UI, 9, "bold")).pack(anchor="w")
        ent_nota = ttk.Entry(frame_nota, width=45)
        ent_nota.pack(fill="x", pady=5)

        def confirmar_estorno():
            nota = ent_nota.get().strip()
            if not nota:
                messagebox.showwarning("Aviso", "Informe o motivo do estorno para continuar!", parent=win_estorno)
                return

            conta["pago"] = "Não"
            conta["data_pagamento"] = ""
            desc_atual = conta.get("descricao", "")
            conta["descricao"] = f"{desc_atual} [Estornado: {nota}]"

            self.salvar_dados()
            self.atualizar_tabela_e_cards()
            win_estorno.destroy()
            janela_pai.destroy()
            messagebox.showinfo("Sucesso", "Lançamento estornado com sucesso!")

        btn_confirmar = tk.Button(
            win_estorno,
            text="↩️ Confirmar Estorno",
            bg=self.COR_AZUL_ESCURO,
            fg="white",
            font=(FONTE_UI, 9, "bold"),
            command=confirmar_estorno,
            cursor="hand2",
            pady=5
        )
        btn_confirmar.pack(fill="x", padx=30, pady=15)

        self._centralizar_dialogo(win_estorno, 380, 0)

    def acao_excluir(self, id_conta, janela):
        janela.destroy()
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a conta ID #{id_conta}?",
        ):
            self.contas = [c for c in self.contas if c["id"] != id_conta]

            for idx, c in enumerate(self.contas, start=1):
                c["id"] = idx

            self.salvar_dados()
            self.atualizar_tabela_e_cards()
            messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")

    # ---------------- MÓDULO DE RELATÓRIO E IMPRESSÃO ----------------

    def _contas_filtradas_atuais(self):
        """Retorna as contas que respeitam os filtros ativos (busca, tipo e período),
        na mesma lógica usada para popular a tabela."""
        termo_busca = self.ent_pesquisa.get().strip().lower()
        filtro_tipo = self.combo_filtro_tipo.get()
        filtro_periodo = self.combo_periodo.get()

        resultado = []
        for conta in self.contas:
            dias_vencer, status = self.calcular_status(conta)
            tipo = conta.get("tipo", "")

            try:
                dt_venc = datetime.strptime(conta.get("data_vencimento", ""), "%d/%m/%Y").date()
            except ValueError:
                dt_venc = None
            try:
                dt_lanc = datetime.strptime(conta.get("data_lancamento", ""), "%d/%m/%Y").date()
            except ValueError:
                dt_lanc = None

            if not self._valida_filtro_tipo(conta, filtro_tipo, status):
                continue

            data_ref_periodo = dt_venc if tipo != "Registro" else dt_lanc
            if not self._valida_filtro_periodo(data_ref_periodo, filtro_periodo):
                continue

            if termo_busca:
                conteudo = f"{conta['id']} {conta['data_lancamento']} {tipo} {conta['descricao']} {conta['valor']:.2f} {conta['data_vencimento']} {conta['forma_pagamento']} {status}".lower()
                if termo_busca not in conteudo:
                    continue

            resultado.append((conta, status))
        return resultado

    def exportar_relatorio_pdf(self):
        contas_filtradas = self._contas_filtradas_atuais()
        if not contas_filtradas:
            messagebox.showwarning("Aviso", "Nenhum lançamento encontrado com os filtros atuais para exportar.")
            return

        caminho_pdf = filedialog.asksaveasfilename(
            title="Salvar relatório em PDF",
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialfile=f"relatorio_contas_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        )
        if not caminho_pdf:
            return

        LINHAS_POR_PAGINA = 22
        total_geral = sum(c["valor"] for c, _ in contas_filtradas)

        try:
            with PdfPages(caminho_pdf) as pdf:
                for inicio in range(0, len(contas_filtradas), LINHAS_POR_PAGINA):
                    bloco = contas_filtradas[inicio:inicio + LINHAS_POR_PAGINA]

                    fig = Figure(figsize=(11.7, 8.3))
                    ax = fig.add_subplot(111)
                    ax.axis("off")

                    fig.suptitle("Relatório de Contas", fontsize=14, fontweight="bold", x=0.06, ha="left")
                    fig.text(0.06, 0.925, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}  •  {len(contas_filtradas)} lançamento(s)  •  Total: {formatar_moeda(total_geral)}", fontsize=9, color="#555")

                    linhas_tabela = [
                        [
                            str(c["id"]),
                            c["data_lancamento"],
                            c["tipo"],
                            (c["descricao"][:45] + "…") if len(c["descricao"]) > 45 else c["descricao"],
                            formatar_moeda(c["valor"]),
                            c["data_vencimento"],
                            c["forma_pagamento"],
                            status,
                        ]
                        for c, status in bloco
                    ]

                    tabela = ax.table(
                        cellText=linhas_tabela,
                        colLabels=["ID", "Lançamento", "Tipo", "Descrição", "Valor", "Vencimento", "Forma", "Status"],
                        loc="upper center",
                        cellLoc="left",
                        bbox=[0.0, 0.0, 1.0, 0.88],
                    )
                    tabela.auto_set_font_size(False)
                    tabela.set_fontsize(8)

                    for (linha, _col), celula in tabela.get_celld().items():
                        celula.set_edgecolor("#d7dee5")
                        if linha == 0:
                            celula.set_facecolor("#eef2f6")
                            celula.set_text_props(fontweight="bold")

                    pdf.savefig(fig)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar o PDF:\n{e}")
            return

        if messagebox.askyesno("Sucesso", "Relatório PDF gerado com sucesso!\nDeseja abrir o arquivo agora?"):
            abrir_arquivo_externo(caminho_pdf)

    def abrir_janela_relatorio(self):
        win_rel = tk.Toplevel(self.root)
        win_rel.title("Gerar Relatório para Impressão")
        win_rel.resizable(False, False)

        tk.Label(
            win_rel,
            text="Configurar Relatório / Impressão",
            font=(FONTE_UI, 11, "bold"),
            fg="#7d5fc4"
        ).pack(pady=(15, 10))

        frame_opts = tk.Frame(win_rel, padx=20)
        frame_opts.pack(fill="both", expand=True)

        tk.Label(frame_opts, text="Filtrar por Vencimento entre:", font=(FONTE_UI, 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(5, 5))

        tk.Label(frame_opts, text="Data Inicial:").grid(row=1, column=0, sticky="w")
        ent_data_ini = ttk.Entry(frame_opts, width=15)
        ent_data_ini.grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(frame_opts, text="Data Final:").grid(row=2, column=0, sticky="w")
        ent_data_fim = ttk.Entry(frame_opts, width=15)
        ent_data_fim.grid(row=2, column=1, sticky="w", pady=2)

        tk.Label(frame_opts, text="*(Deixe em branco para considerar todas as datas)", font=(FONTE_UI, 7), fg="#777").grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(frame_opts, text="Tipo / Status:").grid(row=4, column=0, sticky="w", pady=5)
        combo_rel_tipo = ttk.Combobox(
            frame_opts,
            values=[
                "Todos",
                "A Pagar - Em Aberto / Vencido",
                "A Pagar - Pago",
                "A Receber - Em Aberto / Vencido",
                "A Receber - Recebido",
                "Registro (No Ato)"
            ],
            state="readonly",
            width=26
        )
        combo_rel_tipo.set("Todos")
        combo_rel_tipo.grid(row=4, column=1, sticky="w", pady=5)

        def gerar_html():
            str_ini = ent_data_ini.get().strip()
            str_fim = ent_data_fim.get().strip()
            tipo_sel = combo_rel_tipo.get()

            dt_ini, dt_fim = None, None
            try:
                if str_ini:
                    dt_ini = datetime.strptime(str_ini, "%d/%m/%Y").date()
                if str_fim:
                    dt_fim = datetime.strptime(str_fim, "%d/%m/%Y").date()
            except ValueError:
                messagebox.showwarning("Aviso", "Formato de data inválido! Use DD/MM/AAAA.", parent=win_rel)
                return

            contas_filtradas = []
            total_valor = 0.0

            for c in self.contas:
                dias, status = self.calcular_status(c)

                if not self._valida_filtro_tipo(c, tipo_sel, status):
                    continue

                venc_str = c.get("data_vencimento", "")
                if dt_ini or dt_fim:
                    try:
                        dt_venc = datetime.strptime(venc_str, "%d/%m/%Y").date()
                        if dt_ini and dt_venc < dt_ini:
                            continue
                        if dt_fim and dt_venc > dt_fim:
                            continue
                    except ValueError:
                        continue

                contas_filtradas.append((c, status))
                total_valor += c.get("valor", 0.0)

            if not contas_filtradas:
                messagebox.showinfo("Informação", "Nenhum registro encontrado com os filtros selecionados.", parent=win_rel)
                return

            caminho_html = os.path.abspath("relatorio_contas.html")
            with open(caminho_html, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório Financeiro</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
        h1 {{ text-align: center; color: #222; margin-bottom: 5px; }}
        .sub {{ text-align: center; font-size: 12px; color: #666; margin-bottom: 20px; }}
        .summary {{ background: #eef2f6; padding: 12px; border-radius: 5px; margin-bottom: 20px; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #eef2f6; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #ffffff; }}
        .valor {{ text-align: right; }}
        .center {{ text-align: center; }}
        .btn-print {{ display: block; width: 200px; margin: 0 auto 20px auto; padding: 10px; background: #7d5fc4; color: white; text-align: center; font-weight: bold; text-decoration: none; border-radius: 5px; }}
        @media print {{ .btn-print {{ display: none; }} }}
    </style>
</head>
<body>
    <a href="#" class="btn-print" onclick="window.print(); return false;">🖨️ Imprimir / Salvar PDF</a>
    <h1>Relatório Financeiro de Contas</h1>
    <div class="sub">Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</div>

    <div class="summary">
        <strong>Filtro Aplicado:</strong> {tipo_sel}<br>
        <strong>Período:</strong> {str_ini if str_ini else 'Início'} até {str_fim if str_fim else 'Fim'}<br>
        <strong>Total de Registros:</strong> {len(contas_filtradas)} | <strong>Valor Somado:</strong> {formatar_moeda(total_valor)}
    </div>

    <table>
        <thead>
            <tr>
                <th class="center">ID</th>
                <th class="center">Lançamento</th>
                <th class="center">Tipo</th>
                <th>Descrição</th>
                <th class="center">Vencimento</th>
                <th class="center">Forma Pagto</th>
                <th class="center">Status</th>
                <th class="valor">Valor (R$)</th>
            </tr>
        </thead>
        <tbody>
""")
                for c, status in contas_filtradas:
                    f.write(f"""
            <tr>
                <td class="center">{c.get('id')}</td>
                <td class="center">{c.get('data_lancamento', '-')}</td>
                <td class="center">{c.get('tipo')}</td>
                <td>{c.get('descricao')}</td>
                <td class="center">{c.get('data_vencimento')}</td>
                <td class="center">{c.get('forma_pagamento')}</td>
                <td class="center">{status}</td>
                <td class="valor">{formatar_moeda(c.get('valor', 0.0))}</td>
            </tr>""")

                f.write("""
        </tbody>
    </table>
</body>
</html>""")

            webbrowser.open(f"file://{caminho_html}")
            win_rel.destroy()

        btn_gerar = tk.Button(
            win_rel,
            text="🌐 Gerar e Abrir Relatório",
            bg="#7d5fc4",
            fg="white",
            font=(FONTE_UI, 9, "bold"),
            command=gerar_html,
            cursor="hand2",
            pady=5
        )
        btn_gerar.pack(fill="x", padx=20, pady=15)

        self._centralizar_dialogo(win_rel, 450, 0)

    # ---------------- IMPORTAÇÃO E EXPORTAÇÃO CSV ----------------

    def abrir_janela_exportar(self):
        if not self.contas:
            messagebox.showwarning("Aviso", "Não há contas para exportar!")
            return

        self._criar_janela_selecao(
            titulo="Exportar Seleção de Contas (CSV)",
            lista_dados=self.contas,
            texto_confirmar="📤 Exportar Selecionados",
            acao_confirmar=self._executar_exportacao,
        )

    def _executar_exportacao(self, selecionados, janela):
        if not selecionados:
            messagebox.showwarning("Aviso", "Nenhum item foi selecionado para exportação!")
            return

        caminho = filedialog.asksaveasfilename(
            title="Exportar Arquivo CSV",
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os Arquivos", "*.*")],
        )

        if caminho:
            try:
                dados_exportar = [dict(item) for item in selecionados]
                for idx, item in enumerate(dados_exportar, start=1):
                    item["id"] = idx

                campos = [
                    "id", "data_lancamento", "tipo", "descricao",
                    "valor", "data_vencimento", "forma_pagamento", "pago"
                ]
                with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
                    escritor = csv.DictWriter(f, fieldnames=campos, delimiter=";")
                    escritor.writeheader()
                    for item in dados_exportar:
                        escritor.writerow(item)

                janela.destroy()
                messagebox.showinfo("Sucesso", f"{len(dados_exportar)} conta(s) exportada(s) com sucesso em CSV!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao exportar ficheiro CSV:\n{e}")

    def abrir_janela_importar(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV para Importar",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os Arquivos", "*.*")],
        )

        if not caminho:
            return

        try:
            dados_importados = []
            with open(caminho, "r", encoding="utf-8-sig", newline="") as f:
                leitor = csv.DictReader(f, delimiter=";")
                for row in leitor:
                    dados_importados.append({
                        "id": len(dados_importados) + 1,
                        "data_lancamento": row.get("data_lancamento", datetime.now().strftime("%d/%m/%Y")),
                        "tipo": row.get("tipo", "A Pagar"),
                        "descricao": row.get("descricao", ""),
                        "valor": float(row.get("valor", 0.0)),
                        "data_vencimento": row.get("data_vencimento", ""),
                        "forma_pagamento": row.get("forma_pagamento", "Pix"),
                        "pago": row.get("pago", "Não"),
                    })

            if not dados_importados:
                raise ValueError("Nenhum registro encontrado no arquivo CSV.")

            self._criar_janela_selecao(
                titulo="Importar Seleção de Contas (CSV)",
                lista_dados=dados_importados,
                texto_confirmar="📥 Importar Selecionados",
                acao_confirmar=self._executar_importacao,
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ler o arquivo CSV:\n{e}")

    def _executar_importacao(self, selecionados, janela):
        if not selecionados:
            messagebox.showwarning("Aviso", "Nenhum item foi selecionado para importação!")
            return

        for item in selecionados:
            nova_conta = dict(item)
            nova_conta["id"] = len(self.contas) + 1
            self.contas.append(nova_conta)

        for idx, c in enumerate(self.contas, start=1):
            c["id"] = idx

        self.salvar_dados()
        self.atualizar_tabela_e_cards()
        janela.destroy()
        messagebox.showinfo("Sucesso", f"{len(selecionados)} conta(s) importada(s) com sucesso!")

    def _criar_janela_selecao(self, titulo, lista_dados, texto_confirmar, acao_confirmar):
        win = tk.Toplevel(self.root)
        win.title(titulo)
        win.minsize(450, 350)

        tk.Label(
            win,
            text="Marque as contas que deseja incluir:",
            font=(FONTE_UI, 10, "bold"),
        ).pack(anchor="w", padx=15, pady=(15, 5))

        frame_scroll = tk.Frame(win)
        frame_scroll.pack(fill="both", expand=True, padx=15, pady=5)

        canvas = tk.Canvas(frame_scroll, borderwidth=1, relief="sunken", bg=self.COR_PAINEL, highlightthickness=0)
        win.canvas_rolagem = canvas  # usado por _on_roda: a roda rola esta lista, não a página de trás
        scrollbar = ttk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.COR_PAINEL)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        janela_lista = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        checks = []

        def _ajustar_largura(event):
            canvas.itemconfig(janela_lista, width=event.width)
            for cb in checks:
                cb.config(wraplength=max(event.width - 50, 150))

        canvas.bind("<Configure>", _ajustar_largura)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        vars_check = []
        for conta in lista_dados:
            var = tk.BooleanVar(value=True)
            desc = conta.get("descricao", "Sem Descrição")
            valor = conta.get("valor", 0.0)
            venc = conta.get("data_vencimento", "-")
            tipo = conta.get("tipo", "")

            texto_cb = f"[{tipo}] {desc} - {formatar_moeda(valor)} (Venc: {venc})"
            cb = tk.Checkbutton(
                scrollable_frame,
                text=texto_cb,
                variable=var,
                anchor="w",
                justify="left",
                bg=self.COR_PAINEL,
                activebackground=self.COR_PAINEL,
                activeforeground=self.COR_TEXTO,
                highlightthickness=0,
            )
            cb.pack(fill="x", padx=5, pady=2)
            checks.append(cb)
            vars_check.append((var, conta))

        def alternar_todos():
            estado_atual = any(v.get() for v, _ in vars_check)
            novo_estado = not estado_atual
            for v, _ in vars_check:
                v.set(novo_estado)

        frame_botoes = tk.Frame(win, pady=10, padx=15)
        frame_botoes.pack(fill="x")

        btn_marcar = tk.Button(
            frame_botoes,
            text="Selecionar / Desmarcar Tudo",
            command=alternar_todos,
            font=(FONTE_UI, 9),
            cursor="hand2",
        )
        btn_marcar.pack(side="left")

        def ao_confirmar():
            selecionados = [c for v, c in vars_check if v.get()]
            acao_confirmar(selecionados, win)

        btn_confirmar = tk.Button(
            frame_botoes,
            text=texto_confirmar,
            bg="#2f9e57",
            fg="white",
            font=(FONTE_UI, 9, "bold"),
            padx=10,
            command=ao_confirmar,
            cursor="hand2",
        )
        btn_confirmar.pack(side="right")

        self._centralizar_dialogo(win, 520, 450)


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        # Evita a interface "borrada" em telas com escala acima de 100%
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    app = GerenciadorContasApp(root)
    root.mainloop()

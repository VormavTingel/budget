import sqlite3
from datetime import date, datetime
from typing import Optional

import ttkbootstrap as tb
from tkinter import messagebox
from ttkbootstrap.constants import *

import matplotlib

from monthly_app.application.services import FinanceService
from monthly_app.config import FIX_CATS, FORMAS_PAGTO, RECEITA_COLS, RESERVA_META_PCT, VAR_CATS

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

PALETTE = {
    "primary": "#6647F0",
    "accent": "#4E8DFF",
    "orange": "#7CB8FF",
    "blue": "#2F80FF",
    "background": "#F7F8FC",
    "dark": "#292D34",
}


class App(tb.Window):
    def __init__(self, service: FinanceService):
        super().__init__(themename="litera")
        self.service = service
        self.title("Gestao Financeira (Mensal)")
        self.attributes("-fullscreen", True)
        self.option_add("*Font", "{Segoe UI} 10")
        self.palette = PALETTE
        self._apply_palette()

        self.current_ym = self._default_ym()
        self.month_id = self.service.ensure_month(self.current_ym)

        self._build_ui()
        self.refresh_all()

    def _default_ym(self) -> str:
        now = date.today()
        return f"{now.year:04d}-{now.month:02d}"

    def _apply_palette(self):
        colors = self.style.colors
        colors.set("primary", self.palette["primary"])
        colors.set("secondary", self.palette["accent"])
        colors.set("success", self.palette["blue"])
        colors.set("info", self.palette["blue"])
        colors.set("warning", self.palette["orange"])
        colors.set("danger", self.palette["accent"])
        colors.set("dark", self.palette["dark"])
        colors.set("light", self.palette["background"])
        colors.set("bg", self.palette["background"])
        colors.set("fg", self.palette["dark"])
        colors.set("selectbg", self.palette["primary"])
        colors.set("selectfg", self.palette["background"])
        colors.set("inputbg", "#FFFFFF")
        colors.set("inputfg", self.palette["dark"])
        colors.set("border", "#DDE1EE")

        # Less dense widgets for an app-like look
        self.style.configure("Treeview", rowheight=32)
        self.style.configure("Treeview.Heading", padding=(8, 8))
        self.style.configure("TButton", padding=(10, 8))
        self.style.configure("TEntry", padding=(8, 6))
        self.style.configure("TCombobox", padding=(8, 6))

        self.configure(bg=self.palette["background"])

    def _build_ui(self):
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        shell = tb.Frame(self, padding=0, bootstyle="light")
        shell.pack(fill=BOTH, expand=True)
        main = tb.Frame(shell, padding=(14, 12, 14, 8), bootstyle="light")
        main.pack(fill=BOTH, expand=True)

        header_card = tb.Labelframe(main, text="Workspace", padding=(14, 12), bootstyle="primary")
        header_card.pack(fill=X, pady=(0, 10))

        top = tb.Frame(header_card)
        top.pack(fill=X)

        tb.Label(top, text="Monthly", font=("Segoe UI", 17, "bold")).pack(side=LEFT, padx=(0, 12))
        tb.Label(top, text="Mes", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 6))

        self.month_var = tb.StringVar(value=self.current_ym)
        self.month_combo = tb.Combobox(top, textvariable=self.month_var, values=self._month_values(), width=12, state="readonly")
        self.month_combo.pack(side=LEFT)
        self.month_combo.bind("<<ComboboxSelected>>", lambda e: self.on_month_change())

        tb.Button(top, text="Novo mes", bootstyle="primary-outline", command=self.create_new_month).pack(side=LEFT, padx=8)
        tb.Label(top, text="Meta (%)", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(10, 6))
        self.meta_var = tb.DoubleVar(value=RESERVA_META_PCT)
        self.meta_entry = tb.Entry(top, textvariable=self.meta_var, width=8)
        self.meta_entry.pack(side=LEFT)
        tb.Button(top, text="Salvar", bootstyle="primary", command=self.save_meta).pack(side=LEFT, padx=6)
        tb.Button(top, text="Tela cheia", bootstyle="secondary-outline", command=lambda: self.attributes("-fullscreen", not self.attributes("-fullscreen"))).pack(side=RIGHT)

        filters_card = tb.Labelframe(main, text="Filtros", padding=(14, 10), bootstyle="light")
        filters_card.pack(fill=X, pady=(0, 10))

        filters = tb.Frame(filters_card)
        filters.pack(fill=X)
        tb.Label(filters, text="Busca:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 6))
        self.search_var = tb.StringVar(value="")
        tb.Entry(filters, textvariable=self.search_var, width=26).pack(side=LEFT)
        self.search_var.trace_add("write", lambda *_: self._on_filter_change())

        tb.Label(filters, text="Escopo:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(12, 6))
        self.search_scope_var = tb.StringVar(value="Tudo")
        scope_cb = tb.Combobox(filters, textvariable=self.search_scope_var, values=["Tudo", "Fixos", "Variaveis"], width=12, state="readonly")
        scope_cb.pack(side=LEFT)
        scope_cb.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        tb.Label(filters, text="Fixos:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(12, 6))
        self.fixed_paid_filter_var = tb.StringVar(value="Todos")
        fixed_cb = tb.Combobox(filters, textvariable=self.fixed_paid_filter_var, values=["Todos", "Pagos", "Nao pagos"], width=12, state="readonly")
        fixed_cb.pack(side=LEFT)
        fixed_cb.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        tb.Label(filters, text="Pessoa:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(12, 6))
        self.variable_person_filter_var = tb.StringVar(value="Todas")
        self.person_filter_combo = tb.Combobox(
            filters,
            textvariable=self.variable_person_filter_var,
            values=self._person_filter_values(),
            width=18,
            state="readonly",
        )
        self.person_filter_combo.pack(side=LEFT)
        self.person_filter_combo.bind("<<ComboboxSelected>>", self._on_person_filter_selected)

        tb.Button(filters, text="Limpar filtros", bootstyle="secondary-outline", command=self._clear_filters).pack(side=RIGHT)

        self.page_container = tb.Frame(main, padding=(0, 0, 0, 8), bootstyle="light")
        self.page_container.pack(fill=BOTH, expand=True)

        self.tab_receita = tb.Labelframe(self.page_container, text="Receita", padding=12, bootstyle="light")
        self.tab_fixos = tb.Labelframe(self.page_container, text="Custos Fixos", padding=12, bootstyle="light")
        self.tab_variaveis = tb.Labelframe(self.page_container, text="Custos Variaveis", padding=12, bootstyle="light")
        self.tab_dashboard = tb.Labelframe(self.page_container, text="Dashboard", padding=12, bootstyle="light")

        self.pages = {
            "receita": self.tab_receita,
            "fixos": self.tab_fixos,
            "variaveis": self.tab_variaveis,
            "dashboard": self.tab_dashboard,
        }

        for frame in self.pages.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.bottom_nav = tb.Frame(main, padding=(8, 8), bootstyle="light")
        self.bottom_nav.pack(fill=X, pady=(4, 0))
        self.nav_buttons = {}
        for key, label in [
            ("dashboard", "Dashboard"),
            ("receita", "Receita"),
            ("fixos", "Fixos"),
            ("variaveis", "Variaveis"),
        ]:
            btn = tb.Button(
                self.bottom_nav,
                text=label,
                bootstyle="light",
                command=lambda k=key: self._switch_page(k),
                width=16,
            )
            btn.pack(side=LEFT, fill=X, expand=True, padx=4)
            self.nav_buttons[key] = btn

        self._build_receita()
        self._build_fixos()
        self._build_variaveis()
        self._build_dashboard()
        self._switch_page("dashboard")

    def _switch_page(self, page_key: str):
        for key, frame in self.pages.items():
            if key == page_key:
                frame.lift()
            btn_style = "primary" if key == page_key else "light"
            self.nav_buttons[key].configure(bootstyle=btn_style)

    def _clear_filters(self):
        self.search_var.set("")
        self.search_scope_var.set("Tudo")
        self.fixed_paid_filter_var.set("Todos")
        self.variable_person_filter_var.set("Todas")
        self._on_filter_change()

    def _on_filter_change(self):
        self.refresh_fixos()
        self.refresh_variaveis()

    def _search_matches(self, text: str) -> bool:
        needle = self.search_var.get().strip().lower()
        if not needle:
            return True
        return needle in text.lower()

    def _filter_scope_allows(self, scope_name: str) -> bool:
        scope = self.search_scope_var.get()
        return scope in ("Tudo", scope_name)

    def _person_filter_values(self):
        names = [nome for nome, _email in self.service.list_people()]
        return ["Todas"] + names + ["Adicionar pessoa..."]

    def _refresh_person_filter_values(self):
        current = self.variable_person_filter_var.get()
        values = self._person_filter_values()
        self.person_filter_combo.configure(values=values)
        if current not in values:
            self.variable_person_filter_var.set("Todas")

    def _on_person_filter_selected(self, _event=None):
        selected = self.variable_person_filter_var.get()
        if selected == "Adicionar pessoa...":
            self._open_add_person_dialog()
            return
        self._on_filter_change()

    def _open_add_person_dialog(self, on_success=None, on_cancel=None):
        dlg = tb.Toplevel(self)
        dlg.title("Adicionar pessoa")
        dlg.geometry("420x210")
        dlg.resizable(False, False)

        frm = tb.Frame(dlg, padding=14)
        frm.pack(fill=BOTH, expand=True)

        nome_var = tb.StringVar()
        email_var = tb.StringVar()

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Nome", width=12).pack(side=LEFT)
        tb.Entry(row, textvariable=nome_var).pack(side=LEFT, fill=X, expand=True)

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Email", width=12).pack(side=LEFT)
        tb.Entry(row, textvariable=email_var).pack(side=LEFT, fill=X, expand=True)

        def salvar():
            nome = nome_var.get().strip()
            email = email_var.get().strip().lower()
            try:
                if not nome or not email or "@" not in email or "." not in email.split("@")[-1]:
                    raise ValueError
                self.service.add_person(nome, email)
                dlg.destroy()
                if on_success:
                    on_success(nome)
                else:
                    self._refresh_person_filter_values()
                    self.variable_person_filter_var.set(nome)
                    self._on_filter_change()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Nome ou email ja cadastrado.")
            except Exception:
                messagebox.showerror("Erro", "Informe nome e email validos.")

        def cancelar():
            dlg.destroy()
            if on_cancel:
                on_cancel()
            else:
                self.variable_person_filter_var.set("Todas")
                self._on_filter_change()

        btn = tb.Frame(frm)
        btn.pack(fill=X, pady=12)
        tb.Button(btn, text="Salvar", bootstyle=SUCCESS, command=salvar).pack(side=LEFT)
        tb.Button(btn, text="Cancelar", bootstyle=SECONDARY, command=cancelar).pack(side=LEFT, padx=8)

    def _month_values(self):
        vals = self.service.get_months()
        if self.current_ym not in vals:
            vals.append(self.current_ym)
        return sorted(vals)

    def _build_receita(self):
        frame = tb.Frame(self.tab_receita, padding=12)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text="Receitas por fonte (R$)", font=("Segoe UI", 12, "bold")).pack(anchor=W, pady=(0, 10))

        grid = tb.Frame(frame)
        grid.pack(anchor=W)

        self.income_vars = {k: tb.DoubleVar(value=0.0) for k in RECEITA_COLS}

        for i, col in enumerate(RECEITA_COLS):
            r = i // 3
            c = (i % 3) * 2
            tb.Label(grid, text=col).grid(row=r, column=c, sticky=W, padx=(0, 8), pady=6)
            ent = tb.Entry(grid, textvariable=self.income_vars[col], width=18)
            ent.grid(row=r, column=c + 1, sticky=W, pady=6)
            ent.bind("<FocusOut>", lambda e, k=col: self.save_income(k))
            ent.bind("<Return>", lambda e, k=col: self.save_income(k))

        tb.Separator(frame).pack(fill=X, pady=14)

        self.lbl_receita_status = tb.Label(frame, text="", font=("Segoe UI", 11))
        self.lbl_receita_status.pack(anchor=W)

        tb.Button(frame, text="Recalcular / Atualizar", bootstyle=INFO, command=self.refresh_all).pack(anchor=W, pady=10)

    def save_income(self, col: str):
        try:
            val = float(self.income_vars[col].get())
            if val < 0:
                raise ValueError("Valor negativo")
            self.service.set_income(self.month_id, col, val)
            self.refresh_all()
        except Exception:
            messagebox.showerror("Erro", f"Valor invalido em {col}.")

    def _build_fixos(self):
        frame = tb.Frame(self.tab_fixos, padding=12)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text="Custos Fixos (mensais)", font=("Segoe UI", 12, "bold")).pack(anchor=W, pady=(0, 10))

        self.fix_tree = tb.Treeview(frame, columns=("cat", "valor", "venc", "pago", "id"), show="headings", height=18)
        self.fix_tree.heading("cat", text="Categoria")
        self.fix_tree.heading("valor", text="Valor (R$)")
        self.fix_tree.heading("venc", text="Vencimento (dia)")
        self.fix_tree.heading("pago", text="Pago?")
        self.fix_tree.heading("id", text="")
        self.fix_tree.column("cat", width=260)
        self.fix_tree.column("valor", width=120, anchor=E)
        self.fix_tree.column("venc", width=130, anchor=CENTER)
        self.fix_tree.column("pago", width=80, anchor=CENTER)
        self.fix_tree.column("id", width=0, stretch=False)
        self.fix_tree.pack(fill=BOTH, expand=True)

        btns = tb.Frame(frame)
        btns.pack(fill=X, pady=10)
        tb.Button(btns, text="Adicionar", bootstyle=SUCCESS, command=self.add_fixed_dialog).pack(side=LEFT)
        tb.Button(btns, text="Editar item selecionado", bootstyle=PRIMARY, command=self.edit_fixed_dialog).pack(side=LEFT)
        tb.Button(btns, text="Marcar como pago/nao pago", bootstyle=SECONDARY, command=self.toggle_fixed_paid).pack(side=LEFT, padx=8)
        tb.Button(btns, text="Atualizar", bootstyle=INFO, command=self.refresh_all).pack(side=LEFT, padx=8)

    def add_fixed_dialog(self):
        dlg = tb.Toplevel(self)
        dlg.title("Adicionar custo fixo")
        dlg.geometry("420x300")
        dlg.resizable(False, False)

        frm = tb.Frame(dlg, padding=14)
        frm.pack(fill=BOTH, expand=True)

        cat_var = tb.StringVar()
        v_var = tb.DoubleVar(value=0.0)
        d_var = tb.IntVar(value=5)
        p_var = tb.StringVar(value="Nao")

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Categoria", width=14).pack(side=LEFT)
        tb.Entry(row, textvariable=cat_var).pack(side=LEFT, fill=X, expand=True)

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Valor (R$)", width=14).pack(side=LEFT)
        tb.Entry(row, textvariable=v_var).pack(side=LEFT, fill=X, expand=True)

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Vencimento", width=14).pack(side=LEFT)
        tb.Entry(row, textvariable=d_var).pack(side=LEFT, fill=X, expand=True)

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Pago?", width=14).pack(side=LEFT)
        tb.Combobox(row, values=["Sim", "Nao"], textvariable=p_var, state="readonly").pack(side=LEFT, fill=X, expand=True)

        def salvar():
            try:
                categoria = cat_var.get().strip()
                if not categoria:
                    raise ValueError
                valor = float(v_var.get())
                if valor < 0:
                    raise ValueError
                venc = int(d_var.get())
                if not (1 <= venc <= 31):
                    raise ValueError
                pago = 1 if p_var.get() == "Sim" else 0
                self.service.add_fixed(self.month_id, categoria, valor, venc, pago)
                dlg.destroy()
                self.refresh_all()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Categoria ja existe neste mes.")
            except Exception:
                messagebox.showerror("Erro", "Verifique categoria, valor e vencimento (1 a 31).")

        btn = tb.Frame(frm)
        btn.pack(fill=X, pady=12)
        tb.Button(btn, text="Salvar", bootstyle=SUCCESS, command=salvar).pack(side=LEFT)
        tb.Button(btn, text="Cancelar", bootstyle=SECONDARY, command=dlg.destroy).pack(side=LEFT, padx=8)

    def edit_fixed_dialog(self):
        sel = self.fix_tree.selection()
        if not sel:
            messagebox.showwarning("Atencao", "Selecione um item.")
            return
        iid = sel[0]
        vals = self.fix_tree.item(iid, "values")
        fixed_id = int(vals[4])
        cat = vals[0]
        valor = float(vals[1])
        venc = int(vals[2])
        pago = 1 if vals[3] == "Sim" else 0
        self._open_fixed_editor(fixed_id, cat, valor, venc, pago)

    def toggle_fixed_paid(self):
        sel = self.fix_tree.selection()
        if not sel:
            messagebox.showwarning("Atencao", "Selecione um item.")
            return
        iid = sel[0]
        vals = self.fix_tree.item(iid, "values")
        fixed_id = int(vals[4])
        _, valor_s, venc_s, pago_s = vals[0], vals[1], vals[2], vals[3]
        pago = 0 if pago_s == "Sim" else 1
        try:
            self.service.update_fixed(fixed_id, float(valor_s), int(venc_s), pago)
            self.refresh_all()
        except Exception:
            messagebox.showerror("Erro", "Falha ao atualizar item.")

    def _open_fixed_editor(self, fixed_id: int, categoria: str, valor: float, venc: int, pago: int):
        dlg = tb.Toplevel(self)
        dlg.title(f"Editar: {categoria}")
        dlg.geometry("420x260")
        dlg.resizable(False, False)

        frm = tb.Frame(dlg, padding=14)
        frm.pack(fill=BOTH, expand=True)

        tb.Label(frm, text=categoria, font=("Segoe UI", 12, "bold")).pack(anchor=W, pady=(0, 10))

        v_var = tb.DoubleVar(value=float(valor))
        d_var = tb.IntVar(value=int(venc))
        p_var = tb.StringVar(value="Sim" if pago else "Nao")

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Valor (R$)", width=14).pack(side=LEFT)
        tb.Entry(row, textvariable=v_var).pack(side=LEFT, fill=X, expand=True)

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Vencimento", width=14).pack(side=LEFT)
        tb.Entry(row, textvariable=d_var).pack(side=LEFT, fill=X, expand=True)

        row = tb.Frame(frm)
        row.pack(fill=X, pady=6)
        tb.Label(row, text="Pago?", width=14).pack(side=LEFT)
        tb.Combobox(row, values=["Sim", "Nao"], textvariable=p_var, state="readonly").pack(side=LEFT, fill=X, expand=True)

        def salvar():
            try:
                vv = float(v_var.get())
                if vv < 0:
                    raise ValueError
                dd = int(d_var.get())
                if not (1 <= dd <= 31):
                    raise ValueError
                pp = 1 if p_var.get() == "Sim" else 0
                self.service.update_fixed(fixed_id, vv, dd, pp)
                dlg.destroy()
                self.refresh_all()
            except Exception:
                messagebox.showerror("Erro", "Verifique valor e vencimento (1 a 31).")

        btn = tb.Frame(frm)
        btn.pack(fill=X, pady=12)
        tb.Button(btn, text="Salvar", bootstyle=SUCCESS, command=salvar).pack(side=LEFT)
        tb.Button(btn, text="Cancelar", bootstyle=SECONDARY, command=dlg.destroy).pack(side=LEFT, padx=8)

    def _build_variaveis(self):
        frame = tb.Frame(self.tab_variaveis, padding=12)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text="Lancamentos de Custos Variaveis", font=("Segoe UI", 12, "bold")).pack(anchor=W, pady=(0, 10))

        cols = ("data", "desc", "cat", "pay", "pessoa", "valor", "obs", "id")
        self.var_tree = tb.Treeview(frame, columns=cols, show="headings", height=18)
        self.var_tree.heading("data", text="Data")
        self.var_tree.heading("desc", text="Descricao")
        self.var_tree.heading("cat", text="Categoria")
        self.var_tree.heading("pay", text="Pagamento")
        self.var_tree.heading("pessoa", text="Pessoa")
        self.var_tree.heading("valor", text="Valor (R$)")
        self.var_tree.heading("obs", text="Obs")
        self.var_tree.heading("id", text="")

        self.var_tree.column("data", width=95)
        self.var_tree.column("desc", width=220)
        self.var_tree.column("cat", width=160)
        self.var_tree.column("pay", width=110)
        self.var_tree.column("pessoa", width=90)
        self.var_tree.column("valor", width=110, anchor=E)
        self.var_tree.column("obs", width=180)
        self.var_tree.column("id", width=0, stretch=False)

        self.var_tree.pack(fill=BOTH, expand=True)

        btns = tb.Frame(frame)
        btns.pack(fill=X, pady=8)
        tb.Button(btns, text="Adicionar", bootstyle=SUCCESS, command=self.add_variable_dialog).pack(side=LEFT)
        tb.Button(btns, text="Editar item selecionado", bootstyle=PRIMARY, command=self.edit_variable_dialog).pack(side=LEFT, padx=8)
        tb.Button(btns, text="Excluir selecionado", bootstyle=DANGER, command=self.delete_variable).pack(side=LEFT)
        tb.Button(btns, text="Atualizar", bootstyle=INFO, command=self.refresh_all).pack(side=LEFT, padx=8)

    def add_variable_dialog(self):
        self._open_variable_editor()

    def edit_variable_dialog(self):
        sel = self.var_tree.selection()
        if not sel:
            messagebox.showwarning("Atencao", "Selecione um lancamento.")
            return
        iid = sel[0]
        vals = self.var_tree.item(iid, "values")
        self._open_variable_editor(
            var_id=int(vals[7]),
            data_s=vals[0],
            desc=vals[1],
            cat=vals[2],
            pay=vals[3],
            pessoa=vals[4],
            valor=vals[5],
            obs=vals[6],
        )

    def _open_variable_editor(
        self,
        var_id: Optional[int] = None,
        data_s: str = "",
        desc: str = "",
        cat: str = "",
        pay: str = "",
        pessoa: str = "",
        valor: str = "",
        obs: str = "",
    ):
        dlg = tb.Toplevel(self)
        dlg.title("Adicionar lancamento" if var_id is None else "Editar lancamento")
        dlg.geometry("460x360")
        dlg.resizable(False, False)

        frm = tb.Frame(dlg, padding=14)
        frm.pack(fill=BOTH, expand=True)

        data_var = tb.StringVar(value=data_s or "")
        desc_var = tb.StringVar(value=desc or "")
        pay_var = tb.StringVar(value=pay or "")
        pessoa_var = tb.StringVar(value=pessoa or "")
        valor_var = tb.StringVar(value=str(valor) if valor is not None else "")
        obs_var = tb.StringVar(value=obs or "")

        def add_row(label: str, var):
            row = tb.Frame(frm)
            row.pack(fill=X, pady=5)
            tb.Label(row, text=label, width=14).pack(side=LEFT)
            tb.Entry(row, textvariable=var).pack(side=LEFT, fill=X, expand=True)

        add_row("Data", data_var)
        add_row("Descricao", desc_var)
        add_row("Pagamento", pay_var)
        person_row = tb.Frame(frm)
        person_row.pack(fill=X, pady=5)
        tb.Label(person_row, text="Pessoa", width=14).pack(side=LEFT)
        person_values = [nome for nome, _email in self.service.list_people()]
        if pessoa_var.get() and pessoa_var.get() not in person_values and pessoa_var.get() != "Adicionar pessoa...":
            person_values.append(pessoa_var.get())
        person_values = sorted(person_values) + ["Adicionar pessoa..."]
        person_combo = tb.Combobox(person_row, textvariable=pessoa_var, values=person_values, state="readonly")
        person_combo.pack(side=LEFT, fill=X, expand=True)
        last_person = {"value": pessoa_var.get()}

        def on_person_selected(_event=None):
            if pessoa_var.get() != "Adicionar pessoa...":
                last_person["value"] = pessoa_var.get()
                return

            def success(nome: str):
                updated_values = [n for n, _e in self.service.list_people()]
                if nome not in updated_values:
                    updated_values.append(nome)
                person_combo.configure(values=sorted(updated_values) + ["Adicionar pessoa..."])
                pessoa_var.set(nome)
                last_person["value"] = nome
                self._refresh_person_filter_values()

            def cancel():
                pessoa_var.set(last_person["value"])

            self._open_add_person_dialog(on_success=success, on_cancel=cancel)

        person_combo.bind("<<ComboboxSelected>>", on_person_selected)
        add_row("Valor (R$)", valor_var)
        add_row("Obs", obs_var)

        def salvar():
            try:
                d = data_var.get().strip()
                if d:
                    datetime.strptime(d, "%Y-%m-%d")
                val = float(valor_var.get().strip())
                if val < 0:
                    raise ValueError

                if var_id is None:
                    self.service.add_variable(
                        self.month_id,
                        d,
                        desc_var.get().strip(),
                        "",
                        pay_var.get().strip(),
                        pessoa_var.get().strip(),
                        val,
                        obs_var.get().strip(),
                    )
                else:
                    self.service.update_variable(
                        var_id,
                        d,
                        desc_var.get().strip(),
                        "",
                        pay_var.get().strip(),
                        pessoa_var.get().strip(),
                        val,
                        obs_var.get().strip(),
                    )
                dlg.destroy()
                self.refresh_all()
            except Exception:
                messagebox.showerror("Erro", "Verifique data (YYYY-MM-DD) e valor.")

        btn = tb.Frame(frm)
        btn.pack(fill=X, pady=12)
        tb.Button(btn, text="Salvar", bootstyle=SUCCESS, command=salvar).pack(side=LEFT)
        tb.Button(btn, text="Cancelar", bootstyle=SECONDARY, command=dlg.destroy).pack(side=LEFT, padx=8)

    def delete_variable(self):
        sel = self.var_tree.selection()
        if not sel:
            messagebox.showwarning("Atencao", "Selecione um lancamento.")
            return
        iid = sel[0]
        vals = self.var_tree.item(iid, "values")
        var_id = int(vals[7])
        if messagebox.askyesno("Confirmar", "Excluir lancamento selecionado?"):
            self.service.delete_variable(var_id)
            self.refresh_all()

    def _build_dashboard(self):
        frame = tb.Frame(self.tab_dashboard, padding=12)
        frame.pack(fill=BOTH, expand=True)

        top = tb.Frame(frame)
        top.pack(fill=X, pady=(0, 10))

        self.kpi_receita_var = tb.StringVar(value="R$ 0,00")
        self.kpi_custos_var = tb.StringVar(value="R$ 0,00")
        self.kpi_resultado_var = tb.StringVar(value="R$ 0,00")
        self.kpi_reserva_var = tb.StringVar(value="0,00%")

        cards = [
            ("Receita Total", self.kpi_receita_var, "success"),
            ("Custos Totais", self.kpi_custos_var, "warning"),
            ("Resultado", self.kpi_resultado_var, "primary"),
            ("Reserva", self.kpi_reserva_var, "info"),
        ]
        for title, value_var, style in cards:
            card = tb.Labelframe(top, text=title, bootstyle=style, padding=10)
            card.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
            tb.Label(card, textvariable=value_var, font=("Segoe UI", 14, "bold")).pack(anchor=W)

        self.fig = Figure(figsize=(9.5, 4.5), dpi=100)
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        self.fig.patch.set_facecolor(self.palette["background"])
        self.ax1.set_facecolor("#FFFFFF")
        self.ax2.set_facecolor("#FFFFFF")

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True, pady=10)

        tb.Button(frame, text="Atualizar graficos", bootstyle=INFO, command=self.refresh_all).pack(anchor=E)

    def on_month_change(self):
        ym = self.month_var.get()
        self.current_ym = ym
        self.month_id = self.service.ensure_month(ym)
        self.meta_var.set(self.service.get_meta_reserva_pct(self.month_id))
        self.refresh_all()

    def create_new_month(self):
        y, m = map(int, self.current_ym.split("-"))
        m += 1
        if m == 13:
            m = 1
            y += 1
        new_ym = f"{y:04d}-{m:02d}"
        source_month_id = self.month_id
        target_month_id = self.service.ensure_month(new_ym)
        self.service.clone_month_basics(source_month_id, target_month_id)
        self.month_combo["values"] = self._month_values()
        self.month_var.set(new_ym)
        self.on_month_change()

    def save_meta(self):
        try:
            pct = float(self.meta_var.get())
            if pct <= 0 or pct > 1:
                raise ValueError
            self.service.set_meta_reserva_pct(self.month_id, pct)
            self.refresh_all()
        except Exception:
            messagebox.showerror("Erro", "Meta deve ser entre 0 e 1 (ex: 0.15 = 15%).")

    def refresh_all(self):
        self.refresh_receita()
        self.refresh_fixos()
        self.refresh_variaveis()
        self.refresh_dashboard()

    def refresh_receita(self):
        inc = self.service.get_incomes(self.month_id)
        for k, v in inc.items():
            self.income_vars[k].set(v)

        t = self.service.totals(self.month_id)
        txt = (
            f"Total Receita: R$ {t.total_receita:.2f} | "
            f"Fixos: R$ {t.total_fix:.2f} | Variaveis: R$ {t.total_var:.2f} | "
            f"Resultado: R$ {t.resultado:.2f} | "
            f"Reserva: {t.reserva_pct*100:.2f}% (Meta {t.meta_pct*100:.0f}%) | "
            f"Atingiu meta: {'SIM' if t.atingiu else 'NAO'}"
        )
        self.lbl_receita_status.config(text=txt)

    def refresh_fixos(self):
        for item in self.fix_tree.get_children():
            self.fix_tree.delete(item)

        show_paid = self.fixed_paid_filter_var.get()
        allow_fixed_scope = self._filter_scope_allows("Fixos")
        for row in self.service.list_fixed(self.month_id):
            if allow_fixed_scope and not self._search_matches(f"{row.categoria} {row.valor:.2f} {row.vencimento_dia} {'Sim' if row.pago else 'Nao'}"):
                continue
            if show_paid == "Pagos" and row.pago != 1:
                continue
            if show_paid == "Nao pagos" and row.pago != 0:
                continue
            iid = f"fix_{row.id}"
            self.fix_tree.insert("", END, iid=iid, values=(row.categoria, f"{row.valor:.2f}", str(row.vencimento_dia), "Sim" if row.pago else "Nao", str(row.id)))

        self.fix_tree.bind("<Double-1>", self._on_fixed_double_click)

    def _on_fixed_double_click(self, event):
        sel = self.fix_tree.selection()
        if not sel:
            return
        self.edit_fixed_dialog()

    def refresh_variaveis(self):
        for item in self.var_tree.get_children():
            self.var_tree.delete(item)

        person_filter = self.variable_person_filter_var.get()
        allow_var_scope = self._filter_scope_allows("Variaveis")
        rows = self.service.list_variable(self.month_id)
        for row in rows:
            if person_filter not in ("Todas", "Adicionar pessoa...") and (row.pessoa or "") != person_filter:
                continue
            if allow_var_scope and not self._search_matches(
                f"{row.data or ''} {row.descricao or ''} {row.categoria or ''} {row.forma_pagto or ''} {row.pessoa or ''} {row.valor:.2f} {row.obs or ''}"
            ):
                continue
            iid = f"var_{row.id}"
            self.var_tree.insert(
                "",
                END,
                iid=iid,
                values=(
                    row.data or "",
                    row.descricao or "",
                    row.categoria or "",
                    row.forma_pagto or "",
                    row.pessoa or "",
                    f"{float(row.valor):.2f}",
                    row.obs or "",
                    str(row.id),
                ),
            )

        self.var_tree.bind("<Double-1>", self._on_variable_double_click)

    def _on_variable_double_click(self, event):
        sel = self.var_tree.selection()
        if not sel:
            return
        self.edit_variable_dialog()

    def refresh_dashboard(self):
        t = self.service.totals(self.month_id)
        self.kpi_receita_var.set(f"R$ {t.total_receita:.2f}")
        self.kpi_custos_var.set(f"R$ {(t.total_fix + t.total_var):.2f}")
        self.kpi_resultado_var.set(f"R$ {t.resultado:.2f}")
        self.kpi_reserva_var.set(f"{t.reserva_pct*100:.2f}% (meta {t.meta_pct*100:.0f}%)")

        self.ax1.clear()
        self.ax2.clear()
        self.fig.patch.set_facecolor(self.palette["background"])
        self.ax1.set_facecolor("#FFFFFF")
        self.ax2.set_facecolor("#FFFFFF")

        receita = t.total_receita
        custos = t.total_fix + t.total_var
        resultado = t.resultado

        self.ax1.bar(
            ["Receita", "Custos", "Resultado"],
            [receita, custos, resultado],
            color=[self.palette["primary"], self.palette["orange"], self.palette["blue"]],
        )
        self.ax1.set_title("Receita x Custos")
        self.ax1.set_ylabel("R$")

        series = self.service.annual_series()
        if series:
            yms = [s[0] for s in series]
            res = [s[4] for s in series]
            rec = [s[1] for s in series]
            self.ax2.plot(yms, rec, label="Receita", color=self.palette["primary"], linewidth=2.2)
            self.ax2.plot(yms, res, label="Resultado", color=self.palette["accent"], linewidth=2.2)
            self.ax2.set_title("Evolucao (meses cadastrados)")
            self.ax2.tick_params(axis="x", rotation=45)
            self.ax2.legend()

        self.fig.tight_layout()
        self.canvas.draw()

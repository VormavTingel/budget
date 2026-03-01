import sqlite3
from typing import Dict, List, Tuple

from monthly_app.config import FIX_CATS, RECEITA_COLS, RESERVA_META_PCT
from monthly_app.domain.entities import FixedCost, Totals, VariableCost


class SQLiteFinanceRepository:
    def __init__(self, path: str = "financas.db"):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._migrate()

    def _migrate(self):
        c = self.conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS months (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ym TEXT UNIQUE NOT NULL,
                meta_reserva_pct REAL NOT NULL DEFAULT 0.15
            );
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS incomes (
                month_id INTEGER PRIMARY KEY,
                Ether REAL NOT NULL DEFAULT 0,
                Mazza REAL NOT NULL DEFAULT 0,
                Melissa REAL NOT NULL DEFAULT 0,
                Rogério REAL NOT NULL DEFAULT 0,
                Nelly REAL NOT NULL DEFAULT 0,
                Asami REAL NOT NULL DEFAULT 0,
                Erica REAL NOT NULL DEFAULT 0,
                Uber REAL NOT NULL DEFAULT 0,
                Outros REAL NOT NULL DEFAULT 0,
                FOREIGN KEY(month_id) REFERENCES months(id) ON DELETE CASCADE
            );
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS fixed_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_id INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                valor REAL NOT NULL DEFAULT 0,
                vencimento_dia INTEGER NOT NULL DEFAULT 5,
                pago INTEGER NOT NULL DEFAULT 0,
                UNIQUE(month_id, categoria),
                FOREIGN KEY(month_id) REFERENCES months(id) ON DELETE CASCADE
            );
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS variable_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_id INTEGER NOT NULL,
                data TEXT,
                descricao TEXT,
                categoria TEXT,
                forma_pagto TEXT,
                pessoa TEXT,
                valor REAL NOT NULL DEFAULT 0,
                obs TEXT,
                FOREIGN KEY(month_id) REFERENCES months(id) ON DELETE CASCADE
            );
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE
            );
            """
        )
        self.conn.commit()

    def ensure_month(self, ym: str) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO months(ym, meta_reserva_pct) VALUES(?, ?)", (ym, RESERVA_META_PCT))
        self.conn.commit()
        cur.execute("SELECT id FROM months WHERE ym=?", (ym,))
        (mid,) = cur.fetchone()

        cur.execute("INSERT OR IGNORE INTO incomes(month_id) VALUES(?)", (mid,))
        for cat in FIX_CATS:
            cur.execute(
                """
                INSERT OR IGNORE INTO fixed_costs(month_id, categoria, valor, vencimento_dia, pago)
                VALUES(?, ?, 0, 5, 0)
                """,
                (mid, cat),
            )
        self.conn.commit()
        return mid

    def get_months(self) -> List[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT ym FROM months ORDER BY ym")
        return [r[0] for r in cur.fetchall()]

    def get_meta_reserva_pct(self, month_id: int) -> float:
        cur = self.conn.cursor()
        cur.execute("SELECT meta_reserva_pct FROM months WHERE id=?", (month_id,))
        return float(cur.fetchone()[0])

    def set_meta_reserva_pct(self, month_id: int, pct: float):
        self.conn.execute("UPDATE months SET meta_reserva_pct=? WHERE id=?", (pct, month_id))
        self.conn.commit()

    def get_incomes(self, month_id: int) -> Dict[str, float]:
        cur = self.conn.cursor()
        cur.execute("SELECT " + ",".join(RECEITA_COLS) + " FROM incomes WHERE month_id=?", (month_id,))
        row = cur.fetchone()
        return {k: float(v) for k, v in zip(RECEITA_COLS, row)} if row else {k: 0.0 for k in RECEITA_COLS}

    def set_income(self, month_id: int, col: str, value: float):
        self.conn.execute(f"UPDATE incomes SET [{col}]=? WHERE month_id=?", (value, month_id))
        self.conn.commit()

    def list_people(self) -> List[Tuple[str, str]]:
        cur = self.conn.cursor()
        cur.execute("SELECT nome, email FROM people ORDER BY nome")
        return [(row[0], row[1]) for row in cur.fetchall()]

    def add_person(self, nome: str, email: str):
        self.conn.execute(
            """
            INSERT INTO people(nome, email)
            VALUES(?, ?)
            """,
            (nome.strip(), email.strip().lower()),
        )
        self.conn.commit()

    def list_fixed(self, month_id: int) -> List[FixedCost]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, categoria, valor, vencimento_dia, pago
            FROM fixed_costs
            WHERE month_id=?
            ORDER BY categoria
            """,
            (month_id,),
        )
        return [FixedCost(*row) for row in cur.fetchall()]

    def add_fixed(self, month_id: int, categoria: str, valor: float, vencimento: int, pago: int):
        self.conn.execute(
            """
            INSERT INTO fixed_costs(month_id, categoria, valor, vencimento_dia, pago)
            VALUES(?,?,?,?,?)
            """,
            (month_id, categoria, valor, vencimento, pago),
        )
        self.conn.commit()

    def update_fixed(self, fixed_id: int, valor: float, vencimento: int, pago: int):
        self.conn.execute(
            """
            UPDATE fixed_costs SET valor=?, vencimento_dia=?, pago=?
            WHERE id=?
            """,
            (valor, vencimento, pago, fixed_id),
        )
        self.conn.commit()

    def list_variable(self, month_id: int) -> List[VariableCost]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, data, descricao, categoria, forma_pagto, pessoa, valor, obs
            FROM variable_costs
            WHERE month_id=?
            ORDER BY COALESCE(data,'9999-12-31') DESC, id DESC
            """,
            (month_id,),
        )
        return [VariableCost(*row) for row in cur.fetchall()]

    def add_variable(self, month_id: int, data_s: str, desc: str, cat: str, pay: str, pessoa: str, valor: float, obs: str):
        self.conn.execute(
            """
            INSERT INTO variable_costs(month_id, data, descricao, categoria, forma_pagto, pessoa, valor, obs)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (month_id, data_s, desc, cat, pay, pessoa, valor, obs),
        )
        self.conn.commit()

    def update_variable(self, var_id: int, data_s: str, desc: str, cat: str, pay: str, pessoa: str, valor: float, obs: str):
        self.conn.execute(
            """
            UPDATE variable_costs
            SET data=?, descricao=?, categoria=?, forma_pagto=?, pessoa=?, valor=?, obs=?
            WHERE id=?
            """,
            (data_s, desc, cat, pay, pessoa, valor, obs, var_id),
        )
        self.conn.commit()

    def delete_variable(self, var_id: int):
        self.conn.execute("DELETE FROM variable_costs WHERE id=?", (var_id,))
        self.conn.commit()

    def totals(self, month_id: int) -> Totals:
        inc = self.get_incomes(month_id)
        total_receita = sum(inc.values())

        cur = self.conn.cursor()
        cur.execute("SELECT COALESCE(SUM(valor),0) FROM fixed_costs WHERE month_id=?", (month_id,))
        total_fix = float(cur.fetchone()[0])

        cur.execute("SELECT COALESCE(SUM(valor),0) FROM variable_costs WHERE month_id=?", (month_id,))
        total_var = float(cur.fetchone()[0])

        resultado = total_receita - total_fix - total_var
        reserva_pct = (resultado / total_receita) if total_receita else 0.0
        meta_pct = self.get_meta_reserva_pct(month_id)

        return Totals(
            total_receita=total_receita,
            total_fix=total_fix,
            total_var=total_var,
            resultado=resultado,
            reserva_pct=reserva_pct,
            meta_pct=meta_pct,
            atingiu=reserva_pct >= meta_pct,
        )

    def annual_series(self) -> List[Tuple[str, float, float, float, float]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, ym FROM months ORDER BY ym")
        months = cur.fetchall()
        out: List[Tuple[str, float, float, float, float]] = []
        for mid, ym in months:
            t = self.totals(mid)
            out.append((ym, t.total_receita, t.total_fix, t.total_var, t.resultado))
        return out

    def clone_month_basics(self, source_month_id: int, target_month_id: int):
        cur = self.conn.cursor()

        cur.execute("SELECT " + ",".join(RECEITA_COLS) + " FROM incomes WHERE month_id=?", (source_month_id,))
        src_income = cur.fetchone()
        if src_income:
            set_clause = ", ".join([f"[{col}]=?" for col in RECEITA_COLS])
            cur.execute(f"UPDATE incomes SET {set_clause} WHERE month_id=?", (*src_income, target_month_id))

        cur.execute(
            """
            SELECT categoria, valor, vencimento_dia, pago
            FROM fixed_costs
            WHERE month_id=?
            """,
            (source_month_id,),
        )
        for categoria, valor, vencimento, pago in cur.fetchall():
            cur.execute(
                """
                UPDATE fixed_costs
                SET valor=?, vencimento_dia=?, pago=?
                WHERE month_id=? AND categoria=?
                """,
                (valor, vencimento, pago, target_month_id, categoria),
            )

        self.conn.commit()

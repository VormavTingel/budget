from typing import Dict, List, Tuple

from monthly_app.domain.entities import FixedCost, Totals, VariableCost
from monthly_app.infrastructure.sqlite_repo import SQLiteFinanceRepository


class FinanceService:
    def __init__(self, repo: SQLiteFinanceRepository):
        self.repo = repo

    def ensure_month(self, ym: str) -> int:
        return self.repo.ensure_month(ym)

    def get_months(self) -> List[str]:
        return self.repo.get_months()

    def get_meta_reserva_pct(self, month_id: int) -> float:
        return self.repo.get_meta_reserva_pct(month_id)

    def set_meta_reserva_pct(self, month_id: int, pct: float):
        self.repo.set_meta_reserva_pct(month_id, pct)

    def get_incomes(self, month_id: int) -> Dict[str, float]:
        return self.repo.get_incomes(month_id)

    def set_income(self, month_id: int, col: str, value: float):
        self.repo.set_income(month_id, col, value)

    def list_people(self) -> List[Tuple[str, str]]:
        return self.repo.list_people()

    def add_person(self, nome: str, email: str):
        self.repo.add_person(nome, email)

    def list_fixed(self, month_id: int) -> List[FixedCost]:
        return self.repo.list_fixed(month_id)

    def add_fixed(self, month_id: int, categoria: str, valor: float, vencimento: int, pago: int):
        self.repo.add_fixed(month_id, categoria, valor, vencimento, pago)

    def update_fixed(self, fixed_id: int, valor: float, vencimento: int, pago: int):
        self.repo.update_fixed(fixed_id, valor, vencimento, pago)

    def list_variable(self, month_id: int) -> List[VariableCost]:
        return self.repo.list_variable(month_id)

    def add_variable(self, month_id: int, data_s: str, desc: str, cat: str, pay: str, pessoa: str, valor: float, obs: str):
        self.repo.add_variable(month_id, data_s, desc, cat, pay, pessoa, valor, obs)

    def update_variable(self, var_id: int, data_s: str, desc: str, cat: str, pay: str, pessoa: str, valor: float, obs: str):
        self.repo.update_variable(var_id, data_s, desc, cat, pay, pessoa, valor, obs)

    def delete_variable(self, var_id: int):
        self.repo.delete_variable(var_id)

    def totals(self, month_id: int) -> Totals:
        return self.repo.totals(month_id)

    def annual_series(self) -> List[Tuple[str, float, float, float, float]]:
        return self.repo.annual_series()

    def clone_month_basics(self, source_month_id: int, target_month_id: int):
        self.repo.clone_month_basics(source_month_id, target_month_id)

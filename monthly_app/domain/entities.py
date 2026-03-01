from dataclasses import dataclass
from typing import Optional


@dataclass
class FixedCost:
    id: int
    categoria: str
    valor: float
    vencimento_dia: int
    pago: int


@dataclass
class VariableCost:
    id: int
    data: Optional[str]
    descricao: Optional[str]
    categoria: Optional[str]
    forma_pagto: Optional[str]
    pessoa: Optional[str]
    valor: float
    obs: Optional[str]


@dataclass
class Totals:
    total_receita: float
    total_fix: float
    total_var: float
    resultado: float
    reserva_pct: float
    meta_pct: float
    atingiu: bool

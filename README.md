# Monthly - Gestao Financeira Mensal

Aplicativo desktop em Python para controle financeiro mensal, com interface grafica em Tkinter/ttkbootstrap e persistencia em SQLite.

## Funcionalidades
- Cadastro e selecao de meses (`YYYY-MM`)
- Controle de receitas por fonte
- Controle de custos fixos e variaveis
- Cadastro de pessoas para associar lancamentos
- Meta de reserva mensal (ex.: `0.15` para 15%)
- Dashboard com indicadores e graficos

## Requisitos
- Python 3.10+
- Dependencias:
  - `ttkbootstrap`
  - `matplotlib`

## Instalacao
```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
pip install ttkbootstrap matplotlib
```

## Como executar
Na raiz do projeto:

```bash
python monthly.py
```

O banco local `financas.db` sera criado/atualizado automaticamente.

## Estrutura do projeto
```text
monthly.py                  # ponto de entrada
monthly_app/
  application/              # servicos de aplicacao
  domain/                   # entidades de dominio
  infrastructure/           # repositorio SQLite
  presentation/             # interface Tkinter
  config.py                 # configuracoes e categorias
```

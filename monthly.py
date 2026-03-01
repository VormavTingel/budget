from monthly_app.application.services import FinanceService
from monthly_app.infrastructure.sqlite_repo import SQLiteFinanceRepository
from monthly_app.presentation.tk_app import App


def main():
    service = FinanceService(SQLiteFinanceRepository(path="financas.db"))
    App(service).mainloop()


if __name__ == "__main__":
    main()

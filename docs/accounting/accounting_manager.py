from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Account, AccountType, JournalEntry, JournalLine, FiscalYear

class AccountingManager:
    def create_account(self, session: Session, code: str, name: str, account_type: AccountType,
                      description: str = None, parent_code: str = None) -> Account:
        """새로운 계정과목을 생성합니다."""
        account = Account(
            code=code,
            name=name,
            type=account_type,
            description=description
        )
        
        if parent_code:
            parent = session.query(Account).filter_by(code=parent_code).first()
            if parent:
                account.parent_id = parent.id
        
        session.add(account)
        session.commit()
        return account

    def create_journal_entry(self, session: Session, entry_date: datetime,
                           description: str, lines: list, created_by: str) -> JournalEntry:
        """새로운 전표를 생성합니다."""
        # 차변과 대변의 합계가 일치하는지 검증
        total_debit = sum(line['debit'] for line in lines)
        total_credit = sum(line['credit'] for line in lines)
        
        if abs(total_debit - total_credit) > 0.01:  # 반올림 오차 허용
            raise ValueError("차변과 대변의 합계가 일치하지 않습니다.")
        
        entry = JournalEntry(
            entry_date=entry_date,
            description=description,
            created_by=created_by
        )
        
        session.add(entry)
        session.flush()  # ID 생성을 위해 flush
        
        for line in lines:
            journal_line = JournalLine(
                entry_id=entry.id,
                account_id=line['account_id'],
                debit=line['debit'],
                credit=line['credit'],
                description=line.get('description')
            )
            session.add(journal_line)
        
        session.commit()
        return entry

    def create_fiscal_year(self, session: Session, year: int) -> FiscalYear:
        """새로운 회계연도를 생성합니다."""
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        fiscal_year = FiscalYear(
            year=year,
            start_date=start_date,
            end_date=end_date
        )
        
        session.add(fiscal_year)
        session.commit()
        return fiscal_year

    def close_fiscal_year(self, session: Session, fiscal_year_id: int, closed_by: str) -> FiscalYear:
        """회계연도를 마감합니다."""
        fiscal_year = session.query(FiscalYear).get(fiscal_year_id)
        if not fiscal_year:
            raise ValueError("회계연도를 찾을 수 없습니다.")
        
        if fiscal_year.is_closed:
            raise ValueError("이미 마감된 회계연도입니다.")
        
        # 수익과 비용 계정의 잔액을 자본금으로 대체
        retained_earnings = self._calculate_retained_earnings(session, fiscal_year)
        
        if retained_earnings != 0:
            # 결산 전표 생성
            closing_entry = self.create_journal_entry(
                session=session,
                entry_date=fiscal_year.end_date,
                description=f"{fiscal_year.year}년 결산 전표",
                lines=[
                    {
                        'account_id': self._get_retained_earnings_account(session).id,
                        'debit': retained_earnings if retained_earnings > 0 else 0,
                        'credit': -retained_earnings if retained_earnings < 0 else 0,
                        'description': "당기순이익(손실) 대체"
                    }
                ],
                created_by=closed_by
            )
        
        fiscal_year.is_closed = True
        fiscal_year.closed_at = datetime.utcnow()
        fiscal_year.closed_by = closed_by
        
        session.commit()
        return fiscal_year

    def _calculate_retained_earnings(self, session: Session, fiscal_year: FiscalYear) -> float:
        """해당 회계연도의 당기순이익을 계산합니다."""
        total_revenue = 0
        total_expense = 0
        
        # 수익과 비용 계정의 전표 내역 조회
        revenue_accounts = session.query(Account).filter_by(type=AccountType.REVENUE).all()
        expense_accounts = session.query(Account).filter_by(type=AccountType.EXPENSE).all()
        
        for account in revenue_accounts:
            for line in account.journal_lines:
                if (line.entry.entry_date >= fiscal_year.start_date and
                    line.entry.entry_date <= fiscal_year.end_date):
                    total_revenue += line.credit - line.debit
        
        for account in expense_accounts:
            for line in account.journal_lines:
                if (line.entry.entry_date >= fiscal_year.start_date and
                    line.entry.entry_date <= fiscal_year.end_date):
                    total_expense += line.debit - line.credit
        
        return total_revenue - total_expense

    def _get_retained_earnings_account(self, session: Session) -> Account:
        """이익잉여금 계정을 조회하거나 생성합니다."""
        retained_earnings = session.query(Account).filter_by(code="3200").first()
        
        if not retained_earnings:
            retained_earnings = self.create_account(
                session=session,
                code="3200",
                name="이익잉여금",
                account_type=AccountType.EQUITY,
                description="당기순이익 누적액"
            )
        
        return retained_earnings 
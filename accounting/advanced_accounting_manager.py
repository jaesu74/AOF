from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import (
    Budget, BudgetType, CostCenter, CostAllocation,
    CashFlow, TaxReport, AccountAnalysis, Account,
    JournalEntry, JournalLine
)

class AdvancedAccountingManager:
    def create_budget(self, session: Session, fiscal_year_id: int, account_id: int,
                     budget_type: BudgetType, period_start: datetime, period_end: datetime,
                     amount: float, description: str = None) -> Budget:
        """새로운 예산을 생성합니다."""
        budget = Budget(
            fiscal_year_id=fiscal_year_id,
            account_id=account_id,
            type=budget_type,
            period_start=period_start,
            period_end=period_end,
            amount=amount,
            description=description
        )
        
        session.add(budget)
        session.commit()
        return budget

    def analyze_budget_variance(self, session: Session, budget_id: int) -> dict:
        """예산 실적을 분석합니다."""
        budget = session.query(Budget).get(budget_id)
        if not budget:
            raise ValueError("예산을 찾을 수 없습니다.")
        
        # 실제 금액 계산
        actual_amount = session.query(func.sum(JournalLine.debit - JournalLine.credit))\
            .join(JournalEntry)\
            .filter(
                JournalLine.account_id == budget.account_id,
                JournalEntry.entry_date >= budget.period_start,
                JournalEntry.entry_date <= budget.period_end
            ).scalar() or 0
        
        variance = actual_amount - budget.amount
        variance_percentage = (variance / budget.amount) * 100 if budget.amount != 0 else 0
        
        return {
            "budget_amount": budget.amount,
            "actual_amount": actual_amount,
            "variance": variance,
            "variance_percentage": variance_percentage
        }

    def create_cost_center(self, session: Session, code: str, name: str,
                          description: str = None) -> CostCenter:
        """새로운 원가 중심점을 생성합니다."""
        cost_center = CostCenter(
            code=code,
            name=name,
            description=description
        )
        
        session.add(cost_center)
        session.commit()
        return cost_center

    def allocate_costs(self, session: Session, journal_line_id: int,
                      allocations: list) -> list[CostAllocation]:
        """비용을 원가 중심점에 배부합니다."""
        journal_line = session.query(JournalLine).get(journal_line_id)
        if not journal_line:
            raise ValueError("전표 항목을 찾을 수 없습니다.")
        
        # 배부 비율의 합이 1인지 검증
        total_ratio = sum(alloc['ratio'] for alloc in allocations)
        if abs(total_ratio - 1.0) > 0.01:  # 반올림 오차 허용
            raise ValueError("배부 비율의 합이 1이 아닙니다.")
        
        cost_allocations = []
        total_amount = journal_line.debit - journal_line.credit
        
        for alloc in allocations:
            cost_allocation = CostAllocation(
                journal_line_id=journal_line_id,
                cost_center_id=alloc['cost_center_id'],
                ratio=alloc['ratio'],
                amount=total_amount * alloc['ratio']
            )
            session.add(cost_allocation)
            cost_allocations.append(cost_allocation)
        
        session.commit()
        return cost_allocations

    def generate_cash_flow_statement(self, session: Session, start_date: datetime,
                                   end_date: datetime) -> list[CashFlow]:
        """현금 흐름표를 생성합니다."""
        # 영업활동 현금흐름
        operating_entries = session.query(JournalEntry)\
            .filter(
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.is_posted == True
            ).all()
        
        cash_flows = []
        
        for entry in operating_entries:
            cash_amount = 0
            for line in entry.lines:
                if line.account.code.startswith('1'):  # 현금 및 현금성 자산
                    cash_amount += line.debit - line.credit
            
            if cash_amount != 0:
                flow_type = self._determine_cash_flow_type(entry)
                cash_flow = CashFlow(
                    entry_id=entry.id,
                    type=flow_type,
                    amount=abs(cash_amount),
                    description=entry.description
                )
                session.add(cash_flow)
                cash_flows.append(cash_flow)
        
        session.commit()
        return cash_flows

    def generate_tax_report(self, session: Session, report_type: str,
                          period_start: datetime, period_end: datetime) -> TaxReport:
        """세금 신고 자료를 생성합니다."""
        if report_type not in ["VAT", "CORPORATE_TAX"]:
            raise ValueError("지원하지 않는 세금 신고 유형입니다.")
        
        total_amount = 0
        
        if report_type == "VAT":
            # 매출/매입 부가세 계산
            vat_accounts = session.query(Account)\
                .filter(Account.code.in_(['21510', '11510']))\
                .all()  # 부가세 예수금, 부가세 대급금
            
            for account in vat_accounts:
                entries = session.query(JournalLine)\
                    .join(JournalEntry)\
                    .filter(
                        JournalLine.account_id == account.id,
                        JournalEntry.entry_date >= period_start,
                        JournalEntry.entry_date <= period_end
                    ).all()
                
                for entry in entries:
                    total_amount += entry.credit - entry.debit
        
        else:  # CORPORATE_TAX
            # 당기순이익 계산
            revenue_accounts = session.query(Account)\
                .filter(Account.type == "REVENUE").all()
            expense_accounts = session.query(Account)\
                .filter(Account.type == "EXPENSE").all()
            
            total_revenue = 0
            total_expense = 0
            
            for account in revenue_accounts:
                entries = session.query(JournalLine)\
                    .join(JournalEntry)\
                    .filter(
                        JournalLine.account_id == account.id,
                        JournalEntry.entry_date >= period_start,
                        JournalEntry.entry_date <= period_end
                    ).all()
                
                for entry in entries:
                    total_revenue += entry.credit - entry.debit
            
            for account in expense_accounts:
                entries = session.query(JournalLine)\
                    .join(JournalEntry)\
                    .filter(
                        JournalLine.account_id == account.id,
                        JournalEntry.entry_date >= period_start,
                        JournalEntry.entry_date <= period_end
                    ).all()
                
                for entry in entries:
                    total_expense += entry.debit - entry.credit
            
            total_amount = total_revenue - total_expense
        
        tax_report = TaxReport(
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            total_amount=total_amount
        )
        
        session.add(tax_report)
        session.commit()
        return tax_report

    def submit_tax_report(self, session: Session, report_id: int,
                         submitted_by: str) -> TaxReport:
        """세금 신고 자료를 제출합니다."""
        tax_report = session.query(TaxReport).get(report_id)
        if not tax_report:
            raise ValueError("세금 신고 자료를 찾을 수 없습니다.")
        
        if tax_report.status != "DRAFT":
            raise ValueError("이미 제출된 세금 신고 자료입니다.")
        
        tax_report.status = "SUBMITTED"
        tax_report.submitted_at = datetime.utcnow()
        tax_report.submitted_by = submitted_by
        
        session.commit()
        return tax_report

    def analyze_account(self, session: Session, account_id: int,
                       analysis_date: datetime) -> AccountAnalysis:
        """계정과목을 분석합니다."""
        account = session.query(Account).get(account_id)
        if not account:
            raise ValueError("계정과목을 찾을 수 없습니다.")
        
        # 현재 잔액 계산
        current_balance = session.query(func.sum(JournalLine.debit - JournalLine.credit))\
            .join(JournalEntry)\
            .filter(
                JournalLine.account_id == account_id,
                JournalEntry.entry_date <= analysis_date
            ).scalar() or 0
        
        # 이전 달 잔액 계산
        previous_month = analysis_date.replace(day=1)
        previous_balance = session.query(func.sum(JournalLine.debit - JournalLine.credit))\
            .join(JournalEntry)\
            .filter(
                JournalLine.account_id == account_id,
                JournalEntry.entry_date < previous_month
            ).scalar() or 0
        
        # 추세 분석
        if current_balance > previous_balance:
            trend = "INCREASING"
        elif current_balance < previous_balance:
            trend = "DECREASING"
        else:
            trend = "STABLE"
        
        # 변동률 계산
        variance_percentage = ((current_balance - previous_balance) / previous_balance * 100
                             if previous_balance != 0 else 0)
        
        analysis = AccountAnalysis(
            account_id=account_id,
            analysis_date=analysis_date,
            balance=current_balance,
            trend=trend,
            variance_percentage=variance_percentage
        )
        
        session.add(analysis)
        session.commit()
        return analysis

    def _determine_cash_flow_type(self, entry: JournalEntry) -> str:
        """현금 흐름의 유형을 결정합니다."""
        # 간단한 규칙으로 현금 흐름 유형 결정
        for line in entry.lines:
            if line.account.code.startswith('4'):  # 수익 계정
                return "OPERATING"
            elif line.account.code.startswith('5'):  # 비용 계정
                return "OPERATING"
            elif line.account.code.startswith('15'):  # 투자자산
                return "INVESTING"
            elif line.account.code.startswith('2') and int(line.account.code) > 2200:  # 비유동부채
                return "FINANCING"
            elif line.account.code.startswith('31'):  # 자본금
                return "FINANCING"
        
        return "OPERATING"  # 기본값 
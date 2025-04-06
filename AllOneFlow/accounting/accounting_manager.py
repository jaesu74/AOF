from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
import logging
from ..database.models import (
    Account, AccountType, Transaction, JournalEntry, JournalLine,
    FiscalYear, FinancialStatement, VATType
)

class AccountingManager:
    """회계 관리를 담당하는 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.VAT_RATE = 0.1  # 부가가치세율 10%
    
    def create_account(self, session: Session, code: str, name: str, 
                      account_type: AccountType, description: str = None,
                      parent_code: str = None) -> Account:
        """
        새로운 계정과목을 생성합니다.
        """
        try:
            # 상위 계정과목 조회
            parent_account = None
            if parent_code:
                parent_account = session.query(Account).filter_by(code=parent_code).first()
            
            # 계정과목 생성
            account = Account(
                code=code,
                name=name,
                type=account_type,
                description=description,
                parent_id=parent_account.id if parent_account else None
            )
            session.add(account)
            session.commit()
            return account
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"계정과목 생성 중 오류 발생: {str(e)}")
            raise
    
    def create_journal_entry(self, session: Session, entry_date: datetime,
                           description: str, lines: List[Dict], created_by: str) -> JournalEntry:
        """
        전표를 생성합니다.
        
        Args:
            lines: [{"account_code": "101", "debit": 1000, "credit": 0, "description": "설명"}, ...]
        """
        try:
            # 차변/대변 합계 검증
            total_debit = sum(line['debit'] for line in lines)
            total_credit = sum(line['credit'] for line in lines)
            if total_debit != total_credit:
                raise ValueError("차변과 대변의 합계가 일치하지 않습니다.")
            
            # 전표 생성
            entry = JournalEntry(
                entry_date=entry_date,
                description=description,
                created_by=created_by
            )
            session.add(entry)
            
            # 전표 라인 생성
            for line in lines:
                account = session.query(Account).filter_by(code=line['account_code']).first()
                if not account:
                    raise ValueError(f"계정과목을 찾을 수 없습니다: {line['account_code']}")
                
                journal_line = JournalLine(
                    entry=entry,
                    account=account,
                    debit=line['debit'],
                    credit=line['credit'],
                    description=line.get('description')
                )
                session.add(journal_line)
            
            session.commit()
            return entry
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"전표 생성 중 오류 발생: {str(e)}")
            raise
    
    def process_transaction_vat(self, session: Session, transaction: Transaction) -> Optional[JournalEntry]:
        """
        거래에 대한 부가가치세를 처리하고 전표를 생성합니다.
        """
        try:
            if transaction.vat_type == VATType.TAXABLE:
                # 부가세 계산
                vat_amount = transaction.amount * self.VAT_RATE
                transaction.vat_amount = vat_amount
                
                # 전표 생성
                entry_lines = [
                    # 거래 금액 처리
                    {
                        "account_code": "101",  # 현금
                        "debit": transaction.amount + vat_amount,
                        "credit": 0,
                        "description": "거래 금액"
                    },
                    {
                        "account_code": "401",  # 매출
                        "debit": 0,
                        "credit": transaction.amount,
                        "description": "매출 금액"
                    },
                    # 부가세 처리
                    {
                        "account_code": "255",  # 부가세 예수금
                        "debit": 0,
                        "credit": vat_amount,
                        "description": "부가세"
                    }
                ]
                
                entry = self.create_journal_entry(
                    session=session,
                    entry_date=transaction.transaction_date,
                    description=transaction.description,
                    lines=entry_lines,
                    created_by="SYSTEM"
                )
                
                # 거래와 전표 연결
                transaction.journal_entry = entry
                session.commit()
                
                return entry
                
            return None
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"부가세 처리 중 오류 발생: {str(e)}")
            raise
    
    def generate_financial_statements(self, session: Session, fiscal_year_id: int) -> Dict:
        """
        재무제표를 생성합니다.
        """
        try:
            fiscal_year = session.query(FiscalYear).get(fiscal_year_id)
            if not fiscal_year:
                raise ValueError("회계연도를 찾을 수 없습니다.")
            
            # 해당 회계연도의 전표 조회
            entries = session.query(JournalLine).join(JournalEntry).join(Account).filter(
                and_(
                    JournalEntry.entry_date >= fiscal_year.start_date,
                    JournalEntry.entry_date <= fiscal_year.end_date,
                    JournalEntry.is_posted == True
                )
            ).all()
            
            # 계정과목별 합계 계산
            account_balances = {}
            for line in entries:
                if line.account.code not in account_balances:
                    account_balances[line.account.code] = {
                        "name": line.account.name,
                        "type": line.account.type.value,
                        "debit": 0,
                        "credit": 0,
                        "balance": 0
                    }
                
                account_balances[line.account.code]["debit"] += line.debit
                account_balances[line.account.code]["credit"] += line.credit
                
                # 계정과목 유형에 따른 잔액 계산
                if line.account.type in [AccountType.ASSET, AccountType.EXPENSE]:
                    account_balances[line.account.code]["balance"] = (
                        account_balances[line.account.code]["debit"] -
                        account_balances[line.account.code]["credit"]
                    )
                else:
                    account_balances[line.account.code]["balance"] = (
                        account_balances[line.account.code]["credit"] -
                        account_balances[line.account.code]["debit"]
                    )
            
            # 재무상태표 데이터 구성
            balance_sheet = {
                "assets": {},
                "liabilities": {},
                "equity": {}
            }
            
            # 손익계산서 데이터 구성
            income_statement = {
                "revenue": {},
                "expense": {}
            }
            
            for code, data in account_balances.items():
                if data["type"] == AccountType.ASSET.value:
                    balance_sheet["assets"][code] = data
                elif data["type"] == AccountType.LIABILITY.value:
                    balance_sheet["liabilities"][code] = data
                elif data["type"] == AccountType.EQUITY.value:
                    balance_sheet["equity"][code] = data
                elif data["type"] == AccountType.REVENUE.value:
                    income_statement["revenue"][code] = data
                elif data["type"] == AccountType.EXPENSE.value:
                    income_statement["expense"][code] = data
            
            # 재무제표 저장
            statements = {
                "balance_sheet": balance_sheet,
                "income_statement": income_statement
            }
            
            for statement_type, data in statements.items():
                financial_statement = FinancialStatement(
                    fiscal_year_id=fiscal_year.id,
                    statement_type=statement_type,
                    period_end=fiscal_year.end_date,
                    data=json.dumps(data, ensure_ascii=False)
                )
                session.add(financial_statement)
            
            session.commit()
            return statements
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"재무제표 생성 중 오류 발생: {str(e)}")
            raise 
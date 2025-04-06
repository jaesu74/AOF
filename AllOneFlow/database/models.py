from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class AccountType(enum.Enum):
    """계정과목 유형"""
    ASSET = "자산"
    LIABILITY = "부채"
    EQUITY = "자본"
    REVENUE = "수익"
    EXPENSE = "비용"

class VATType(enum.Enum):
    """부가가치세 유형"""
    TAXABLE = "과세"
    ZERO_RATED = "영세"
    EXEMPT = "면세"

class Account(Base):
    """계정과목 정보"""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)  # 계정과목 코드
    name = Column(String(100), nullable=False)  # 계정과목명
    type = Column(Enum(AccountType), nullable=False)  # 계정 유형
    description = Column(String(200))  # 설명
    is_active = Column(Boolean, default=True)  # 사용 여부
    parent_id = Column(Integer, ForeignKey('accounts.id'))  # 상위 계정과목
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("Account", remote_side=[id])
    children = relationship("Account")

class JournalEntry(Base):
    """전표"""
    __tablename__ = 'journal_entries'
    
    id = Column(Integer, primary_key=True)
    entry_date = Column(DateTime, nullable=False)  # 전표 일자
    description = Column(String(200))  # 적요
    reference = Column(String(50))  # 참조번호
    is_posted = Column(Boolean, default=False)  # 승인 여부
    created_by = Column(String(50), nullable=False)  # 작성자
    approved_by = Column(String(50))  # 승인자
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lines = relationship("JournalLine", back_populates="entry")

class JournalLine(Base):
    """전표 라인"""
    __tablename__ = 'journal_lines'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    cost_center_id = Column(Integer, ForeignKey('cost_centers.id'))  # 원가 중심점
    debit = Column(Float, default=0.0)  # 차변
    credit = Column(Float, default=0.0)  # 대변
    description = Column(String(200))  # 상세 설명
    
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")
    cost_center = relationship("CostCenter")
    cost_allocations = relationship("CostAllocation", backref="journal_line")

class Transaction(Base):
    """ERP 시스템에서 가져온 거래 정보"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    transaction_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(200))
    category = Column(String(50))
    is_anomaly = Column(Boolean, default=False)
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))  # 연결된 전표
    vat_type = Column(Enum(VATType), default=VATType.TAXABLE)  # 부가세 유형
    vat_amount = Column(Float, default=0.0)  # 부가세 금액
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contract = relationship("Contract", backref="transactions")
    journal_entry = relationship("JournalEntry")

class FiscalYear(Base):
    """회계연도"""
    __tablename__ = 'fiscal_years'
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime)
    
    def __init__(self, year: int):
        self.year = year
        self.start_date = datetime(year, 1, 1)  # 1월 1일부터
        self.end_date = datetime(year, 12, 31)  # 12월 31일까지

class FinancialStatement(Base):
    """재무제표"""
    __tablename__ = 'financial_statements'
    
    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    statement_type = Column(String(50), nullable=False)  # 재무상태표, 손익계산서 등
    period_end = Column(DateTime, nullable=False)  # 기준일
    data = Column(String(5000), nullable=False)  # JSON 형태의 재무제표 데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    
    fiscal_year = relationship("FiscalYear")

class Contract(Base):
    """계약 정보를 저장하는 모델"""
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True)
    company_name = Column(String(100), nullable=False)
    contact_person = Column(String(50), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    contract_type = Column(String(50), nullable=False)
    status = Column(String(20), default='draft')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Report(Base):
    """생성된 보고서 정보를 저장하는 모델"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    report_type = Column(String(50), nullable=False)
    generated_date = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(200), nullable=False)
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    
    contract = relationship("Contract", backref="reports")

class BudgetType(enum.Enum):
    """예산 유형"""
    ANNUAL = "연간"
    QUARTERLY = "분기"
    MONTHLY = "월간"
    PROJECT = "프로젝트"

class Budget(Base):
    """예산 정보"""
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    type = Column(Enum(BudgetType), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    actual_amount = Column(Float, default=0.0)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    fiscal_year = relationship("FiscalYear")
    account = relationship("Account")

class CostCenter(Base):
    """원가 중심점"""
    __tablename__ = 'cost_centers'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(200))
    is_active = Column(Boolean, default=True)
    parent_id = Column(Integer, ForeignKey('cost_centers.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("CostCenter", remote_side=[id])
    children = relationship("CostCenter")

class CostAllocation(Base):
    """원가 배부 내역"""
    __tablename__ = 'cost_allocations'
    
    id = Column(Integer, primary_key=True)
    journal_line_id = Column(Integer, ForeignKey('journal_lines.id'), nullable=False)
    cost_center_id = Column(Integer, ForeignKey('cost_centers.id'), nullable=False)
    allocation_ratio = Column(Float, nullable=False)  # 배부 비율
    amount = Column(Float, nullable=False)  # 배부 금액
    created_at = Column(DateTime, default=datetime.utcnow)
    
    journal_line = relationship("JournalLine")
    cost_center = relationship("CostCenter")

class CashFlow(Base):
    """현금 흐름"""
    __tablename__ = 'cash_flows'
    
    id = Column(Integer, primary_key=True)
    transaction_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    flow_type = Column(String(50), nullable=False)  # 영업/투자/재무 활동
    description = Column(String(200))
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    journal_entry = relationship("JournalEntry")

class TaxReport(Base):
    """세금 신고 자료"""
    __tablename__ = 'tax_reports'
    
    id = Column(Integer, primary_key=True)
    report_type = Column(String(50), nullable=False)  # 부가세/법인세 등
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_revenue = Column(Float, default=0.0)
    total_expense = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    status = Column(String(20), default='draft')  # draft/submitted/approved
    submitted_at = Column(DateTime)
    data = Column(JSON)  # 세부 신고 데이터
    created_at = Column(DateTime, default=datetime.utcnow)

class AccountAnalysis(Base):
    """계정과목 분석"""
    __tablename__ = 'account_analyses'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    analysis_date = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # daily/weekly/monthly/yearly
    total_debit = Column(Float, default=0.0)
    total_credit = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    trend_data = Column(JSON)  # 추세 분석 데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("Account")

def init_db(db_url='sqlite:///alloneflow.db'):
    """데이터베이스 초기화 및 테이블 생성"""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine 
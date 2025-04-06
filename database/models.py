from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()

class AccountType(enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(Enum(AccountType), nullable=False)
    description = Column(String(500))
    parent_id = Column(Integer, ForeignKey('accounts.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent = relationship("Account", remote_side=[id])
    journal_lines = relationship("JournalLine", back_populates="account")

class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    
    id = Column(Integer, primary_key=True)
    entry_date = Column(DateTime, nullable=False)
    description = Column(String(500))
    is_posted = Column(Boolean, default=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(100))
    
    lines = relationship("JournalLine", back_populates="entry")

class JournalLine(Base):
    __tablename__ = 'journal_lines'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    debit = Column(Float, default=0)
    credit = Column(Float, default=0)
    description = Column(String(500))
    
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="journal_lines")

class FiscalYear(Base):
    __tablename__ = 'fiscal_years'
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime)
    closed_by = Column(String(100))

class BudgetType(enum.Enum):
    ANNUAL = "ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"
    PROJECT = "PROJECT"

class Budget(Base):
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    type = Column(Enum(BudgetType), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    fiscal_year = relationship("FiscalYear")
    account = relationship("Account")

class CostCenter(Base):
    __tablename__ = 'cost_centers'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CostAllocation(Base):
    __tablename__ = 'cost_allocations'
    
    id = Column(Integer, primary_key=True)
    journal_line_id = Column(Integer, ForeignKey('journal_lines.id'), nullable=False)
    cost_center_id = Column(Integer, ForeignKey('cost_centers.id'), nullable=False)
    ratio = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    journal_line = relationship("JournalLine")
    cost_center = relationship("CostCenter")

class CashFlow(Base):
    __tablename__ = 'cash_flows'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=False)
    type = Column(String(50), nullable=False)  # OPERATING, INVESTING, FINANCING
    amount = Column(Float, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    entry = relationship("JournalEntry")

class TaxReport(Base):
    __tablename__ = 'tax_reports'
    
    id = Column(Integer, primary_key=True)
    report_type = Column(String(50), nullable=False)  # VAT, CORPORATE_TAX
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="DRAFT")  # DRAFT, SUBMITTED, APPROVED
    submitted_at = Column(DateTime)
    submitted_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class AccountAnalysis(Base):
    __tablename__ = 'account_analyses'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    analysis_date = Column(DateTime, nullable=False)
    balance = Column(Float, nullable=False)
    trend = Column(String(50))  # INCREASING, DECREASING, STABLE
    variance_percentage = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("Account") 
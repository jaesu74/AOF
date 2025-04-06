from flask import Flask, request, jsonify, send_file
from datetime import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..database.models import (
    Base, Contract, Transaction, Report, Account, AccountType,
    JournalEntry, FiscalYear, Budget, BudgetType, CostCenter,
    CostAllocation, CashFlow, TaxReport, AccountAnalysis
)
from ..contract_automation.contract_generator import ContractGenerator
from ..erp_integration.erp_connector import ERPConnector
from ..anomaly_detection.anomaly_detector import AnomalyDetector
from ..report_generation.report_generator import ReportGenerator
from ..accounting.accounting_manager import AccountingManager
from ..accounting.advanced_accounting_manager import AdvancedAccountingManager
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 데이터베이스 설정
engine = create_engine('sqlite:///alloneflow.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# 컴포넌트 초기화
contract_generator = ContractGenerator()
erp_connector = ERPConnector(
    api_base_url=os.getenv('ERP_API_URL'),
    api_key=os.getenv('ERP_API_KEY')
)
anomaly_detector = AnomalyDetector()
report_generator = ReportGenerator()
accounting_manager = AccountingManager()
advanced_accounting_manager = AdvancedAccountingManager()

@app.route('/api/contracts', methods=['POST'])
def create_contract():
    """새로운 계약을 생성합니다."""
    try:
        data = request.json
        
        # 계약서 생성
        contract_content = contract_generator.generate_contract(
            template_name="service_contract.html",
            data=data
        )
        
        # 계약 정보 저장
        session = Session()
        contract = Contract(
            company_name=data['company_name'],
            contact_person=data['contact_person'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            contract_type=data['contract_type']
        )
        session.add(contract)
        session.commit()
        
        # 계약서 파일 저장
        output_path = f"contracts/contract_{contract.id}.html"
        saved_path = contract_generator.save_contract(contract_content, output_path)
        
        return jsonify({
            "message": "계약이 성공적으로 생성되었습니다.",
            "contract_id": contract.id,
            "file_path": saved_path
        }), 201
        
    except Exception as e:
        logger.error(f"계약 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/transactions/sync', methods=['POST'])
def sync_transactions():
    """ERP 시스템에서 거래 내역을 동기화합니다."""
    try:
        data = request.json
        start_date = datetime.fromisoformat(data['start_date'])
        end_date = datetime.fromisoformat(data['end_date'])
        
        # 거래 내역 조회
        transactions = erp_connector.fetch_transactions(start_date, end_date)
        
        # 데이터베이스에 저장
        session = Session()
        erp_connector.sync_transactions(session, transactions)
        
        # 이상 거래 탐지
        is_anomaly, scores = anomaly_detector.detect_anomalies(transactions)
        
        # 이상 거래 정보 업데이트
        transaction_ids = [t['id'] for t in transactions]
        anomaly_detector.update_transaction_anomalies(session, transaction_ids, is_anomaly)
        
        return jsonify({
            "message": "거래 내역이 성공적으로 동기화되었습니다.",
            "total_transactions": len(transactions),
            "anomalies_detected": sum(is_anomaly)
        })
        
    except Exception as e:
        logger.error(f"거래 내역 동기화 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/weekly', methods=['POST'])
def generate_weekly_report():
    """주간 보고서를 생성합니다."""
    try:
        data = request.json
        start_date = datetime.fromisoformat(data['start_date'])
        contract_id = data.get('contract_id')
        
        session = Session()
        report_path = report_generator.create_weekly_report(
            session, start_date, contract_id
        )
        
        return jsonify({
            "message": "보고서가 성공적으로 생성되었습니다.",
            "report_path": report_path
        })
        
    except Exception as e:
        logger.error(f"보고서 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/download/<report_id>', methods=['GET'])
def download_report(report_id):
    """생성된 보고서를 다운로드합니다."""
    try:
        session = Session()
        report = session.query(Report).get(report_id)
        
        if not report:
            return jsonify({"error": "보고서를 찾을 수 없습니다."}), 404
            
        return send_file(
            report.file_path,
            as_attachment=True,
            download_name=os.path.basename(report.file_path)
        )
        
    except Exception as e:
        logger.error(f"보고서 다운로드 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts', methods=['POST'])
def create_account():
    """새로운 계정과목을 생성합니다."""
    try:
        data = request.json
        session = Session()
        
        account = accounting_manager.create_account(
            session=session,
            code=data['code'],
            name=data['name'],
            account_type=AccountType[data['type']],
            description=data.get('description'),
            parent_code=data.get('parent_code')
        )
        
        return jsonify({
            "message": "계정과목이 성공적으로 생성되었습니다.",
            "account_id": account.id,
            "code": account.code
        }), 201
        
    except Exception as e:
        logger.error(f"계정과목 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts', methods=['GET'])
def list_accounts():
    """계정과목 목록을 조회합니다."""
    try:
        session = Session()
        accounts = session.query(Account).all()
        
        return jsonify({
            "accounts": [{
                "id": acc.id,
                "code": acc.code,
                "name": acc.name,
                "type": acc.type.value,
                "description": acc.description,
                "is_active": acc.is_active,
                "parent_id": acc.parent_id
            } for acc in accounts]
        })
        
    except Exception as e:
        logger.error(f"계정과목 조회 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/journal-entries', methods=['POST'])
def create_journal_entry():
    """새로운 전표를 생성합니다."""
    try:
        data = request.json
        session = Session()
        
        entry = accounting_manager.create_journal_entry(
            session=session,
            entry_date=datetime.fromisoformat(data['entry_date']),
            description=data['description'],
            lines=data['lines'],
            created_by=data['created_by']
        )
        
        return jsonify({
            "message": "전표가 성공적으로 생성되었습니다.",
            "entry_id": entry.id
        }), 201
        
    except Exception as e:
        logger.error(f"전표 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/journal-entries/<int:entry_id>/post', methods=['POST'])
def post_journal_entry(entry_id):
    """전표를 승인 처리합니다."""
    try:
        data = request.json
        session = Session()
        
        entry = session.query(JournalEntry).get(entry_id)
        if not entry:
            return jsonify({"error": "전표를 찾을 수 없습니다."}), 404
        
        entry.is_posted = True
        entry.approved_by = data['approved_by']
        session.commit()
        
        return jsonify({
            "message": "전표가 승인되었습니다.",
            "entry_id": entry.id
        })
        
    except Exception as e:
        logger.error(f"전표 승인 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fiscal-years', methods=['POST'])
def create_fiscal_year():
    """새로운 회계연도를 생성합니다."""
    try:
        data = request.json
        session = Session()
        
        fiscal_year = FiscalYear(year=data['year'])
        session.add(fiscal_year)
        session.commit()
        
        return jsonify({
            "message": "회계연도가 성공적으로 생성되었습니다.",
            "fiscal_year_id": fiscal_year.id,
            "year": fiscal_year.year
        }), 201
        
    except Exception as e:
        logger.error(f"회계연도 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fiscal-years/<int:fiscal_year_id>/close', methods=['POST'])
def close_fiscal_year(fiscal_year_id):
    """회계연도를 마감합니다."""
    try:
        session = Session()
        
        fiscal_year = session.query(FiscalYear).get(fiscal_year_id)
        if not fiscal_year:
            return jsonify({"error": "회계연도를 찾을 수 없습니다."}), 404
        
        # 재무제표 생성
        statements = accounting_manager.generate_financial_statements(
            session=session,
            fiscal_year_id=fiscal_year_id
        )
        
        # 회계연도 마감
        fiscal_year.is_closed = True
        fiscal_year.closed_at = datetime.now()
        session.commit()
        
        return jsonify({
            "message": "회계연도가 마감되었습니다.",
            "fiscal_year_id": fiscal_year.id,
            "statements": statements
        })
        
    except Exception as e:
        logger.error(f"회계연도 마감 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/budgets', methods=['POST'])
def create_budget():
    """새로운 예산을 생성합니다."""
    try:
        data = request.json
        session = Session()
        
        budget = advanced_accounting_manager.create_budget(
            session=session,
            fiscal_year_id=data['fiscal_year_id'],
            account_id=data['account_id'],
            budget_type=BudgetType[data['type']],
            period_start=datetime.fromisoformat(data['period_start']),
            period_end=datetime.fromisoformat(data['period_end']),
            amount=data['amount'],
            description=data.get('description')
        )
        
        return jsonify({
            "message": "예산이 성공적으로 생성되었습니다.",
            "budget_id": budget.id
        }), 201
        
    except Exception as e:
        logger.error(f"예산 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/budgets/<int:budget_id>/variance', methods=['GET'])
def analyze_budget_variance(budget_id):
    """예산 실적을 분석합니다."""
    try:
        session = Session()
        analysis = advanced_accounting_manager.analyze_budget_variance(
            session=session,
            budget_id=budget_id
        )
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"예산 분석 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cost-centers', methods=['POST'])
def create_cost_center():
    """새로운 원가 중심점을 생성합니다."""
    try:
        data = request.json
        session = Session()
        
        cost_center = CostCenter(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            parent_id=data.get('parent_id')
        )
        session.add(cost_center)
        session.commit()
        
        return jsonify({
            "message": "원가 중심점이 성공적으로 생성되었습니다.",
            "cost_center_id": cost_center.id
        }), 201
        
    except Exception as e:
        logger.error(f"원가 중심점 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/journal-lines/<int:journal_line_id>/allocate-costs', methods=['POST'])
def allocate_costs(journal_line_id):
    """원가를 배부합니다."""
    try:
        data = request.json
        session = Session()
        
        allocations = advanced_accounting_manager.allocate_costs(
            session=session,
            journal_line_id=journal_line_id,
            allocations=data['allocations']
        )
        
        return jsonify({
            "message": "원가가 성공적으로 배부되었습니다.",
            "allocations": [{
                "id": alloc.id,
                "cost_center_id": alloc.cost_center_id,
                "ratio": alloc.allocation_ratio,
                "amount": alloc.amount
            } for alloc in allocations]
        })
        
    except Exception as e:
        logger.error(f"원가 배부 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cash-flow-statements', methods=['POST'])
def generate_cash_flow_statement():
    """현금 흐름표를 생성합니다."""
    try:
        data = request.json
        session = Session()
        
        statement = advanced_accounting_manager.generate_cash_flow_statement(
            session=session,
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date'])
        )
        
        return jsonify(statement)
        
    except Exception as e:
        logger.error(f"현금 흐름표 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tax-reports', methods=['POST'])
def generate_tax_report():
    """세금 신고 자료를 생성합니다."""
    try:
        data = request.json
        session = Session()
        
        report = advanced_accounting_manager.generate_tax_report(
            session=session,
            report_type=data['report_type'],
            period_start=datetime.fromisoformat(data['period_start']),
            period_end=datetime.fromisoformat(data['period_end'])
        )
        
        return jsonify({
            "message": "세금 신고 자료가 성공적으로 생성되었습니다.",
            "report_id": report.id,
            "report_type": report.report_type,
            "tax_amount": report.tax_amount,
            "status": report.status
        })
        
    except Exception as e:
        logger.error(f"세금 신고 자료 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tax-reports/<int:report_id>/submit', methods=['POST'])
def submit_tax_report(report_id):
    """세금 신고 자료를 제출 상태로 변경합니다."""
    try:
        session = Session()
        report = session.query(TaxReport).get(report_id)
        
        if not report:
            return jsonify({"error": "세금 신고 자료를 찾을 수 없습니다."}), 404
        
        report.status = 'submitted'
        report.submitted_at = datetime.now()
        session.commit()
        
        return jsonify({
            "message": "세금 신고 자료가 제출되었습니다.",
            "report_id": report.id,
            "status": report.status,
            "submitted_at": report.submitted_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"세금 신고 자료 제출 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts/<int:account_id>/analysis', methods=['POST'])
def analyze_account(account_id):
    """계정과목을 분석합니다."""
    try:
        data = request.json
        session = Session()
        
        analysis = advanced_accounting_manager.analyze_account(
            session=session,
            account_id=account_id,
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            period_type=data.get('period_type', 'monthly')
        )
        
        return jsonify({
            "message": "계정과목 분석이 완료되었습니다.",
            "analysis_id": analysis.id,
            "account_id": analysis.account_id,
            "total_debit": analysis.total_debit,
            "total_credit": analysis.total_credit,
            "balance": analysis.balance,
            "trend_data": analysis.trend_data
        })
        
    except Exception as e:
        logger.error(f"계정과목 분석 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 
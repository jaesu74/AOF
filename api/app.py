from flask import Flask, request, jsonify, send_from_directory, redirect
from datetime import datetime
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, FiscalYear, Account, AccountType
from accounting.accounting_manager import AccountingManager
from accounting.advanced_accounting_manager import AdvancedAccountingManager
from flask_cors import CORS
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

app = Flask(__name__, static_folder='static')
CORS(app)

# 데이터베이스 설정
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'alloneflow.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

# 관리자 객체 초기화
accounting_manager = AccountingManager()
advanced_accounting_manager = AdvancedAccountingManager()

# 데이터베이스 초기화 함수
def init_db():
    """데이터베이스 초기화 함수"""
    try:
        # 테이블 생성
        Base.metadata.create_all(engine)
        logger.info("데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
        raise

# 정적 파일 제공
@app.route('/')
def index():
    """메인 페이지로 리다이렉트"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """정적 파일 제공"""
    return send_from_directory(app.static_folder, path)

@app.route('/api/fiscal-years', methods=['POST'])
def create_fiscal_year():
    """새로운 회계연도를 생성합니다."""
    try:
        data = request.get_json(force=True)
        
        if not data or 'year' not in data:
            return jsonify({"error": "year 필드가 필요합니다."}), 400
        
        session = Session()
        
        try:
            fiscal_year = accounting_manager.create_fiscal_year(
                session=session,
                year=int(data['year'])
            )
            session.commit()
            
            response = jsonify({
                "message": "회계연도가 성공적으로 생성되었습니다.",
                "fiscal_year_id": fiscal_year.id,
                "year": fiscal_year.year,
                "start_date": fiscal_year.start_date.isoformat(),
                "end_date": fiscal_year.end_date.isoformat()
            })
            response.status_code = 201
            return response
            
        except Exception as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500
            
        finally:
            session.close()
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fiscal-years', methods=['GET'])
def list_fiscal_years():
    """모든 회계연도를 조회합니다."""
    try:
        session = Session()
        fiscal_years = session.query(FiscalYear).all()
        
        return jsonify([{
            "id": fy.id,
            "year": fy.year,
            "start_date": fy.start_date.isoformat(),
            "end_date": fy.end_date.isoformat(),
            "is_closed": fy.is_closed
        } for fy in fiscal_years])
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/accounts', methods=['POST'])
def create_account():
    """새로운 계정과목을 생성합니다."""
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['code', 'name', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} 필드가 필요합니다."}), 400
        
        session = Session()
        
        try:
            account = Account(
                code=data['code'],
                name=data['name'],
                type=AccountType[data['type']],
                description=data.get('description'),
                parent_id=data.get('parent_id'),
                is_active=data.get('is_active', True)
            )
            session.add(account)
            session.commit()
            
            return jsonify({
                "message": "계정과목이 생성되었습니다.",
                "account_id": account.id,
                "code": account.code,
                "name": account.name,
                "type": account.type.name,
                "description": account.description,
                "parent_id": account.parent_id,
                "is_active": account.is_active
            }), 201
            
        except Exception as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500
            
        finally:
            session.close()
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """모든 계정과목을 조회합니다."""
    try:
        session = Session()
        accounts = session.query(Account).all()
        
        result = []
        for account in accounts:
            result.append({
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'type': account.type.name,
                'description': account.description,
                'parent_id': account.parent_id,
                'is_active': account.is_active,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'updated_at': account.updated_at.isoformat() if account.updated_at else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/accounts/<string:code>', methods=['GET'])
def get_account(code):
    """특정 계정과목을 조회합니다."""
    try:
        session = Session()
        account = session.query(Account).filter(Account.code == code).first()
        
        if not account:
            return jsonify({"error": "계정과목을 찾을 수 없습니다."}), 404
            
        return jsonify({
            "id": account.id,
            "code": account.code,
            "name": account.name,
            "type": account.type.name,
            "description": account.description,
            "parent_id": account.parent_id,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None
        })
        
    except Exception as e:
        logger.error(f"계정과목 조회 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

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
            budget_type=data['type'],
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
        
        cost_center = advanced_accounting_manager.create_cost_center(
            session=session,
            code=data['code'],
            name=data['name'],
            description=data.get('description')
        )
        
        return jsonify({
            "message": "원가 중심점이 성공적으로 생성되었습니다.",
            "cost_center_id": cost_center.id,
            "code": cost_center.code
        }), 201
        
    except Exception as e:
        logger.error(f"원가 중심점 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/journal-lines/<int:journal_line_id>/allocate-costs', methods=['POST'])
def allocate_costs(journal_line_id):
    """비용을 원가 중심점에 배부합니다."""
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
                "ratio": alloc.ratio,
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
        
        cash_flows = advanced_accounting_manager.generate_cash_flow_statement(
            session=session,
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date'])
        )
        
        return jsonify({
            "message": "현금 흐름표가 성공적으로 생성되었습니다.",
            "cash_flows": [{
                "id": flow.id,
                "type": flow.type,
                "amount": flow.amount,
                "description": flow.description
            } for flow in cash_flows]
        })
        
    except Exception as e:
        logger.error(f"현금 흐름표 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tax-reports', methods=['POST'])
def generate_tax_report():
    """세금 신고 자료를 생성합니다."""
    try:
        data = request.json
        session = Session()
        
        tax_report = advanced_accounting_manager.generate_tax_report(
            session=session,
            report_type=data['report_type'],
            period_start=datetime.fromisoformat(data['period_start']),
            period_end=datetime.fromisoformat(data['period_end'])
        )
        
        return jsonify({
            "message": "세금 신고 자료가 성공적으로 생성되었습니다.",
            "report_id": tax_report.id,
            "total_amount": tax_report.total_amount
        }), 201
        
    except Exception as e:
        logger.error(f"세금 신고 자료 생성 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tax-reports/<int:report_id>/submit', methods=['POST'])
def submit_tax_report(report_id):
    """세금 신고 자료를 제출합니다."""
    try:
        data = request.json
        session = Session()
        
        tax_report = advanced_accounting_manager.submit_tax_report(
            session=session,
            report_id=report_id,
            submitted_by=data['submitted_by']
        )
        
        return jsonify({
            "message": "세금 신고 자료가 성공적으로 제출되었습니다.",
            "report_id": tax_report.id,
            "status": tax_report.status,
            "submitted_at": tax_report.submitted_at.isoformat()
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
            analysis_date=datetime.fromisoformat(data['analysis_date'])
        )
        
        return jsonify({
            "message": "계정과목 분석이 성공적으로 완료되었습니다.",
            "analysis_id": analysis.id,
            "balance": analysis.balance,
            "trend": analysis.trend,
            "variance_percentage": analysis.variance_percentage
        })
        
    except Exception as e:
        logger.error(f"계정과목 분석 중 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fiscal-years/<int:fiscal_year_id>/close', methods=['POST'])
def close_fiscal_year(fiscal_year_id):
    """회계연도를 마감합니다."""
    try:
        data = request.get_json(force=True)
        
        if not data or 'closed_by' not in data:
            return jsonify({"error": "closed_by 필드가 필요합니다."}), 400
        
        session = Session()
        
        try:
            fiscal_year = session.query(FiscalYear).get(fiscal_year_id)
            if not fiscal_year:
                return jsonify({"error": "회계연도를 찾을 수 없습니다."}), 404
            
            fiscal_year = accounting_manager.close_fiscal_year(
                session=session,
                fiscal_year_id=fiscal_year_id,
                closed_by=data['closed_by']
            )
            session.commit()
            
            return jsonify({
                "message": "회계연도가 성공적으로 마감되었습니다.",
                "fiscal_year_id": fiscal_year.id,
                "year": fiscal_year.year,
                "closed_at": fiscal_year.closed_at.isoformat(),
                "closed_by": fiscal_year.closed_by
            })
            
        except Exception as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500
            
        finally:
            session.close()
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 서버 시작 시 데이터베이스 초기화
    init_db()
    
    logger.info("Starting server...")
    app.run(host='0.0.0.0', port=5000, debug=True) 
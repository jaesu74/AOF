from flask import Flask, request, jsonify, send_from_directory, redirect
from datetime import datetime
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, FiscalYear, Account, AccountType
from accounting.accounting_manager import AccountingManager
from accounting.advanced_accounting_manager import AdvancedAccountingManager
from accounting.excel_manager import ExcelManager
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
excel_manager = ExcelManager()

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

# ================ 보고서 생성 API ================
@app.route('/api/reports', methods=['POST'])
def create_report():
    """새로운 보고서를 생성합니다."""
    try:
        data = request.get_json()
        required_fields = ['fiscal_year_id', 'report_type', 'period_start', 'period_end']
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} 필드가 필요합니다."}), 400
        
        # 실제 DB 모델이 없으므로 임시 응답
        # 실제 구현시에는 보고서 생성 및 저장 로직 추가
        
        report = {
            "id": 1,
            "fiscal_year_id": data['fiscal_year_id'],
            "report_type": data['report_type'],
            "period_start": data['period_start'],
            "period_end": data['period_end'],
            "created_at": datetime.now().isoformat(),
            "file_path": "reports/sample_report.pdf"
        }
        
        return jsonify({
            "message": "보고서가 생성되었습니다.",
            "report": report
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def list_reports():
    """생성된 보고서 목록을 조회합니다."""
    try:
        # 실제 DB 모델이 없으므로 임시 데이터 반환
        # 실제 구현시에는 DB에서 보고서 목록 조회
        
        reports = [
            {
                "id": 1,
                "report_type": "BUDGET_VS_ACTUAL",
                "period_start": "2024-01-01",
                "period_end": "2024-03-31",
                "created_at": "2024-04-05T10:00:00",
                "file_path": "reports/budget_vs_actual_q1_2024.pdf"
            },
            {
                "id": 2,
                "report_type": "FINANCIAL_STATEMENT",
                "period_start": "2024-01-01",
                "period_end": "2024-03-31",
                "created_at": "2024-04-05T11:00:00",
                "file_path": "reports/financial_statement_q1_2024.pdf"
            }
        ]
        
        return jsonify(reports), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/<int:report_id>/download', methods=['GET'])
def download_report(report_id):
    """보고서 파일을 다운로드합니다."""
    try:
        # 실제 구현시에는 DB에서 보고서 조회 및 파일 경로 가져오기
        # 샘플 정적 파일로 응답
        return send_from_directory(app.static_folder, 'sample_report.pdf', as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================ 계약 관리 API ================
@app.route('/api/contracts/standard/download', methods=['GET'])
def download_standard_contract():
    """표준 근로계약서를 다운로드합니다."""
    try:
        # 샘플 정적 파일로 응답
        return send_from_directory(app.static_folder, 'standard_contract.pdf', as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contracts/upload', methods=['POST'])
def upload_contract():
    """계약서를 업로드합니다."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400
            
        file = request.files['file']
        name = request.form.get('name', '')
        description = request.form.get('description', '')
        
        if file.filename == '':
            return jsonify({"error": "선택된 파일이 없습니다."}), 400
            
        # 실제 구현시에는 파일 저장 및 DB에 계약 정보 저장
        # 임시 응답
        contract = {
            "id": 1,
            "name": name,
            "description": description,
            "file_path": f"contracts/{file.filename}",
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "message": "계약서가 업로드되었습니다.",
            "contract": contract
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contracts', methods=['GET'])
def list_contracts():
    """계약서 목록을 조회합니다."""
    try:
        # 실제 DB 모델이 없으므로 임시 데이터 반환
        contracts = [
            {
                "id": 1,
                "name": "표준 근로계약서",
                "description": "신규 직원용 표준 근로계약서",
                "file_path": "contracts/standard_contract.pdf",
                "created_at": "2024-04-01T09:00:00"
            },
            {
                "id": 2,
                "name": "프리랜서 계약서",
                "description": "프리랜서 용역 계약서",
                "file_path": "contracts/freelancer_contract.pdf",
                "created_at": "2024-04-02T10:00:00"
            }
        ]
        
        return jsonify(contracts), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contracts/<int:contract_id>/download', methods=['GET'])
def download_contract(contract_id):
    """계약서 파일을 다운로드합니다."""
    try:
        # 실제 구현시에는 DB에서 계약서 조회 및 파일 경로 가져오기
        # 샘플 정적 파일로 응답
        return send_from_directory(app.static_folder, 'standard_contract.pdf', as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================ ERP 시스템 통합 API ================
@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """문서를 업로드합니다."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400
            
        file = request.files['file']
        type = request.form.get('type', '')
        name = request.form.get('name', '')
        description = request.form.get('description', '')
        
        if file.filename == '':
            return jsonify({"error": "선택된 파일이 없습니다."}), 400
            
        # 실제 구현시에는 파일 저장 및 DB에 문서 정보 저장
        # 임시 응답
        document = {
            "id": 1,
            "type": type,
            "name": name,
            "description": description,
            "file_path": f"documents/{file.filename}",
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "message": "문서가 업로드되었습니다.",
            "document": document
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """문서 목록을 조회합니다."""
    try:
        # 실제 DB 모델이 없으므로 임시 데이터 반환
        documents = [
            {
                "id": 1,
                "type": "ACCOUNTING",
                "name": "2024년 1분기 세무자료",
                "description": "1분기 부가세 신고 자료",
                "file_path": "documents/vat_2024_q1.pdf",
                "created_at": "2024-04-01T09:00:00"
            },
            {
                "id": 2,
                "type": "RECEIPT",
                "name": "3월 법인카드 영수증",
                "description": "3월분 법인카드 사용 영수증 모음",
                "file_path": "documents/receipts_march_2024.pdf",
                "created_at": "2024-04-02T10:00:00"
            }
        ]
        
        return jsonify(documents), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/merge', methods=['POST'])
def merge_documents():
    """여러 문서를 병합합니다."""
    try:
        data = request.get_json()
        
        if 'name' not in data or 'document_ids' not in data:
            return jsonify({"error": "name과 document_ids 필드가 필요합니다."}), 400
            
        # 실제 구현시에는 문서 병합 처리 및 저장
        # 임시 응답
        merged_document = {
            "id": 3,
            "type": "OTHER",
            "name": data['name'],
            "description": "병합된 문서",
            "file_path": "documents/merged_document.pdf",
            "source_documents": data['document_ids'],
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "message": "문서가 병합되었습니다.",
            "document": merged_document
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<int:document_id>/download', methods=['GET'])
def download_document(document_id):
    """문서 파일을 다운로드합니다."""
    try:
        # 실제 구현시에는 DB에서 문서 조회 및 파일 경로 가져오기
        # 샘플 정적 파일로 응답
        return send_from_directory(app.static_folder, 'sample_document.pdf', as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================ 회계 엑셀 API ================
@app.route('/api/excel/accounting/download', methods=['GET'])
def download_accounting_excel():
    """기본 회계 엑셀 파일을 다운로드합니다."""
    try:
        # 실제 파일 경로로 변경 필요
        original_excel_path = os.path.join(os.path.dirname(app.root_path), 'test용 회계 액셀.xlsx')
        if os.path.exists(original_excel_path):
            return send_from_directory(os.path.dirname(original_excel_path), os.path.basename(original_excel_path), as_attachment=True)
        else:
            # 파일이 없는 경우 샘플 파일 생성 후 전송
            session = Session()
            try:
                output_path = os.path.join(app.static_folder, 'sample_files', 'accounting_template.xlsx')
                if not os.path.exists(os.path.dirname(output_path)):
                    os.makedirs(os.path.dirname(output_path))
                excel_manager.create_custom_excel_template(session, output_path)
                return send_from_directory(os.path.dirname(output_path), os.path.basename(output_path), as_attachment=True)
            finally:
                session.close()
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/excel/custom/download', methods=['GET'])
def download_custom_excel():
    """커스텀 회계 엑셀 파일을 다운로드합니다."""
    try:
        session = Session()
        try:
            output_path = os.path.join(app.static_folder, 'sample_files', 'custom_accounting.xlsx')
            if not os.path.exists(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))
            excel_manager.create_custom_excel_template(session, output_path)
            return send_from_directory(os.path.dirname(output_path), os.path.basename(output_path), as_attachment=True)
        finally:
            session.close()
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/excel/upload', methods=['POST'])
def upload_excel():
    """엑셀 파일을 업로드합니다."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400
            
        file = request.files['file']
        name = request.form.get('name', '')
        description = request.form.get('description', '')
        
        if file.filename == '' or not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"error": "올바른 엑셀 파일이 아닙니다."}), 400
            
        # 실제 구현시에는 파일 저장 및 DB에 엑셀 파일 정보 저장
        # 임시 응답
        excel_file = {
            "id": 1,
            "name": name,
            "description": description,
            "file_path": f"excel/{file.filename}",
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "message": "엑셀 파일이 업로드되었습니다.",
            "excel_file": excel_file
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/excel/files', methods=['GET'])
def list_excel_files():
    """엑셀 파일 목록을 조회합니다."""
    try:
        # 실제 DB 모델이 없으므로 임시 데이터 반환
        files = [
            {
                "id": 1,
                "name": "회계 기본 엑셀",
                "description": "회계 처리를 위한 기본 엑셀 템플릿",
                "file_path": "excel/accounting_template.xlsx",
                "created_at": "2024-04-01T09:00:00"
            },
            {
                "id": 2,
                "name": "예산 계획 엑셀",
                "description": "연간 예산 계획 엑셀",
                "file_path": "excel/budget_plan_2024.xlsx",
                "created_at": "2024-04-02T10:00:00"
            }
        ]
        
        return jsonify(files), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/excel/files/<int:file_id>/download', methods=['GET'])
def download_excel_file(file_id):
    """엑셀 파일을 다운로드합니다."""
    try:
        # 실제 구현시에는 DB에서 엑셀 파일 조회 및 파일 경로 가져오기
        # 샘플 정적 파일로 응답
        return send_from_directory(app.static_folder, 'accounting_template.xlsx', as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================ 법인카드 관리 API ================
@app.route('/api/card-statements/upload', methods=['POST'])
def upload_card_statement():
    """법인카드 명세서를 업로드합니다."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 없습니다."}), 400
            
        file = request.files['file']
        company = request.form.get('company', '')
        month = request.form.get('month', '')
        
        if file.filename == '':
            return jsonify({"error": "선택된 파일이 없습니다."}), 400

        # 임시 파일로 저장
        temp_file_path = os.path.join(app.static_folder, 'sample_files', file.filename)
        if not os.path.exists(os.path.dirname(temp_file_path)):
            os.makedirs(os.path.dirname(temp_file_path))
        file.save(temp_file_path)
        
        try:
            # 파일 파싱 시도
            df = excel_manager.parse_card_statement(temp_file_path, company)
            
            # 실제 구현시에는 파싱된 데이터를 DB에 저장
            statements_count = len(df)
            
            return jsonify({
                "message": "법인카드 명세서가 업로드 및 분석되었습니다.",
                "statements_count": statements_count,
                "parsed_data": df.head(5).to_dict(orient='records')  # 참고용 샘플 데이터
            }), 201
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/card-statements', methods=['GET'])
def list_card_statements():
    """법인카드 사용 내역을 조회합니다."""
    try:
        month = request.args.get('month', '')
        
        # 실제 DB 모델이 없으므로 임시 데이터 반환
        statements = generate_sample_card_statements('shinhan', month)
        
        return jsonify(statements), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/card-statements/unprocessed', methods=['GET'])
def list_unprocessed_card_statements():
    """미처리된 법인카드 사용 내역을 조회합니다."""
    try:
        month = request.args.get('month', '')
        
        # 실제 DB 모델이 없으므로 임시 데이터 반환
        all_statements = generate_sample_card_statements('shinhan', month)
        unprocessed = [s for s in all_statements if s['process_status'] == 'UNPROCESSED']
        
        return jsonify(unprocessed), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/card-statements/process', methods=['POST'])
def process_card_statements():
    """법인카드 지출을 회계 처리합니다."""
    try:
        data = request.get_json()
        
        if 'account_id' not in data or 'statement_ids' not in data:
            return jsonify({"error": "account_id와 statement_ids 필드가 필요합니다."}), 400
            
        # 실제 구현시에는 법인카드 지출 회계 처리 로직
        # 임시 응답
        
        return jsonify({
            "message": "법인카드 지출이 처리되었습니다.",
            "processed_count": len(data['statement_ids'])
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 법인카드 명세서 샘플 데이터 생성 함수
def generate_sample_card_statements(company, month):
    """샘플 법인카드 사용 내역을 생성합니다."""
    now = datetime.now()
    statements = []
    
    # 원하는 월이 있으면 해당 월로 설정
    if month:
        year, month = month.split('-')
        year, month = int(year), int(month)
    else:
        year, month = now.year, now.month
    
    # 카드사별 마스킹된 카드번호 형식
    card_numbers = {
        'shinhan': '9410-****-****-1234',
        'kookmin': '5432-****-****-6789',
        'hana': '3456-****-****-7890',
        'ibk': '6789-****-****-1234'
    }
    
    # 샘플 가맹점 목록
    merchants = [
        "스타벅스 강남점", "이마트 용산점", "CU 한강로점", "교보문고 광화문점",
        "롯데마트 서초점", "CGV 용산아이파크몰", "KFC 종로점", "버거킹 신촌점",
        "맥도날드 홍대점", "올리브영 강남역점", "GS25 신사점", "공차 강남점"
    ]
    
    # 10개 정도의 더미 데이터 생성
    for i in range(1, 16):
        # 1-28일 사이의 날짜 생성
        day = min(i * 2, 28)
        date = datetime(year, month, day)
        
        # 금액 생성 (5,000 ~ 150,000)
        amount = (i * 8500) + 5000
        if i % 3 == 0:
            amount = amount * 2
            
        # 승인번호 생성
        approval_number = f"{year % 100}{month:02d}{day:02d}{i:04d}"
        
        # 처리 상태 (홀수번 아이템은 미처리, 짝수번 아이템은 처리완료)
        process_status = "UNPROCESSED" if i % 2 == 1 else "PROCESSED"
        
        # 가맹점 선택
        merchant_index = (i - 1) % len(merchants)
        
        # 법인카드 사용 내역 생성
        statement = {
            "id": i,
            "card_company": company,
            "card_number": card_numbers.get(company, "****-****-****-****"),
            "transaction_date": date.isoformat(),
            "merchant_name": merchants[merchant_index],
            "amount": amount,
            "approval_number": approval_number,
            "process_status": process_status
        }
        
        statements.append(statement)
    
    return statements

if __name__ == '__main__':
    # 서버 시작 시 데이터베이스 초기화
    init_db()
    
    logger.info("Starting server...")
    app.run(host='0.0.0.0', port=5000, debug=True) 
import requests
from datetime import datetime
from typing import Dict, List, Optional
import logging
from sqlalchemy.orm import Session
from ..database.models import Transaction

class ERPConnector:
    """ERP 시스템과의 연동을 담당하는 클래스"""
    
    def __init__(self, api_base_url: str, api_key: str):
        """
        Args:
            api_base_url (str): ERP API의 기본 URL
            api_key (str): API 인증 키
        """
        self.api_base_url = api_base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
    
    def fetch_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        지정된 기간의 거래 내역을 가져옵니다.
        
        Args:
            start_date (datetime): 조회 시작일
            end_date (datetime): 조회 종료일
            
        Returns:
            List[Dict]: 거래 내역 목록
        """
        try:
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            response = requests.get(
                f"{self.api_base_url}/transactions",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()["transactions"]
        except requests.exceptions.RequestException as e:
            self.logger.error(f"거래 내역 조회 중 오류 발생: {str(e)}")
            raise
    
    def sync_transactions(self, db_session: Session, transactions: List[Dict]) -> None:
        """
        가져온 거래 내역을 데이터베이스에 동기화합니다.
        
        Args:
            db_session (Session): 데이터베이스 세션
            transactions (List[Dict]): 동기화할 거래 내역 목록
        """
        try:
            for trans_data in transactions:
                transaction = Transaction(
                    transaction_date=datetime.fromisoformat(trans_data["date"]),
                    amount=trans_data["amount"],
                    description=trans_data["description"],
                    category=trans_data["category"],
                    contract_id=trans_data.get("contract_id")
                )
                db_session.add(transaction)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"거래 내역 동기화 중 오류 발생: {str(e)}")
            raise
    
    def get_invoice_details(self, invoice_id: str) -> Optional[Dict]:
        """
        특정 인보이스의 상세 정보를 조회합니다.
        
        Args:
            invoice_id (str): 조회할 인보이스 ID
            
        Returns:
            Optional[Dict]: 인보이스 상세 정보
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/invoices/{invoice_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"인보이스 조회 중 오류 발생: {str(e)}")
            return None

# 사용 예시
if __name__ == "__main__":
    # 테스트용 설정
    erp = ERPConnector(
        api_base_url="https://api.erp-system.com/v1",
        api_key="your-api-key-here"
    )
    
    # 최근 1주일 거래 내역 조회
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    transactions = erp.fetch_transactions(start_date, end_date)
    print(f"조회된 거래 내역 수: {len(transactions)}") 
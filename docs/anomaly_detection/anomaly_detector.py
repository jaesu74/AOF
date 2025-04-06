import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Tuple
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from ..database.models import Transaction

class AnomalyDetector:
    """Isolation Forest를 사용한 이상 지출 탐지 클래스"""
    
    def __init__(self, contamination: float = 0.1):
        """
        Args:
            contamination (float): 예상되는 이상치의 비율 (0.0 ~ 0.5)
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42
        )
        self.logger = logging.getLogger(__name__)
    
    def prepare_features(self, transactions: List[Dict]) -> pd.DataFrame:
        """
        거래 데이터에서 특성을 추출합니다.
        
        Args:
            transactions (List[Dict]): 거래 내역 목록
            
        Returns:
            pd.DataFrame: 특성이 추출된 데이터프레임
        """
        df = pd.DataFrame(transactions)
        
        # 시계열 특성 추출
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['day_of_week'] = df['transaction_date'].dt.dayofweek
        df['hour'] = df['transaction_date'].dt.hour
        
        # 금액 관련 특성
        df['amount_abs'] = df['amount'].abs()
        
        # 사용할 특성 선택
        features = ['amount_abs', 'day_of_week', 'hour']
        return df[features]
    
    def detect_anomalies(self, transactions: List[Dict]) -> Tuple[List[bool], List[float]]:
        """
        거래 내역에서 이상 지출을 탐지합니다.
        
        Args:
            transactions (List[Dict]): 거래 내역 목록
            
        Returns:
            Tuple[List[bool], List[float]]: (이상치 여부 목록, 이상 점수 목록)
        """
        try:
            if not transactions:
                return [], []
            
            # 특성 추출
            X = self.prepare_features(transactions)
            
            # 모델 학습 및 예측
            self.model.fit(X)
            predictions = self.model.predict(X)  # 1: 정상, -1: 이상치
            scores = self.model.score_samples(X)
            
            # 결과 변환 (True: 이상치, False: 정상)
            is_anomaly = [pred == -1 for pred in predictions]
            
            return is_anomaly, scores.tolist()
            
        except Exception as e:
            self.logger.error(f"이상 탐지 중 오류 발생: {str(e)}")
            raise
    
    def update_transaction_anomalies(self, db_session: Session, transaction_ids: List[int], 
                                   is_anomaly: List[bool]) -> None:
        """
        탐지된 이상치 정보를 데이터베이스에 업데이트합니다.
        
        Args:
            db_session (Session): 데이터베이스 세션
            transaction_ids (List[int]): 거래 ID 목록
            is_anomaly (List[bool]): 이상치 여부 목록
        """
        try:
            for trans_id, anomaly in zip(transaction_ids, is_anomaly):
                transaction = db_session.query(Transaction).get(trans_id)
                if transaction:
                    transaction.is_anomaly = anomaly
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"이상치 정보 업데이트 중 오류 발생: {str(e)}")
            raise

# 사용 예시
if __name__ == "__main__":
    # 테스트용 데이터 생성
    test_transactions = [
        {
            "transaction_date": datetime.now().isoformat(),
            "amount": amount,
            "category": "일반 지출"
        }
        for amount in [1000, 2000, 1500, 50000, 1800, 1200, 100000]  # 마지막 두 거래는 이상치
    ]
    
    # 이상치 탐지
    detector = AnomalyDetector(contamination=0.2)
    is_anomaly, scores = detector.detect_anomalies(test_transactions)
    
    # 결과 출력
    for i, (anomaly, score) in enumerate(zip(is_anomaly, scores)):
        print(f"거래 {i+1}: {'이상치' if anomaly else '정상'} (점수: {score:.3f})") 
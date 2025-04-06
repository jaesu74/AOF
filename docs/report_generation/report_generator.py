from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session
from ..database.models import Transaction, Report

class ReportGenerator:
    """PDF 보고서 생성을 담당하는 클래스"""
    
    def __init__(self, output_dir: str = 'reports'):
        """
        Args:
            output_dir (str): 보고서가 저장될 디렉토리 경로
        """
        self.output_dir = output_dir
        self.styles = getSampleStyleSheet()
        self.logger = logging.getLogger(__name__)
        
        # 한글 지원을 위한 폰트 설정
        self.styles.add(ParagraphStyle(
            name='KoreanNormal',
            fontName='Malgun Gothic',
            fontSize=10,
            leading=12
        ))
    
    def create_weekly_report(self, db_session: Session, start_date: datetime,
                           contract_id: Optional[int] = None) -> str:
        """
        주간 보고서를 생성합니다.
        
        Args:
            db_session (Session): 데이터베이스 세션
            start_date (datetime): 보고서 시작일
            contract_id (Optional[int]): 특정 계약에 대한 보고서 생성 시 계약 ID
            
        Returns:
            str: 생성된 보고서 파일 경로
        """
        try:
            end_date = start_date + timedelta(days=7)
            
            # 거래 내역 조회
            query = db_session.query(Transaction).filter(
                Transaction.transaction_date.between(start_date, end_date)
            )
            if contract_id:
                query = query.filter(Transaction.contract_id == contract_id)
            transactions = query.all()
            
            # 보고서 파일명 생성
            filename = f"{self.output_dir}/weekly_report_{start_date.strftime('%Y%m%d')}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4)
            
            # 보고서 내용 생성
            story = []
            
            # 제목 추가
            title = Paragraph("주간 거래 내역 보고서", self.styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # 기간 정보 추가
            period = Paragraph(
                f"보고 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
                self.styles['KoreanNormal']
            )
            story.append(period)
            story.append(Spacer(1, 12))
            
            # 거래 내역 테이블 생성
            if transactions:
                data = [['날짜', '금액', '설명', '이상 여부']]
                for trans in transactions:
                    data.append([
                        trans.transaction_date.strftime('%Y-%m-%d'),
                        f"{trans.amount:,.0f}원",
                        trans.description,
                        '이상치' if trans.is_anomaly else '정상'
                    ])
                
                table = Table(data, colWidths=[1.5*inch, 1.5*inch, 3*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Malgun Gothic-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Malgun Gothic'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ]))
                story.append(table)
                
                # 통계 정보 추가
                story.append(Spacer(1, 20))
                stats = [
                    f"총 거래 건수: {len(transactions)}건",
                    f"총 거래 금액: {sum(t.amount for t in transactions):,.0f}원",
                    f"이상 거래 건수: {sum(1 for t in transactions if t.is_anomaly)}건"
                ]
                for stat in stats:
                    story.append(Paragraph(stat, self.styles['KoreanNormal']))
                    story.append(Spacer(1, 6))
            
            else:
                story.append(Paragraph("해당 기간에 거래 내역이 없습니다.", self.styles['KoreanNormal']))
            
            # PDF 생성
            doc.build(story)
            
            # 보고서 정보 저장
            report = Report(
                report_type="weekly",
                generated_date=datetime.now(),
                file_path=filename,
                contract_id=contract_id
            )
            db_session.add(report)
            db_session.commit()
            
            return filename
            
        except Exception as e:
            self.logger.error(f"보고서 생성 중 오류 발생: {str(e)}")
            raise

# 사용 예시
if __name__ == "__main__":
    from datetime import datetime, timedelta
    
    # 테스트용 데이터 생성
    start_date = datetime.now() - timedelta(days=7)
    
    generator = ReportGenerator()
    report_path = generator.create_weekly_report(None, start_date)
    print(f"보고서가 생성되었습니다: {report_path}") 
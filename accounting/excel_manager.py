import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
from sqlalchemy.orm import Session
from database.models import Account, AccountType, JournalEntry, JournalLine

class ExcelManager:
    """Excel 파일 관리를 담당하는 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def read_excel_template(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Excel 회계 템플릿을 읽어서 시트별로 데이터프레임을 반환합니다.
        
        Args:
            file_path (str): Excel 파일 경로
            
        Returns:
            Dict[str, pd.DataFrame]: 시트명과 해당 데이터프레임의 딕셔너리
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            sheets = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets[sheet_name] = df
            
            return sheets
        except Exception as e:
            self.logger.error(f"Excel 파일 읽기 중 오류 발생: {str(e)}")
            raise
    
    def import_chart_of_accounts(self, session: Session, df: pd.DataFrame) -> List[Account]:
        """
        Excel 데이터프레임에서 계정과목을 가져와 데이터베이스에 저장합니다.
        
        Args:
            session (Session): 데이터베이스 세션
            df (pd.DataFrame): 계정과목 데이터프레임
            
        Returns:
            List[Account]: 생성된 계정과목 리스트
        """
        try:
            accounts = []
            
            # 데이터프레임 컬럼 확인 및 필요한 컬럼 매핑
            required_columns = ['계정코드', '계정명', '계정유형']
            if not all(col in df.columns for col in required_columns):
                raise ValueError("계정과목 데이터프레임에 필요한 컬럼이 없습니다.")
            
            for _, row in df.iterrows():
                # 계정 유형 매핑
                account_type_map = {
                    '자산': AccountType.ASSET,
                    '부채': AccountType.LIABILITY,
                    '자본': AccountType.EQUITY,
                    '수익': AccountType.REVENUE,
                    '비용': AccountType.EXPENSE
                }
                
                # 계정과목 정보 추출
                code = str(row['계정코드']).strip()
                name = str(row['계정명']).strip()
                account_type_str = str(row['계정유형']).strip()
                description = str(row.get('설명', ''))
                
                # 이미 존재하는 계정과목인지 확인
                existing_account = session.query(Account).filter_by(code=code).first()
                if existing_account:
                    continue
                
                # 계정 유형 매핑
                if account_type_str not in account_type_map:
                    self.logger.warning(f"알 수 없는 계정 유형: {account_type_str}, 기본값 '자산'으로 설정")
                    account_type = AccountType.ASSET
                else:
                    account_type = account_type_map[account_type_str]
                
                # 계정과목 생성
                account = Account(
                    code=code,
                    name=name,
                    type=account_type,
                    description=description
                )
                
                session.add(account)
                accounts.append(account)
            
            session.commit()
            return accounts
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"계정과목 가져오기 중 오류 발생: {str(e)}")
            raise
    
    def import_journal_entries(self, session: Session, df: pd.DataFrame) -> List[JournalEntry]:
        """
        Excel 데이터프레임에서 전표를 가져와 데이터베이스에 저장합니다.
        
        Args:
            session (Session): 데이터베이스 세션
            df (pd.DataFrame): 전표 데이터프레임
            
        Returns:
            List[JournalEntry]: 생성된 전표 리스트
        """
        try:
            entries = []
            
            # 데이터프레임 컬럼 확인 및 필요한 컬럼 매핑
            required_columns = ['날짜', '적요', '계정코드', '차변', '대변']
            if not all(col in df.columns for col in required_columns):
                raise ValueError("전표 데이터프레임에 필요한 컬럼이 없습니다.")
            
            # 날짜별로 그룹화
            grouped = df.groupby('날짜')
            
            for date, group in grouped:
                # 날짜 처리
                try:
                    if isinstance(date, str):
                        entry_date = datetime.strptime(date, '%Y-%m-%d')
                    else:
                        entry_date = pd.to_datetime(date).to_pydatetime()
                except Exception:
                    self.logger.warning(f"잘못된 날짜 형식: {date}, 현재 날짜로 설정")
                    entry_date = datetime.now()
                
                # 적요 처리
                descriptions = group['적요'].unique()
                description = descriptions[0] if len(descriptions) > 0 else "Excel에서 가져온 전표"
                
                # 전표 생성
                entry = JournalEntry(
                    entry_date=entry_date,
                    description=description,
                    created_by="Excel Import"
                )
                
                session.add(entry)
                session.flush()  # ID 할당을 위해 flush
                
                # 전표 라인 생성
                for _, row in group.iterrows():
                    code = str(row['계정코드']).strip()
                    debit = float(row['차변']) if not pd.isna(row['차변']) else 0
                    credit = float(row['대변']) if not pd.isna(row['대변']) else 0
                    
                    # 계정과목 조회
                    account = session.query(Account).filter_by(code=code).first()
                    if not account:
                        self.logger.warning(f"계정과목을 찾을 수 없음: {code}, 이 라인은 건너뜁니다.")
                        continue
                    
                    # 전표 라인 생성
                    line = JournalLine(
                        entry_id=entry.id,
                        account_id=account.id,
                        debit=debit,
                        credit=credit,
                        description=row.get('라인설명', '')
                    )
                    
                    session.add(line)
                
                entries.append(entry)
            
            session.commit()
            return entries
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"전표 가져오기 중 오류 발생: {str(e)}")
            raise
    
    def export_chart_of_accounts(self, session: Session) -> pd.DataFrame:
        """
        데이터베이스의 계정과목을 Excel로 내보낼 수 있는 데이터프레임으로 변환합니다.
        
        Args:
            session (Session): 데이터베이스 세션
            
        Returns:
            pd.DataFrame: 계정과목 데이터프레임
        """
        try:
            accounts = session.query(Account).all()
            
            # 계정 유형 매핑
            account_type_map = {
                AccountType.ASSET: '자산',
                AccountType.LIABILITY: '부채',
                AccountType.EQUITY: '자본',
                AccountType.REVENUE: '수익',
                AccountType.EXPENSE: '비용'
            }
            
            data = []
            for account in accounts:
                data.append({
                    '계정코드': account.code,
                    '계정명': account.name,
                    '계정유형': account_type_map.get(account.type, '기타'),
                    '설명': account.description or ''
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            self.logger.error(f"계정과목 내보내기 중 오류 발생: {str(e)}")
            raise
    
    def export_journal_entries(self, session: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        데이터베이스의 전표를 Excel로 내보낼 수 있는 데이터프레임으로 변환합니다.
        
        Args:
            session (Session): 데이터베이스 세션
            start_date (Optional[datetime]): 조회 시작일 (기본값: None)
            end_date (Optional[datetime]): 조회 종료일 (기본값: None)
            
        Returns:
            pd.DataFrame: 전표 데이터프레임
        """
        try:
            # 전표 조회 쿼리 생성
            query = session.query(JournalEntry)
            
            # 날짜 필터 적용
            if start_date:
                query = query.filter(JournalEntry.entry_date >= start_date)
            if end_date:
                query = query.filter(JournalEntry.entry_date <= end_date)
            
            # 날짜순 정렬
            entries = query.order_by(JournalEntry.entry_date).all()
            
            data = []
            for entry in entries:
                for line in entry.lines:
                    data.append({
                        '날짜': entry.entry_date.strftime('%Y-%m-%d'),
                        '적요': entry.description,
                        '계정코드': line.account.code,
                        '계정명': line.account.name,
                        '차변': line.debit if line.debit > 0 else None,
                        '대변': line.credit if line.credit > 0 else None,
                        '라인설명': line.description or ''
                    })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            self.logger.error(f"전표 내보내기 중 오류 발생: {str(e)}")
            raise
    
    def create_custom_excel_template(self, session: Session, output_path: str) -> str:
        """
        커스텀 회계 Excel 템플릿을 생성합니다.
        
        Args:
            session (Session): 데이터베이스 세션
            output_path (str): 저장할 파일 경로
            
        Returns:
            str: 생성된 파일 경로
        """
        try:
            # 계정과목 데이터프레임 생성
            accounts_df = self.export_chart_of_accounts(session)
            
            # 전표 템플릿 데이터프레임 생성
            journal_template = pd.DataFrame(columns=[
                '날짜', '적요', '계정코드', '계정명', '차변', '대변', '라인설명'
            ])
            
            # 빈 시산표 데이터프레임 생성
            trial_balance_template = pd.DataFrame(columns=[
                '계정코드', '계정명', '기초잔액', '차변합계', '대변합계', '잔액'
            ])
            
            # 재무제표 템플릿 데이터프레임 생성
            financial_statements_template = pd.DataFrame(columns=[
                '구분', '항목', '금액'
            ])
            
            # Excel 파일 생성
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                accounts_df.to_excel(writer, sheet_name='계정과목', index=False)
                journal_template.to_excel(writer, sheet_name='전표입력', index=False)
                trial_balance_template.to_excel(writer, sheet_name='시산표', index=False)
                financial_statements_template.to_excel(writer, sheet_name='재무제표', index=False)
                
                # 워크시트 포맷 설정
                workbook = writer.book
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    
                    # 열 너비 설정
                    worksheet.set_column('A:Z', 15)
                    
                    # 헤더 포맷
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'bg_color': '#D9E1F2',
                        'border': 1
                    })
                    
                    # 헤더에 포맷 적용
                    for col_num, value in enumerate(writer.sheets[sheet_name].table.columns):
                        worksheet.write(0, col_num, value, header_format)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"커스텀 Excel 템플릿 생성 중 오류 발생: {str(e)}")
            raise
    
    def parse_card_statement(self, file_path: str, card_company: str) -> pd.DataFrame:
        """
        법인카드 명세서를 파싱합니다.
        
        Args:
            file_path (str): 명세서 파일 경로
            card_company (str): 카드사 코드
            
        Returns:
            pd.DataFrame: 파싱된 명세서 데이터프레임
        """
        try:
            # 파일 확장자 확인
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # 카드사별 파싱 로직
            if card_company == 'shinhan':
                return self._parse_shinhan_card(file_path, ext)
            elif card_company == 'kookmin':
                return self._parse_kookmin_card(file_path, ext)
            elif card_company == 'hana':
                return self._parse_hana_card(file_path, ext)
            elif card_company == 'ibk':
                return self._parse_ibk_card(file_path, ext)
            else:
                # 기본 파싱 로직
                return self._parse_default_card(file_path, ext)
            
        except Exception as e:
            self.logger.error(f"법인카드 명세서 파싱 중 오류 발생: {str(e)}")
            raise
    
    def _parse_shinhan_card(self, file_path: str, ext: str) -> pd.DataFrame:
        """신한카드 명세서를 파싱합니다."""
        try:
            # CSV 또는 Excel 파일 처리
            if ext == '.csv':
                df = pd.read_csv(file_path, encoding='cp949')
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {ext}")
            
            # 주요 컬럼 매핑 (실제 신한카드 명세서 형식에 맞게 조정 필요)
            column_mapping = {
                '이용일자': 'transaction_date',
                '가맹점명': 'merchant_name',
                '이용금액': 'amount',
                '승인번호': 'approval_number'
            }
            
            # 컬럼 이름 변경
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df.rename(columns={old_col: new_col}, inplace=True)
            
            # 필수 컬럼 확인
            required_columns = ['transaction_date', 'merchant_name', 'amount']
            if not all(col in df.columns for col in required_columns):
                # 지원하지 않는 형식이면 기본 파싱 로직 사용
                return self._parse_default_card(file_path, ext)
            
            # 날짜 변환
            if 'transaction_date' in df.columns:
                df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
            
            # 금액 컬럼 숫자로 변환
            if 'amount' in df.columns:
                df['amount'] = pd.to_numeric(df['amount'].astype(str).str.replace(',', ''), errors='coerce')
            
            # 기타 필요한 컬럼 추가
            df['card_company'] = 'shinhan'
            df['card_number'] = '9410-****-****-1234'  # 가상의 마스킹된 카드번호
            df['process_status'] = 'UNPROCESSED'
            
            return df
            
        except Exception as e:
            self.logger.error(f"신한카드 명세서 파싱 중 오류 발생: {str(e)}")
            # 오류 발생 시 기본 파싱 로직 사용
            return self._parse_default_card(file_path, ext)
    
    def _parse_kookmin_card(self, file_path: str, ext: str) -> pd.DataFrame:
        """국민카드 명세서를 파싱합니다."""
        # 신한카드와 유사한 로직
        try:
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                # 지원하지 않는 형식이면 기본 파싱 로직 사용
                return self._parse_default_card(file_path, ext)
            
            # KB카드 데이터 처리 로직 구현
            # (실제 KB카드 명세서 형식에 맞게 조정 필요)
            
            df['card_company'] = 'kookmin'
            df['card_number'] = '5432-****-****-6789'
            df['process_status'] = 'UNPROCESSED'
            
            return df
            
        except Exception as e:
            self.logger.error(f"국민카드 명세서 파싱 중 오류 발생: {str(e)}")
            return self._parse_default_card(file_path, ext)
    
    def _parse_hana_card(self, file_path: str, ext: str) -> pd.DataFrame:
        """하나카드 명세서를 파싱합니다."""
        # 유사한 로직 구현
        return self._parse_default_card(file_path, ext)
    
    def _parse_ibk_card(self, file_path: str, ext: str) -> pd.DataFrame:
        """기업카드 명세서를 파싱합니다."""
        # 유사한 로직 구현
        return self._parse_default_card(file_path, ext)
    
    def _parse_default_card(self, file_path: str, ext: str) -> pd.DataFrame:
        """기본 카드 명세서 파싱 로직"""
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path, encoding='cp949')
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                # 지원하지 않는 파일 형식
                self.logger.warning(f"지원하지 않는 파일 형식: {ext}, 빈 데이터프레임 반환")
                return pd.DataFrame(columns=['transaction_date', 'merchant_name', 'amount', 'approval_number', 'card_company', 'card_number', 'process_status'])
            
            # 명세서 형식을 자동 감지하여 처리
            # 날짜, 가맹점, 금액 컬럼을 찾기 위한 키워드
            date_keywords = ['일자', '날짜', 'date', '이용일', '이용일자', '거래일']
            merchant_keywords = ['가맹점', '상호', '가맹점명', '거래처', 'merchant', '이용하신곳']
            amount_keywords = ['금액', '이용금액', '거래금액', 'amount', '결제금액']
            
            # 컬럼 자동 매핑
            column_mapping = {}
            
            for col in df.columns:
                col_lower = str(col).lower()
                
                # 날짜 컬럼 찾기
                if any(keyword in col_lower for keyword in date_keywords):
                    column_mapping[col] = 'transaction_date'
                    
                # 가맹점 컬럼 찾기
                elif any(keyword in col_lower for keyword in merchant_keywords):
                    column_mapping[col] = 'merchant_name'
                    
                # 금액 컬럼 찾기
                elif any(keyword in col_lower for keyword in amount_keywords):
                    column_mapping[col] = 'amount'
            
            # 매핑된 컬럼이 충분하지 않은 경우
            if len(column_mapping) < 3:
                self.logger.warning("파일 형식을 인식할 수 없습니다. 기본 변환을 시도합니다.")
                # 임시로 처음 3개 컬럼을 기본 매핑
                if len(df.columns) >= 3:
                    column_mapping = {
                        df.columns[0]: 'transaction_date',
                        df.columns[1]: 'merchant_name',
                        df.columns[2]: 'amount'
                    }
            
            # 컬럼 이름 변경
            df_mapped = df.rename(columns=column_mapping)
            
            # 필수 컬럼 확인 및 추가
            required_columns = ['transaction_date', 'merchant_name', 'amount', 'approval_number', 'card_company', 'card_number', 'process_status']
            
            for col in required_columns:
                if col not in df_mapped.columns:
                    if col == 'approval_number':
                        # 승인번호가 없으면 랜덤 생성
                        df_mapped[col] = range(10000, 10000 + len(df_mapped))
                    elif col == 'card_company':
                        df_mapped[col] = 'unknown'
                    elif col == 'card_number':
                        df_mapped[col] = '****-****-****-****'
                    elif col == 'process_status':
                        df_mapped[col] = 'UNPROCESSED'
                    else:
                        df_mapped[col] = None
            
            # 날짜 변환
            try:
                df_mapped['transaction_date'] = pd.to_datetime(df_mapped['transaction_date'], errors='coerce')
            except Exception:
                self.logger.warning("날짜 변환 실패, 현재 날짜로 설정합니다.")
                df_mapped['transaction_date'] = datetime.now()
            
            # 금액 컬럼 숫자로 변환
            try:
                df_mapped['amount'] = pd.to_numeric(df_mapped['amount'].astype(str).str.replace(',', ''), errors='coerce')
            except Exception:
                self.logger.warning("금액 변환 실패, 0으로 설정합니다.")
                df_mapped['amount'] = 0
            
            return df_mapped
            
        except Exception as e:
            self.logger.error(f"기본 카드 명세서 파싱 중 오류 발생: {str(e)}")
            # 오류 발생 시 빈 데이터프레임 반환
            return pd.DataFrame(columns=['transaction_date', 'merchant_name', 'amount', 'approval_number', 'card_company', 'card_number', 'process_status']) 
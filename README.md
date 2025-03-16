# AllOneFlow

계약 자동화, 정산 관리, AI 기반 이상 지출 탐지, 자동 보고서 생성 기능을 제공하는 통합 관리 시스템입니다.

## 주요 기능

1. **계약 자동화**
   - 표준 템플릿 기반의 계약서 자동 생성
   - 고객 정보, 계약 조건 등 자동 치환
   - WYSIWYG 스타일의 템플릿 편집 지원

2. **정산 관리**
   - ERP/회계 시스템과 RESTful API 연동
   - 지출 내역, 인보이스, 결제 데이터 실시간 동기화
   - 표준 스키마 기반 데이터 매핑

3. **AI 기반 이상 지출 탐지**
   - Isolation Forest 알고리즘 활용
   - 비정상적인 지출 패턴 자동 탐지
   - 실시간 모니터링 및 알림

4. **자동 보고서 생성**
   - 주간 단위 데이터 집계
   - PDF 형식의 보고서 자동 생성
   - 대시보드 스냅샷 포함

## 시스템 요구사항

- Python 3.8 이상
- SQLite 3.x
- 필요한 Python 패키지는 requirements.txt 참조

## 설치 방법

1. 저장소 클론
   ```bash
   git clone https://github.com/your-username/alloneflow.git
   cd alloneflow
   ```

2. 가상환경 생성 및 활성화
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. 필요한 패키지 설치
   ```bash
   pip install -r requirements.txt
   ```

4. 환경 변수 설정
   ```bash
   cp .env.example .env
   # .env 파일을 열어 필요한 설정값 입력
   ```

## 사용 방법

1. 서버 실행
   ```bash
   python -m api.app
   ```

2. API 엔드포인트
   - 계약 생성: POST /api/contracts
   - 거래 내역 동기화: POST /api/transactions/sync
   - 주간 보고서 생성: POST /api/reports/weekly
   - 보고서 다운로드: GET /api/reports/download/{report_id}

## API 사용 예시

1. 계약 생성
   ```bash
   curl -X POST http://localhost:5000/api/contracts \
   -H "Content-Type: application/json" \
   -d '{
       "company_name": "테스트 기업",
       "contact_person": "홍길동",
       "start_date": "2024-01-01",
       "end_date": "2024-12-31",
       "contract_type": "서비스 이용 계약"
   }'
   ```

2. 거래 내역 동기화
   ```bash
   curl -X POST http://localhost:5000/api/transactions/sync \
   -H "Content-Type: application/json" \
   -d '{
       "start_date": "2024-01-01",
       "end_date": "2024-01-31"
   }'
   ```

## 프로젝트 구조

```
AllOneFlow/
├── api/
│   └── app.py                 # Flask API 서버
├── contract_automation/
│   └── contract_generator.py  # 계약서 생성 모듈
├── erp_integration/
│   └── erp_connector.py       # ERP 연동 모듈
├── anomaly_detection/
│   └── anomaly_detector.py    # 이상 탐지 모듈
├── report_generation/
│   └── report_generator.py    # 보고서 생성 모듈
├── database/
│   └── models.py             # 데이터베이스 모델
├── templates/                 # 계약서, 보고서 템플릿
├── tests/                    # 테스트 코드
├── requirements.txt          # 패키지 의존성
└── README.md                 # 프로젝트 문서
```

## 라이선스

MIT License

## 기여 방법

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 
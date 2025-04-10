# 법인카드 명세서 자동 처리 시스템 구현 보고서

## 개요
본 문서는 AllOneFlow 회계 시스템의 법인카드 명세서 자동 처리 기능에 대한 구현 현황과 각 카드사별 연동 가능성을 보고합니다.

## 구현 현황

현재 시스템은 다음 4개 주요 법인카드사의 명세서를 처리할 수 있는 기본 프레임워크를 구축했습니다:
1. 신한카드
2. 국민카드
3. 하나카드
4. 기업카드

### 지원 파일 형식
- Excel (.xlsx, .xls)
- CSV (.csv)

### 기본 처리 과정
1. 파일 업로드
2. 카드사에 따른 전용 파서로 데이터 추출
3. 데이터 정제 및 표준화
4. 회계 시스템에 통합
5. 자동 분개 처리

## 카드사별 연동 가능성 평가

### 1. 신한카드
- **연동 가능성**: 높음 (⭐⭐⭐⭐⭐)
- **명세서 형식**: 표준화된 Excel/CSV 제공
- **API 제공**: 신한 오픈 API 플랫폼을 통해 데이터 연동 가능
- **특이사항**: 
  - 가맹점 정보가 상세하게 제공됨
  - 승인번호, 카드번호, 거래일시 등 구조화된 데이터 제공
  - 법인카드 관리 시스템(Shinhan pCard)과 연동 가능

### 2. 국민카드
- **연동 가능성**: 높음 (⭐⭐⭐⭐)
- **명세서 형식**: 표준화된 Excel 제공
- **API 제공**: KB 오픈 API를 통한 연동 가능
- **특이사항**:
  - 엑셀 형식이 주기적으로 변경되어 정기적인 업데이트 필요
  - 다양한 카테고리 정보 제공으로 비용 분류 자동화에 유리
  - 법인카드 포털에서 일괄 다운로드 기능 제공

### 3. 하나카드
- **연동 가능성**: 중간 (⭐⭐⭐)
- **명세서 형식**: PDF 및 Excel 제공
- **API 제공**: 제한적 API 제공
- **특이사항**:
  - PDF 형식이 주요 제공 형태로, OCR 처리 필요할 수 있음
  - 엑셀 다운로드는 기업 전용 서비스(하나 비즈니스카드)에서만 제공
  - 데이터 형식이 다소 복잡하여 추가 정제 작업 필요

### 4. 기업카드
- **연동 가능성**: 중간 (⭐⭐⭐)
- **명세서 형식**: CSV 및 PDF 제공
- **API 제공**: 현재 공개 API 미제공
- **특이사항**:
  - CSV 형식에서 인코딩 이슈가 종종 발생
  - 가맹점 정보가 가끔 불완전하게 제공됨
  - 기업 인터넷뱅킹 서비스를 통한 추출 필요

## 향후 개선 방안

### 1. 데이터 추출 강화
- OCR 기술 도입으로 PDF 명세서 처리 기능 강화
- 머신러닝 모델을 활용한 가맹점 정보 자동 분류 시스템 구축
- 카드사 형식 변경에 자동 대응하는 적응형 파싱 알고리즘 개발

### 2. 직접 API 연동
- 각 카드사 API와 직접 연동하여 수동 파일 다운로드 과정 생략
- 실시간 거래 정보 수집으로 즉각적인 회계 반영
- 사용자 인증 및 보안 프로토콜 구현

### 3. 자동화 확대
- 반복적인 지출 패턴 학습을 통한 계정 자동 매핑
- 예외 항목 자동 감지 및 알림 시스템
- 예산 대비 지출 실시간 모니터링 기능

## 제안된 현금 전표 처리 AI 모델

현금 전표를 읽어 엑셀에 자동으로 입력할 수 있는 AI 모델 5가지를 추천합니다:

1. **Microsoft Azure Form Recognizer**
   - 특징: 전표 양식 자동 인식, 고품질 OCR, 코드 없이 사용자 정의 가능
   - 장점: Microsoft Excel과의 통합이 원활함
   - 단점: 클라우드 기반으로 인터넷 연결 필요

2. **Google Document AI**
   - 특징: 구조화된 문서 처리에 특화, 고성능 OCR
   - 장점: 다양한 언어와 서식 지원, Google Sheets와 통합 용이
   - 단점: 복잡한 커스터마이징에 전문적 지식 필요

3. **Amazon Textract**
   - 특징: 테이블, 양식, 텍스트 추출에 최적화
   - 장점: AWS 서비스 통합으로 확장성 높음
   - 단점: 한글 지원은 있으나 영어보다 정확도 낮을 수 있음

4. **ABBYY FlexiCapture**
   - 특징: 엔터프라이즈급 문서 처리, 워크플로우 자동화
   - 장점: 높은 정확도, 복잡한 양식 처리 가능
   - 단점: 상대적으로 높은 비용

5. **Nanonets OCR API**
   - 특징: 머신러닝 기반 문서 인식, 낮은 코드 요구사항
   - 장점: 빠른 학습 능력, 맞춤형 필드 추출 가능
   - 단점: 대용량 처리시 추가 비용 발생

## 결론

법인카드 명세서 자동 처리 시스템은 현재 기본적인 파싱 기능이 구현되었으며, 특히 신한카드와 국민카드는 높은 수준의 연동이 가능합니다. 각 카드사별 명세서 형식에 최적화된 파서의 지속적인 개선과 API 직접 연동을 통해 더욱 효율적인 시스템으로 발전시킬 수 있을 것입니다.

현금 전표 처리를 위한 AI 모델 도입은 수동 입력 과정을 크게 줄이고 정확도를 높일 수 있는 기회를 제공할 것입니다. 특히 국내 환경에 맞는 한글 문서 인식 역량을 갖춘 모델 선택이 중요합니다.

---
작성일: 2024년 4월 6일 
# AllOneFlow API 문서

이 저장소는 AllOneFlow 시스템의 API 문서를 제공합니다.

## API 문서 접근 방법

API 문서는 다음 URL에서 접근할 수 있습니다:
- [https://api.aof.wvl.co.kr](https://api.aof.wvl.co.kr)

## 개요

AllOneFlow API는 회계 관리, 계약 자동화, 보고서 생성 및 법인카드 관리를 위한 RESTful 엔드포인트를 제공합니다.

## 주요 엔드포인트

### 회계 관리
- 회계연도 관리: `/api/fiscal-years`
- 계정과목 관리: `/api/accounts`
- 전표 관리: `/api/journal-entries`

### 보고서 관리
- 보고서 생성: `/api/reports`
- 보고서 다운로드: `/api/reports/download/{report_id}`

### 계약 관리
- 표준 계약서 다운로드: `/api/contracts/standard/download`
- 계약서 업로드: `/api/contracts/upload`

### 법인카드 관리
- 법인카드 명세서 업로드: `/api/card-statements/upload`
- 법인카드 명세서 목록 조회: `/api/card-statements`

### 회계 엑셀
- 회계 엑셀 다운로드: `/api/excel/accounting/download`
- 엑셀 파일 업로드: `/api/excel/upload`

## 인증

현재 버전에서는 API 키 인증이 필요하지 않습니다. 향후 릴리스에서 인증 메커니즘이 추가될 예정입니다.

## 자세한 정보

더 자세한 내용은 [AllOneFlow 홈페이지](https://aof.wvl.co.kr)를 방문하세요. 
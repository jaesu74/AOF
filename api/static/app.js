document.addEventListener('DOMContentLoaded', function() {
    // 탭 전환 기능
    const navLinks = document.querySelectorAll('nav a');
    const sections = document.querySelectorAll('main section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 탭 활성화
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // 섹션 활성화
            const sectionId = this.getAttribute('data-section');
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === sectionId) {
                    section.classList.add('active');
                }
            });
        });
    });
    
    // 기본 데이터 로드
    loadFiscalYears();
    loadAccounts();
    setCurrentDate();
    
    // 이벤트 리스너 등록
    document.getElementById('create-fiscal-year').addEventListener('click', createFiscalYear);
    document.getElementById('refresh-fiscal-years').addEventListener('click', loadFiscalYears);
    document.getElementById('create-account').addEventListener('click', createAccount);
    document.getElementById('refresh-accounts').addEventListener('click', loadAccounts);
    document.getElementById('add-line').addEventListener('click', addJournalLine);
    document.getElementById('create-journal-entry').addEventListener('click', createJournalEntry);
    
    // 차변/대변 입력 시 합계 계산
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('debit') || e.target.classList.contains('credit')) {
            calculateTotals();
        }
    });
    
    // 새로운 기능들을 위한 이벤트 리스너
    if (document.getElementById('generate-report')) {
        document.getElementById('generate-report').addEventListener('click', generateReport);
        document.getElementById('refresh-reports').addEventListener('click', loadReports);
    }
    
    if (document.getElementById('download-standard-contract')) {
        document.getElementById('download-standard-contract').addEventListener('click', downloadStandardContract);
        document.getElementById('upload-contract').addEventListener('click', uploadContract);
        document.getElementById('refresh-contracts').addEventListener('click', loadContracts);
    }
    
    if (document.getElementById('upload-document')) {
        document.getElementById('upload-document').addEventListener('click', uploadDocument);
        document.getElementById('merge-documents').addEventListener('click', mergeDocuments);
        document.getElementById('refresh-documents').addEventListener('click', loadDocuments);
    }
    
    if (document.getElementById('download-accounting-excel')) {
        document.getElementById('download-accounting-excel').addEventListener('click', downloadAccountingExcel);
        document.getElementById('download-custom-excel').addEventListener('click', downloadCustomExcel);
        document.getElementById('upload-excel').addEventListener('click', uploadExcelFile);
        document.getElementById('refresh-excel-files').addEventListener('click', loadExcelFiles);
    }
    
    if (document.getElementById('upload-card-statement')) {
        document.getElementById('upload-card-statement').addEventListener('click', uploadCardStatement);
        document.getElementById('filter-card-statements').addEventListener('click', filterCardStatements);
        document.getElementById('process-card-expenses').addEventListener('click', processCardExpenses);
    }
    
    // 새로운 섹션 초기화
    initializeFunctions();
});

// 현재 날짜 설정
function setCurrentDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    document.getElementById('entry-date').value = `${year}-${month}-${day}`;
}

// 회계연도 목록 로드
function loadFiscalYears() {
    fetch('/api/fiscal-years')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('fiscal-years-table');
            tableBody.innerHTML = '';
            
            data.forEach(fy => {
                const row = document.createElement('tr');
                
                const startDate = new Date(fy.start_date).toLocaleDateString();
                const endDate = new Date(fy.end_date).toLocaleDateString();
                const status = fy.is_closed ? '마감됨' : '활성';
                const closeButton = fy.is_closed ? '-' : `<button onclick="closeFiscalYear(${fy.id})">마감</button>`;
                
                row.innerHTML = `
                    <td>${fy.id}</td>
                    <td>${fy.year}</td>
                    <td>${startDate}</td>
                    <td>${endDate}</td>
                    <td>${status}</td>
                    <td>${closeButton}</td>
                `;
                
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            showToast('회계연도 데이터를 불러오는 데 실패했습니다.', true);
            console.error('Error:', error);
        });
}

// 회계연도 생성
function createFiscalYear() {
    const year = document.getElementById('year').value;
    
    fetch('/api/fiscal-years', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ year: parseInt(year) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('회계연도가 성공적으로 생성되었습니다.');
        loadFiscalYears();
    })
    .catch(error => {
        showToast(error.message || '회계연도 생성에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 회계연도 마감
function closeFiscalYear(id) {
    if (!confirm('이 회계연도를 마감하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
        return;
    }
    
    fetch(`/api/fiscal-years/${id}/close`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ closed_by: 'admin' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('회계연도가 성공적으로 마감되었습니다.');
        loadFiscalYears();
    })
    .catch(error => {
        showToast(error.message || '회계연도 마감에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 계정과목 목록 로드
function loadAccounts() {
    fetch('/api/accounts')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('accounts-table');
            tableBody.innerHTML = '';
            
            // 계정과목 테이블 업데이트
            data.forEach(account => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${account.id}</td>
                    <td>${account.code}</td>
                    <td>${account.name}</td>
                    <td>${getAccountTypeDisplayName(account.type)}</td>
                    <td>${account.description || '-'}</td>
                `;
                tableBody.appendChild(row);
            });
            
            // 전표 라인 드롭다운 업데이트
            const accountSelects = document.querySelectorAll('.account-select');
            accountSelects.forEach(select => {
                select.innerHTML = '<option value="">계정과목 선택</option>';
                data.forEach(account => {
                    select.innerHTML += `<option value="${account.id}">${account.code} - ${account.name}</option>`;
                });
            });
        })
        .catch(error => {
            showToast('계정과목 데이터를 불러오는 데 실패했습니다.', true);
            console.error('Error:', error);
        });
}

// 계정과목 생성
function createAccount() {
    const code = document.getElementById('account-code').value;
    const name = document.getElementById('account-name').value;
    const type = document.getElementById('account-type').value;
    const description = document.getElementById('account-description').value;
    
    if (!code || !name || !type) {
        showToast('코드, 이름, 유형은 필수 입력 항목입니다.', true);
        return;
    }
    
    fetch('/api/accounts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code, name, type, description })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('계정과목이 성공적으로 생성되었습니다.');
        loadAccounts();
        
        // 폼 초기화
        document.getElementById('account-code').value = '';
        document.getElementById('account-name').value = '';
        document.getElementById('account-description').value = '';
    })
    .catch(error => {
        showToast(error.message || '계정과목 생성에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 전표 라인 추가
function addJournalLine() {
    const journalLines = document.getElementById('journal-lines');
    const lineCount = journalLines.querySelectorAll('.journal-line').length + 1;
    
    const lineDiv = document.createElement('div');
    lineDiv.className = 'journal-line';
    lineDiv.innerHTML = `
        <div class="form-group">
            <label for="account-id-${lineCount}">계정:</label>
            <select id="account-id-${lineCount}" class="account-select">
                <option value="">계정과목 선택</option>
            </select>
        </div>
        <div class="form-group">
            <label for="debit-${lineCount}">차변:</label>
            <input type="number" id="debit-${lineCount}" class="debit" value="0">
        </div>
        <div class="form-group">
            <label for="credit-${lineCount}">대변:</label>
            <input type="number" id="credit-${lineCount}" class="credit" value="0">
        </div>
        <div class="form-group">
            <label for="line-description-${lineCount}">설명:</label>
            <input type="text" id="line-description-${lineCount}">
        </div>
        <button class="remove-line" onclick="removeJournalLine(this)">삭제</button>
    `;
    
    journalLines.insertBefore(lineDiv, document.getElementById('add-line'));
    
    // 계정과목 목록 로드
    loadAccountsForSelect(document.getElementById(`account-id-${lineCount}`));
}

// 전표 라인 삭제
function removeJournalLine(button) {
    const lineDiv = button.parentElement;
    lineDiv.remove();
    calculateTotals();
}

// 계정과목 선택 상자 업데이트
function loadAccountsForSelect(selectElement) {
    fetch('/api/accounts')
        .then(response => response.json())
        .then(data => {
            selectElement.innerHTML = '<option value="">계정과목 선택</option>';
            data.forEach(account => {
                selectElement.innerHTML += `<option value="${account.id}">${account.code} - ${account.name}</option>`;
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 차변/대변 합계 계산
function calculateTotals() {
    const debits = document.querySelectorAll('.debit');
    const credits = document.querySelectorAll('.credit');
    
    let totalDebit = 0;
    let totalCredit = 0;
    
    debits.forEach(input => {
        totalDebit += parseFloat(input.value) || 0;
    });
    
    credits.forEach(input => {
        totalCredit += parseFloat(input.value) || 0;
    });
    
    document.getElementById('total-debit').textContent = totalDebit.toLocaleString();
    document.getElementById('total-credit').textContent = totalCredit.toLocaleString();
    
    // 불균형이면 배경색 변경
    const totalsDiv = document.querySelector('.totals');
    if (totalDebit !== totalCredit) {
        totalsDiv.style.backgroundColor = '#ffe0e0';
    } else {
        totalsDiv.style.backgroundColor = '#e0ffe0';
    }
}

// 전표 생성
function createJournalEntry() {
    const entryDate = document.getElementById('entry-date').value;
    const description = document.getElementById('entry-description').value;
    const createdBy = document.getElementById('created-by').value;
    
    if (!entryDate || !description || !createdBy) {
        showToast('전표일자, 설명, 작성자는 필수 입력 항목입니다.', true);
        return;
    }
    
    // 전표 라인 데이터 수집
    const lineElements = document.querySelectorAll('.journal-line');
    const lines = [];
    
    let totalDebit = 0;
    let totalCredit = 0;
    
    for (let i = 0; i < lineElements.length; i++) {
        const lineElement = lineElements[i];
        const accountSelect = lineElement.querySelector('.account-select');
        const debitInput = lineElement.querySelector('.debit');
        const creditInput = lineElement.querySelector('.credit');
        const lineDescriptionInput = lineElement.querySelector('input[id^="line-description-"]');
        
        const accountId = accountSelect.value;
        const debit = parseFloat(debitInput.value) || 0;
        const credit = parseFloat(creditInput.value) || 0;
        const lineDescription = lineDescriptionInput.value;
        
        if (!accountId) {
            showToast(`${i+1}번째 라인의 계정과목을 선택해주세요.`, true);
            return;
        }
        
        if (debit === 0 && credit === 0) {
            showToast(`${i+1}번째 라인의 차변 또는 대변을 입력해주세요.`, true);
            return;
        }
        
        lines.push({
            account_id: parseInt(accountId),
            debit,
            credit,
            description: lineDescription
        });
        
        totalDebit += debit;
        totalCredit += credit;
    }
    
    if (lines.length === 0) {
        showToast('최소 하나 이상의 전표 라인이 필요합니다.', true);
        return;
    }
    
    if (totalDebit !== totalCredit) {
        showToast('차변과 대변의 합계가 일치해야 합니다.', true);
        return;
    }
    
    const data = {
        entry_date: entryDate,
        description,
        created_by: createdBy,
        lines
    };
    
    fetch('/api/journal-entries', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('전표가 성공적으로 생성되었습니다.');
        
        // 폼 초기화
        document.getElementById('entry-description').value = '';
        document.querySelectorAll('.journal-line').forEach((line, index) => {
            if (index > 0) {
                line.remove();
            } else {
                line.querySelector('.account-select').value = '';
                line.querySelector('.debit').value = '0';
                line.querySelector('.credit').value = '0';
                line.querySelector('input[id^="line-description-"]').value = '';
            }
        });
        calculateTotals();
    })
    .catch(error => {
        showToast(error.message || '전표 생성에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 계정과목 유형 표시 이름 변환
function getAccountTypeDisplayName(type) {
    const typeMap = {
        'ASSET': '자산',
        'LIABILITY': '부채',
        'EQUITY': '자본',
        'REVENUE': '수익',
        'EXPENSE': '비용'
    };
    return typeMap[type] || type;
}

// 토스트 메시지 표시
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = isError ? 'toast error visible' : 'toast visible';
    
    setTimeout(() => {
        toast.className = isError ? 'toast error' : 'toast';
    }, 3000);
}

// 새로운 기능 초기화
function initializeFunctions() {
    // 모든 섹션 초기화
    initializeReportSection();
    initializeContractSection();
    initializeERPSection();
    initializeExcelSection();
    initializeCardSection();
    
    // 현재 날짜 설정
    setAllDateInputs();
}

// 모든 날짜 입력 필드에 현재 날짜 설정
function setAllDateInputs() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    
    // 보고서 기간 설정
    if (document.getElementById('report-period-start')) {
        document.getElementById('report-period-start').value = `${year}-${month}-01`;
    }
    if (document.getElementById('report-period-end')) {
        document.getElementById('report-period-end').value = `${year}-${month}-${day}`;
    }
    
    // 카드명세서 월 설정
    if (document.getElementById('statement-month')) {
        document.getElementById('statement-month').value = `${year}-${month}`;
    }
    if (document.getElementById('card-statement-filter-month')) {
        document.getElementById('card-statement-filter-month').value = `${year}-${month}`;
    }
}

// ================ 보고서 생성 기능 ================
function initializeReportSection() {
    loadFiscalYearsForSelect('report-fiscal-year');
    loadReports();
}

// 회계연도 선택상자 로드
function loadFiscalYearsForSelect(selectId) {
    if (!document.getElementById(selectId)) return;
    
    fetch('/api/fiscal-years')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById(selectId);
            select.innerHTML = '<option value="">회계연도 선택</option>';
            
            data.forEach(fy => {
                select.innerHTML += `<option value="${fy.id}">${fy.year}년</option>`;
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 보고서 생성
function generateReport() {
    const fiscalYearId = document.getElementById('report-fiscal-year').value;
    const reportType = document.getElementById('report-type').value;
    const periodStart = document.getElementById('report-period-start').value;
    const periodEnd = document.getElementById('report-period-end').value;
    
    if (!fiscalYearId || !reportType || !periodStart || !periodEnd) {
        showToast('모든 필드를 입력해주세요.', true);
        return;
    }
    
    showToast('보고서 생성 중입니다. 잠시만 기다려주세요.');
    
    fetch('/api/reports', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            fiscal_year_id: parseInt(fiscalYearId),
            report_type: reportType,
            period_start: periodStart,
            period_end: periodEnd
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('보고서가 성공적으로 생성되었습니다.');
        loadReports();
    })
    .catch(error => {
        showToast(error.message || '보고서 생성에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 보고서 목록 로드
function loadReports() {
    if (!document.getElementById('reports-table')) return;
    
    fetch('/api/reports')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('reports-table');
            tableBody.innerHTML = '';
            
            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">생성된 보고서가 없습니다.</td></tr>';
                return;
            }
            
            data.forEach(report => {
                const row = document.createElement('tr');
                const createdAt = new Date(report.created_at).toLocaleString();
                const period = `${new Date(report.period_start).toLocaleDateString()} ~ ${new Date(report.period_end).toLocaleDateString()}`;
                
                row.innerHTML = `
                    <td>${report.id}</td>
                    <td>${getReportTypeName(report.report_type)}</td>
                    <td>${createdAt}</td>
                    <td>${period}</td>
                    <td><a href="/api/reports/${report.id}/download" class="download-link">다운로드</a></td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            showToast('보고서 목록을 불러오는 데 실패했습니다.', true);
            console.error('Error:', error);
        });
}

// 보고서 유형 이름 변환
function getReportTypeName(type) {
    const typeMap = {
        'BUDGET_VS_ACTUAL': '예산 대비 실적',
        'FINANCIAL_STATEMENT': '재무제표',
        'CASH_FLOW': '현금흐름표',
        'TAX_SUMMARY': '세금 요약'
    };
    return typeMap[type] || type;
}

// ================ 계약 관리 기능 ================
function initializeContractSection() {
    loadContracts();
}

// 표준 근로계약서 다운로드
function downloadStandardContract() {
    window.location.href = '/api/contracts/standard/download';
}

// 계약서 업로드
function uploadContract() {
    const name = document.getElementById('contract-name').value;
    const description = document.getElementById('contract-description').value;
    const fileInput = document.getElementById('contract-file');
    
    if (!name || !fileInput.files[0]) {
        showToast('계약서 이름과 파일을 선택해주세요.', true);
        return;
    }
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('file', fileInput.files[0]);
    
    showToast('계약서 업로드 중입니다. 잠시만 기다려주세요.');
    
    fetch('/api/contracts/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('계약서가 성공적으로 업로드되었습니다.');
        document.getElementById('contract-name').value = '';
        document.getElementById('contract-description').value = '';
        fileInput.value = '';
        loadContracts();
    })
    .catch(error => {
        showToast(error.message || '계약서 업로드에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 계약서 목록 로드
function loadContracts() {
    if (!document.getElementById('contracts-table')) return;
    
    fetch('/api/contracts')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('contracts-table');
            tableBody.innerHTML = '';
            
            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">업로드된 계약서가 없습니다.</td></tr>';
                return;
            }
            
            data.forEach(contract => {
                const row = document.createElement('tr');
                const uploadDate = new Date(contract.created_at).toLocaleString();
                
                row.innerHTML = `
                    <td>${contract.id}</td>
                    <td>${contract.name}</td>
                    <td>${contract.description || '-'}</td>
                    <td>${uploadDate}</td>
                    <td><a href="/api/contracts/${contract.id}/download" class="download-link">다운로드</a></td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            showToast('계약서 목록을 불러오는 데 실패했습니다.', true);
            console.error('Error:', error);
        });
}

// ================ ERP 시스템 통합 기능 ================
function initializeERPSection() {
    loadDocuments();
    updateMergeDocumentList();
}

// 문서 업로드
function uploadDocument() {
    const type = document.getElementById('document-type').value;
    const name = document.getElementById('document-name').value;
    const description = document.getElementById('document-description').value;
    const fileInput = document.getElementById('document-file');
    
    if (!type || !name || !fileInput.files[0]) {
        showToast('모든 필수 필드를 입력해주세요.', true);
        return;
    }
    
    const formData = new FormData();
    formData.append('type', type);
    formData.append('name', name);
    formData.append('description', description);
    formData.append('file', fileInput.files[0]);
    
    showToast('문서 업로드 중입니다. 잠시만 기다려주세요.');
    
    fetch('/api/documents/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('문서가 성공적으로 업로드되었습니다.');
        document.getElementById('document-name').value = '';
        document.getElementById('document-description').value = '';
        fileInput.value = '';
        loadDocuments();
        updateMergeDocumentList();
    })
    .catch(error => {
        showToast(error.message || '문서 업로드에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 문서 병합
function mergeDocuments() {
    const mergeName = document.getElementById('merge-name').value;
    const checkboxes = document.querySelectorAll('#merge-document-list input[type="checkbox"]:checked');
    
    if (!mergeName || checkboxes.length < 2) {
        showToast('병합할 문서 이름과 2개 이상의 문서를 선택해주세요.', true);
        return;
    }
    
    const documentIds = Array.from(checkboxes).map(checkbox => checkbox.value);
    
    showToast('문서 병합 중입니다. 잠시만 기다려주세요.');
    
    fetch('/api/documents/merge', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: mergeName,
            document_ids: documentIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('문서가 성공적으로 병합되었습니다.');
        document.getElementById('merge-name').value = '';
        // 체크박스 초기화
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        loadDocuments();
    })
    .catch(error => {
        showToast(error.message || '문서 병합에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 문서 목록 로드
function loadDocuments() {
    if (!document.getElementById('documents-table')) return;
    
    fetch('/api/documents')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('documents-table');
            tableBody.innerHTML = '';
            
            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center;">업로드된 문서가 없습니다.</td></tr>';
                return;
            }
            
            data.forEach(doc => {
                const row = document.createElement('tr');
                const uploadDate = new Date(doc.created_at).toLocaleString();
                
                row.innerHTML = `
                    <td>${doc.id}</td>
                    <td>${getDocumentTypeName(doc.type)}</td>
                    <td>${doc.name}</td>
                    <td>${doc.description || '-'}</td>
                    <td>${uploadDate}</td>
                    <td><a href="/api/documents/${doc.id}/download" class="download-link">다운로드</a></td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            showToast('문서 목록을 불러오는 데 실패했습니다.', true);
            console.error('Error:', error);
        });
}

// 병합 문서 목록 업데이트
function updateMergeDocumentList() {
    if (!document.getElementById('merge-document-list')) return;
    
    fetch('/api/documents')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('merge-document-list');
            container.innerHTML = '';
            
            if (data.length === 0) {
                container.innerHTML = '<p>병합할 문서가 없습니다. 먼저 문서를 업로드해주세요.</p>';
                return;
            }
            
            data.forEach(doc => {
                const item = document.createElement('div');
                item.className = 'checkbox-item';
                item.innerHTML = `
                    <input type="checkbox" id="doc-${doc.id}" value="${doc.id}">
                    <label for="doc-${doc.id}">${doc.name} (${getDocumentTypeName(doc.type)})</label>
                `;
                container.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 문서 유형 이름 변환
function getDocumentTypeName(type) {
    const typeMap = {
        'ACCOUNTING': '회계',
        'CONTRACT': '계약',
        'RECEIPT': '증빙',
        'REPORT': '보고서',
        'OTHER': '기타'
    };
    return typeMap[type] || type;
}

// ================ 회계 엑셀 기능 ================
function initializeExcelSection() {
    loadExcelFiles();
}

// 기본 회계 엑셀 다운로드
function downloadAccountingExcel() {
    window.location.href = '/api/excel/accounting/download';
}

// 커스텀 회계 엑셀 다운로드
function downloadCustomExcel() {
    window.location.href = '/api/excel/custom/download';
}

// 엑셀 파일 업로드
function uploadExcelFile() {
    const name = document.getElementById('excel-name').value;
    const description = document.getElementById('excel-description').value;
    const fileInput = document.getElementById('excel-file');
    
    if (!name || !fileInput.files[0]) {
        showToast('파일 이름과 엑셀 파일을 선택해주세요.', true);
        return;
    }
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('file', fileInput.files[0]);
    
    showToast('엑셀 파일 업로드 중입니다. 잠시만 기다려주세요.');
    
    fetch('/api/excel/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('엑셀 파일이 성공적으로 업로드되었습니다.');
        document.getElementById('excel-name').value = '';
        document.getElementById('excel-description').value = '';
        fileInput.value = '';
        loadExcelFiles();
    })
    .catch(error => {
        showToast(error.message || '엑셀 파일 업로드에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 엑셀 파일 목록 로드
function loadExcelFiles() {
    if (!document.getElementById('excel-files-table')) return;
    
    fetch('/api/excel/files')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('excel-files-table');
            tableBody.innerHTML = '';
            
            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">업로드된 엑셀 파일이 없습니다.</td></tr>';
                return;
            }
            
            data.forEach(file => {
                const row = document.createElement('tr');
                const uploadDate = new Date(file.created_at).toLocaleString();
                
                row.innerHTML = `
                    <td>${file.id}</td>
                    <td>${file.name}</td>
                    <td>${file.description || '-'}</td>
                    <td>${uploadDate}</td>
                    <td><a href="/api/excel/files/${file.id}/download" class="download-link">다운로드</a></td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            showToast('엑셀 파일 목록을 불러오는 데 실패했습니다.', true);
            console.error('Error:', error);
        });
}

// ================ 법인카드 관리 기능 ================
function initializeCardSection() {
    loadAccounts();
    loadCardStatements();
}

// 카드사 명세서 업로드 및 분석
function uploadCardStatement() {
    const company = document.getElementById('card-company').value;
    const month = document.getElementById('statement-month').value;
    const fileInput = document.getElementById('card-statement-file');
    
    if (!company || !month || !fileInput.files[0]) {
        showToast('카드사, 명세서 월, 파일을 모두 선택해주세요.', true);
        return;
    }
    
    const formData = new FormData();
    formData.append('company', company);
    formData.append('month', month);
    formData.append('file', fileInput.files[0]);
    
    showToast('명세서 업로드 및 분석 중입니다. 잠시만 기다려주세요.');
    
    fetch('/api/card-statements/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('명세서가 성공적으로 업로드 및 분석되었습니다.');
        document.getElementById('card-statement-file').value = '';
        loadCardStatements();
        updateCardExpenseItems();
    })
    .catch(error => {
        showToast(error.message || '명세서 업로드에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 카드 명세서 조회
function filterCardStatements() {
    loadCardStatements();
}

// 카드 명세서 목록 로드
function loadCardStatements() {
    if (!document.getElementById('card-statements-table')) return;
    
    const month = document.getElementById('card-statement-filter-month').value;
    let url = '/api/card-statements';
    if (month) {
        url += `?month=${month}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('card-statements-table');
            tableBody.innerHTML = '';
            
            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center;">법인카드 사용 내역이 없습니다.</td></tr>';
                return;
            }
            
            data.forEach(statement => {
                const row = document.createElement('tr');
                const date = new Date(statement.transaction_date).toLocaleDateString();
                
                row.innerHTML = `
                    <td>${date}</td>
                    <td>${getCardCompanyName(statement.card_company)}</td>
                    <td>${maskCardNumber(statement.card_number)}</td>
                    <td>${statement.merchant_name}</td>
                    <td>${statement.amount.toLocaleString()}원</td>
                    <td>${statement.approval_number}</td>
                    <td>${getProcessStatusName(statement.process_status)}</td>
                `;
                tableBody.appendChild(row);
            });
            
            updateCardExpenseItems();
        })
        .catch(error => {
            showToast('법인카드 사용 내역을 불러오는 데 실패했습니다.', true);
            console.error('Error:', error);
        });
}

// 카드 지출 항목 업데이트
function updateCardExpenseItems() {
    if (!document.getElementById('card-expense-items')) return;
    
    const month = document.getElementById('card-statement-filter-month').value;
    let url = '/api/card-statements/unprocessed';
    if (month) {
        url += `?month=${month}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('card-expense-items');
            container.innerHTML = '';
            
            if (data.length === 0) {
                container.innerHTML = '<p>처리할 지출 항목이 없습니다.</p>';
                return;
            }
            
            data.forEach(item => {
                const div = document.createElement('div');
                div.className = 'checkbox-item';
                const date = new Date(item.transaction_date).toLocaleDateString();
                
                div.innerHTML = `
                    <input type="checkbox" id="expense-${item.id}" value="${item.id}">
                    <label for="expense-${item.id}">${date} - ${item.merchant_name} (${item.amount.toLocaleString()}원)</label>
                `;
                container.appendChild(div);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 카드 지출 회계 처리
function processCardExpenses() {
    const accountId = document.getElementById('card-expense-account').value;
    const checkboxes = document.querySelectorAll('#card-expense-items input[type="checkbox"]:checked');
    
    if (!accountId || checkboxes.length === 0) {
        showToast('지출 계정과 처리할 항목을 선택해주세요.', true);
        return;
    }
    
    const statementIds = Array.from(checkboxes).map(checkbox => checkbox.value);
    
    showToast('법인카드 지출 처리 중입니다. 잠시만 기다려주세요.');
    
    fetch('/api/card-statements/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            account_id: parseInt(accountId),
            statement_ids: statementIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showToast('법인카드 지출이 성공적으로 처리되었습니다.');
        loadCardStatements();
    })
    .catch(error => {
        showToast(error.message || '법인카드 지출 처리에 실패했습니다.', true);
        console.error('Error:', error);
    });
}

// 카드사 이름 변환
function getCardCompanyName(code) {
    const companyMap = {
        'shinhan': '신한카드',
        'kookmin': '국민카드',
        'hana': '하나카드',
        'ibk': '기업카드'
    };
    return companyMap[code] || code;
}

// 카드번호 마스킹
function maskCardNumber(cardNumber) {
    if (!cardNumber) return '';
    return cardNumber.replace(/(\d{4})(\d{4})(\d{4})(\d{4})/, '$1-$2-$3-$4').replace(/-\d{4}-\d{4}-/g, '-****-****-');
}

// 처리 상태 이름 변환
function getProcessStatusName(status) {
    const statusMap = {
        'PROCESSED': '처리완료',
        'UNPROCESSED': '미처리'
    };
    return statusMap[status] || status;
} 
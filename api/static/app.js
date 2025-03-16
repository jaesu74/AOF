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
    toast.className = 'toast';
    
    if (isError) {
        toast.classList.add('error');
    }
    
    toast.classList.add('visible');
    
    setTimeout(() => {
        toast.classList.remove('visible');
    }, 3000);
} 
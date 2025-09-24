// 공시 탭 통합 스크립트
document.addEventListener('DOMContentLoaded', function() {

    // 기존 스타일을 보완하는 공시 전용 스타일 추가
    function addDisclosureStyles() {
        const disclosureCSS = `
.disclosure-container {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 140px);
    gap: 16px;
}

.disclosure-filter-panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.filter-controls {
    display: flex;
    gap: 12px;
}

.filter-select {
    padding: 8px 12px;
    border: 1px solid var(--line);
    border-radius: 12px;
    font-size: 14px;
    background: var(--panel);
    cursor: pointer;
    color: var(--text);
}

.filter-select:focus {
    outline: none;
    border-color: var(--acc);
}

.disclosure-list {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.disclosure-item {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px;
    box-shadow: var(--shadow);
    cursor: pointer;
    transition: all 0.2s ease;
}

.disclosure-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,.12);
}

.disclosure-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    font-size: 14px;
    color: var(--muted);
}

.company-tag {
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    color: white;
}

.company-tag.samsung {
    background: var(--acc);
}

.company-tag.sk {
    background: var(--red);
}

.company-tag.kakao {
    background: var(--orange);
}

.company-tag.default {
    background: var(--muted);
}

.disclosure-type-chip {
    border: 1px solid var(--line);
    background: #faf7f0;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 13px;
    color: var(--text);
}

.disclosure-type-chip.earnings {
    background: #e3f2fd;
    border-color: #90caf9;
    color: #1565c0;
}

.disclosure-type-chip.major {
    background: #fff3e0;
    border-color: #ffcc02;
    color: #ef6c00;
}

.disclosure-type-chip.correction {
    background: #ffebee;
    border-color: #ef9a9a;
    color: #c62828;
}

.disclosure-time {
    font-size: 12px;
    color: var(--muted);
    margin-left: auto;
}

.disclosure-title-text {
    font-size: 16px;
    font-weight: 500;
    color: var(--text);
    line-height: 1.4;
    margin: 10px 0;
}

.disclosure-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.disclosure-status {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 11px;
}

.status-badge.verified {
    background: #e8f5e8;
    border: 1px solid #a5d6a7;
    color: #2e7d32;
}

.status-badge.processing {
    background: #fff3e0;
    border: 1px solid #ffcc02;
    color: #ef6c00;
}

.status-badge.pending {
    background: #e3f2fd;
    border: 1px solid #90caf9;
    color: #1565c0;
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
}

.impact-score {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
}

.more-cta {
    width: 100%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--panel);
    border: 1px solid var(--line);
    color: var(--text);
    padding: 12px 14px;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.more-cta:hover {
    background: #f7efe0;
    border-color: var(--acc);
}

.loading-item {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: var(--muted);
    font-size: 14px;
}

.loading-dots {
    display: flex;
    gap: 4px;
}

.loading-dots span {
    width: 4px;
    height: 4px;
    background: var(--muted);
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
    0%, 80%, 100% {
        transform: scale(0);
    }
    40% {
        transform: scale(1);
    }
}
        `;

        const styleElement = document.createElement('style');
        styleElement.textContent = disclosureCSS;
        document.head.appendChild(styleElement);
    }

    // HTML 컴포넌트 생성 (기존 클래스 활용)
    function createDisclosureHTML() {
        return `
<div class="disclosure-container">
    <div class="panel disclosure-filter-panel">
        <div class="panel-head">
            <h2 class="panel-title">📋 최신 공시</h2>
        </div>
        <div class="filter-controls">
            <select class="filter-select" id="companyFilter">
                <option value="">전체 기업</option>
                <option value="삼성전자">삼성전자</option>
                <option value="SK하이닉스">SK하이닉스</option>
                <option value="카카오">카카오</option>
                <option value="NAVER">NAVER</option>
                <option value="LG전자">LG전자</option>
            </select>
            <select class="filter-select" id="typeFilter">
                <option value="">전체 유형</option>
                <option value="실적발표">실적발표</option>
                <option value="주요사항보고">주요사항보고</option>
                <option value="공시정정">공시정정</option>
            </select>
        </div>
    </div>

    <div class="list disclosure-list" id="disclosureList">
        <!-- 공시 항목들이 여기에 동적으로 추가됩니다 -->
    </div>

    <button class="more-cta" id="loadMoreDisclosures">더 많은 공시 보기</button>
</div>
        `;
    }

    // 공시 뷰가 활성화될 때 컴포넌트 로드
    function loadDisclosureComponent() {
        const disclosureView = document.getElementById('view-disclosure');

        if (!disclosureView) {
            console.error('공시 뷰를 찾을 수 없습니다.');
            return;
        }

        // CSS 스타일 추가
        addDisclosureStyles();

        // HTML 컴포넌트 삽입
        const componentHTML = createDisclosureHTML();
        disclosureView.innerHTML = `<div class="section">${componentHTML}</div>`;

        // 공시 기능 초기화
        initDisclosureList();
    }

    // 공시 리스트 클래스 및 기능 구현
    function initDisclosureList() {
        class DisclosureList {
            constructor() {
                this.disclosureList = document.getElementById('disclosureList');
                this.companyFilter = document.getElementById('companyFilter');
                this.typeFilter = document.getElementById('typeFilter');
                this.loadMoreBtn = document.getElementById('loadMoreDisclosures');
                this.currentPage = 1;
                this.isLoading = false;

                if (!this.disclosureList) {
                    console.error('공시 리스트 요소들을 찾을 수 없습니다.');
                    return;
                }

                this.bindEvents();
                this.loadInitialData();
            }

            bindEvents() {
                // 필터 변경 이벤트
                this.companyFilter?.addEventListener('change', () => {
                    this.resetAndReload();
                });

                this.typeFilter?.addEventListener('change', () => {
                    this.resetAndReload();
                });

                // 더보기 버튼 클릭
                this.loadMoreBtn?.addEventListener('click', () => {
                    this.loadMoreDisclosures();
                });

                // 공시 항목 클릭 이벤트 (이벤트 위임)
                this.disclosureList?.addEventListener('click', (e) => {
                    const disclosureItem = e.target.closest('.disclosure-item');
                    if (disclosureItem) {
                        this.showDisclosureDetail(disclosureItem.dataset.id);
                    }
                });
            }

            async loadInitialData() {
                this.setLoading(true);
                try {
                    const disclosures = await this.fetchDisclosures(1);
                    this.renderDisclosures(disclosures, true);
                } catch (error) {
                    console.error('초기 공시 데이터 로드 실패:', error);
                    this.showError('공시 데이터를 불러올 수 없습니다.');
                } finally {
                    this.setLoading(false);
                }
            }

            async loadMoreDisclosures() {
                if (this.isLoading) return;

                this.setLoading(true);
                try {
                    this.currentPage++;
                    const disclosures = await this.fetchDisclosures(this.currentPage);
                    this.renderDisclosures(disclosures, false);
                } catch (error) {
                    console.error('추가 공시 데이터 로드 실패:', error);
                    this.currentPage--; // 페이지 롤백
                } finally {
                    this.setLoading(false);
                }
            }

            resetAndReload() {
                this.currentPage = 1;
                this.disclosureList.innerHTML = '';
                this.loadInitialData();
            }

            async fetchDisclosures(page = 1) {
                // 임시 목업 데이터 (실제로는 API 호출)
                await new Promise(resolve => setTimeout(resolve, 500)); // 로딩 시뮬레이션

                const mockDisclosures = [
                    {
                        id: '1',
                        company: '삼성전자',
                        type: '실적발표',
                        title: '2024년 3분기 연결재무제표 잠정실적(공정공시)',
                        time: '2시간 전',
                        status: 'verified',
                        statusText: '검증완료',
                        impact: 85
                    },
                    {
                        id: '2',
                        company: 'SK하이닉스',
                        type: '주요사항보고',
                        title: '반도체 신규 투자계획 발표',
                        time: '4시간 전',
                        status: 'processing',
                        statusText: '본격중',
                        impact: 65
                    },
                    {
                        id: '3',
                        company: '카카오',
                        type: '공시정정',
                        title: '주요사항보고서 정정신고서',
                        time: '6시간 전',
                        status: 'verified',
                        statusText: '검증완료',
                        impact: 75
                    },
                    {
                        id: '4',
                        company: 'NAVER',
                        type: '실적발표',
                        title: '2024년 3분기 실적 발표 안내',
                        time: '8시간 전',
                        status: 'pending',
                        statusText: '대기중',
                        impact: 70
                    },
                    {
                        id: '5',
                        company: 'LG전자',
                        type: '주요사항보고',
                        title: '해외 자회사 설립 관련 공시',
                        time: '10시간 전',
                        status: 'verified',
                        statusText: '검증완료',
                        impact: 60
                    }
                ];

                // 필터링
                let filteredDisclosures = mockDisclosures;
                const companyFilter = this.companyFilter?.value;
                const typeFilter = this.typeFilter?.value;

                if (companyFilter) {
                    filteredDisclosures = filteredDisclosures.filter(d => d.company === companyFilter);
                }

                if (typeFilter) {
                    filteredDisclosures = filteredDisclosures.filter(d => d.type === typeFilter);
                }

                return filteredDisclosures;
            }

            renderDisclosures(disclosures, replace = false) {
                if (replace) {
                    this.disclosureList.innerHTML = '';
                }

                disclosures.forEach(disclosure => {
                    const item = this.createDisclosureItem(disclosure);
                    this.disclosureList.appendChild(item);
                });
            }

            createDisclosureItem(disclosure) {
                const item = document.createElement('article');
                item.className = 'rumor-card disclosure-item'; // 기존 rumor-card 클래스 재활용
                item.dataset.id = disclosure.id;

                const companyClass = this.getCompanyClass(disclosure.company);
                const typeClass = this.getTypeClass(disclosure.type);
                const statusClass = this.getStatusClass(disclosure.status);

                item.innerHTML = `
                    <div class="meta disclosure-meta">
                        <span class="company-tag ${companyClass}">${disclosure.company}</span>
                        <span class="chip disclosure-type-chip ${typeClass}">${disclosure.type}</span>
                        <span class="time disclosure-time">${disclosure.time}</span>
                    </div>
                    <h3 class="title disclosure-title-text">${disclosure.title}</h3>
                    <div class="status disclosure-footer">
                        <div class="disclosure-status">
                            <span class="badge status-badge ${statusClass}">
                                <span class="dot status-dot"></span>
                                ${disclosure.statusText}
                            </span>
                            <span class="score impact-score">${disclosure.impact}</span>
                        </div>
                        <a class="more ghost small" href="#">상세보기</a>
                    </div>
                `;

                return item;
            }

            getCompanyClass(company) {
                const companyClasses = {
                    '삼성전자': 'samsung',
                    'SK하이닉스': 'sk',
                    '카카오': 'kakao'
                };
                return companyClasses[company] || 'default';
            }

            getTypeClass(type) {
                const typeClasses = {
                    '실적발표': 'earnings',
                    '주요사항보고': 'major',
                    '공시정정': 'correction'
                };
                return typeClasses[type] || '';
            }

            getStatusClass(status) {
                const statusClasses = {
                    'verified': 'verified',
                    'processing': 'processing',
                    'pending': 'pending'
                };
                return statusClasses[status] || 'pending';
            }

            showDisclosureDetail(disclosureId) {
                console.log('공시 상세보기:', disclosureId);
                // 실제로는 상세 모달이나 새 페이지로 이동
                alert(`공시 상세보기 (ID: ${disclosureId})\n\n이 기능은 추후 구현될 예정입니다.`);
            }

            setLoading(loading) {
                this.isLoading = loading;

                if (this.loadMoreBtn) {
                    this.loadMoreBtn.disabled = loading;
                    this.loadMoreBtn.textContent = loading ? '로딩 중...' : '더 많은 공시 보기';
                }

                if (loading && this.currentPage === 1) {
                    // 초기 로딩 표시
                    this.disclosureList.innerHTML = `
                        <div class="loading-item">
                            <span>공시 데이터를 불러오는 중</span>
                            <div class="loading-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    `;
                }
            }

            showError(message) {
                this.disclosureList.innerHTML = `
                    <div class="disclosure-item" style="text-align: center; color: #dc2626;">
                        <div class="disclosure-title-text">⚠️ ${message}</div>
                    </div>
                `;
            }
        }

        window.disclosureList = new DisclosureList();
    }

    // 뷰 전환 감지 (MutationObserver 사용)
    function handleViewChange() {
        const disclosureView = document.getElementById('view-disclosure');

        if (!disclosureView) {
            console.error('공시 뷰를 찾을 수 없습니다.');
            return;
        }

        // MutationObserver를 사용해 공시 뷰가 활성화될 때마다 감지
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    if (disclosureView.classList.contains('active') && !disclosureView.querySelector('.disclosure-container')) {
                        console.log('공시 뷰 활성화 감지 - 공시 컴포넌트 로딩');
                        loadDisclosureComponent();
                    }
                }
            });
        });

        // 공시 뷰의 class 변경을 관찰
        observer.observe(disclosureView, { attributes: true, attributeFilter: ['class'] });

        // 페이지 로드 시 공시 뷰가 이미 활성화되어 있다면 로드
        if (disclosureView.classList.contains('active') && !disclosureView.querySelector('.disclosure-container')) {
            loadDisclosureComponent();
        }

        // hashchange 이벤트도 감지 (라우터 동작 보완)
        window.addEventListener('hashchange', function() {
            setTimeout(() => {
                if (location.hash === '#disclosure' && disclosureView.classList.contains('active') && !disclosureView.querySelector('.disclosure-container')) {
                    console.log('Hash 변경으로 공시 뷰 활성화 감지');
                    loadDisclosureComponent();
                }
            }, 50);
        });
    }

    handleViewChange();
});
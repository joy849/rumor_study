// 루머 체크 탭 스크립트
document.addEventListener('DOMContentLoaded', function() {

    // HTML 로드 함수
    async function loadHTML(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.text();
    }

    // 루머 뷰가 활성화될 때 컴포넌트 로드
    async function loadRumorComponent() {
        const rumorView = document.getElementById('view-rumor');

        if (!rumorView) {
            console.error('루머 뷰를 찾을 수 없습니다.');
            return;
        }

        try {
            console.log('루머 컴포넌트 로딩 시작...');

            // HTML 파일 로드
            const htmlContent = await loadHTML('features/rumor/rumor.html');
            rumorView.innerHTML = htmlContent;

            console.log('rumor.html 로드 완료');

            // 이벤트 리스너 초기화
            initRumorEvents();

        } catch (error) {
            console.error('루머 컴포넌트 로드 실패:', error);
            rumorView.innerHTML = '<div class="placeholder"><p>루머 체크 로드 중 오류가 발생했습니다.</p></div>';
        }
    }

    // 루머 관련 이벤트 초기화
    function initRumorEvents() {
        // 루머 검증 버튼
        const runCheckBtn = document.getElementById('runCheck');
        if (runCheckBtn) {
            runCheckBtn.addEventListener('click', function() {
                const input = document.getElementById('rumorInput');
                if (input && input.value.trim()) {
                    console.log('루머 검증:', input.value);
                    // TODO: API 호출
                }
            });
        }

        // 더 보기 버튼
        const loadMoreBtn = document.getElementById('loadMore');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', function() {
                console.log('더 많은 루머 로드');
                // TODO: 페이징 API 호출
            });
        }
    }

    // 탭 전환 감지
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const rumorView = document.getElementById('view-rumor');
                if (rumorView && rumorView.classList.contains('active')) {
                    if (!rumorView.dataset.loaded) {
                        loadRumorComponent();
                        rumorView.dataset.loaded = 'true';
                    }
                }
            }
        });
    });

    const rumorView = document.getElementById('view-rumor');
    if (rumorView) {
        observer.observe(rumorView, { attributes: true });

        // 초기 로드 (기본 활성 탭인 경우)
        if (rumorView.classList.contains('active')) {
            loadRumorComponent();
            rumorView.dataset.loaded = 'true';
        }
    }
});

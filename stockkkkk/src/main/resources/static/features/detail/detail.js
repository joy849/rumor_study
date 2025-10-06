// 루머 상세 페이지 스크립트
document.addEventListener('DOMContentLoaded', function() {

    async function loadHTML(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.text();
    }

    async function loadDetailComponent() {
        const detailView = document.getElementById('view-detail');

        if (!detailView) {
            console.error('상세 뷰를 찾을 수 없습니다.');
            return;
        }

        try {
            console.log('상세 컴포넌트 로딩 시작...');

            const htmlContent = await loadHTML('features/detail/detail.html');
            detailView.innerHTML = htmlContent;

            console.log('detail.html 로드 완료');

            initDetailEvents();

        } catch (error) {
            console.error('상세 컴포넌트 로드 실패:', error);
            detailView.innerHTML = '<div class="placeholder"><p>상세 정보 로드 중 오류가 발생했습니다.</p></div>';
        }
    }

    function initDetailEvents() {
        // 뒤로 가기 버튼
        const backBtn = document.querySelector('[data-nav="#rumor"]');
        if (backBtn) {
            backBtn.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.hash = '#rumor';
            });
        }

        // 공유 버튼
        const shareBtn = document.querySelector('.action-btn.share');
        if (shareBtn) {
            shareBtn.addEventListener('click', function() {
                console.log('공유하기 클릭');
                // TODO: 공유 기능 구현
            });
        }

        // 신고 버튼
        const reportBtn = document.querySelector('.action-btn.report');
        if (reportBtn) {
            reportBtn.addEventListener('click', function() {
                console.log('신고하기 클릭');
                // TODO: 신고 기능 구현
            });
        }
    }

    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const detailView = document.getElementById('view-detail');
                if (detailView && detailView.classList.contains('active')) {
                    if (!detailView.dataset.loaded) {
                        loadDetailComponent();
                        detailView.dataset.loaded = 'true';
                    }
                }
            }
        });
    });

    const detailView = document.getElementById('view-detail');
    if (detailView) {
        observer.observe(detailView, { attributes: true });

        // 초기 로드
        if (detailView.classList.contains('active')) {
            loadDetailComponent();
            detailView.dataset.loaded = 'true';
        }
    }
});

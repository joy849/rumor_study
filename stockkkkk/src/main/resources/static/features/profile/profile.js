// 프로필 탭 스크립트
document.addEventListener('DOMContentLoaded', function() {

    async function loadHTML(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.text();
    }

    async function loadProfileComponent() {
        const profileView = document.getElementById('view-profile');

        if (!profileView) {
            console.error('프로필 뷰를 찾을 수 없습니다.');
            return;
        }

        try {
            console.log('프로필 컴포넌트 로딩 시작...');

            const htmlContent = await loadHTML('features/profile/profile.html');
            profileView.innerHTML = htmlContent;

            console.log('profile.html 로드 완료');

        } catch (error) {
            console.error('프로필 컴포넌트 로드 실패:', error);
            profileView.innerHTML = '<div class="placeholder"><p>프로필 로드 중 오류가 발생했습니다.</p></div>';
        }
    }

    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const profileView = document.getElementById('view-profile');
                if (profileView && profileView.classList.contains('active')) {
                    if (!profileView.innerHTML.trim() || !profileView.dataset.loaded) {
                        loadProfileComponent();
                        profileView.dataset.loaded = 'true';
                    }
                }
            }
        });
    });

    const profileView = document.getElementById('view-profile');
    if (profileView) {
        observer.observe(profileView, { attributes: true });

        // 초기 로드 (기본 활성 탭인 경우)
        if (profileView.classList.contains('active')) {
            loadProfileComponent();
            profileView.dataset.loaded = 'true';
        }
    }
});

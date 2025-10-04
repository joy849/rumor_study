// 홈화면 대화창 통합 스크립트 - Components 폴더 파일들을 활용
document.addEventListener('DOMContentLoaded', function() {

    // JavaScript 파일 로드 함수
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
            document.head.appendChild(script);
        });
    }

    // HTML 파일 로드 함수
    async function loadHTML(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.text();
    }

    // 홈 뷰가 활성화될 때 대화창 컴포넌트 로드
    async function loadHomeChatComponent() {
        const homeView = document.getElementById('view-home');

        if (!homeView) {
            console.error('홈 뷰를 찾을 수 없습니다.');
            return;
        }

        try {
            console.log('홈 채팅 컴포넌트 로딩 시작...');

            // 1. HTML 파일 로드
            const htmlContent = await loadHTML('features/home/components/home-chat.html');
            console.log('home-chat.html 로드 완료');

            // 2. HTML을 홈 뷰에 삽입
            homeView.innerHTML = `
                <div class="section">
                    ${htmlContent}
                </div>
            `;

            // 3. JavaScript 파일 로드 및 채팅 기능 초기화
            await loadScript('features/home/components/home-chat.js');
            console.log('home-chat.js 로드 완료');

            // 4. HomeChat 클래스 초기화 (home-chat.js에서 정의됨)
            if (window.HomeChat) {
                window.homeChat = new window.HomeChat();
                console.log('HomeChat 인스턴스 생성 완료');
            } else {
                console.error('HomeChat 클래스를 찾을 수 없습니다.');
            }

        } catch (error) {
            console.error('홈 채팅 컴포넌트 로드 실패:', error);

            // 폴백: 간단한 에러 메시지 표시
            homeView.innerHTML = `
                <div class="section">
                    <div style="
                        padding: 40px;
                        text-align: center;
                        background: #f8f9fa;
                        border-radius: 8px;
                        border: 1px solid #e9ecef;
                    ">
                        <h3 style="color: #6c757d; margin-bottom: 16px;">채팅 컴포넌트 로드 중 오류가 발생했습니다</h3>
                        <p style="color: #868e96; font-size: 14px;">페이지를 새로고침해주세요.</p>
                        <button onclick="location.reload()" style="
                            margin-top: 16px;
                            padding: 8px 16px;
                            background: #007bff;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                        ">새로고침</button>
                    </div>
                </div>
            `;
        }
    }

    // 네비게이션 이벤트 감지
    function handleViewChange() {
        const homeView = document.getElementById('view-home');

        if (!homeView) {
            console.error('홈 뷰를 찾을 수 없습니다.');
            return;
        }

        // MutationObserver를 사용해 홈 뷰가 활성화될 때마다 감지
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    if (homeView.classList.contains('active') && !homeView.querySelector('.chat-container')) {
                        console.log('홈 뷰 활성화 감지 - 채팅 컴포넌트 로딩');
                        loadHomeChatComponent();
                    }
                }
            });
        });

        // 홈 뷰의 class 변경을 관찰
        observer.observe(homeView, { attributes: true, attributeFilter: ['class'] });

        // 페이지 로드 시 홈이 이미 활성화되어 있다면 로드
        if (homeView.classList.contains('active') && !homeView.querySelector('.chat-container')) {
            loadHomeChatComponent();
        }

        // hashchange 이벤트도 감지 (라우터 동작 보완)
        window.addEventListener('hashchange', function() {
            setTimeout(() => {
                if (location.hash === '#home' && homeView.classList.contains('active') && !homeView.querySelector('.chat-container')) {
                    console.log('Hash 변경으로 홈 뷰 활성화 감지');
                    loadHomeChatComponent();
                }
            }, 50);
        });
    }

    handleViewChange();
});
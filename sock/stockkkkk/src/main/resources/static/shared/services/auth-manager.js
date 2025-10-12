// ===== 인증 관리 시스템 =====
window.AuthManager = {
    // 토큰 저장 (로그인 상태 유지 옵션 반영)
    setTokens(accessToken, refreshToken, keepLogin = false) {
        const storage = keepLogin ? localStorage : sessionStorage;
        storage.setItem('accessToken', accessToken);
        if (refreshToken) {
            storage.setItem('refreshToken', refreshToken);
        }
    },

    // 사용자 정보 저장
    setUserInfo(userInfo, keepLogin = false) {
        const storage = keepLogin ? localStorage : sessionStorage;
        storage.setItem('user', JSON.stringify({
            ...userInfo,
            loginTime: new Date().toISOString()
        }));
    },

    // 토큰 조회
    getToken() {
        return localStorage.getItem('accessToken') || sessionStorage.getItem('accessToken');
    },

    // 사용자 정보 조회
    getUserInfo() {
        const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    },

    // 모든 토큰 및 사용자 정보 삭제
    removeTokens() {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        sessionStorage.removeItem('accessToken');
        sessionStorage.removeItem('refreshToken');
        sessionStorage.removeItem('user');
    },

    // 로그인 상태 확인
    isAuthenticated() {
        return !!this.getToken();
    },

    // 로그아웃
    logout() {
        this.removeTokens();
        this.updateUI();
    },

    // UI 업데이트
    updateUI() {
        const isAuth = this.isAuthenticated();
        const loginBtn = document.getElementById('loginBtn');

        if (loginBtn) {
            // 기존 이벤트 리스너 제거를 위해 복제
            const newLoginBtn = loginBtn.cloneNode(true);
            loginBtn.parentNode.replaceChild(newLoginBtn, loginBtn);

            if (isAuth) {
                const user = this.getUserInfo();
                newLoginBtn.textContent = user?.name || user?.email || '내정보';
                newLoginBtn.addEventListener('click', () => {
                    if (confirm('로그아웃 하시겠습니까?')) {
                        this.logout();
                        alert('로그아웃되었습니다.');
                    }
                });
            } else {
                newLoginBtn.textContent = '로그인';
                newLoginBtn.addEventListener('click', () => {
                    if (window.LoginModal) {
                        window.LoginModal.open();
                    }
                });
            }
        }
    },

    // 페이지 로드 시 로그인 상태 확인
    checkLoginStatus() {
        const token = this.getToken();
        if (token) {
            this.updateUI();
        }
    }
};

// ===== API 클라이언트 =====
window.ApiClient = {
    getToken() {
        return localStorage.getItem('accessToken') || sessionStorage.getItem('accessToken');
    },

    getRefreshToken() {
        return localStorage.getItem('refreshToken') || sessionStorage.getItem('refreshToken');
    },

    async fetchWithAuth(url, options = {}) {
        const token = this.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, { ...options, headers });

            // 토큰 만료 시 자동 갱신 시도
            if (response.status === 401 && token) {
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.getToken()}`;
                    return fetch(url, { ...options, headers });
                } else {
                    if (window.AuthManager) {
                        AuthManager.logout();
                    }
                    throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
                }
            }

            return response;
        } catch (error) {
            console.error('API 요청 오류:', error);
            throw error;
        }
    },

    async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) return false;

        try {
            const response = await fetch('/api/ausers/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                const storage = localStorage.getItem('accessToken') ? localStorage : sessionStorage;
                storage.setItem('accessToken', data.accessToken);
                return true;
            }
        } catch (error) {
            console.error('토큰 갱신 실패:', error);
        }

        return false;
    }
};

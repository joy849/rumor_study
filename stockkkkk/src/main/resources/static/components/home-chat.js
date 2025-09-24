class HomeChat {
    constructor() {
        this.chatMessages = null;
        this.chatInput = null;
        this.sendButton = null;
        this.isLoading = false;
        this.init();
    }

    init() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');

        if (!this.chatMessages || !this.chatInput || !this.sendButton) {
            console.error('채팅 컴포넌트 요소들을 찾을 수 없습니다.');
            return;
        }

        this.bindEvents();
    }

    bindEvents() {
        // 전송 버튼 클릭
        this.sendButton.addEventListener('click', () => {
            this.handleSendMessage();
        });

        // Enter 키 입력
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
    }

    async handleSendMessage() {
        const message = this.chatInput.value.trim();

        if (!message || this.isLoading) {
            return;
        }

        // 사용자 메시지 추가
        this.addMessage(message, 'user');
        this.chatInput.value = '';

        // 로딩 상태 설정
        this.setLoading(true);

        try {
            // API 요청
            const response = await this.sendToAPI(message);

            // AI 응답 추가
            this.addMessage(response, 'bot');
        } catch (error) {
            console.error('API 요청 실패:', error);
            this.addMessage('죄송합니다. 서버와의 연결에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.', 'bot', true);
        } finally {
            this.setLoading(false);
        }
    }

    async sendToAPI(query) {
        const API_URL = "http://211.188.53.220:6001/summarize";

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // API 응답에서 실제 메시지 추출 (응답 형식에 따라 조정 필요)
        return data.answer || data.response || data.result || '응답을 받을 수 없습니다.';
    }

    addMessage(text, type, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}${isError ? ' error-message' : ''}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.textContent = text;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.getCurrentTime();

        messageDiv.appendChild(bubbleDiv);
        messageDiv.appendChild(timeDiv);

        this.chatMessages.appendChild(messageDiv);

        // 스크롤을 맨 아래로
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.sendButton.disabled = loading;
        this.chatInput.disabled = loading;

        if (loading) {
            // 로딩 메시지 추가
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message bot loading-message';
            loadingDiv.id = 'loading-message';

            loadingDiv.innerHTML = `
                <div class="message-bubble">
                    <div class="loading-message">
                        <span>답변을 생성하고 있습니다</span>
                        <div class="loading-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            `;

            this.chatMessages.appendChild(loadingDiv);
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        } else {
            // 로딩 메시지 제거
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) {
                loadingMessage.remove();
            }
        }
    }

    getCurrentTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }
}

// 홈화면이 로드될 때 채팅 컴포넌트 초기화
window.homeChat = null;

function initHomeChat() {
    if (window.homeChat) {
        return;
    }

    // 홈 화면 컴포넌트가 로드된 후 초기화
    setTimeout(() => {
        window.homeChat = new HomeChat();
    }, 100);
}

// 전역으로 노출하여 필요시 호출할 수 있도록 함
window.initHomeChat = initHomeChat;
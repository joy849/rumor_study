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
            this.addMessage(response.result, 'bot', false, response.isDisclosure, message);
        } catch (error) {
            console.error('API 요청 실패:', error);
            this.addMessage('죄송합니다. 서버와의 연결에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.', 'bot', true);
        } finally {
            this.setLoading(false);
        }
    }

    async sendToAPI(query) {
        const API_URL = "http://211.188.53.220:10000/auto-search";

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

        // 공시 여부 확인
        const isDisclosure = data.question_type === '공시';

        // API 응답에서 실제 메시지 추출
        let result;
        if (data.result) {
            if (data.result.summary) {
                result = data.result.summary;
            } else if (data.result.answer) {
                result = data.result.answer;
            } else if (data.result.verification_result) {
                result = data.result.verification_result;
            } else {
                result = JSON.stringify(data.result);
            }
        } else {
            result = data.answer || data.response || '응답을 받을 수 없습니다.';
        }

        return {
            result: result,
            isDisclosure: isDisclosure,
            originalQuery: query,
            originalData: data.result
        };
    }


    async performModeAnalysis(query, summary, mode) {
        const ANALYSIS_API_URL = "http://211.188.53.220:10000/analyze_mode";

        try {
            const response = await fetch(ANALYSIS_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    mode: mode, // Use provided mode
                    summary: summary
                })
            });

            if (!response.ok) {
                console.warn('Mode analysis request failed:', response.status);
                return null;
            }

            const data = await response.json();
            return data.analysis;
        } catch (error) {
            console.warn('Mode analysis failed:', error);
            return null;
        }
    }

    combineResults(originalResult, additionalAnalysis) {
        const original = originalResult.summary || originalResult.answer;

        if (!additionalAnalysis) {
            return original;
        }

        return `${original}\n\n📊 **추가 분석:**\n${additionalAnalysis}`;
    }

    addMessage(text, type, isError = false, isDisclosure = false, originalQuery = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}${isError ? ' error-message' : ''}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';

        // bot 메시지는 마크다운으로 렌더링, user 메시지는 텍스트 그대로
        if (type === 'bot' && typeof marked !== 'undefined') {
            bubbleDiv.innerHTML = marked.parse(text);
        } else {
            bubbleDiv.textContent = text;
        }

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.getCurrentTime();

        messageDiv.appendChild(bubbleDiv);
        messageDiv.appendChild(timeDiv);

        // 공시 메시지인 경우 분석 버튼 추가
        if (isDisclosure && type === 'bot' && !isError) {
            const analysisButtons = document.createElement('div');
            analysisButtons.className = 'analysis-buttons';

            const beginnerBtn = document.createElement('button');
            beginnerBtn.className = 'analysis-btn beginner';
            beginnerBtn.innerHTML = '🔰 초보자 모드로 분석';
            beginnerBtn.onclick = () => this.handleAnalysisClick('beginner', originalQuery, text, messageDiv);

            const analystBtn = document.createElement('button');
            analystBtn.className = 'analysis-btn analyst';
            analystBtn.innerHTML = '📊 애널리스트 모드로 분석';
            analystBtn.onclick = () => this.handleAnalysisClick('analyst', originalQuery, text, messageDiv);

            analysisButtons.appendChild(beginnerBtn);
            analysisButtons.appendChild(analystBtn);
            messageDiv.appendChild(analysisButtons);
        }

        this.chatMessages.appendChild(messageDiv);

        // 스크롤을 맨 아래로
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async handleAnalysisClick(mode, query, summary, messageDiv) {
        // 기존 분석 결과가 있으면 제거
        const existingAnalysis = messageDiv.querySelector('.additional-analysis');
        if (existingAnalysis) {
            existingAnalysis.remove();
        }

        // 버튼 비활성화
        const buttons = messageDiv.querySelectorAll('.analysis-btn');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.textContent = '분석 중...';
        });

        try {
            const analysis = await this.performModeAnalysis(query, summary, mode);

            if (analysis) {
                // 분석 결과 추가
                const analysisDiv = document.createElement('div');
                analysisDiv.className = 'additional-analysis';

                // 분석 결과를 마크다운으로 렌더링
                const renderedAnalysis = typeof marked !== 'undefined'
                    ? marked.parse(analysis)
                    : analysis;

                analysisDiv.innerHTML = `
                    <div class="analysis-header">
                        ${mode === 'beginner' ? '🔰' : '📊'} ${mode === 'beginner' ? '초보자' : '애널리스트'} 모드 분석
                    </div>
                    <div class="analysis-content">${renderedAnalysis}</div>
                `;

                messageDiv.appendChild(analysisDiv);
            } else {
                alert('분석 요청에 실패했습니다.');
            }
        } catch (error) {
            console.error('Analysis failed:', error);
            alert('분석 중 오류가 발생했습니다.');
        } finally {
            // 버튼 다시 활성화
            buttons.forEach((btn, index) => {
                btn.disabled = false;
                btn.innerHTML = index === 0 ? '🔰 초보자 모드로 분석' : '📊 애널리스트 모드로 분석';
            });
        }

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

// HomeChat 클래스를 전역으로 노출
window.HomeChat = HomeChat;
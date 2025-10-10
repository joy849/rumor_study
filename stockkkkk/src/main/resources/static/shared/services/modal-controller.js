// ===== 모달 컨트롤러 =====
function modalController(dialog){
    if (!dialog) {
        console.error('Modal element not found');
        return { open: () => {}, close: () => {} };
    }

    const card = dialog.querySelector('.modal-card');
    const trap = window.createFocusTrap ? createFocusTrap(dialog) : null;

    function open(){
        dialog.showModal();
        if (trap) trap.activate();
    }

    function close(){
        dialog.close();
        if (trap) trap.deactivate();
    }

    dialog.addEventListener('cancel', (e)=>{ e.preventDefault(); close(); });

    // 배경 클릭으로 닫기
    if (card) {
        dialog.addEventListener('click', (e)=>{
            const rect = card.getBoundingClientRect();
            const inside = e.clientX>=rect.left && e.clientX<=rect.right && e.clientY>=rect.top && e.clientY<=rect.bottom;
            if(!inside) close();
        });
    }

    // 닫기 버튼 처리
    const closeBtn = dialog.querySelector('.modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', close);
    }

    return { open, close };
}

// 모달 초기화 함수 (모달 로드 완료 후 호출)
window.initializeModals = function() {
    const $ = (s) => document.querySelector(s);

    // 전역 변수로 설정
    window.SubmitModal = modalController($('#submitModal'));
    window.LoginModal  = modalController($('#loginModal'));
    window.DetailModal = modalController($('#detailModal'));

    console.log('✅ 모달 컨트롤러 초기화 완료');

    // 로그인/회원가입 탭 전환 로직 초기화
    initLoginModalTabs();

    // AuthManager UI 업데이트
    if (window.AuthManager) {
        AuthManager.updateUI();
        AuthManager.checkLoginStatus();
    } else {
        // AuthManager가 없으면 기본 로그인 버튼 이벤트
        const loginBtn = $('#loginBtn');
        if (loginBtn) {
            loginBtn.onclick = () => {
                if (window.LoginModal) {
                    window.LoginModal.open();
                }
            };
        }
    }
};

// 로그인 모달 탭 전환 로직
function initLoginModalTabs() {
    const tabLogin = document.getElementById('tabLogin');
    const tabJoin = document.getElementById('tabJoin');
    const loginFields = document.getElementById('loginFields');
    const signupBox = document.getElementById('signupBox');
    const suAgree = document.getElementById('suAgree');
    const primaryBtn = document.getElementById('primaryAction');

    if (!tabLogin || !tabJoin || !primaryBtn) {
        console.error('로그인 모달 요소를 찾을 수 없습니다.');
        return;
    }

    let mode = 'login';

    function setMode(next) {
        mode = next;
        const isLogin = mode === 'login';

        if (loginFields) loginFields.hidden = !isLogin;
        if (signupBox) signupBox.hidden = isLogin;

        primaryBtn.textContent = isLogin ? '로그인' : '회원가입';
        primaryBtn.disabled = (!isLogin && !(suAgree && suAgree.checked));

        tabLogin.classList.toggle('active', isLogin);
        tabJoin.classList.toggle('active', !isLogin);
    }

    tabLogin.addEventListener('click', () => setMode('login'));
    tabJoin.addEventListener('click', () => setMode('signup'));

    if (suAgree) {
        suAgree.addEventListener('change', () => {
            if (mode === 'signup') {
                primaryBtn.disabled = !suAgree.checked;
            }
        });
    }

    setMode('login');

    // primaryAction 버튼 클릭 이벤트
    primaryBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        if (mode === 'login') {
            await handleLogin();
        } else {
            await handleSignup();
        }
    });

    // 로그인 처리
    async function handleLogin() {
        const email = document.getElementById('loginEmail')?.value.trim();
        const password = document.getElementById('loginPw')?.value.trim();
        const keepLogin = document.getElementById('keepLogin')?.checked;

        if (!email || !password) {
            alert('이메일과 비밀번호를 입력해주세요.');
            return;
        }

        primaryBtn.disabled = true;
        primaryBtn.textContent = '로그인 중...';

        try {
            const response = await fetch('/api/ausers/openSession', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || '로그인에 실패했습니다.');
            }

            window.AuthManager.setTokens(data.accessToken, data.refreshToken, keepLogin);
            window.AuthManager.setUserInfo({ email }, keepLogin);
            window.AuthManager.updateUI();
            window.LoginModal.close();

            alert('로그인되었습니다!');

            document.getElementById('loginEmail').value = '';
            document.getElementById('loginPw').value = '';

        } catch (error) {
            alert(error.message || '로그인에 실패했습니다.');
        } finally {
            primaryBtn.disabled = false;
            primaryBtn.textContent = '로그인';
        }
    }

    // 회원가입 처리
    async function handleSignup() {
        const name = document.getElementById('suName')?.value.trim();
        const email = document.getElementById('suEmail')?.value.trim();
        const password = document.getElementById('suPw')?.value;
        const passwordConfirm = document.getElementById('suPw2')?.value;
        const agreed = document.getElementById('suAgree')?.checked;

        if (!name || !email || !password || !passwordConfirm) {
            alert('모든 항목을 입력해주세요.');
            return;
        }

        if (password.length < 8) {
            alert('비밀번호는 8자 이상이어야 합니다.');
            return;
        }

        if (password !== passwordConfirm) {
            alert('비밀번호가 일치하지 않습니다.');
            return;
        }

        if (!agreed) {
            alert('약관에 동의해 주세요.');
            return;
        }

        primaryBtn.disabled = true;
        primaryBtn.textContent = '가입 중...';

        try {
            const response = await fetch('/api/ausers/regCreate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password, passwordConfirm })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || '회원가입에 실패했습니다.');
            }

            window.AuthManager.setTokens(data.accessToken, data.refreshToken, false);
            window.AuthManager.setUserInfo({ name, email }, false);
            window.AuthManager.updateUI();
            window.LoginModal.close();

            alert('회원가입이 완료되었습니다!');

            document.getElementById('suName').value = '';
            document.getElementById('suEmail').value = '';
            document.getElementById('suPw').value = '';
            document.getElementById('suPw2').value = '';
            document.getElementById('suAgree').checked = false;

            setMode('login');

        } catch (error) {
            alert(error.message || '회원가입에 실패했습니다.');
        } finally {
            primaryBtn.disabled = false;
            primaryBtn.textContent = '회원가입';
        }
    }

    console.log('✅ 로그인 모달 탭 전환 초기화 완료');
}

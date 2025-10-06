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

    // 모달 열기 버튼 이벤트
    const openSubmitBtn = $('#openSubmit');
    if (openSubmitBtn) {
        openSubmitBtn.addEventListener('click', ()=>{
            // 로그인이 필요한 기능 보호
            if (window.AuthManager && !AuthManager.isAuthenticated()) {
                alert('로그인이 필요한 서비스입니다.');
                LoginModal.open();
                return;
            }
            SubmitModal.open();
        }, {passive:true});
    }

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

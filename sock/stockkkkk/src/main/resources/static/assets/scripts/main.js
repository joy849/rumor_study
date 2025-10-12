// ===== 유틸리티 =====
const $ = (s,el=document)=>el.querySelector(s);
const $$ = (s,el=document)=>Array.from(el.querySelectorAll(s));
const isFocusable = (el)=>el && !el.disabled && el.tabIndex > -1 || /^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(el?.tagName);

// 포커스 트랩 (모달/드로어용)
function createFocusTrap(container){
    let lastFocused = null;
    const selector = 'a[href],button,textarea,input,select,[tabindex]:not([tabindex="-1"])';
    function onKey(e){
        if(e.key !== 'Tab') return;
        const nodes = $$(selector, container).filter(el=>el.offsetParent!==null && !el.hasAttribute('inert'));
        if(!nodes.length) return;
        const first = nodes[0], last = nodes[nodes.length-1];
        if(e.shiftKey && document.activeElement === first){ last.focus(); e.preventDefault(); }
        else if(!e.shiftKey && document.activeElement === last){ first.focus(); e.preventDefault(); }
    }
    return {
        activate(){
            lastFocused = document.activeElement;
            container.addEventListener('keydown', onKey);
            const first = $$(selector, container).find(isFocusable);
            first?.focus();
        },
        deactivate(){
            container.removeEventListener('keydown', onKey);
            lastFocused?.focus();
        }
    };
}

// rAF 트윈 헬퍼
function rafTween({from=0,to=1,duration=220,ease=(t)=>t,onUpdate,onComplete}){
    const start = performance.now();
    function frame(now){
        const t = Math.min(1, (now-start)/duration);
        const v = from + (to-from)*ease(t);
        onUpdate?.(v);
        if(t<1) requestAnimationFrame(frame);
        else onComplete?.();
    }
    requestAnimationFrame(frame);
}
const easeOutCubic = t => 1 - Math.pow(1 - t, 3);

// ===== 드로어 (우측) =====
const Drawer = (()=>{
    const root = $('#drawer');
    const inner = $('.drawer-inner', root);
    const overlay = $('#drawerOverlay');
    const btnOpen = $('#hamburger');
    const btnClose = $('#closeDrawer');
    const trap = createFocusTrap(root);
    let isOpen = false;

    function a11y(){ root.setAttribute('aria-hidden', String(!isOpen)); btnOpen.setAttribute('aria-expanded', String(isOpen)); }

    function show(){
        if(isOpen) return;
        isOpen = true; a11y();
        root.style.display = 'block';
        inner.style.transform = 'translateX(100%)';
        overlay.style.opacity = '0';
        trap.activate();
        rafTween({
            from:0, to:1, duration:220, ease:easeOutCubic,
            onUpdate:v=>{
                inner.style.transform = `translateX(${(100 - v*100)}%)`;
                overlay.style.opacity = String(0.5*v);
            }
        });
    }
    function hide(){
        if(!isOpen) return;
        isOpen = false; a11y();
        rafTween({
            from:1, to:0, duration:200, ease:easeOutCubic,
            onUpdate:v=>{
                inner.style.transform = `translateX(${(100 - v*100)}%)`;
                overlay.style.opacity = String(0.5*v);
            },
            onComplete:()=>{ root.style.display = 'none'; trap.deactivate(); }
        });
    }

    btnOpen && btnOpen.addEventListener('click', ()=> isOpen?hide():show(), {passive:true});
    btnClose.addEventListener('click', hide, {passive:true});
    overlay.addEventListener('click', hide, {passive:true});

    // 드로어 내부의 링크나 버튼 클릭 시 닫기
    inner.addEventListener('click', (e)=>{
        const el = e.target.closest('a,button');
        if(!el) return;
        if(el.id === 'closeDrawer') return; // 닫기 버튼은 이미 처리됨
        hide();
    }, {passive:true});

    // 모든 메뉴 아이템 클릭 시 닫기
    $$('.drawer-nav a').forEach(a=>a.addEventListener('click', hide, {passive:true}));

    // ESC 키 지원
    window.addEventListener('keydown', e=>{ if(e.key==='Escape' && isOpen) hide(); }, {passive:true});

    return { show, hide };
})();

// ===== 라우터 (탭 & 드로어 링크) =====
const Router = (()=>{
    const defaultView = 'rumor';
    const protectedViews = ['profile']; // 로그인이 필요한 페이지

    function setActive(view){
        // 보호된 페이지에 대한 인증 체크
        if (protectedViews.includes(view) && window.AuthManager && !AuthManager.isAuthenticated()) {
            alert('로그인이 필요한 페이지입니다.');
            if (window.LoginModal) LoginModal.open();
            return;
        }

        $$('.view').forEach(v=>v.classList.toggle('active', v.dataset.view===view));
        $$('.tab').forEach(t=>t.classList.toggle('active', t.dataset.view===view));
        $$('.drawer-nav a').forEach(a=>a.classList.toggle('active', a.dataset.view===view));
        try{ window.scrollTo({top:0, behavior:'smooth'});}catch{ window.scrollTo(0,0); }
    }

    function viewFromHash(){
        const h = (location.hash || '').replace(/^#/, '');
        const valid = new Set(['home','disclosure','rumor','verify','profile','detail']);
        return valid.has(h) ? h : defaultView;
    }

    function routeTo(view){
        view = view || defaultView;

        // 보호된 페이지에 대한 인증 체크
        if (protectedViews.includes(view) && window.AuthManager && !AuthManager.isAuthenticated()) {
            alert('로그인이 필요한 페이지입니다.');
            if (window.LoginModal) LoginModal.open();
            return;
        }

        // 해시 업데이트로 공유 가능하고 뒤로/앞으로 가기 지원
        const nextHash = '#' + view;
        if(location.hash !== nextHash){
            location.hash = nextHash;
        }
        setActive(view);
    }

    // 클릭 핸들러 -> routeTo
    $$('.tabbar .tab').forEach(tab=>tab.addEventListener('click', (e)=>{
        e.preventDefault();
        routeTo(tab.dataset.view);
    }, {passive:false}));
    $$('.drawer-nav a').forEach(a=>a.addEventListener('click', (e)=>{
        e.preventDefault();
        routeTo(a.dataset.view);
    }, {passive:false}));
    $$('[data-nav="#rumor"]').forEach(btn=>btn.addEventListener('click', ()=>routeTo('rumor'), {passive:true}));

    // 뒤로/앞으로 가기 지원
    window.addEventListener('hashchange', ()=>{
        const view = viewFromHash();
        if (protectedViews.includes(view) && window.AuthManager && !AuthManager.isAuthenticated()) {
            alert('로그인이 필요한 페이지입니다.');
            if (window.LoginModal) LoginModal.open();
            history.replaceState(null, '', '#' + defaultView);
            setActive(defaultView);
        } else {
            setActive(view);
        }
    }, {passive:true});

    // 로드 시 초기 라우트
    const initialView = viewFromHash();
    if (protectedViews.includes(initialView) && window.AuthManager && !AuthManager.isAuthenticated()) {
        setActive(defaultView);
        history.replaceState(null, '', '#' + defaultView);
    } else {
        setActive(initialView);
    }

    return { setActive: routeTo, routeTo };
})();


// ===== ESC 키 지원 =====
document.addEventListener('keydown', (e)=>{
    if(e.key !== 'Escape') return;
    // 열린 모달 닫기
    const openDialog = document.querySelector('dialog[open]');
    if(openDialog){ openDialog.close(); return; }
    // 드로어 닫기
    if(Drawer) Drawer.hide();
}, {passive:true});


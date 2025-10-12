/* alert() 재정의 */
(function(){
    function ensureNoticeDialog(){
        var dlg = document.getElementById('noticeDialog');
        if(!dlg){
            dlg = document.createElement('dialog');
            dlg.id = 'noticeDialog';
            dlg.className = 'modal';
            dlg.setAttribute('aria-labelledby', 'noticeTitle');
            dlg.innerHTML = ''
                + '<form method="dialog" class="modal-card">'
                + '  <div class="modal-head"><h2 id="noticeTitle">알림</h2></div>'
                + '  <p id="noticeMsg" style="margin:8px 0 4px;"></p>'
                + '  <div class="modal-actions"><button value="ok" class="cta small" autofocus>확인</button></div>'
                + '</form>';
            document.body.appendChild(dlg);
            var card = dlg.querySelector('.modal-card');
            dlg.addEventListener('click', function(e){
                var r = card.getBoundingClientRect();
                var inside = e.clientX>=r.left && e.clientX<=r.right && e.clientY>=r.top && e.clientY<=r.bottom;
                if(!inside) dlg.close();
            });
        }
        return dlg;
    }

    window.alert = function(message){
        var dlg = ensureNoticeDialog();
        var p = dlg.querySelector('#noticeMsg');
        if(p) p.textContent = (message==null ? '' : String(message));
        dlg.showModal();
    };
})();

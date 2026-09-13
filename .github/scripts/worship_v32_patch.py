from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')


def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'PATCH FAIL [{label}] expected 1 match, got {c}')
    s=s.replace(old,new,1)

if "const APP_VERSION='v3.2';" not in s:
    rep("const APP_VERSION='v3.1';","const APP_VERSION='v3.2';",'version')

    rep('html,body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;-webkit-font-smoothing:antialiased}',
        'html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;-webkit-font-smoothing:antialiased;overflow-x:hidden;overflow-y:auto}',
        'page scroll root')
    rep('button,input,select{font:inherit}button{cursor:pointer}',
        'button,input,select{font:inherit}button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:.5}',
        'disabled button')
    rep('.app{max-width:900px;margin:0 auto;min-height:100vh;padding-bottom:90px}',
        '.app{max-width:900px;margin:0 auto;min-height:100vh;padding-bottom:calc(160px + env(safe-area-inset-bottom))}',
        'bottom scroll space')
    rep('main{padding:15px}', 'main{padding:15px 15px 36px}', 'main padding')
    rep('.sheetModal{position:fixed;left:50%;bottom:0;z-index:90;width:min(900px,100%);max-height:80vh;overflow:auto;background:#fff;border-radius:22px 22px 0 0;transform:translate(-50%,100%);transition:.2s;box-shadow:0 -20px 60px rgba(0,0,0,.18);padding-bottom:env(safe-area-inset-bottom)}',
        '.sheetModal{position:fixed;left:50%;bottom:0;z-index:90;width:min(900px,100%);max-height:88vh;max-height:88dvh;overflow-x:hidden;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch;background:#fff;border-radius:22px 22px 0 0;transform:translate(-50%,100%);transition:.2s;box-shadow:0 -20px 60px rgba(0,0,0,.18);padding-bottom:calc(28px + env(safe-area-inset-bottom))}',
        'modal scrolling')
    rep('.modalBody{padding:12px 14px}', '.modalBody{padding:12px 14px 36px}', 'modal bottom padding')

    rep('let needsFullRefresh=false;', 'let needsFullRefresh=false;\nlet readInFlight=false;\nlet startupSyncTimer=null;', 'request state')

    old_boot="""async function bootstrap(showLoading=true,silentFailure=false){
  const started=performance.now();
  if(!silentFailure){
    setProcess(STATE?'동기화 중…':'연결 중…','working');
    clearConnectionError();
  }
  logEvent('INFO',silentFailure?'BOOTSTRAP_BG_START':'BOOTSTRAP_START',`cached=${!!STATE}`);

  try{
    const res=await jsonp('bootstrap',{},BOOTSTRAP_TIMEOUT_MS,{background:silentFailure});
    if(!res||!res.ok)throw new Error((res&&res.error)||'초기 데이터를 불러오지 못했습니다.');

    STATE=res.data;
    pending.forEach(applyOptimistic);
    cacheState();
    needsFullRefresh=false;

    const today=new Date((STATE.serverToday||keyOf(new Date()))+'T00:00:00');
    if(!viewMonth)viewMonth=new Date(today.getFullYear(),today.getMonth(),1);

    renderAll();
    clearConnectionError();
    if(!silentFailure||['동기화 중…','연결 중…','오프라인','동기화 실패 · 캐시 사용'].includes(processStatus)){
      setProcess('연결 완료','ok');
    }
    logEvent('INFO',silentFailure?'BOOTSTRAP_BG_OK':'BOOTSTRAP_OK',`ms=${Math.round(performance.now()-started)} revision=${STATE.revision}`);

    if(pending.length)flushQueue();
    return true;
  }catch(e){
    if(silentFailure&&STATE){
      logEvent('WARN','BOOTSTRAP_BG_FAIL',e&&e.message?e.message:String(e));
      return false;
    }
    logEvent('ERROR','BOOTSTRAP_FAIL',e&&e.message?e.message:String(e));
    if(STATE){
      renderAll();
      setProcess(navigator.onLine?'동기화 실패 · 캐시 사용':'오프라인 · 캐시 사용',navigator.onLine?'error':'offline');
      showToast('기존 데이터로 표시 중');
    }else{
      showApiError(e&&e.message?e.message:String(e));
    }
    return false;
  }
}"""
    new_boot="""async function bootstrap(showLoading=true,silentFailure=false){
  if(STATE&&(pending.length||flushing)){
    needsFullRefresh=true;
    logEvent('INFO','BOOTSTRAP_DEFER','save pending');
    return false;
  }
  if(readInFlight){
    logEvent('INFO','BOOTSTRAP_DEFER','read in flight');
    return false;
  }

  readInFlight=true;
  const started=performance.now();
  if(!silentFailure){
    setProcess(STATE?'동기화 중…':'연결 중…','working');
    clearConnectionError();
  }
  logEvent('INFO',silentFailure?'BOOTSTRAP_BG_START':'BOOTSTRAP_START',`cached=${!!STATE}`);

  try{
    const res=await jsonp('bootstrap',{},BOOTSTRAP_TIMEOUT_MS,{background:silentFailure});
    if(!res||!res.ok)throw new Error((res&&res.error)||'초기 데이터를 불러오지 못했습니다.');

    STATE=res.data;
    pending.forEach(applyOptimistic);
    cacheState();
    needsFullRefresh=false;

    const today=new Date((STATE.serverToday||keyOf(new Date()))+'T00:00:00');
    if(!viewMonth)viewMonth=new Date(today.getFullYear(),today.getMonth(),1);

    renderAll();
    clearConnectionError();
    if(!silentFailure||['동기화 중…','연결 중…','오프라인','동기화 실패 · 캐시 사용'].includes(processStatus)){
      setProcess('연결 완료','ok');
    }
    logEvent('INFO',silentFailure?'BOOTSTRAP_BG_OK':'BOOTSTRAP_OK',`ms=${Math.round(performance.now()-started)} revision=${STATE.revision}`);
    return true;
  }catch(e){
    if(silentFailure&&STATE){
      logEvent('WARN','BOOTSTRAP_BG_FAIL',e&&e.message?e.message:String(e));
      return false;
    }
    logEvent('ERROR','BOOTSTRAP_FAIL',e&&e.message?e.message:String(e));
    if(STATE){
      renderAll();
      setProcess(navigator.onLine?'동기화 실패 · 캐시 사용':'오프라인 · 캐시 사용',navigator.onLine?'error':'offline');
      showToast('기존 데이터로 표시 중');
    }else{
      showApiError(e&&e.message?e.message:String(e));
    }
    return false;
  }finally{
    readInFlight=false;
    if(pending.length&&!flushing){
      clearTimeout(retryTimer);
      retryTimer=setTimeout(flushQueue,50);
    }
  }
}"""
    rep(old_boot,new_boot,'bootstrap serialization')

    rep("function queueMutation(type,payload){\n  const m={",
        "function queueMutation(type,payload){\n  if(type==='rotationComplete'&&pending.some(x=>x.type==='rotationComplete'&&String((x.payload||{}).month)===String(payload.month))){\n    showToast('이미 편성 저장 처리 중입니다');\n    return;\n  }\n  const m={",
        'dedupe rotation')

    rep("async function flushQueue(){\n  if(flushing||!pending.length)return;\n\n  flushing=true;",
        "async function flushQueue(){\n  if(flushing||!pending.length)return;\n  if(readInFlight){\n    setProcess('저장 대기…','working');\n    clearTimeout(retryTimer);\n    retryTimer=setTimeout(flushQueue,250);\n    return;\n  }\n\n  flushing=true;",
        'save waits for read')

    rep("      bootstrap(false,true);\n    }\n  }catch(e){",
        "      setTimeout(()=>bootstrap(false,true),250);\n    }\n  }catch(e){",
        'post save delayed refresh')

    rep("  document.getElementById('monthTitle').textContent=`${y}년 ${m}월`;\n  document.getElementById('monthEdit').classList.toggle('on',monthEdit);",
        "  document.getElementById('monthTitle').textContent=`${y}년 ${m}월`;\n  const completeBtn=document.getElementById('completeMonth');\n  const rotationSaving=pending.some(x=>x.type==='rotationComplete'&&String((x.payload||{}).month)===mk);\n  completeBtn.disabled=rotationSaving;\n  completeBtn.textContent=rotationSaving?'저장 중…':'이 달 편성 완료';\n  document.getElementById('monthEdit').classList.toggle('on',monthEdit);",
        'rotation button state')

    rep("function openModal(title,body){\n  document.getElementById('modalTitle').textContent=title;\n  document.getElementById('modalBody').innerHTML=body;\n  document.getElementById('backdrop').classList.add('show');\n  document.getElementById('modal').classList.add('show');\n}",
        "function openModal(title,body){\n  document.getElementById('modalTitle').textContent=title;\n  document.getElementById('modalBody').innerHTML=body;\n  document.getElementById('backdrop').classList.add('show');\n  const modal=document.getElementById('modal');\n  modal.classList.add('show');\n  modal.scrollTop=0;\n}",
        'modal scroll reset')

    old_poll="""async function pollRevision(){
  if(!STATE||pending.length)return;
  if(needsFullRefresh){
    logEvent('INFO','POST_SAVE_REFRESH_RETRY','pending full refresh');
    await bootstrap(false,true);
    return;
  }
  try{
    const r=await jsonp('revision',{},8000,{background:true});
    if(r&&r.ok&&Number(r.revision)!==Number(STATE.revision)){
      logEvent('INFO','REMOTE_CHANGE',`local=${STATE.revision} remote=${r.revision}`);
      await bootstrap(false,true);
    }
  }catch(e){logEvent('WARN','REVISION_FAIL',e&&e.message?e.message:String(e))}
}"""
    new_poll="""async function pollRevision(){
  if(!STATE||pending.length||flushing||readInFlight)return;
  if(needsFullRefresh){
    logEvent('INFO','POST_SAVE_REFRESH_RETRY','pending full refresh');
    await bootstrap(false,true);
    return;
  }

  readInFlight=true;
  let refreshNeeded=false;
  try{
    const r=await jsonp('revision',{},6000,{background:true});
    if(r&&r.ok&&Number(r.revision)!==Number(STATE.revision)){
      logEvent('INFO','REMOTE_CHANGE',`local=${STATE.revision} remote=${r.revision}`);
      needsFullRefresh=true;
      refreshNeeded=true;
    }
  }catch(e){
    logEvent('WARN','REVISION_FAIL',e&&e.message?e.message:String(e));
  }finally{
    readInFlight=false;
    if(pending.length&&!flushing){
      clearTimeout(retryTimer);
      retryTimer=setTimeout(flushQueue,50);
    }
  }

  if(refreshNeeded&&!pending.length&&!flushing)await bootstrap(false,true);
}"""
    rep(old_poll,new_poll,'revision serialization')

    old_start="""if(loadCachedState()){
  const today=new Date((STATE.serverToday||keyOf(new Date()))+'T00:00:00');
  viewMonth=new Date(today.getFullYear(),today.getMonth(),1);
  pending.forEach(applyOptimistic);
  renderAll();
  setProcess('동기화 중…','working');
  logEvent('INFO','CACHE_RENDERED',`revision=${STATE.revision}`);
}else{
  viewMonth=new Date(localNow.getFullYear(),localNow.getMonth(),1);
  setProcess('연결 중…','working');
}

renderPlaylist();
bootstrap(false);

pollTimer=setInterval(pollRevision,25000);
window.addEventListener('online',()=>{logEvent('INFO','NETWORK','online');if(pending.length)flushQueue();else bootstrap(false,!!STATE)});"""
    new_start="""const hadCachedState=loadCachedState();
if(hadCachedState){
  const today=new Date((STATE.serverToday||keyOf(new Date()))+'T00:00:00');
  viewMonth=new Date(today.getFullYear(),today.getMonth(),1);
  pending.forEach(applyOptimistic);
  renderAll();
  logEvent('INFO','CACHE_RENDERED',`revision=${STATE.revision}`);
  if(pending.length){
    setProcess('저장 대기…','working');
    setTimeout(flushQueue,80);
  }else{
    setProcess('연결 완료','ok');
    startupSyncTimer=setTimeout(pollRevision,1200);
  }
}else{
  viewMonth=new Date(localNow.getFullYear(),localNow.getMonth(),1);
  setProcess('연결 중…','working');
  bootstrap(false);
}

renderPlaylist();

pollTimer=setInterval(pollRevision,30000);
window.addEventListener('online',()=>{logEvent('INFO','NETWORK','online');if(pending.length)flushQueue();else if(STATE)pollRevision();else bootstrap(false)});"""
    rep(old_start,new_start,'cached startup')

    p.write_text(s,encoding='utf-8')

# Preflight
s=p.read_text(encoding='utf-8')
checks={
 'version':"const APP_VERSION='v3.2';" in s,
 'cached startup':'const hadCachedState=loadCachedState();' in s and "startupSyncTimer=setTimeout(pollRevision,1200)" in s,
 'no unconditional startup bootstrap':'renderPlaylist();\n\nbootstrap(false);' not in s,
 'read serialization':'let readInFlight=false;' in s and "if(readInFlight){\n    setProcess('저장 대기…'" in s,
 'poll serialization':'pending.length||flushing||readInFlight' in s,
 'rotation dedupe':"이미 편성 저장 처리 중입니다" in s,
 'rotation button':'rotationSaving' in s and "completeBtn.disabled=rotationSaving" in s,
 'bottom scroll space':'padding-bottom:calc(160px + env(safe-area-inset-bottom))' in s,
 'modal scroll':'max-height:88dvh' in s and '-webkit-overflow-scrolling:touch' in s,
 'storage preserved':"const STORAGE_PREFIX='worship_fast_v3_';" in s,
}
failed=[k for k,v in checks.items() if not v]
if failed:
    raise SystemExit('PREFLIGHT FAIL: '+', '.join(failed))

start=s.find('<script>')
end=s.rfind('</script>')
if start<0 or end<=start:
    raise SystemExit('PREFLIGHT FAIL: script block missing')
Path('/tmp/worship-v32.js').write_text(s[start+len('<script>'):end],encoding='utf-8')
print('PREFLIGHT OK:',', '.join(checks.keys()))

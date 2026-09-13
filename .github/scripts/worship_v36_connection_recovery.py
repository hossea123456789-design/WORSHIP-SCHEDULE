from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'PATCH FAIL [{label}] expected 1 match, got {c}')
    s=s.replace(old,new,1)

def rep_first(old,new,label):
    global s
    c=s.count(old)
    if c<1:
        raise SystemExit(f'PATCH FAIL [{label}] expected at least 1 match, got {c}')
    s=s.replace(old,new,1)

rep("const APP_VERSION='v3.5';","const APP_VERSION='v3.6';",'version')
rep("let lastHardConnectionToastAt=0;","let lastHardConnectionToastAt=0;\nlet hardConnectionDown=false;",'connection state')

rep("script.onerror=()=>finish(new Error('Apps Script API에 연결하지 못했습니다.'));",
    "script.onerror=()=>{logEvent(options.background?'WARN':'ERROR','API_SCRIPT_ERROR',`action=${action} online=${navigator.onLine} host=${new URL(API_URL).host}`);finish(new Error('Apps Script API에 연결하지 못했습니다.'))};",
    'jsonp diagnostics')

old_hard="""    if(isHardConnectionError(e)){
      // Endpoint 자체가 로드되지 않는 상태에서는 즉시 연속 재시도하지 않습니다.
      // 사용자 변경은 큐에 그대로 보존하고 30초 뒤 재시도합니다.
      m.attempts=0;
      saveQueue();
      setProcess('서버 연결 끊김 · 저장 보류','offline');
      const now=Date.now();
      if(now-lastHardConnectionToastAt>15000){
        lastHardConnectionToastAt=now;
        showToast('서버 연결 끊김 · 저장 내용은 보류 중입니다');
      }
      clearTimeout(retryTimer);
      retryTimer=setTimeout(flushQueue,30000);
      return;
    }
"""
new_hard="""    if(isHardConnectionError(e)){
      // 서버 진입 자체가 실패한 경우 저장 요청을 반복해서 두드리지 않습니다.
      // pending은 유지하고 revision 헬스체크가 성공한 뒤에만 저장을 재개합니다.
      hardConnectionDown=true;
      m.attempts=0;
      saveQueue();
      setProcess('서버 연결 끊김 · 저장 보류','offline');
      const now=Date.now();
      if(now-lastHardConnectionToastAt>15000){
        lastHardConnectionToastAt=now;
        showToast('서버 연결 끊김 · 저장 내용은 안전하게 보류 중입니다');
      }
      clearTimeout(retryTimer);
      retryTimer=null;
      return;
    }
"""
rep(old_hard,new_hard,'hard failure retry stop')

# 이 동일한 조각은 bootstrap finally와 pollRevision finally에 모두 존재합니다.
# 파일 순서상 첫 번째는 bootstrap이므로 첫 번째 것만 먼저 보호합니다.
rep_first("if(pending.length&&!flushing){\n      clearTimeout(retryTimer);\n      retryTimer=setTimeout(flushQueue,50);\n    }",
    "if(pending.length&&!flushing&&!hardConnectionDown){\n      clearTimeout(retryTimer);\n      retryTimer=setTimeout(flushQueue,50);\n    }",
    'bootstrap finally guard')

old_poll="""async function pollRevision(){
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
}
"""
new_poll="""async function pollRevision(){
  if(!STATE||flushing||readInFlight)return;
  // 정상 연결 상태에서 저장 대기 중이면 mutate가 우선입니다.
  // 단, hardConnectionDown 상태에서는 pending이 있어도 revision 헬스체크를 허용합니다.
  if(pending.length&&!hardConnectionDown)return;
  if(needsFullRefresh&&!pending.length&&!hardConnectionDown){
    logEvent('INFO','POST_SAVE_REFRESH_RETRY','pending full refresh');
    await bootstrap(false,true);
    return;
  }

  readInFlight=true;
  let refreshNeeded=false;
  let recovered=false;
  try{
    const r=await jsonp('revision',{},6000,{background:true});
    if(r&&r.ok){
      if(hardConnectionDown){
        hardConnectionDown=false;
        recovered=true;
        clearConnectionError();
        logEvent('INFO','API_RECOVERED',`revision=${r.revision} pending=${pending.length}`);
      }
      if(Number(r.revision)!==Number(STATE.revision)){
        logEvent('INFO','REMOTE_CHANGE',`local=${STATE.revision} remote=${r.revision}`);
        needsFullRefresh=true;
        refreshNeeded=true;
      }
    }
  }catch(e){
    if(isHardConnectionError(e))hardConnectionDown=true;
    logEvent('WARN','REVISION_FAIL',e&&e.message?e.message:String(e));
  }finally{
    readInFlight=false;
  }

  if(recovered&&pending.length&&!flushing){
    setProcess('서버 연결 복구 · 저장 재개','working');
    clearTimeout(retryTimer);
    retryTimer=setTimeout(flushQueue,80);
    return;
  }
  if(refreshNeeded&&!pending.length&&!flushing)await bootstrap(false,true);
}
"""
rep(old_poll,new_poll,'poll recovery')

old_start="""  if(pending.length){
    setProcess('저장 대기…','working');
    setTimeout(flushQueue,80);
  }else{
    setProcess('연결 완료','ok');
    startupSyncTimer=setTimeout(pollRevision,1200);
  }
"""
new_start="""  if(pending.length){
    hardConnectionDown=true;
    setProcess('저장 보류 · 서버 확인 중','working');
    startupSyncTimer=setTimeout(pollRevision,500);
  }else{
    setProcess('연결 완료','ok');
    startupSyncTimer=setTimeout(pollRevision,1200);
  }
"""
rep(old_start,new_start,'startup pending healthcheck')

rep("window.addEventListener('online',()=>{logEvent('INFO','NETWORK','online');if(pending.length)flushQueue();else if(STATE)pollRevision();else bootstrap(false)});",
    "window.addEventListener('online',()=>{logEvent('INFO','NETWORK','online');if(STATE){if(pending.length)hardConnectionDown=true;pollRevision()}else bootstrap(false)});",
    'online recovery')

p.write_text(s,encoding='utf-8')

checks={
  'version':"const APP_VERSION='v3.6';" in s,
  'hard flag':'let hardConnectionDown=false;' in s,
  'no hard retry':'retryTimer=setTimeout(flushQueue,30000)' not in s,
  'healthcheck with pending':'if(pending.length&&!hardConnectionDown)return;' in s,
  'recovery resume':"API_RECOVERED" in s and "retryTimer=setTimeout(flushQueue,80)" in s,
  'startup healthcheck':"setProcess('저장 보류 · 서버 확인 중','working')" in s,
  'script diagnostics':'API_SCRIPT_ERROR' in s,
  'status spacing':'bottom:calc(72px + env(safe-area-inset-bottom))' in s and 'bottom:calc(116px + env(safe-area-inset-bottom))' in s,
  'score still isolated':'scoreUploadBtn' not in s,
}
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('PREFLIGHT FAIL: '+', '.join(failed))
start=s.rfind('<script>'); end=s.rfind('</script>')
if start<0 or end<=start: raise SystemExit('script block missing')
Path('/tmp/worship-v36.js').write_text(s[start+len('<script>'):end],encoding='utf-8')
print('PREFLIGHT OK:', ', '.join(checks))

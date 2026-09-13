from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Start from the last known-working v3.2 frontend copied by the workflow.
if "const APP_VERSION='v3.2';" not in s:
    raise SystemExit('expected v3.2 baseline')
s=s.replace("const APP_VERSION='v3.2';","const APP_VERSION='v3.5';",1)

# Separate fixed status and toast vertically and constrain widths on mobile.
old_status=r"\.processStatus\{position:fixed;left:50%;bottom:88px;z-index:115;transform:translateX\(-50%\);display:flex;align-items:center;gap:6px;min-height:30px;padding:7px 11px;border:1px solid var\(--line\);border-radius:999px;background:rgba\(255,255,255,\.97\);box-shadow:0 6px 18px rgba\(15,23,42,\.10\);font-size:9px;font-weight:900;color:#596174;white-space:nowrap\}"
new_status=".processStatus{position:fixed;left:50%;bottom:calc(72px + env(safe-area-inset-bottom));z-index:115;transform:translateX(-50%);display:flex;align-items:center;gap:6px;min-height:30px;max-width:calc(100vw - 24px);padding:7px 11px;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.97);box-shadow:0 6px 18px rgba(15,23,42,.10);font-size:9px;font-weight:900;color:#596174;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;pointer-events:none}.processStatus #processStatusText{overflow:hidden;text-overflow:ellipsis}"
s,n=re.subn(old_status,new_status,s,count=1)
if n!=1: raise SystemExit(f'process status css patch count={n}')
old_toast=r"\.toast\{position:fixed;left:50%;bottom:95px;z-index:110;transform:translate\(-50%,15px\);opacity:0;background:#171a2b;color:#fff;border-radius:999px;padding:9px 12px;font-size:10px;font-weight:900;transition:\.2s;white-space:nowrap;pointer-events:none\}"
new_toast=".toast{position:fixed;left:50%;bottom:calc(116px + env(safe-area-inset-bottom));z-index:120;transform:translate(-50%,15px);opacity:0;max-width:calc(100vw - 24px);background:#171a2b;color:#fff;border-radius:999px;padding:9px 12px;font-size:10px;font-weight:900;transition:.2s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;pointer-events:none}"
s,n=re.subn(old_toast,new_toast,s,count=1)
if n!=1: raise SystemExit(f'toast css patch count={n}')

# Track hard connection failures without hammering the endpoint.
old="let startupSyncTimer=null;"
new="let startupSyncTimer=null;\nlet lastHardConnectionToastAt=0;"
if s.count(old)!=1: raise SystemExit('startup state anchor mismatch')
s=s.replace(old,new,1)

anchor="function showApiError(message){showConnectionError(message||'Apps Script 응답을 확인할 수 없습니다.')}\n\n"
helper="function showApiError(message){showConnectionError(message||'Apps Script 응답을 확인할 수 없습니다.')}\n\nfunction isHardConnectionError(err){\n  const msg=String(err&&err.message?err.message:err||'');\n  return msg.includes('Apps Script API에 연결하지 못했습니다.');\n}\n\n"
if s.count(anchor)!=1: raise SystemExit('showApiError anchor mismatch')
s=s.replace(anchor,helper,1)

needle="""  }catch(e){\n    flushing=false;\n    logEvent('ERROR','SAVE_FAIL',`type=${m.type} attempt=${m.attempts} msg=${e&&e.message?e.message:e}`);\n\n    if(Number(m.attempts||0)<3){\n"""
replacement="""  }catch(e){\n    flushing=false;\n    logEvent('ERROR','SAVE_FAIL',`type=${m.type} attempt=${m.attempts} msg=${e&&e.message?e.message:e}`);\n\n    if(isHardConnectionError(e)){\n      // Endpoint 자체가 로드되지 않는 상태에서는 즉시 연속 재시도하지 않습니다.\n      // 사용자 변경은 큐에 그대로 보존하고 30초 뒤 재시도합니다.\n      m.attempts=0;\n      saveQueue();\n      setProcess('서버 연결 끊김 · 저장 보류','offline');\n      const now=Date.now();\n      if(now-lastHardConnectionToastAt>15000){\n        lastHardConnectionToastAt=now;\n        showToast('서버 연결 끊김 · 저장 내용은 보류 중입니다');\n      }\n      clearTimeout(retryTimer);\n      retryTimer=setTimeout(flushQueue,30000);\n      return;\n    }\n\n    if(Number(m.attempts||0)<3){\n"""
if s.count(needle)!=1: raise SystemExit('save catch anchor mismatch')
s=s.replace(needle,replacement,1)

p.write_text(s,encoding='utf-8')

# Extract inline JS for syntax check.
start=s.rfind('<script>')
end=s.rfind('</script>')
if start<0 or end<=start: raise SystemExit('script block missing')
Path('/tmp/worship-v35.js').write_text(s[start+len('<script>'):end],encoding='utf-8')

checks={
  'version': "const APP_VERSION='v3.5';" in s,
  'storage-preserved': "const STORAGE_PREFIX='worship_fast_v3_';" in s,
  'api-preserved': "AKfycby9srJlhi9sWjpMxJSpyhWgkNRP6RwOyVDRyPRsUDDSceflQgnFP9A7yXaGIXGuj9Ad0Q" in s,
  'serialization': 'let readInFlight=false;' in s and 'let needsFullRefresh=false;' in s,
  'bottom-scroll': 'padding-bottom:calc(160px + env(safe-area-inset-bottom))' in s,
  'status-separated': 'bottom:calc(72px + env(safe-area-inset-bottom))' in s,
  'toast-separated': 'bottom:calc(116px + env(safe-area-inset-bottom))' in s,
  'hard-fail-queue-preserved': "setProcess('서버 연결 끊김 · 저장 보류','offline')" in s and 'retryTimer=setTimeout(flushQueue,30000)' in s,
  'score-rollback': 'scoreUploadBtn' not in s and 'scorePost(' not in s,
}
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('PREFLIGHT FAIL: '+', '.join(failed))
print('PREFLIGHT OK:', ', '.join(checks))

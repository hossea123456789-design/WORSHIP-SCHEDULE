from pathlib import Path
p=Path('ScoreUpload_Addon.gs.txt')
s=p.read_text(encoding='utf-8')
s=s.replace("function doPost(e) {\n  try {\n    const p = (e && e.parameter) || {};", "function doPost(e) {\n  const p = (e && e.parameter) || {};\n  const requestId = String(p.requestId || '');\n  try {")
s=s.replace("scoreReply_({ ok: false, error: '지원하지 않는 요청입니다.' })", "scoreReply_({ ok: false, error: '지원하지 않는 요청입니다.' }, requestId)")
s=s.replace("scoreReply_({ ok: true, file: getCurrentScoreMeta_() })", "scoreReply_({ ok: true, file: getCurrentScoreMeta_() }, requestId)")
s=s.replace("scoreReply_(uploadCurrentScore_(p))", "scoreReply_(uploadCurrentScore_(p), requestId)")
s=s.replace("scoreReply_({ ok: true, file: null })", "scoreReply_({ ok: true, file: null }, requestId)")
s=s.replace("scoreReply_({ ok: false, error: '지원하지 않는 악보 작업입니다.' })", "scoreReply_({ ok: false, error: '지원하지 않는 악보 작업입니다.' }, requestId)")
s=s.replace("scoreReply_({ ok: false, error: String(err && err.message ? err.message : err) })", "scoreReply_({ ok: false, error: String(err && err.message ? err.message : err) }, requestId)")
s=s.replace("function scoreReply_(data) {\n  const payload = Object.assign({ source: 'worship-score-api' }, data || {});", "function scoreReply_(data, requestId) {\n  const payload = Object.assign({ source: 'worship-score-api', requestId: String(requestId || '') }, data || {});")
if "requestId: String(requestId || '')" not in s:
    raise SystemExit('requestId patch failed')
p.write_text(s,encoding='utf-8')

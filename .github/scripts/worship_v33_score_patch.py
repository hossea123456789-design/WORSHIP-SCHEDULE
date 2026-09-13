from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'PATCH FAIL [{label}] expected 1 match, got {c}')
    s=s.replace(old,new,1)

if "const APP_VERSION='v3.3';" not in s:
    rep("const APP_VERSION='v3.2';","const APP_VERSION='v3.3';",'version')

    old_css='.playlistCard{padding:13px}.youtubeBox{position:relative;width:100%;aspect-ratio:16/9;border-radius:15px;overflow:hidden;background:#111;margin:10px 0}.youtubeBox iframe{position:absolute;inset:0;width:100%;height:100%;border:0}.ytLink{display:inline-flex;text-decoration:none;background:#ff0000;color:#fff;border-radius:10px;padding:9px 11px;font-size:10px;font-weight:950}'
    new_css=old_css + '.scoreCard{margin-top:12px;overflow:hidden}.scoreHead{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:13px 14px;border-bottom:1px solid var(--line)}.scoreHead h3{margin:0;font-size:13px}.scoreBody{padding:13px}.scoreEmpty{padding:22px 14px;text-align:center;border:1px dashed #d7dae3;border-radius:14px;background:#fafbfe}.scoreEmpty b{display:block;font-size:12px;margin-bottom:5px}.scoreEmpty span{display:block;font-size:9px;color:var(--muted);line-height:1.5}.scoreMeta{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}.scoreName{font-size:12px;font-weight:950;word-break:break-all}.scoreSub{font-size:9px;color:var(--muted);margin-top:3px}.scoreActions{display:flex;gap:6px;flex-wrap:wrap}.scorePreview{position:relative;width:100%;height:62vh;min-height:420px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#f2f4f7;margin-top:10px}.scorePreview iframe{position:absolute;inset:0;width:100%;height:100%;border:0}.scoreStatus{font-size:10px;color:var(--muted);margin-top:8px}.scoreStatus.error{color:#b42318}.scoreStatus.working{color:var(--accent);font-weight:900}@media(max-width:520px){.scorePreview{height:58vh;min-height:360px}}'
    rep(old_css,new_css,'score css')

    old_html='<section id="tab-playlist" class="panel"><div class="sectionTitle"><h2>찬양 재생목록</h2></div><div class="card playlistCard"><div class="youtubeBox"><iframe id="youtubeFrame" title="주일 찬양 재생목록" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div><a class="ytLink" id="youtubeLink" target="_blank" rel="noopener">▶ YouTube에서 열기</a></div></section>'
    new_html='''<section id="tab-playlist" class="panel"><div class="sectionTitle"><h2>찬양 재생목록</h2></div><div class="card playlistCard"><div class="youtubeBox"><iframe id="youtubeFrame" title="주일 찬양 재생목록" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div><a class="ytLink" id="youtubeLink" target="_blank" rel="noopener">▶ YouTube에서 열기</a></div>
<div class="card scoreCard"><div class="scoreHead"><h3>악보 자료</h3><button class="primaryBtn" id="scoreUploadBtn">+ 악보 올리기</button></div><div class="scoreBody"><input id="scoreFileInput" type="file" accept=".pdf,.ppt,.pptx,.doc,.docx,.jpg,.jpeg,.png" hidden><div id="scoreArea"><div class="scoreEmpty"><b>등록된 악보가 없습니다</b><span>PDF · PPT · PPTX 등 파일을 올리면 팀원 모두 같은 최신 악보를 볼 수 있습니다.</span></div></div><div class="scoreStatus" id="scoreStatus"></div></div></div></section>'''
    rep(old_html,new_html,'score html')

    rep("let startupSyncTimer=null;","let startupSyncTimer=null;\nlet SCORE_META=null;\nlet scoreBusy=false;",'score state')

    old_render='''function renderPlaylist(){
  const playlistUrl=STATE&&STATE.config&&STATE.config.PLAYLIST_URL
    ?STATE.config.PLAYLIST_URL
    :`https://youtube.com/playlist?list=${PLAYLIST_ID}`;

  document.getElementById('youtubeFrame').src=`https://www.youtube.com/embed/videoseries?list=${PLAYLIST_ID}`;
  document.getElementById('youtubeLink').href=playlistUrl;
}'''
    new_render=old_render + r'''

function formatBytes(n){
  const v=Number(n||0);
  if(!v)return'';
  if(v<1024*1024)return`${Math.max(1,Math.round(v/1024))}KB`;
  return`${(v/1024/1024).toFixed(v>=10*1024*1024?0:1)}MB`;
}

function setScoreStatus(text,type=''){
  const el=document.getElementById('scoreStatus');
  if(!el)return;
  el.textContent=text||'';
  el.className='scoreStatus'+(type?' '+type:'');
}

function renderScore(){
  const area=document.getElementById('scoreArea');
  const btn=document.getElementById('scoreUploadBtn');
  if(!area||!btn)return;
  btn.disabled=scoreBusy;
  btn.textContent=scoreBusy?'업로드 중…':(SCORE_META?'+ 새 악보로 교체':'+ 악보 올리기');

  if(!SCORE_META){
    area.innerHTML='<div class="scoreEmpty"><b>등록된 악보가 없습니다</b><span>PDF · PPT · PPTX · DOC · DOCX · JPG · PNG 파일을 올릴 수 있습니다.<br>새 파일을 올리면 이전 악보는 자동 삭제됩니다.</span></div>';
    return;
  }

  const f=SCORE_META;
  area.innerHTML=`<div class="scoreMeta"><div><div class="scoreName">${escapeHtml(f.name||'악보')}</div><div class="scoreSub">${escapeHtml(f.updatedAt||'')}${f.size?` · ${formatBytes(f.size)}`:''}</div></div><div class="scoreActions"><a class="ghostBtn" style="text-decoration:none;display:inline-flex;align-items:center" href="${escapeHtml(f.openUrl||'#')}" target="_blank" rel="noopener">새 창</a></div></div><div class="scorePreview"><iframe src="${escapeHtml(f.previewUrl||'')}" title="악보 미리보기" loading="lazy" allow="fullscreen"></iframe></div>`;
}

function scorePost(action,fields={},timeoutMs=45000){
  const requestId='score_'+Date.now().toString(36)+'_'+Math.random().toString(36).slice(2);
  return new Promise((resolve,reject)=>{
    const iframe=document.createElement('iframe');
    iframe.name='scoreFrame_'+requestId;
    iframe.style.display='none';
    const form=document.createElement('form');
    form.method='POST';
    form.action=API_URL;
    form.target=iframe.name;
    form.style.display='none';

    const add=(name,value)=>{
      const input=document.createElement('input');
      input.type='hidden';
      input.name=name;
      input.value=value==null?'':String(value);
      form.appendChild(input);
    };
    add('app','worship-score');
    add('action',action);
    add('requestId',requestId);
    Object.entries(fields).forEach(([k,v])=>add(k,v));

    let done=false;
    const cleanup=()=>{window.removeEventListener('message',onMessage);clearTimeout(timer);form.remove();iframe.remove()};
    const finish=(err,data)=>{if(done)return;done=true;cleanup();err?reject(err):resolve(data)};
    const onMessage=event=>{
      const msg=event.data||{};
      if(msg.source!=='worship-score-api'||msg.requestId!==requestId)return;
      if(!msg.ok)return finish(new Error(msg.error||'악보 요청에 실패했습니다.'));
      finish(null,msg);
    };
    const timer=setTimeout(()=>finish(new Error('악보 서버 응답 시간이 초과되었습니다.')),timeoutMs);
    window.addEventListener('message',onMessage);
    document.body.appendChild(iframe);
    document.body.appendChild(form);
    form.submit();
  });
}

async function loadScoreMeta(silent=true){
  if(scoreBusy)return;
  try{
    const res=await scorePost('meta',{},15000);
    SCORE_META=res.file||null;
    renderScore();
    setScoreStatus('');
  }catch(e){
    if(!silent)setScoreStatus(e&&e.message?e.message:String(e),'error');
  }
}

function fileToBase64(file){
  return new Promise((resolve,reject)=>{
    const r=new FileReader();
    r.onload=()=>{
      const s=String(r.result||'');
      resolve(s.includes(',')?s.split(',').pop():s);
    };
    r.onerror=()=>reject(new Error('파일을 읽지 못했습니다.'));
    r.readAsDataURL(file);
  });
}

async function uploadScoreFile(file){
  if(!file||scoreBusy)return;
  const ext=(file.name.split('.').pop()||'').toLowerCase();
  if(!['pdf','ppt','pptx','doc','docx','jpg','jpeg','png'].includes(ext)){
    showToast('지원하지 않는 파일 형식입니다');
    return;
  }
  if(file.size>25*1024*1024){
    showToast('악보 파일은 25MB 이하만 가능합니다');
    return;
  }
  if(SCORE_META&&!confirm('기존 악보는 삭제되고 이 파일로 교체됩니다. 계속할까요?'))return;

  scoreBusy=true;
  renderScore();
  setScoreStatus('파일을 읽는 중…','working');
  try{
    const dataBase64=await fileToBase64(file);
    setScoreStatus('Drive에 업로드 중…','working');
    const res=await scorePost('upload',{fileName:file.name,mimeType:file.type||'',dataBase64},90000);
    SCORE_META=res.file||null;
    renderScore();
    setScoreStatus('업로드 완료');
    showToast('악보를 교체했습니다');
  }catch(e){
    setScoreStatus(e&&e.message?e.message:String(e),'error');
    showToast('악보 업로드 실패');
  }finally{
    scoreBusy=false;
    const input=document.getElementById('scoreFileInput');
    if(input)input.value='';
    renderScore();
  }
}'''
    rep(old_render,new_render,'score js')

    rep("document.getElementById('retryConnection').onclick=()=>bootstrap(false);","document.getElementById('retryConnection').onclick=()=>bootstrap(false);\ndocument.getElementById('scoreUploadBtn').onclick=()=>document.getElementById('scoreFileInput').click();\ndocument.getElementById('scoreFileInput').onchange=e=>uploadScoreFile(e.target.files&&e.target.files[0]);",'score handlers')

    rep("  document.getElementById('tab-'+b.dataset.tab).classList.add('active');\n  window.scrollTo({top:0,behavior:'smooth'});","  document.getElementById('tab-'+b.dataset.tab).classList.add('active');\n  if(b.dataset.tab==='playlist'&&!SCORE_META&&!scoreBusy)loadScoreMeta(true);\n  window.scrollTo({top:0,behavior:'smooth'});",'playlist lazy meta')

    rep("renderPlaylist();\n\npollTimer=setInterval(pollRevision,30000);","renderPlaylist();\nrenderScore();\nsetTimeout(()=>loadScoreMeta(true),1400);\n\npollTimer=setInterval(pollRevision,30000);",'startup score meta')

    p.write_text(s,encoding='utf-8')

# preflight
s=p.read_text(encoding='utf-8')
checks={
  'version':"const APP_VERSION='v3.3';" in s,
  'score ui':'id="scoreUploadBtn"' in s and 'id="scoreArea"' in s,
  'score post':"function scorePost(action,fields={},timeoutMs=45000)" in s,
  'single-slot copy':'기존 악보는 삭제되고 이 파일로 교체됩니다.' in s,
  'preview':'scorePreview' in s and 'previewUrl' in s,
  '25mb':'25*1024*1024' in s,
  'formats':"['pdf','ppt','pptx','doc','docx','jpg','jpeg','png']" in s,
}
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('PREFLIGHT FAIL: '+', '.join(failed))
start=s.find('<script>'); end=s.rfind('</script>')
if start<0 or end<=start: raise SystemExit('script block missing')
Path('/tmp/worship-v33.js').write_text(s[start+len('<script>'):end],encoding='utf-8')
print('PREFLIGHT OK', ', '.join(checks))

from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'PATCH FAIL [{label}] expected 1 match, got {c}')
    s=s.replace(old,new,1)

rep("const APP_VERSION='v3.3';","const APP_VERSION='v3.4';",'version')
rep("let SCORE_META=null;\nlet scoreBusy=false;","let SCORE_META=null;\nlet scoreBusy=false;\nlet scoreProgressHideTimer=null;",'score state')

old_css=".scoreStatus{font-size:10px;color:var(--muted);margin-top:8px}.scoreStatus.error{color:#b42318}.scoreStatus.working{color:var(--accent);font-weight:900}@media(max-width:520px){.scorePreview{height:58vh;min-height:360px}}"
new_css=".scoreStatus{font-size:10px;color:var(--muted);margin-top:8px}.scoreStatus.error{color:#b42318}.scoreStatus.working{color:var(--accent);font-weight:900}.scoreProgress{margin-top:10px;padding:10px 11px;border-radius:12px;background:#f7f8fc;border:1px solid var(--line)}.scoreProgress[hidden]{display:none}.scoreProgressTop{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:7px;font-size:9px;font-weight:900;color:#596174}.scoreProgressPct{font-size:11px;color:var(--accent)}.scoreProgressTrack{height:8px;border-radius:999px;background:#e8eaf0;overflow:hidden}.scoreProgressFill{height:100%;width:0;background:var(--accent);border-radius:999px;transition:width .18s ease}.scoreProgressDetail{margin-top:6px;font-size:9px;color:var(--muted);line-height:1.45}.scoreProgress.error .scoreProgressTop,.scoreProgress.error .scoreProgressPct,.scoreProgress.error .scoreProgressDetail{color:#b42318}.scoreProgress.error .scoreProgressFill{background:#d92d20}@media(max-width:520px){.scorePreview{height:58vh;min-height:360px}}"
rep(old_css,new_css,'progress css')

old_html='<div class="scoreStatus" id="scoreStatus"></div></div></div></section>'
new_html='<div class="scoreStatus" id="scoreStatus"></div><div class="scoreProgress" id="scoreProgress" hidden><div class="scoreProgressTop"><span id="scoreProgressLabel">업로드 준비 중</span><span class="scoreProgressPct" id="scoreProgressPct">0%</span></div><div class="scoreProgressTrack"><div class="scoreProgressFill" id="scoreProgressFill"></div></div><div class="scoreProgressDetail" id="scoreProgressDetail"></div></div></div></div></section>'
rep(old_html,new_html,'progress html')

anchor="function renderScore(){"
insert="""function formatRemainingSeconds(sec){
  const n=Math.max(0,Math.round(Number(sec||0)));
  if(n<60)return `약 ${n}초 남음`;
  const m=Math.floor(n/60),s=n%60;
  return s?`약 ${m}분 ${s}초 남음`:`약 ${m}분 남음`;
}

function updateScoreProgress(done,total,startedAt,label='Drive에 업로드 중'){
  const box=document.getElementById('scoreProgress');
  const pctEl=document.getElementById('scoreProgressPct');
  const fill=document.getElementById('scoreProgressFill');
  const labelEl=document.getElementById('scoreProgressLabel');
  const detail=document.getElementById('scoreProgressDetail');
  if(!box||!pctEl||!fill||!labelEl||!detail)return;
  clearTimeout(scoreProgressHideTimer);
  box.hidden=false;
  box.classList.remove('error');
  const safeTotal=Math.max(1,Number(total||1));
  const safeDone=Math.max(0,Math.min(Number(done||0),safeTotal));
  const pct=Math.max(0,Math.min(100,(safeDone/safeTotal)*100));
  labelEl.textContent=label;
  pctEl.textContent=`${Math.floor(pct)}%`;
  fill.style.width=`${pct.toFixed(1)}%`;
  const elapsed=Math.max(.001,(performance.now()-startedAt)/1000);
  let remain='남은 시간 계산 중…';
  if(safeDone>0&&elapsed>=1){
    const rate=safeDone/elapsed;
    if(rate>0)remain=formatRemainingSeconds((safeTotal-safeDone)/rate);
  }
  if(pct>=100)remain='전송 완료';
  detail.textContent=`${formatBytes(safeDone)} / ${formatBytes(safeTotal)} · ${remain}`;
}

function failScoreProgress(message){
  const box=document.getElementById('scoreProgress');
  const label=document.getElementById('scoreProgressLabel');
  const detail=document.getElementById('scoreProgressDetail');
  if(!box||!label||!detail)return;
  box.hidden=false;
  box.classList.add('error');
  label.textContent='업로드 중단';
  detail.textContent=message||'업로드에 실패했습니다.';
}

function hideScoreProgress(delay=0){
  clearTimeout(scoreProgressHideTimer);
  scoreProgressHideTimer=setTimeout(()=>{
    const box=document.getElementById('scoreProgress');
    if(box){box.hidden=true;box.classList.remove('error')}
  },delay);
}

"""
if anchor not in s:
    raise SystemExit('PATCH FAIL [renderScore anchor]')
s=s.replace(anchor,insert+anchor,1)

pattern=r"function fileToBase64\(file\)\{.*?\n\}\n\nasync function uploadScoreFile\(file\)\{.*?\n\}\n\nfunction renderSettings\(\)\{"
replacement=r'''function blobToBase64(blob){
  return new Promise((resolve,reject)=>{
    const r=new FileReader();
    r.onload=()=>{
      const x=String(r.result||'');
      resolve(x.includes(',')?x.split(',').pop():x);
    };
    r.onerror=()=>reject(new Error('파일 조각을 읽지 못했습니다.'));
    r.readAsDataURL(blob);
  });
}

function waitMs(ms){return new Promise(resolve=>setTimeout(resolve,ms))}

async function scoreChunkPostWithRetry(fields){
  let lastError=null;
  for(let attempt=1;attempt<=3;attempt++){
    try{
      return await scorePost('uploadChunk',fields,40000);
    }catch(e){
      lastError=e;
      if(attempt<3)await waitMs(700*attempt);
    }
  }
  throw lastError||new Error('업로드 조각 전송에 실패했습니다.');
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
  const startedAt=performance.now();
  let uploaded=0;
  updateScoreProgress(0,file.size,startedAt,'업로드 준비 중');
  setScoreStatus('Drive 업로드 준비 중…','working');

  try{
    const startRes=await scorePost('uploadStart',{
      fileName:file.name,
      mimeType:file.type||'',
      totalSize:file.size
    },30000);

    const uploadId=String(startRes.uploadId||'');
    const chunkSize=Math.max(256*1024,Number(startRes.chunkSize||768*1024));
    if(!uploadId)throw new Error('업로드 세션을 만들지 못했습니다.');

    setScoreStatus('Drive에 분할 업로드 중…','working');
    let lastRes=null;
    while(uploaded<file.size){
      const endExclusive=Math.min(file.size,uploaded+chunkSize);
      const blob=file.slice(uploaded,endExclusive);
      const dataBase64=await blobToBase64(blob);
      lastRes=await scoreChunkPostWithRetry({
        uploadId,
        start:uploaded,
        end:endExclusive-1,
        totalSize:file.size,
        dataBase64
      });
      const acknowledged=Number(lastRes.receivedBytes||endExclusive);
      uploaded=Math.max(endExclusive,Math.min(file.size,acknowledged));
      updateScoreProgress(uploaded,file.size,startedAt,lastRes.complete?'마무리 중…':'Drive에 업로드 중');
    }

    if(!lastRes||!lastRes.complete||!lastRes.file){
      throw new Error('파일 전송은 끝났지만 Drive 저장 완료 응답을 받지 못했습니다.');
    }

    SCORE_META=lastRes.file;
    updateScoreProgress(file.size,file.size,startedAt,'업로드 완료');
    renderScore();
    setScoreStatus('업로드 완료');
    showToast('악보를 교체했습니다');
    hideScoreProgress(1800);
  }catch(e){
    const msg=e&&e.message?e.message:String(e);
    failScoreProgress(msg);
    setScoreStatus(msg,'error');
    showToast('악보 업로드 실패');
  }finally{
    scoreBusy=false;
    const input=document.getElementById('scoreFileInput');
    if(input)input.value='';
    renderScore();
  }
}

function renderSettings(){'''
s2,n=re.subn(pattern,replacement,s,flags=re.S)
if n!=1:
    raise SystemExit(f'PATCH FAIL [upload block] expected 1 match, got {n}')
s=s2

p.write_text(s,encoding='utf-8')

# Apps Script: final chunk response가 브라우저에서 유실되어 재시도돼도 완료 결과를 되돌려줍니다.
g=Path('ScoreUpload_Addon.gs.txt')
t=g.read_text(encoding='utf-8')
old="""  const meta = JSON.parse(raw);
  const start = Number(p.start || 0);"""
new="""  const meta = JSON.parse(raw);
  if (meta.complete && meta.fileId) {
    const completedFile = DriveApp.getFileById(String(meta.fileId));
    return { ok: true, complete: true, receivedBytes: Number(meta.totalSize || 0), file: buildScoreMeta_(completedFile, String(meta.updatedAt || '')) };
  }
  const start = Number(p.start || 0);"""
if t.count(old)!=1:
    raise SystemExit('PATCH FAIL [completed retry guard]')
t=t.replace(old,new,1)
old2="""    props.deleteProperty(key);

    return { ok: true, complete: true, receivedBytes: totalSize, file: buildScoreMeta_(file, updatedAt) };"""
new2="""    meta.complete = true;
    meta.fileId = fileId;
    meta.updatedAt = updatedAt;
    meta.nextStart = totalSize;
    props.setProperty(key, JSON.stringify(meta));

    return { ok: true, complete: true, receivedBytes: totalSize, file: buildScoreMeta_(file, updatedAt) };"""
if t.count(old2)!=1:
    raise SystemExit('PATCH FAIL [completed session retention]')
t=t.replace(old2,new2,1)
g.write_text(t,encoding='utf-8')

# Extract inline JS for node --check
html=p.read_text(encoding='utf-8')
start=html.rfind('<script>')+len('<script>')
end=html.rfind('</script>')
Path('/tmp/worship-v34.js').write_text(html[start:end],encoding='utf-8')

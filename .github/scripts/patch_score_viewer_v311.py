from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

if "const APP_VERSION='v3.10.0';" not in s:
    raise SystemExit('unexpected app version')
s=s.replace("const APP_VERSION='v3.10.0';","const APP_VERSION='v3.11.0';",1)

old_css=""".scorePreview{height:78vh;min-height:560px}\n.scorePreview:fullscreen,.scorePreview:-webkit-full-screen{width:100vw;height:100vh;min-height:100vh;border:0;border-radius:0;background:#111}\n.scorePreview:fullscreen iframe,.scorePreview:-webkit-full-screen iframe{width:100%;height:100%}\n@media(max-width:520px){.scorePreview{height:70vh;min-height:480px}.scoreMeta{align-items:flex-start;flex-direction:column}.scoreActions{width:100%}.scoreActions .ghostBtn{flex:1;justify-content:center}}"""
new_css=""".scorePreview{height:min(52vh,560px);min-height:320px;background:#f6f7fa}\n.scorePreview.collapsed{height:0!important;min-height:0!important;margin-top:0!important;border-width:0!important;overflow:hidden!important}\n.scoreImagePreview{height:auto!important;min-height:0!important;max-height:none!important;background:#fff;padding:8px;overflow:hidden}\n.scoreImagePreview img{display:block;width:100%;height:auto;max-height:none;object-fit:contain;background:#fff;border-radius:10px;cursor:zoom-in;touch-action:manipulation}\n.scorePreview:fullscreen,.scorePreview:-webkit-full-screen{width:100vw;height:100vh!important;min-height:100vh!important;border:0;border-radius:0;background:#111}\n.scorePreview:fullscreen iframe,.scorePreview:-webkit-full-screen iframe{width:100%;height:100%}\n.scoreImagePreview:fullscreen,.scoreImagePreview:-webkit-full-screen{display:flex;align-items:center;justify-content:center;padding:0;overflow:auto;background:#111}\n.scoreImagePreview:fullscreen img,.scoreImagePreview:-webkit-full-screen img{width:auto;height:auto;max-width:100%;max-height:100%;object-fit:contain;border-radius:0;touch-action:pinch-zoom}\n@media(max-width:520px){.scorePreview{height:46vh;min-height:300px}.scoreImagePreview{height:auto!important;min-height:0!important}.scoreMeta{align-items:flex-start;flex-direction:column}.scoreActions{width:100%}.scoreActions .ghostBtn{flex:1;justify-content:center}}"""
if old_css not in s:
    raise SystemExit('score css target not found')
s=s.replace(old_css,new_css,1)

old_open="""function openScoreFullscreen(){\n  const box=document.querySelector('.scorePreview');\n  if(!box)return;\n  const fn=box.requestFullscreen||box.webkitRequestFullscreen;"""
new_open="""function openScoreFullscreen(){\n  const box=document.querySelector('#scoreArea .scorePreview');\n  if(!box)return;\n  if(box.classList.contains('collapsed')){\n    box.classList.remove('collapsed');\n    const toggle=document.getElementById('scoreTogglePreview');\n    if(toggle)toggle.textContent='미리보기 접기';\n  }\n  const fn=box.requestFullscreen||box.webkitRequestFullscreen;"""
if old_open not in s:
    raise SystemExit('fullscreen target not found')
s=s.replace(old_open,new_open,1)

start=s.find('function renderScore(){')
end=s.find('function scorePost(',start)
if start<0 or end<0:
    raise SystemExit('renderScore block not found')

new_render=r'''function toggleScorePreview(){
  const box=document.querySelector('#scoreArea .scorePreview');
  const btn=document.getElementById('scoreTogglePreview');
  if(!box||!btn)return;
  const collapsed=box.classList.toggle('collapsed');
  btn.textContent=collapsed?'미리보기 펼치기':'미리보기 접기';
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
  const id=String(f.id||'');
  const fileName=String(f.name||'악보');
  const ext=(fileName.split('.').pop()||'').toLowerCase();
  const isImage=['jpg','jpeg','png','webp'].includes(ext);
  const downloadUrl=id?`https://drive.google.com/uc?export=download&id=${encodeURIComponent(id)}`:(f.openUrl||'#');
  const imageUrl=id?`https://drive.google.com/thumbnail?id=${encodeURIComponent(id)}&sz=w2400`:'';
  const previewHtml=(isImage&&imageUrl)
    ?`<div class="scorePreview scoreImagePreview"><img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(fileName)}" loading="lazy" onclick="openScoreFullscreen()"></div>`
    :`<div class="scorePreview"><iframe src="${escapeHtml(f.previewUrl||'')}" title="악보 미리보기" loading="lazy" allow="fullscreen"></iframe></div>`;

  area.innerHTML=`<div class="scoreMeta"><div><div class="scoreName">${escapeHtml(fileName)}</div><div class="scoreSub">${escapeHtml(f.updatedAt||'')}${f.size?` · ${formatBytes(f.size)}`:''}</div></div><div class="scoreActions"><a class="ghostBtn" style="text-decoration:none;display:inline-flex;align-items:center" href="${escapeHtml(downloadUrl)}" target="_blank" rel="noopener">다운로드</a><a class="ghostBtn" style="text-decoration:none;display:inline-flex;align-items:center" href="${escapeHtml(f.openUrl||'#')}" target="_blank" rel="noopener">새 창</a><button class="ghostBtn" id="scoreTogglePreview" type="button" onclick="toggleScorePreview()">미리보기 접기</button><button class="ghostBtn" type="button" onclick="openScoreFullscreen()">전체화면</button></div></div>${previewHtml}`;
}
'''
s=s[:start]+new_render+s[end:]

p.write_text(s,encoding='utf-8')
print('patched score viewer UX v3.11.0')

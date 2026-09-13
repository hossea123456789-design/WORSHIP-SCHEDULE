from pathlib import Path
p=Path('ScoreUpload_Addon.gs.txt')
s=p.read_text(encoding='utf-8')
old="function doPost(e) {"
new="function handleWorshipScorePost_(e) {"
if s.count(old)!=1:
    raise SystemExit(f'expected 1 doPost, got {s.count(old)}')
s=s.replace(old,new,1)
s=s.replace('// Apps Script 프로젝트의 새 .gs 파일에 그대로 붙여넣으세요.','// Apps Script 프로젝트의 새 .gs 파일에 그대로 붙여넣으세요.\n// 주의: 이 파일은 doPost를 정의하지 않습니다. 기존 Code.gs의 단일 doPost에서 handleWorshipScorePost_(e)로 라우팅해야 합니다.',1)
p.write_text(s,encoding='utf-8')

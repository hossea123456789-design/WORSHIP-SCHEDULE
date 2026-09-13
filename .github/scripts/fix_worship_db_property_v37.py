from pathlib import Path
import re

paths=[Path('WorshipApi.gs.txt'),Path('WorshipApi_RECOVERY_v35.gs.txt')]
for p in paths:
    if not p.exists():
        raise SystemExit(f'missing {p}')
    s=p.read_text(encoding='utf-8')

    s,n=re.subn(r"DB_PROP:\s*'WORSHIP_DB_ID'","DB_PROP: 'SPREADSHEET_ID'",s,count=1)
    if n!=1:
        raise SystemExit(f'{p}: DB_PROP patch count={n}')

    pattern=r"function worshipDb_\(\) \{ const id=PropertiesService\.getScriptProperties\(\)\.getProperty\(WORSHIP_API\.DB_PROP\); if\(!id\)throw new Error\('WORSHIP_DB_ID를 찬양팀 스프레드시트 ID로 설정해주세요\.'\); return SpreadsheetApp\.openById\(id\); \}"
    repl="""function worshipDb_() {
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty(WORSHIP_API.DB_PROP) || props.getProperty('WORSHIP_DB_ID');
  if (id) return SpreadsheetApp.openById(id);
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('스프레드시트 연결 정보가 없습니다. 기존 SPREADSHEET_ID 또는 연결 스프레드시트를 확인해주세요.');
  return ss;
}"""
    s,n=re.subn(pattern,repl,s,count=1)
    if n!=1:
        raise SystemExit(f'{p}: worshipDb_ patch count={n}')

    p.write_text(s,encoding='utf-8')

for p in paths:
    s=p.read_text(encoding='utf-8')
    assert "DB_PROP: 'SPREADSHEET_ID'" in s
    assert "getProperty('WORSHIP_DB_ID')" in s
    assert "SpreadsheetApp.getActiveSpreadsheet()" in s
    assert "WORSHIP_DB_ID를 찬양팀 스프레드시트 ID로 설정해주세요." not in s
print('DB PROPERTY PATCH OK')

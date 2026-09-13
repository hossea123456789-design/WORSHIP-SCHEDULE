from pathlib import Path
p=Path('WorshipStandalone.gs.txt')
s=p.read_text(encoding='utf-8')
old_auth="""function authorizeWorshipStandalone() {
  const id = PropertiesService.getScriptProperties().getProperty(WORSHIP_API.DB_PROP);
  if (!id) throw new Error('먼저 setupWorshipStandalone()을 실행해주세요.');
  const ss = SpreadsheetApp.openById(id);
  const name = ss.getName();
  DriveApp.getRootFolder().getName();
  return '권한 승인 완료: ' + name;
}

"""
s=s.replace(old_auth,'')
old_setup="""function setupWorshipStandalone() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('찬양팀_DB 스프레드시트에서 확장 프로그램 > Apps Script로 연 뒤 실행해주세요.');
  PropertiesService.getScriptProperties().setProperty(WORSHIP_API.DB_PROP, ss.getId());
  worshipValidateSchema_(ss);
  return '연결 완료: ' + ss.getName() + ' / ' + ss.getId();
}"""
new_setup="""function setupWorshipStandalone() {
  const active = SpreadsheetApp.getActiveSpreadsheet();
  if (!active) throw new Error('찬양팀_DB 스프레드시트에서 확장 프로그램 > Apps Script로 연 뒤 실행해주세요.');
  const id = active.getId();
  PropertiesService.getScriptProperties().setProperty(WORSHIP_API.DB_PROP, id);

  // 웹앱에서 필요한 전체 스프레드시트 권한을 이 실행에서 미리 승인합니다.
  const ss = SpreadsheetApp.openById(id);
  worshipValidateSchema_(ss);

  // 악보 업로드에서 필요한 Drive 권한도 함께 승인합니다.
  DriveApp.getRootFolder().getName();

  return '연결/권한 승인 완료: ' + ss.getName() + ' / ' + ss.getId();
}"""
if old_setup not in s:
    raise SystemExit('setup function anchor missing')
s=s.replace(old_setup,new_setup,1)
p.write_text(s,encoding='utf-8')
print('patched setupWorshipStandalone to authorize spreadsheet+drive')

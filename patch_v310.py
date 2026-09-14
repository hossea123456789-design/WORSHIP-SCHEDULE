from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'missing patch target: {label}')
    s=s.replace(old,new,1)

rep("const APP_VERSION='v3.9.2';","const APP_VERSION='v3.10.0';",'version')

rep("function monthKey(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)}\nfunction addDays(d,n){const x=new Date(d);x.setDate(x.getDate()+n);return x}","""function monthKey(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)}
function normalizeDateKey(v){
  if(v==null||v==='')return'';
  if(v instanceof Date&&!isNaN(v))return keyOf(v);
  const s=String(v).trim();
  const m=s.match(/^(\\d{4})[-\\/.](\\d{1,2})[-\\/.](\\d{1,2})/);
  if(m)return `${m[1]}-${pad(m[2])}-${pad(m[3])}`;
  return /^\\d{4}-\\d{2}-\\d{2}$/.test(s)?s:'';
}
function normalizeMonthKey(v){
  if(v==null||v==='')return'';
  if(v instanceof Date&&!isNaN(v))return monthKey(v);
  const s=String(v).trim();
  const m=s.match(/^(\\d{4})[-\\/.](\\d{1,2})/);
  if(m)return `${m[1]}-${pad(m[2])}`;
  return /^\\d{4}-\\d{2}$/.test(s)?s:'';
}
function addMonths(d,n){return new Date(d.getFullYear(),d.getMonth()+n,1)}
function addDays(d,n){const x=new Date(d);x.setDate(x.getDate()+n);return x}""",'date helpers')

rep("function holidayMap(){\n  const out={};\n  STATE.holidays.forEach(h=>out[String(h.holiday_date)]={name:String(h.holiday_name||''),type:String(h.holiday_type||'')});\n  return out;\n}","""function holidayMap(){
  const out={};
  STATE.holidays.forEach(h=>{
    const k=normalizeDateKey(h&&h.holiday_date);
    if(k)out[k]={name:String(h.holiday_name||''),type:String(h.holiday_type||'')};
  });
  return out;
}

function horizonStartMonth(){
  const d=new Date(currentTodayKey()+'T00:00:00');
  return new Date(d.getFullYear(),d.getMonth(),1);
}
function horizonEndMonth(){return addMonths(horizonStartMonth(),12)}
function horizonEndKey(){return monthKey(horizonEndMonth())}
function isBeyondHorizon(mk){return monthNum(mk)>monthNum(horizonEndKey())}

let syncProgressTimer=null;
function stopSyncProgress(){if(syncProgressTimer){clearInterval(syncProgressTimer);syncProgressTimer=null}}
function setSyncProgress(pct,label,cached=!!STATE){
  const p=Math.max(0,Math.min(100,Math.round(Number(pct)||0)));
  const prefix=cached?'캐시 데이터 표시 · ':'';
  setProcess(`${prefix}동기화 ${p}% · ${label}`,p>=100?'ok':'working');
}
function startSyncProgress(cached=!!STATE){
  stopSyncProgress();
  const started=performance.now();
  setSyncProgress(cached?8:5,cached?'서버 최신 데이터 확인':'서버 연결 준비',cached);
  syncProgressTimer=setInterval(()=>{
    const sec=(performance.now()-started)/1000;
    let pct,label;
    if(sec<1){pct=cached?18:15;label='서버 요청 전송'}
    else if(sec<3){pct=35+sec*7;label='서버 응답 대기'}
    else if(sec<7){pct=56+(sec-3)*5;label='일정 데이터 동기화'}
    else{pct=Math.min(88,76+(sec-7)*2);label='서버 처리 완료 대기'}
    setSyncProgress(pct,label,cached);
  },500);
}""",'holiday and progress')

rep("""  readInFlight=true;
  const started=performance.now();
  if(!silentFailure){
    setProcess(STATE?'동기화 중…':'연결 중…','working');
    clearConnectionError();
  }
  logEvent('INFO',silentFailure?'BOOTSTRAP_BG_START':'BOOTSTRAP_START',`cached=${!!STATE}`);""","""  readInFlight=true;
  const started=performance.now();
  const hadState=!!STATE;
  if(!silentFailure){
    startSyncProgress(hadState);
    clearConnectionError();
  }
  logEvent('INFO',silentFailure?'BOOTSTRAP_BG_START':'BOOTSTRAP_START',`cached=${hadState}`);""",'bootstrap start')

rep("""    STATE=res.data;
    pending.forEach(applyOptimistic);
    cacheState();
    needsFullRefresh=false;

    const today=new Date((STATE.serverToday||keyOf(new Date()))+'T00:00:00');""","""    if(!silentFailure)setSyncProgress(92,'서버 응답 수신',hadState);
    STATE=res.data;
    pending.forEach(applyOptimistic);
    if(!silentFailure)setSyncProgress(96,'로컬 캐시 갱신',hadState);
    cacheState();
    needsFullRefresh=false;

    const today=new Date((STATE.serverToday||keyOf(new Date()))+'T00:00:00');""",'bootstrap response')

rep("""    renderAll();
    clearConnectionError();
    if(!silentFailure||['동기화 중…','연결 중…','오프라인','동기화 실패 · 캐시 사용'].includes(processStatus)){
      setProcess('연결 완료','ok');
    }
    logEvent('INFO',silentFailure?'BOOTSTRAP_BG_OK':'BOOTSTRAP_OK',`ms=${Math.round(performance.now()-started)} revision=${STATE.revision}`);""","""    if(!silentFailure)setSyncProgress(99,'화면 갱신',hadState);
    renderAll();
    clearConnectionError();
    if(!silentFailure){
      stopSyncProgress();
      setSyncProgress(100,'최신 데이터 반영 완료',false);
      setTimeout(()=>{if(!readInFlight&&!flushing&&!pending.length)setProcess('연결 완료','ok')},900);
    }else if(['동기화 중…','연결 중…','오프라인','동기화 실패 · 캐시 사용'].includes(processStatus)){
      setProcess('연결 완료','ok');
    }
    logEvent('INFO',silentFailure?'BOOTSTRAP_BG_OK':'BOOTSTRAP_OK',`ms=${Math.round(performance.now()-started)} revision=${STATE.revision}`);""",'bootstrap complete')

rep("""  }finally{
    readInFlight=false;""","""  }finally{
    if(!silentFailure&&readInFlight&&processStatus.includes('동기화'))stopSyncProgress();
    readInFlight=false;""",'bootstrap finally')

rep("""function selectedDates(mk){
  const map={};
  defaultSundays(mk).forEach(k=>map[k]=true);

  STATE.events.forEach(e=>{
    const date=String(e.event_date||'');
    if(date.slice(0,7)===mk)map[date]=isActive(e.active);
  });

  return Object.keys(map).filter(k=>map[k]).sort();
}""","""function selectedDates(mk){
  if(isBeyondHorizon(mk))return[];
  const map={};
  defaultSundays(mk).forEach(k=>map[k]=true);

  STATE.events.forEach(e=>{
    const date=normalizeDateKey(e&&e.event_date);
    if(date&&date.slice(0,7)===mk)map[date]=isActive(e.active);
  });

  return Object.keys(map).filter(k=>map[k]&&/^\\d{4}-\\d{2}-\\d{2}$/.test(k)).sort();
}""",'selectedDates')

rep("""function latestBase(mk){
  const target=monthNum(mk);
  const months=[...new Set(
    STATE.rotationBase
      .filter(r=>isActive(r.active))
      .map(r=>String(r.base_month||''))
      .filter(x=>/^\\d{4}-\\d{2}$/.test(x)&&monthNum(x)<=target)
  )].sort((a,b)=>monthNum(a)-monthNum(b));

  return months.length?months[months.length-1]:'';
}""","""function latestBase(mk){
  if(isBeyondHorizon(mk))return'';
  const target=monthNum(mk);
  const months=[...new Set(
    STATE.rotationBase
      .filter(r=>isActive(r.active))
      .map(r=>normalizeMonthKey(r&&r.base_month))
      .filter(x=>/^\\d{4}-\\d{2}$/.test(x)&&monthNum(x)<=target)
  )].sort((a,b)=>monthNum(a)-monthNum(b));

  return months.length?months[months.length-1]:'';
}""",'latestBase')

rep("""  return STATE.assignments
    .filter(a=>isActive(a.active)&&String(a.event_date)===date&&String(a.role_id)===String(roleId))""","""  return STATE.assignments
    .filter(a=>isActive(a.active)&&normalizeDateKey(a.event_date)===date&&String(a.role_id)===String(roleId))""",'explicit assignments')

rep("""  const indices=[...new Set(
    STATE.rotationBase
      .filter(r=>isActive(r.active)&&String(r.base_month)===base)
      .map(r=>Number(r.event_index||0))
  )].sort((a,b)=>a-b);""","""  const indices=[...new Set(
    STATE.rotationBase
      .filter(r=>isActive(r.active)&&normalizeMonthKey(r.base_month)===base)
      .map(r=>Number(r.event_index||0))
      .filter(n=>Number.isFinite(n)&&n>0)
  )].sort((a,b)=>a-b);""",'rotation indices')

rep("""      isActive(r.active)&&
      String(r.base_month)===base&&""","""      isActive(r.active)&&
      normalizeMonthKey(r.base_month)===base&&""",'rotation rows')

rep("""function upcomingWorshipDates(count=2){
  const today=currentTodayKey();
  const start=new Date(today+'T00:00:00');
  const out=[];
  let y=start.getFullYear(),m=start.getMonth();

  for(let step=0;step<18&&out.length<count;step++){
    const mk=`${y}-${String(m+1).padStart(2,'0')}`;
    selectedDates(mk).forEach(date=>{
      if(date>=today&&!out.includes(date))out.push(date);
    });
    m++;
    if(m>=12){m=0;y++}
  }

  return out.sort().slice(0,count);
}""","""function upcomingWorshipDates(count=2){
  const today=currentTodayKey();
  const start=new Date(today+'T00:00:00');
  const out=[];
  let y=start.getFullYear(),m=start.getMonth();
  const end=horizonEndKey();

  for(let step=0;step<=12&&out.length<count;step++){
    const mk=`${y}-${String(m+1).padStart(2,'0')}`;
    if(monthNum(mk)>monthNum(end))break;
    selectedDates(mk).forEach(date=>{
      if(date>=today&&!out.includes(date))out.push(date);
    });
    m++;
    if(m>=12){m=0;y++}
  }

  return out.sort().slice(0,count);
}""",'upcoming horizon')

rep("""  STATE.events=Array.isArray(STATE.events)?STATE.events.filter(Boolean):[];
  STATE.assignments=Array.isArray(STATE.assignments)?STATE.assignments.filter(Boolean):[];
  STATE.rotationBase=Array.isArray(STATE.rotationBase)?STATE.rotationBase.filter(Boolean):[];
  STATE.holidays=Array.isArray(STATE.holidays)?STATE.holidays.filter(Boolean):[];""","""  STATE.events=Array.isArray(STATE.events)?STATE.events.filter(Boolean).map(x=>({...x,event_date:normalizeDateKey(x.event_date)||x.event_date})):[];
  STATE.assignments=Array.isArray(STATE.assignments)?STATE.assignments.filter(Boolean).map(x=>({...x,event_date:normalizeDateKey(x.event_date)||x.event_date})):[];
  STATE.rotationBase=Array.isArray(STATE.rotationBase)?STATE.rotationBase.filter(Boolean).map(x=>({...x,base_month:normalizeMonthKey(x.base_month)||x.base_month})):[];
  STATE.holidays=Array.isArray(STATE.holidays)?STATE.holidays.filter(Boolean).map(x=>({...x,holiday_date:normalizeDateKey(x.holiday_date)||x.holiday_date})):[];""",'state normalization')

rep("""  document.getElementById('monthTitle').textContent=`${y}년 ${m}월`;
  const completeBtn=document.getElementById('completeMonth');""","""  if(isBeyondHorizon(mk)){
    viewMonth=horizonEndMonth();
    return renderMonth();
  }
  document.getElementById('monthTitle').textContent=`${y}년 ${m}월`;
  const prevBtn=document.getElementById('prevMonth');
  const nextBtn=document.getElementById('nextMonth');
  if(prevBtn)prevBtn.disabled=false;
  if(nextBtn){nextBtn.disabled=monthNum(mk)>=monthNum(horizonEndKey());nextBtn.title=nextBtn.disabled?'현재 기준 12개월까지만 자동 편성됩니다.':'';}
  const completeBtn=document.getElementById('completeMonth');""",'month horizon buttons')

rep("""  document.getElementById('rotationDesc').textContent='';
  document.getElementById('matrixInfo').textContent='';""","""  document.getElementById('rotationDesc').textContent=base?`자동 적용 범위 · ${horizonEndKey().replace('-','년 ')}월까지`:`기준 월에서 편성 완료를 누르면 이후 월에 자동 적용됩니다.`;
  document.getElementById('matrixInfo').textContent=`자동 편성 표시 범위: 현재 월부터 ${horizonEndKey().replace('-','년 ')}월까지`;
""",'rotation description')

rep("""document.getElementById('nextMonth').onclick=()=>{
  viewMonth=new Date(viewMonth.getFullYear(),viewMonth.getMonth()+1,1);
  renderMonth();
};""","""document.getElementById('nextMonth').onclick=()=>{
  const next=new Date(viewMonth.getFullYear(),viewMonth.getMonth()+1,1);
  if(monthNum(monthKey(next))>monthNum(horizonEndKey())){
    showToast(`자동 편성은 ${horizonEndKey().replace('-','년 ')}월까지 표시됩니다`);
    return;
  }
  viewMonth=next;
  renderMonth();
};""",'next month clamp')

rep("""if(hadCachedState){
  const today=new Date((STATE.serverToday||keyOf(new Date()))+'T00:00:00');
  viewMonth=new Date(today.getFullYear(),today.getMonth(),1);
  pending.forEach(applyOptimistic);
  renderAll();
  logEvent('INFO','CACHE_RENDERED',`revision=${STATE.revision}`);
  if(pending.length){
    hardConnectionDown=true;
    setProcess('저장 보류 · 서버 확인 중','working');
    startupSyncTimer=setTimeout(pollRevision,500);
  }else{
    setProcess('연결 완료','ok');
    startupSyncTimer=setTimeout(pollRevision,1200);
  }
}else{""","""if(hadCachedState){
  const today=new Date((STATE.serverToday||keyOf(new Date()))+'T00:00:00');
  viewMonth=new Date(today.getFullYear(),today.getMonth(),1);
  pending.forEach(applyOptimistic);
  renderAll();
  logEvent('INFO','CACHE_RENDERED',`revision=${STATE.revision}`);
  if(pending.length){
    hardConnectionDown=true;
    setProcess('저장 보류 · 서버 확인 중','working');
    startupSyncTimer=setTimeout(pollRevision,500);
  }else{
    setProcess('캐시 데이터 표시 · 동기화 8% · 서버 최신 데이터 확인','working');
    startupSyncTimer=setTimeout(()=>bootstrap(false,false),180);
  }
}else{""",'cached startup sync')

p.write_text(s,encoding='utf-8')
print('patched',len(s))

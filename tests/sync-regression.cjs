/* Mock regression: node tests/sync-regression.cjs */
const fs=require('node:fs');const path=require('node:path');
async function runRegression(front,schedule,score){
 const results=[],eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b),check=(name,v)=>{if(!v)throw Error('FAIL '+name);results.push(name)};
 const inline=front.slice(front.indexOf('<script>')+8,front.lastIndexOf('</script>'));
 [inline,schedule,score].forEach(x=>new Function(x));check('all three source syntax checks',true);
 const base={revision:1,roles:[{role_id:'r',role_name:'Role',color_key:'other',allow_multiple:true,active:true}],members:[{member_id:'a',member_name:'A',active:true},{member_id:'b',member_name:'B',active:true}],memberRoles:[],events:[],assignments:[],prayerOrder:[],rotationBase:[],holidays:[],config:{},honorificOptions:['집사님'],memberHonorifics:{a:'집사님',b:'집사님'}};
 const db=new Function('base',schedule+`
 const clone=x=>JSON.parse(JSON.stringify(x));let db=clone(base),receipts=Object.create(null),counter=0,fault=false,locked=false;
 const LockService={getScriptLock:()=>({tryLock:()=>{if(locked)return false;locked=true;return true},waitLock:()=>{if(locked)throw Error('lock');locked=true},releaseLock:()=>{locked=false}})};
 const SpreadsheetApp={flush(){}};
 worshipDb_=()=>db;worshipBuildBootstrapData_=()=>clone(db);worshipMutationReceipts_=()=>({...receipts});
 worshipAppendMutationLogs_=(_,items)=>items.forEach(m=>receipts[m.id]=m.type);worshipAppendMutationLog_=(_,id,client,type)=>{receipts[id]=type};
 worshipIncrementRevision_=()=>++db.revision;worshipClearSnapshot_=()=>{};worshipNow_=()=>'2026-11-26 08:00:00';worshipId_=()=>String(++counter);
 const keys={ASSIGNMENTS:'assignments',EVENTS:'events',ROLES:'roles',MEMBERS:'members',MEMBER_ROLES:'memberRoles',PRAYER_ORDER:'prayerOrder',ROTATION_BASE:'rotationBase'};
 worshipReadTable_=(_,sheet)=>({sheet,objects:clone(db[keys[sheet]]||[]),dirty:false});worshipWriteTable_=t=>{if(!fault)db[keys[t.sheet]]=clone(t.objects)};
 return {state:()=>clone(db),target:worshipTarget_,single:worshipMutate_,batch:worshipMutateBatch_,readback:worshipReadback_,fault:v=>fault=v,receipts:()=>({...receipts})};
 `)(base);
 const m=(id,date,memberIds,baseline=null)=>({id:'mu_test'+String(id).padStart(4,'0'),clientId:'test',type:'assignmentSet',payload:{date,roleId:'r',memberIds},base:baseline,expectedRevision:1});
 const a=m(1,'2026-11-29',['a']),b=m(2,'2026-12-06',['b']);
 check('initial DB verification',db.single(a).ok&&db.receipts()[a.id]==='verified:assignmentSet');
 check('different targets merge across revisions',db.single(b).ok&&db.state().assignments.filter(x=>x.active).length===2);
 const rev=db.state().revision;check('duplicate mutation replay',db.single(a).duplicate&&db.state().revision===rev);
 check('same target conflicting change rejected',db.single(m(3,'2026-11-29',['b'])).conflict===true);
 check('same desired value is not false conflict',db.single(m(4,'2026-11-29',['a'])).ok);
 const clear=m(5,'2026-11-29',[],['a']);check('explicit clear persists',db.single(clear).ok&&eq(db.target(db.state(),clear),[]));
 check('stale writer cannot restore cleared value',db.single(m(6,'2026-11-29',['b'],['a'])).conflict);
 const ba=m(7,'2026-12-13',['a']),bb=m(8,'2026-12-20',['b']);
 check('batch distinct targets and receipts',db.batch({items:[ba,bb],expectedRevision:1}).appliedCount===2&&db.receipts()[ba.id]&&db.receipts()[bb.id]);
 const b1=m(9,'2026-12-27',['a']),b2=m(10,'2026-12-27',['b'],['a']);
 check('batch consecutive same target',db.batch({items:[b1,b2],expectedRevision:1}).ok&&eq(db.target(db.state(),b2),['b']));
 const rb=db.readback(JSON.stringify([ba.id,bb.id,'mu_missing']));check('readback verified IDs and DB revision',rb.source==='sheets'&&eq(rb.verifiedIds,[ba.id,bb.id])&&rb.revision===db.state().revision);
 db.fault(true);const bad=m(11,'2027-01-03',['a']);check('failed DB write does not issue receipt',!db.single(bad).ok&&!db.receipts()[bad.id]);db.fault(false);
 const ev={id:'mu_test0012',clientId:'test',type:'eventSet',payload:{date:'2026-12-25',active:true,title:''},base:null,expectedRevision:1};
 check('date event merges',db.single(ev).ok&&eq(db.target(db.state(),ev),[true,'']));
 const sm=new Function(score+`
 const clone=x=>JSON.parse(JSON.stringify(x));let doc={links:['https://www.youtube.com/watch?v=a'],revision:1,receipts:[]};
 const LockService={getScriptLock:()=>({waitLock(){},releaseLock(){}})};
 readLinkDocument_=()=>clone(doc);writeLinkDocument_=d=>{doc=clone(d)};
 return {set:setAfterYoutubeLinks_,read:getAfterYoutubeLinks_,state:()=>clone(doc)};
 `)();
 const A='https://www.youtube.com/watch?v=a',B='https://www.youtube.com/watch?v=b',C='https://www.youtube.com/watch?v=c';
 const patch=(id,adds,removes)=>({operationId:id,addsJson:JSON.stringify(adds),removesJson:JSON.stringify(removes)});
 check('link delta adds without replacement',eq(sm.set(patch('link_test0001',[B],[])).links,[A,B]));
 check('remote addition and deletion preserve others',eq(sm.set(patch('link_test0002',[C],[A])).links,[B,C]));
 const sr=sm.state().revision;check('duplicate link operation',sm.set(patch('link_test0001',[B],[])).duplicate&&sm.state().revision===sr);
 check('link readback receipt',eq(sm.read('link_test0002').verifiedOperationIds,['link_test0002']));
 function extract(name){const i=inline.search(new RegExp('(?:^|\\n)(?:async )?function '+name+'\\(')),j=inline.indexOf('function ',i),start=inline.slice(i,j).includes('async')?inline.indexOf('async ',i):j,end=inline.indexOf('\n}',j);if(i<0||end<0)throw Error(name);return inline.slice(start,end+2)}
 const src=['verifyScheduleItems_','flushQueue','enqueueItems_','safeApplyServerState_','validScheduleState_'].map(extract).join('\n');
 const client=new Function('base',src+`
 let STATE=JSON.parse(JSON.stringify(base)),serverState_=JSON.parse(JSON.stringify(base)),pending=[],flushing=false,readInFlight=false,retryTimer=null,serverFresh=true,hardConnectionDown=false,readFailureStreak=0,needsFullRefresh=false;
 let storage={},events=[],writes=0,allowWrite=true,serverVersion='v3.22.0',verifyOk=true,inject=null,readVersion=2;
 const serverVersions_={schedule:'legacy'},navigator={onLine:true},MUTATE_TIMEOUT_MS=1000;
 const cloneData_=x=>JSON.parse(JSON.stringify(x)),setTimeout=(f,d)=>1,clearTimeout=()=>{};
 const safeSet=(k,v)=>{if(!allowWrite)return false;storage[k]=v;return true};
 const logEvent=(...v)=>events.push(v),showToast=()=>{},setProcess=(...v)=>events.push(['STATUS',...v]),applyOptimistic=()=>{},renderAll=()=>{},renderSynced_=()=>{},refreshMonthWriteState_=()=>{},cacheState=()=>{};
 const saveQueue=()=>safeSet('queue',JSON.stringify(pending)),scheduleServerReady_=()=>serverVersion==='v3.22.0',observeServer_=()=>{},quarantineItems_=()=>{throw Error('unexpected conflict')};
 const jsonp=async()=>{writes++;if(inject)pending.push(inject);return {ok:true,serverVersion:'v3.22.0',revision:2}};
 const readApi=async(action,params)=>({ok:verifyOk,serverVersion:'v3.22.0',source:'sheets',data:{...base,revision:readVersion},verifiedIds:verifyOk?JSON.parse(params.ids):[]});
 return {enqueue:enqueueItems_,flush:flushQueue,state:()=>STATE,pending:()=>pending.slice(),writes:()=>writes,events:()=>events.slice(),setup:o=>{if(o.pending)pending=o.pending;if('allowWrite'in o)allowWrite=o.allowWrite;if('serverVersion'in o)serverVersion=o.serverVersion;if('verifyOk'in o)verifyOk=o.verifyOk;if('inject'in o)inject=o.inject;if('readVersion'in o)readVersion=o.readVersion},apply:safeApplyServerState_};
 `)(base);
 const first={...a,attempts:0};client.setup({allowWrite:false});check('local write failure does not enqueue',!client.enqueue([first])&&client.pending().length===0);
 client.setup({allowWrite:true,serverVersion:'legacy'});check('local durable queue before network',client.enqueue([first])&&client.pending().length===1);
 await client.flush();check('old server blocks send and preserves pending',client.writes()===0&&client.pending().length===1);
 client.setup({serverVersion:'v3.22.0',verifyOk:false});await client.flush();check('ACK without readback preserves ID',client.pending().length===1&&client.pending()[0].ackRevision===2&&client.writes()===1);
 client.setup({verifyOk:true,readVersion:1});await client.flush();check('older readback preserves pending',client.pending().length===1&&client.writes()===1);
 client.setup({readVersion:2});await client.flush();check('ACK retry reads only and clears verified ID',client.pending().length===0&&client.writes()===1&&client.state().revision===2);
 const later=m(14,'2027-01-17',['b']);client.setup({pending:[m(13,'2027-01-10',['a'])],inject:later,readVersion:3});await client.flush();check('additional edit during save remains queued',client.pending().length===1&&client.pending()[0].id===later.id);
 let rejected=false;try{client.apply({...base,revision:1})}catch(_){rejected=true}check('older state rejected',rejected&&client.state().revision===3);
 rejected=false;try{client.apply({revision:4,roles:[]})}catch(_){rejected=true}check('malformed data rejected',rejected&&client.state().revision===3);
 return results;
}
const root=path.resolve(__dirname,'..');runRegression(...['index.html','Code_FAST_SCHEDULE.gs.txt','WORSHIP_SCORE_API_Code.gs.txt'].map(p=>fs.readFileSync(path.join(root,p),'utf8'))).then(r=>{console.log(r.map((x,i)=>'PASS '+(i+1)+': '+x).join('\n'));console.log(r.length+' checks passed')}).catch(e=>{console.error(e);process.exitCode=1});

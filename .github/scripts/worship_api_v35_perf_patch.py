from pathlib import Path
p=Path('WorshipApi_RECOVERY_v35.gs.txt')
s=p.read_text(encoding='utf-8')
old="""    const ss = worshipDb_();
    worshipValidateSchema_(ss);

    if (worshipMutationAlreadyApplied_(ss, mutationId)) {"""
new="""    const ss = worshipDb_();

    if (worshipMutationAlreadyApplied_(ss, mutationId)) {"""
if s.count(old)!=1:
    raise SystemExit(f'mutate schema anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)
old2="worshipMonthNum_(x) < target"
if s.count(old2)!=1:
    raise SystemExit(f'rotation base anchor mismatch: {s.count(old2)}')
s=s.replace(old2,"worshipMonthNum_(x) <= target",1)
p.write_text(s,encoding='utf-8')
print('patched WorshipApi recovery')

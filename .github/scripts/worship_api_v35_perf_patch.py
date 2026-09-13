from pathlib import Path
import re

p=Path('WorshipApi_RECOVERY_v35.gs.txt')
s=p.read_text(encoding='utf-8')

# 저장 시 전체 10개 시트 스키마를 매번 재검증하지 않습니다.
# bootstrap에서는 검증을 유지하고 mutate 내부의 검증만 제거합니다.
pattern=r"(function worshipMutate_\(mutation\) \{[\s\S]*?const ss = worshipDb_\(\);)\s*worshipValidateSchema_\(ss\);"
s,n=re.subn(pattern,r"\1",s,count=1)
if n!=1:
    raise SystemExit(f'mutate schema patch count={n}')

# 같은 달을 다시 '편성 완료'할 때 기존 해당 월 로테이션도 기준으로 사용할 수 있게 합니다.
patterns=[
    r'worshipMonthNum_\(x\)\s*<\s*target',
]
changed=0
for pat in patterns:
    s,n=re.subn(pat,'worshipMonthNum_(x) <= target',s,count=1)
    changed+=n
    if n: break
if changed!=1:
    raise SystemExit(f'rotation base patch count={changed}')

p.write_text(s,encoding='utf-8')
print('patched WorshipApi recovery')

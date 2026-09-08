#!/usr/bin/env python3
"""Narrow individual structured-evidence clauses against real-run replays."""
import argparse,difflib,hashlib,json,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--f1',type=Path,required=True);p.add_argument('--positive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
changes=[
 ('success-caps-on-failure',"    valid={r['id']", "    bind_census(inventory,counts)\n    valid={r['id']",'Applies successful probe limits to diagnostics'),
 ('counter-omission',"    if dict(actual)!=", "    if not counts and dict(actual)!=",'Compares counter only when empty'),
 ('counter-and-ordinal-omission',"    if dict(actual)!=", "    if not counts and dict(actual)!=",'Checks counter and ordinal completeness only for empty evidence'),
 ('ordinal-gap',"    if seen!=", "    if not seen and seen!=",'Checks ordinal set only when empty'),
 ('receipt-forgery',"    if sorted(records,key=lambda r:r['id'])!=", "    if len(records)<2 and sorted(records,key=lambda r:r['id'])!=",'Compares private ledger only for tiny receipt sets'),
 ('no-result-on-failure',"    (out/'result.json').write_text(json.dumps(result,indent=2))", "    if process_exit==0:(out/'result.json').write_text(json.dumps(result,indent=2))",'Persists results for successful executions only'),
 ('diagnostic-errors-as-public-failure',"errors=['census: '+str(e)]; refusal='evidence_error'", "errors=['census: '+str(e)]; refusal='public_failed'",'Launders invalid census into public failure'),
 ('ignore-driver-state',"    if result.get('execution',{}).get('state')!='terminated':return False", "    if result.get('execution',{}).get('state')=='timeout':return False",'Refuses timeout but admits unrelated driver error'),
 ('ignore-census-state'," or census.get('state')!='valid'", "",'Keeps mode/cause but ignores census validity'),
 ('ignore-completeness-kind'," or census.get('complete_publication') is not False", "",'Admits a complete-publication claim on F1 failure'),
 ('ignore-f1-marker',"'generated SVG contains a PlantUML render failure' in log and ", "",'Accepts unrelated failures with dot/comparator evidence'),
 ('ignore-dot-failure',"any(r.get('tool')=='dot' and r.get('exit')==1 for r in private) and ", "",'Accepts comparator error without a failed Graphviz execution'),
 ('ignore-comparator-failure'," and any(r.get('scope','').startswith('compare:') and r.get('exit')==1 for r in private)", "",'Accepts diagnostic marker without failed comparator launch'),
]
rows=[];original=(H/'execution.py').read_text()
for name,before,after,bound in changes:
    folder=a.out/name;folder.mkdir();assert original.count(before)==1,name
    variant=original.replace(before,after)
    if name=='counter-and-ordinal-omission':variant=variant.replace('    if seen!=','    if not seen and seen!=')
    for f in H.glob('*.py'):shutil.copyfile(f,folder/f.name)
    (folder/'execution.py').write_text(variant)
    (folder/'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),variant.splitlines(True),fromfile='execution.py',tofile='execution.py')))
    argv=[sys.executable,'-B',str(folder/'structured_tests.py'),'--source',str(a.source.resolve()),'--f1',str(a.f1.resolve()),'--positive',str(a.positive.resolve()),'--out',str(folder/'tests')]
    proc=subprocess.run(argv,capture_output=True,text=True,timeout=30)
    (folder/'command.log').write_text(proc.stdout+proc.stderr)
    report=folder/'tests/report.json';tests=json.loads(report.read_text()) if report.is_file() else []
    failed=[r['test'] for r in tests if not r['passed']]
    killed=proc.returncode==1 and bool(failed)
    row=dict(mutant=name,narrows_to=bound,argv=argv,exit=proc.returncode,killed=killed,named_failing_tests=failed,before_sha256=hashlib.sha256(original.encode()).hexdigest(),after_sha256=hashlib.sha256(variant.encode()).hexdigest())
    if not killed:row['survivor_bound']=('Counter equality is subsumed by the exact ordinal-set equality against the same census; the combined counter-and-ordinal narrowing is separately attacked.' if name=='counter-omission' else 'This replay failed to distinguish the narrowed clause; no behavioral kill credited.')
    rows.append(row)
(a.out/'report.json').write_text(json.dumps(rows,indent=2));print(json.dumps(dict(killed=sum(r['killed'] for r in rows),total=len(rows),survivors=[r['mutant'] for r in rows if not r['killed']])));sys.exit(0 if all(r['killed'] or r['mutant']=='counter-omission' for r in rows) else 1)

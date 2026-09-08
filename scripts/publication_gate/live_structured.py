#!/usr/bin/env python3
"""Real-public F1 with post-execution evidence/driver faults in disposable gates.

A failure of controls.py is required: these faults are NOT successful F1 controls.
"""
import argparse,difflib,hashlib,json,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--branch',choices=['path','home'],required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[]
for fault,insert,want in [
 ('malformed-census',"    (out/'counter.json').write_text('{')\n",'evidence_error'),
 ('read-failed-census',"    (out/'counter.json').chmod(0)\n",'evidence_error'),
 ('unrelated-exception',"    raise RuntimeError('injected after real public execution')\n",'driver_error'),
 ('missing-result',"    return 1\n",None),
]:
    folder=a.out/fault;folder.mkdir();gate=folder/'gate';shutil.copytree(H,gate,ignore=shutil.ignore_patterns('__pycache__'))
    original=(gate/'drive.py').read_text();anchor='    result=finalize(out,inventory,expected,proc.returncode)';assert original.count(anchor)==1
    variant=original.replace(anchor,insert+anchor);(gate/'drive.py').write_text(variant)
    (folder/'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),variant.splitlines(True),fromfile='drive.py',tofile='drive.py')))
    cmd=[sys.executable,'-B',str(gate/'controls.py'),'--source',str(a.source.resolve()),'--out',str(folder/'controls'),'--start','2','--count','1','--branch',a.branch]
    with (folder/'command.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=220)
    report=json.loads((folder/'controls/controls-2.json').read_text());control=report[0];result=control['result'];log=(folder/'controls/f1/public.log').read_text()
    passed=r.returncode==1 and control['passed'] is False and 'generated SVG contains a PlantUML render failure' in log and ((result is None and control['result_read_state']=='missing') if want is None else result.get('refusal')==want)
    counter=folder/'controls/f1/counter.json'
    if counter.exists():counter.chmod(0o644)
    rows.append(dict(test='test_real_f1_does_not_credit_'+fault,branch=a.branch,argv=cmd,exit=r.returncode,expected_exit=1,passed=passed,result=result,before_sha256=hashlib.sha256(original.encode()).hexdigest(),after_sha256=hashlib.sha256(variant.encode()).hexdigest(),bound='Post-execution fault injection; real public F1 executes before evidence is damaged. Expected failure of control assertion is not a publication behavioral kill.'))
(a.out/'report.json').write_text(json.dumps(rows,indent=2));print(json.dumps(dict(passed=sum(r['passed'] for r in rows),total=len(rows))));sys.exit(0 if all(r['passed'] for r in rows) else 1)

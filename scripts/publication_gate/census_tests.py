#!/usr/bin/env python3
"""Counter absence/read failure/malformed data must fail closed."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[]
for fault in ['missing','unreadable','malformed','boolean','negative','unknown-scope','over-count']:
    run=a.out/fault;run.mkdir()
    for file in ['counter.json','inventory.json','expected.json','result.json','receipts.jsonl','private.jsonl']:shutil.copyfile(a.run/file,run/file)
    c=run/'counter.json'; data=json.loads(c.read_text()); key='render:c4/dot:probe'
    if fault=='missing':c.unlink()
    elif fault=='unreadable':c.chmod(0)
    elif fault=='malformed':c.write_text('{')
    else:
        if fault=='boolean':data[key]=True
        if fault=='negative':data[key]=-1
        if fault=='unknown-scope':data['injected/dot:probe']=1
        if fault=='over-count':data[key]=100
        c.write_text(json.dumps(data))
    cmd=[sys.executable,'-B',str(H/'assert_case.py'),'--name','test_census_'+fault,'--expected','1',sys.executable,'-B',str(H/'evaluate.py'),'--source',str(a.source.resolve()),'--run',str(run.resolve())]
    r=subprocess.run(cmd,capture_output=True,text=True); rows.append(dict(test='test_census_'+fault,argv=cmd,exit=r.returncode,passed=r.returncode==0,observation=json.loads(r.stdout)))
    if fault=='unreadable':c.chmod(0o644)
(a.out/'report.json').write_text(json.dumps(rows,indent=2));print(sum(r['passed'] for r in rows),'/',len(rows));sys.exit(0 if all(r['passed'] for r in rows) else 1)

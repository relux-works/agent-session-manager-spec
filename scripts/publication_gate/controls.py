#!/usr/bin/env python3
"""Actual full-public negative and neutral controls; bounded subset selection."""
import argparse,json,subprocess,sys
from pathlib import Path
from execution import read_evidence,control_passed
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=3);p.add_argument('--branch',choices=['path','home'],default='path');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
cases=[('absent-caller',1,'public caller missing'),('java11',1,'class file version 61.0'),('f1',1,'SVG contains a PlantUML render failure'),('ambient-ax',0,'publication-no-ax-environment: ax=absent'),('ambient-dot',0,'publication-no-ax-full-entrypoint: exit=0'),('forbidden-ax',1,'no-AX control is invalid: ax is present')]
rows=[]
for control,want,marker in cases[a.start:a.start+a.count]:
    out=a.out/control
    argv=[sys.executable,'-B',str(H/'drive.py'),'--source',str(a.source.resolve()),'--out',str(out.resolve()),'--control',control,'--branch',a.branch]
    with (a.out/(control+'.log')).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
    result_state=read_evidence(out/'result.json');result=result_state['value']
    log_state=read_evidence(out/'public.log','text');log=log_state['value'] or ''
    private=read_evidence(out/'private.jsonl','jsonl')
    passed=control_passed(control,r.returncode,result,log,private['value'] or [])
    row=dict(test='test_public_'+control,argv=argv,exit=r.returncode,expected_exit=want,passed=passed,result=result,result_read_state=result_state['state']);rows.append(row);print(control,'exit',r.returncode,'passed',passed,flush=True)
(a.out/f'controls-{a.start}.json').write_text(json.dumps(rows,indent=2));sys.exit(0 if rows and all(r['passed'] for r in rows) else 1)

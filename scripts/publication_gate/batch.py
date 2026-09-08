#!/usr/bin/env python3
"""Bounded independent real-public mutation batches (at most eight cases)."""
import argparse,concurrent.futures,json,subprocess,sys,time
from pathlib import Path
from inventory import derive
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--branch',required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--count',type=int,default=8)
a=p.parse_args(); assert 0<a.count<=8
inventory=derive(a.source); cases=[('substitute',r['id']) for r in inventory['invocations']]+[('jar-substitute',r['id']) for r in inventory['invocations'] if r['tool']=='java']
subset=list(enumerate(cases))[a.start:a.start+a.count]; assert subset
out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
def execute(item):
    i,(kind,key)=item; name=f'{a.branch}-{i:02d}-{kind}'; run=out/name
    argv=[sys.executable,'-B',str(HERE/'drive.py'),'--source',str(a.source.resolve()),'--out',str(run),'--branch',a.branch,'--kind',kind,'--target-id',key]
    start=time.monotonic()
    with (out/(name+'.log')).open('w') as f: proc=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
    result=json.loads((run/'result.json').read_text()) if (run/'result.json').exists() else {}
    killed=proc.returncode==1 and result.get('public',{}).get('exit')==0 and result.get('applied')==[key] and bool(result.get('errors'))
    row=dict(test=f'test_{a.branch}_complete_identity[{key}]',mutant=name,narrows_to='all required identities except '+key,argv=argv,exit=proc.returncode,seconds=time.monotonic()-start,killed=killed,named_failing_test=f'test_{a.branch}_complete_identity[{key}]' if killed else None,result=result)
    if not killed: row['survivor_bound']='No behavioral kill established; inspect actual application, public exit and errors.'
    print(name,'exit',proc.returncode,'killed',killed,flush=True); return row
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: rows=list(pool.map(execute,subset))
report=out/f'{a.branch}-batch-{a.start:02d}.json';report.write_text(json.dumps(rows,indent=2))
print('killed',sum(r['killed'] for r in rows),'/',len(rows),flush=True)
sys.exit(0 if all(r['killed'] for r in rows) else 1)

#!/usr/bin/env python3
import argparse,difflib,json,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=a.out/'source';shutil.copytree(a.source,source);readme=source/'README.md';readme.write_text(readme.read_text()+'\n')
original=(H/'evaluate.py').read_text();before="inventory['source_hashes'] != binding['source_hashes']";after="inventory['source_hashes']['run_validation.sh'] != binding['source_hashes']['run_validation.sh']";assert original.count(before)==1
mutant=a.out/'evaluate_mutant.py';mutant.write_text(original.replace(before,after));shutil.copyfile(H/'inventory.py',a.out/'inventory.py')
(a.out/'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),mutant.read_text().splitlines(True),fromfile='evaluate.py',tofile='evaluate_mutant.py')))
rows=[]
for name,exe,want in [('test_refuses_wrong_source',H/'evaluate.py',0),('test_refuses_wrong_source_narrowed_to_shell',mutant,1)]:
    argv=[sys.executable,'-B',str(H/'assert_case.py'),'--name',name,'--expected','1',sys.executable,'-B',str(exe.resolve()),'--source',str(source.resolve()),'--run',str(a.run.resolve())]
    r=subprocess.run(argv,capture_output=True,text=True);rows.append(dict(test=name,argv=argv,exit=r.returncode,expected_exit=want,passed=r.returncode==want,observation=json.loads(r.stdout)))
(a.out/'report.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows));sys.exit(0 if all(r['passed'] for r in rows) else 1)

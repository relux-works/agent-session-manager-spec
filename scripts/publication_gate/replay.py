#!/usr/bin/env python3
"""Bounded receipt/completeness tests over real-public captured launches.

These replay evidence; they do not claim to reexecute publication for each omission.
"""
import argparse,copy,json,subprocess,sys
from pathlib import Path
from inventory import derive,bind_census
from evaluate import read_records
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--section',choices=['omissions','jars','evidence','narrowing'],required=True);p.add_argument('--mutations',type=Path)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
records=read_records(a.run/'receipts.jsonl'); trusted=read_records(a.run/'private.jsonl');inv=bind_census(derive(a.source),json.loads((a.run/'counter.json').read_text()));rows=[]
def write(path,data):path.write_text(''.join(json.dumps(r)+'\n' for r in data))
def run(name,rs=None,ts=None,narrow=None,base=None,expected=1,mutant=False,fault=None):
    folder=a.out/name.replace('/','_').replace(':','-');folder.mkdir()
    receipt=folder/'receipt.jsonl';private=folder/'private.jsonl'
    write(receipt,records if rs is None else rs);write(private,trusted if ts is None else ts)
    evidence=private if fault and fault.startswith('private-') else receipt
    fault=fault.removeprefix('private-') if fault else fault
    if fault=='missing':evidence.unlink()
    if fault=='malformed':evidence.write_text('{not json}\n')
    if fault=='unreadable':evidence.chmod(0)
    if fault=='directory':evidence.unlink();evidence.mkdir()
    cmd=[sys.executable,'-B',str(HERE/'evaluate.py'),'--source',str(a.source.resolve()),'--run',str((base or a.run).resolve()),'--receipts',str(receipt.resolve()),'--private',str(private.resolve())]
    if narrow:
        original=(HERE/'evaluate.py').read_text(); key=repr(narrow.get('id'))
        if narrow['kind']=='omit':
            before="required=inventory['invocations']"; after="required=[r for r in inventory['invocations'] if r['id']!="+key+"]"
        elif narrow['kind']=='identity':
            before="if (record['target'],record['sha256'])!="; after="if key!="+key+" and (record['target'],record['sha256'])!="
        elif narrow['kind']=='jars':
            before="if record['artifacts']!="; after="if key!="+key+" and record['artifacts']!="
        else:
            before="if sorted(records,key=lambda r:r['id'])!="; after="if len(records)<2 and sorted(records,key=lambda r:r['id'])!="
        assert original.count(before)==1, 'mutation site must be unique'
        variant=original.replace(before,after); path=folder/'evaluate_mutant.py';path.write_text(variant)
        (folder/'inventory.py').write_bytes((HERE/'inventory.py').read_bytes())
        import difflib,hashlib
        (folder/'mutation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),variant.splitlines(True),fromfile='evaluate.py',tofile='evaluate_mutant.py')))
        (folder/'mutation.json').write_text(json.dumps(dict(change=narrow,before_sha256=hashlib.sha256(original.encode()).hexdigest(),after_sha256=hashlib.sha256(variant.encode()).hexdigest())))
        cmd[2]=str(path.resolve())
    argv=[sys.executable,'-B',str(HERE/'assert_case.py'),'--name',name,'--expected',str(expected),*cmd]
    proc=subprocess.run(argv,capture_output=True,text=True,timeout=20)
    row=dict(test=name,argv=argv,exit=proc.returncode,observation=json.loads(proc.stdout),mutant=mutant)
    if mutant:
        row.update(killed=proc.returncode==1 and row['observation']['gate_exit']==0,named_failing_test=name if proc.returncode==1 else None,narrows_to=narrow)
        if not row['killed']:row['survivor_bound']='This witness did not distinguish the narrowed clause; another refusal may subsume it.'
    else:row['passed']=proc.returncode==0
    (folder/'command.json').write_text(json.dumps(row,indent=2));rows.append(row)
    if fault=='unreadable':evidence.chmod(0o644)

if a.section=='omissions':
    for role in inv['invocations']:
        key=role['id']; filtered=[r for r in records if r['id']!=key]
        run('missing-'+key,filtered,filtered)
    run('missing-all',[],[])
elif a.section=='jars':
    for record in records:
        for path in record['artifacts']:
            changed=copy.deepcopy(records);row=next(r for r in changed if r['id']==record['id']);del row['artifacts'][path]
            run('missing-jar-'+record['id']+'-'+Path(path).name,changed,changed)
    for record in records:
        if record['tool']=='java':
            changed=copy.deepcopy(records);row=next(r for r in changed if r['id']==record['id']);row['artifacts']={k:'0'*64 for k in row['artifacts']}
            run('forged-jar-'+record['id'],changed,changed)
elif a.section=='evidence':
    run('neutral-original',expected=0);run('neutral-order',list(reversed(records)),expected=0)
    for prefix in ['', 'private-']:
        for fault in ['missing','malformed','unreadable','directory']:run(prefix+fault+'-evidence',fault=prefix+fault)
    run('duplicate-observation',records+[records[0]])
    for field in ['target','sha256','pid','argv','scope','id','artifacts','exit']:
        changed=copy.deepcopy(records);del changed[0][field];run('malformed-'+field,changed,changed)
    changed=copy.deepcopy(records);changed[0]['exit']=False
    run('malformed-boolean-exit',changed,changed)
    changed=copy.deepcopy(records);changed[0]['pid']+=100000
    run('caller-minted-receipt',changed)
    # A caller repairs target/hash fields in a truly mixed-JVM run; private ledger disagrees.
    if a.mutations:
        for index,role in enumerate(derive(a.source)['invocations']):
            if role['tool']!='java': continue
            base=a.mutations/f'{a.run.name}-{index:02d}-substitute'
            result=json.loads((base/'result.json').read_text())
            actual=read_records(base/'private.jsonl');forged=copy.deepcopy(actual)
            expected=json.loads((base/'expected.json').read_text())
            for row in forged:
                if row['id']==result['target_id']:row.update(expected['java'])
            run('forged-repair-'+result['target_id'],forged,actual,base=base)
elif a.section=='narrowing':
    for role in inv['invocations']:
        key=role['id'];filtered=[r for r in records if r['id']!=key]
        run('test_refuses_missing-'+key,filtered,filtered,narrow=dict(kind='omit',id=key),mutant=True)
    assert a.mutations
    for base in sorted(a.mutations.glob(a.run.name+'-*')):
        if not base.is_dir():continue
        result=json.loads((base/'result.json').read_text());actual=read_records(base/'private.jsonl');key=result['target_id'];kind='jars' if result['kind']=='jar-substitute' else 'identity'
        run('test_refuses_'+kind+'-'+key,actual,actual,narrow=dict(kind=kind,id=key),base=base,mutant=True)
    changed=copy.deepcopy(records);changed[0]['pid']+=100000
    run('test_refuses_forged',changed,narrow=dict(kind='trust'),mutant=True)
(a.out/'report.json').write_text(json.dumps(rows,indent=2))
passed=sum(r.get('passed',r.get('killed',False)) for r in rows)
print(json.dumps(dict(section=a.section,passed=passed,total=len(rows),survivors=[r['test'] for r in rows if not r.get('passed',r.get('killed',False))])))
sys.exit(0 if passed==len(rows) else 1)

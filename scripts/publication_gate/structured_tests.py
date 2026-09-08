#!/usr/bin/env python3
"""Bounded replay attacks on terminal evidence from actual public runs.

No renderer outputs are simulated. Replay is explicitly not a new publication.
"""
import argparse,copy,importlib.util,json,shutil,sys,traceback
from pathlib import Path
from inventory import derive
from execution import finalize,control_passed,read_evidence

def suite(source,f1,positive,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    inv=derive(source)
    def case(name,run,fault=None,want_state=None,positive_case=False):
        folder=out/name;folder.mkdir()
        for file in ['public.log','private.jsonl','counter.json']:
            shutil.copyfile(run/file,folder/file)
        expected=json.loads((run/'expected.json').read_text())
        if fault:fault(folder)
        error=None
        try:
            result=finalize(folder,inv,expected,0 if positive_case else 1)
            persisted=read_evidence(folder/'result.json')
            log=read_evidence(folder/'public.log','text')['value'] or ''
            private=read_evidence(folder/'private.jsonl','jsonl')['value'] or []
            accepted_control=control_passed('ambient-dot' if positive_case else 'f1',result['gate_exit'],result,log,private)
            passed=persisted['state']=='valid' and persisted['value']==result and (folder/'expected.json').is_file()
            if want_state:passed=passed and result['refusal']=='evidence_error' and result['gate_exit']==1 and not accepted_control and want_state(result)
            else:passed=passed and accepted_control and result['gate_exit']==(0 if positive_case else 1)
        except Exception as e:
            passed=False;error=type(e).__name__+': '+str(e);result=None
        for file in folder.iterdir():
            if file.is_file():file.chmod(0o644)
        row=dict(test=name,passed=bool(passed),result=result,error=error);rows.append(row)
    case('test_f1_structured_diagnostics',f1)
    case('test_positive_completeness',positive,positive_case=True)
    for target in ['counter.json','private.jsonl','public.log']:
        for mode in ['missing','read_failed','malformed']:
            if target=='public.log' and mode=='malformed':continue
            def fault(p,target=target,mode=mode):
                f=p/target
                if mode=='missing':f.unlink()
                elif mode=='read_failed':f.chmod(0)
                else:f.write_text('{')
            key={'counter.json':'counter','private.jsonl':'private','public.log':'log'}[target]
            case('test_'+key+'_'+mode,f1,fault,lambda r,k=key,m=mode:r['evidence'][k]['state']==m)
    for kind in ['boolean','negative','unknown','omission','inflated','ordinal','forged','malformed-process']:
        def fault(p,kind=kind):
            f=p/'counter.json';counts=json.loads(f.read_text());key='render:c4/dot:probe'
            if kind=='boolean':counts[key]=True
            if kind=='negative':counts[key]=-1
            if kind=='unknown':counts['unknown/dot:probe']=1
            if kind=='omission':del counts[key]
            if kind=='inflated':counts[key]+=1
            f.write_text(json.dumps(counts))
            if kind in ['ordinal','forged','malformed-process']:
                ledger=p/'private.jsonl';rs=[json.loads(s) for s in ledger.read_text().splitlines()]
                if kind=='ordinal':rs[0]['id']=rs[0]['id'].rsplit('#',1)[0]+'#2'
                if kind=='forged':rs[0]['pid']+=999
                if kind=='malformed-process':rs[0]['exit']=False
                ledger.write_text(''.join(json.dumps(r)+'\n' for r in rs))
                if kind=='ordinal':
                    log=p/'public.log';lines=log.read_text().splitlines();log.write_text('\n'.join('publication-tool-executions: '+json.dumps(rs) if l.startswith('publication-tool-executions: ') else l for l in lines)+'\n')
        case('test_diagnostic_'+kind,f1,fault,lambda r:r['census']['state']=='invalid')
    def overcount(p):
        f=p/'counter.json';counts=json.loads(f.read_text());counts['render:c4/dot:probe']=100;f.write_text(json.dumps(counts))
    case('test_success_probe_cap_retained',positive,overcount,lambda r:r['census']['state']=='invalid',True)
    base=json.loads((f1/'result.json').read_text());log=(f1/'public.log').read_text();private=[json.loads(s) for s in (f1/'private.jsonl').read_text().splitlines()]
    for kind in ['missing','malformed','read_failed','driver_error','census_invalid','census_complete','refusal_wrong','public_success','entrypoint_absent','marker_absent','dot_success','comparator_success','malformed-census','malformed-execution','boolean-gate-exit','execution-exit-mismatch']:
        result=copy.deepcopy(base);text=log;ledger=copy.deepcopy(private)
        if kind in ['missing','malformed','read_failed']:
            f=out/('result-'+kind+'.json')
            if kind=='malformed':f.write_text('{')
            if kind=='read_failed':f.mkdir()
            observed=read_evidence(f);result=observed['value'];assert observed['state']==kind
        if kind=='malformed-census':result['census']='invalid'
        if kind=='malformed-execution':result['execution']=[]
        if kind=='boolean-gate-exit':result['gate_exit']=True
        if kind=='execution-exit-mismatch':result['execution']['exit']=0
        if kind=='driver_error':result['execution']['state']='driver_error'
        if kind=='census_invalid':result['census']['state']='invalid'
        if kind=='census_complete':result['census']['complete_publication']=True
        if kind=='refusal_wrong':result['refusal']='evidence_error'
        if kind=='public_success':result['public']['exit']=0
        if kind=='entrypoint_absent':result['public']['entrypoint_exit']=None
        if kind=='marker_absent':text=text.replace('generated SVG contains a PlantUML render failure','unrelated failure')
        if kind=='dot_success':
            for r in ledger:
                if r['tool']=='dot':r['exit']=0
        if kind=='comparator_success':
            for r in ledger:
                if r['scope'].startswith('compare:'):r['exit']=0
        passed=not control_passed('f1',1,result,text,ledger)
        rows.append(dict(test='test_f1_refuses_'+kind,passed=passed))
    (out/'report.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(dict(passed=sum(r['passed'] for r in rows),total=len(rows),failed=[r['test'] for r in rows if not r['passed']])))
    return 0 if rows and all(r['passed'] for r in rows) else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--f1',type=Path,required=True);p.add_argument('--positive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    sys.exit(suite(a.source,a.f1,a.positive,a.out))

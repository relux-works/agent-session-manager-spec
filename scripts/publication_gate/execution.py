"""Typed terminal evidence for successful and failed public executions.

Failed runs are diagnostic observations, never a complete-publication claim.
The observer and counter remain trusted local controller inputs.
"""
import json,re
from collections import Counter
from pathlib import Path
from inventory import bind_census
from evaluate import evaluate


def read_evidence(path, kind='json'):
    try:
        text=Path(path).read_text()
    except FileNotFoundError:
        return dict(state='missing',value=None)
    except OSError as e:
        return dict(state='read_failed',value=None,detail=type(e).__name__)
    try:
        value=text if kind=='text' else ([json.loads(s) for s in text.splitlines()] if kind=='jsonl' else json.loads(text))
        if kind=='jsonl' and (not value or not all(isinstance(r,dict) for r in value)):
            raise ValueError('empty or non-object ledger')
        return dict(state='valid',value=value)
    except (ValueError,TypeError) as e:
        return dict(state='malformed',value=None,detail=str(e))


def diagnostic_census(inventory,counts,records,trusted):
    """Account for actual terminated launches without success-path probe caps.

    No inferred complete set on failure: only known source scope, exact ordinals,
    typed records, and independent ledger/counter consistency are asserted.
    """
    valid={r['id'].rsplit('#',1)[0]:r for r in inventory['invocations']}
    if not isinstance(counts,dict) or any(type(n) is not int or n<0 for n in counts.values()):
        raise ValueError('malformed launch census')
    if set(counts)-set(valid):raise ValueError('unknown launch census scope')
    if not isinstance(records,list) or not isinstance(trusted,list):raise ValueError('malformed observations')
    seen=set(); actual=Counter()
    for r in trusted:
        if not isinstance(r,dict) or not isinstance(r.get('id'),str):raise ValueError('malformed diagnostic id')
        key,ordinal=r['id'].rsplit('#',1); role=valid.get(key)
        if role is None or not ordinal.isdecimal() or int(ordinal)<1 or r['id'] in seen:raise ValueError('invalid diagnostic invocation')
        if r['tool']!=role['tool'] or r['scope']!=role['scope']:raise ValueError('diagnostic scope mismatch')
        if type(r['pid']) is not int or r['pid']<=0 or type(r['exit']) is not int:raise ValueError('malformed diagnostic process')
        if not isinstance(r['target'],str) or not r['target'] or not isinstance(r['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',r['sha256']):raise ValueError('malformed diagnostic identity')
        if not isinstance(r['artifacts'],dict) or any(not isinstance(p,str) or not isinstance(d,str) or not re.fullmatch('[0-9a-f]{64}',d) for p,d in r['artifacts'].items()):raise ValueError('malformed diagnostic artifacts')
        if not isinstance(r['argv'],list) or not all(isinstance(a,str) for a in r['argv']):raise ValueError('malformed diagnostic argv')
        if role['arguments'] is not None and r['argv']!=role['arguments']:raise ValueError('diagnostic arguments mismatch')
        seen.add(r['id']);actual[key]+=1
    if dict(actual)!={k:n for k,n in counts.items() if n}:raise ValueError('counter / ledger mismatch')
    if seen!={f'{k}#{n}' for k,count in counts.items() for n in range(1,count+1)}:raise ValueError('diagnostic ordinal gap')
    if sorted(records,key=lambda r:r['id'])!=sorted(trusted,key=lambda r:r['id']):raise ValueError('forged receipt / private ledger mismatch')
    return dict(state='valid',mode='failed_execution_diagnostics',counts=counts,observed=len(trusted),complete_publication=False)


def finalize(out,inventory,expected,process_exit):
    out=Path(out)
    evidence={name:read_evidence(out/file,kind) for name,file,kind in [('log','public.log','text'),('private','private.jsonl','jsonl'),('counter','counter.json','json')]}
    log=evidence['log']['value'] or ''
    lines=[line.split(': ',1)[1] for line in log.splitlines() if line.startswith('publication-tool-executions: ')]
    try:
        records=json.loads(lines[0]) if len(lines)==1 else None
        if not isinstance(records,list) or not records or not all(isinstance(r,dict) for r in records):raise ValueError('missing or malformed public receipts')
        receipt=dict(state='valid',value=records)
    except (ValueError,TypeError) as e:
        records=None
        receipt=dict(state='missing' if not lines else 'malformed',value=None,detail=str(e))
    evidence['receipts']=receipt
    private=evidence['private']['value'] or []
    calls=re.findall(r'^publication-no-ax-full-entrypoint: exit=(-?\d+)$',log,re.M)
    public=dict(exit=process_exit,entrypoint_exit=int(calls[0]) if len(calls)==1 else None,called=len(calls)==1 and bool(private),coverage='publication-no-ax-full-entrypoint: exit=0' in log and 'publication-invalid-plant-control: exit=1' in log)
    errors=[]; census=dict(state='not_evaluated',mode='unknown',complete_publication=False)
    bad=[name+': '+row['state'] for name,row in evidence.items() if row['state']!='valid']
    if bad:
        errors+=bad; refusal='evidence_error'
    else:
        try:
            if process_exit==0:
                bound=bind_census(inventory,evidence['counter']['value'])
                errors=evaluate(bound,expected,records,private,public)
                census=dict(state='valid',mode='successful_publication',required_executable_count=bound['required_executable_count'],conditional_probe_count=bound['conditional_probe_count'],expected=len(bound['invocations']),complete_publication=not errors)
                refusal='identity_or_completeness' if errors else None
            else:
                census=diagnostic_census(inventory,evidence['counter']['value'],records,private)
                errors=['public caller missing or failed']; refusal='public_failed'
        except (ValueError,TypeError,KeyError,IndexError) as e:
            census=dict(state='invalid',mode='unknown',complete_publication=False,error=str(e))
            errors=['census: '+str(e)]; refusal='evidence_error'
    if process_exit!=0 or not public['called'] or not public['coverage']:
        if 'public caller missing or failed' not in errors:errors.append('public caller missing or failed')
    result=dict(schema=2,execution=dict(state='terminated',exit=process_exit),public=public,census=census,evidence={k:{f:v for f,v in r.items() if f!='value'} for k,r in evidence.items()},refusal=refusal,gate_exit=int(bool(errors)),errors=errors,applied=[r.get('id') for r in private if isinstance(r,dict) and r.get('applied')],observed=len(private),required=census.get('expected'),jar_facts=sum(len(r.get('artifacts',{})) for r in private if isinstance(r,dict) and isinstance(r.get('artifacts',{}),dict)))
    (out/'receipts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in (records or [])))
    (out/'expected.json').write_text(json.dumps(expected,indent=2))
    (out/'result.json').write_text(json.dumps(result,indent=2))
    return result


def control_passed(control,exit_code,result,log,private):
    """A negative control proves its cause, never merely a nonzero exit."""
    if not isinstance(result,dict) or result.get('schema')!=2:return False
    if any(not isinstance(result.get(k),dict) for k in ['execution','public','census','evidence']):return False
    if type(result.get('gate_exit')) is not int:return False
    if result['execution'].get('exit')!=result['public'].get('exit'):return False
    if result.get('execution',{}).get('state')!='terminated':return False
    if exit_code!=result.get('gate_exit'):return False
    public=result.get('public',{}); census=result.get('census',{})
    if control in ('ambient-ax','ambient-dot','serial-render'):
        return exit_code==0 and census.get('complete_publication') is True and public.get('coverage') is True
    if exit_code!=1 or public.get('exit')!=1:return False
    if control=='absent-caller':return public.get('called') is False and result.get('evidence',{}).get('private',{}).get('state')=='missing'
    if control=='forbidden-ax':return public.get('called') is False and 'no-AX control is invalid: ax is present' in log
    if control in ('preflight', 'baseline-refusal'):
        # These controls stop before any isolated publication launch. Missing
        # observations are legitimate here; unreadable/partial evidence is not.
        evidence=result['evidence']
        marker='publication environment error: ' if control=='preflight' else 'baseline-public-validator: exit=1'
        return (public.get('called') is False and public.get('entrypoint_exit') is None
                and evidence.get('log',{}).get('state')=='valid'
                and all(evidence.get(k,{}).get('state')=='missing' for k in ('private','counter','receipts'))
                and marker in log)
    if result.get('refusal')!='public_failed' or census.get('state')!='valid' or census.get('mode')!='failed_execution_diagnostics' or census.get('complete_publication') is not False:return False
    if not public.get('called') or public.get('entrypoint_exit')!=1:return False
    if control=='publication-failure':return True
    if control=='java11':return 'class file version 61.0' in log and any(r.get('tool')=='java' and r.get('exit')!=0 for r in private)
    if control=='f1':
        return 'generated SVG contains a PlantUML render failure' in log and any(r.get('tool')=='dot' and r.get('exit')==1 for r in private) and any(r.get('scope','').startswith('compare:') and r.get('exit')==1 for r in private)
    return False

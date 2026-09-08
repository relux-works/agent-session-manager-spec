"""One closed-set completeness and selected identity decision."""
import json
from pathlib import Path

class EvidenceError(ValueError): pass

def read_records(path):
    try: text=Path(path).read_text()
    except FileNotFoundError as e: raise EvidenceError('missing evidence') from e
    except OSError as e: raise EvidenceError('evidence read failed: '+type(e).__name__) from e
    try:
        records=[json.loads(line) for line in text.splitlines()]
        if not records or not all(isinstance(r,dict) for r in records): raise ValueError()
        return records
    except (ValueError,TypeError) as e: raise EvidenceError('malformed evidence') from e

def evaluate(inventory, expected, records, trusted, public):
    errors=[]; required=inventory['invocations']
    if public.get('exit')!=0 or not public.get('called') or not public.get('coverage'):
        errors.append('public caller missing or failed')
    wanted={r['id']:r for r in required}; seen={}
    if not isinstance(records,list): return ['malformed evidence']
    for record in records:
        try:
            key=record['id']; role=wanted.get(key)
            if role is None:
                errors.append('unexpected invocation: '+str(key)); continue
            if key in seen: errors.append('duplicate invocation: '+key)
            seen[key]=record
            if record['tool']!=role['tool'] or record['scope']!=role['scope']: errors.append('scope mismatch: '+key)
            if type(record['pid']) is not int or record['pid']<=0 or type(record['exit']) is not int or record['exit']!=0: errors.append('launch failed: '+key)
            identity=expected[role['tool']]
            if (record['target'],record['sha256'])!=(identity['target'],identity['sha256']): errors.append('substituted executable: '+key)
            artifacts=expected['structurizr_jars'] if role['scope'].startswith('structurizr:') else expected['plantuml_jars']
            if record['artifacts']!=(artifacts if record['tool']=='java' else {}): errors.append('substituted or omitted JAR: '+key)
            args=record['argv']
            if not isinstance(args,list) or not all(isinstance(a,str) for a in args): raise ValueError('argv')
            if role['arguments'] is not None and args!=role['arguments']: errors.append('arguments mismatch: '+key)
            scope=role['scope']
            if scope.startswith('structurizr:'):
                op=scope.split(':')[1]
                if op not in args or '-w' not in args or args[args.index('-w')+1]!='diagrams/c4/workspace.dsl': errors.append('operation mismatch: '+key)
            if scope.startswith('render:') and role['tool'] in ('plantuml','java'):
                operation=next(o for o in inventory['operations'] if o['scope']==scope)
                if sorted(Path(a).name for a in args if a.endswith('.puml'))!=sorted(Path(p).name for p in operation['inputs']) or '-tsvg' not in args: errors.append('render scope mismatch: '+key)
            if scope.startswith('compare:'):
                if '--compare-svg' not in args or Path(args[args.index('--compare-svg')+1]).name!=scope.split(':',1)[1] or Path(args[-1]).name!=scope.split(':',1)[1]: errors.append('comparator mismatch: '+key)
        except (KeyError,ValueError,TypeError,IndexError) as e: errors.append('malformed observation: '+str(e))
    for key in wanted:
        if key not in seen: errors.append('missing invocation: '+key)
    # Private launch ledger cannot be replaced by a caller-minted successful receipt.
    # Omission mutants suppress one member in both evidence streams, retaining others.
    try:
        if sorted(records,key=lambda r:r['id'])!=sorted(trusted,key=lambda r:r['id']): errors.append('forged receipt / private ledger mismatch')
    except (KeyError,TypeError): errors.append('malformed private ledger')
    return errors

if __name__=='__main__':
    import argparse,sys
    from inventory import derive,bind_census
    p=argparse.ArgumentParser(); p.add_argument('--run',type=Path,required=True); p.add_argument('--source',type=Path,required=True); p.add_argument('--receipts',type=Path); p.add_argument('--private',type=Path)
    a=p.parse_args()
    try:
        inventory=derive(a.source)
        binding=json.loads((a.run/'inventory.json').read_text())
        if inventory['source_hashes'] != binding['source_hashes']:
            raise EvidenceError('source binding mismatch')
        inventory=bind_census(inventory,json.loads((a.run/'counter.json').read_text()))
        errors=evaluate(inventory,json.loads((a.run/'expected.json').read_text()),read_records(a.receipts or a.run/'receipts.jsonl'),read_records(a.private or a.run/'private.jsonl'),json.loads((a.run/'result.json').read_text())['public'])
    except (EvidenceError,OSError,ValueError) as e: errors=[str(e)]
    print(json.dumps(dict(errors=errors,accepted=not errors)))
    sys.exit(1 if errors else 0)

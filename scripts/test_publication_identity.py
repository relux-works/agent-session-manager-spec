#!/usr/bin/env python3
"""Source-adopted gate witnesses through real publication, in bounded batches."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT/'scripts/publication_gate'
sys.path.insert(0, str(GATE))
from inventory import derive


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path)
    p.add_argument('--assert-result', type=Path)
    p.add_argument('--assert-kind', choices=['identity', 'f1', 'pin'])
    p.add_argument('--test-name')
    p.add_argument('--branch', choices=['path', 'home'])
    p.add_argument('--section', choices=['mixed', 'substitutions', 'pins'], default='mixed')
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--count', type=int, default=8)
    a = p.parse_args()
    if a.assert_result:
        data = json.loads(a.assert_result.read_text())
        if a.assert_kind == 'pin':
            refused = data.get('gate_exit') == 1 and data.get('refusal') == 'driver_error' and any('workflow' in e for e in data.get('errors', []))
        elif a.assert_kind == 'f1':
            refused = data.get('gate_exit') == 1 and data.get('refusal') == 'evidence_error'
        else:
            refused = data.get('gate_exit') == 1 and data.get('public', {}).get('exit') == 0 and data.get('refusal') == 'identity_or_completeness'
        print(a.test_name, 'PASS' if refused else 'FAIL')
        return 0 if refused else 1
    if not a.out or not a.branch:
        p.error('--out and --branch are required for execution')
    a.out.mkdir(parents=True, exist_ok=False)
    rows = []

    def run(name, args, gate=GATE, narrowed=False, f1=False, pin=False):
        out = a.out/name
        argv = [sys.executable, '-B', str(gate/'drive.py'), '--source', str(ROOT),
                '--out', str(out), '--branch', a.branch, *args]
        result = subprocess.run(argv, text=True, capture_output=True, timeout=180)
        (a.out/(name+'.log')).write_text(result.stdout+result.stderr)
        data = json.loads((out/'result.json').read_text())
        witness_name = 'test_'+name.replace('-narrowed','')
        witness_argv = [sys.executable, '-B', str(Path(__file__).resolve()), '--assert-result', str(out/'result.json'),
                        '--assert-kind', 'pin' if pin else 'f1' if f1 else 'identity', '--test-name', witness_name]
        witness = subprocess.run(witness_argv, text=True, capture_output=True)
        refused = result.returncode == 1 and witness.returncode == 0
        row = dict(test='test_'+name, argv=argv, exit=result.returncode, result=data,
                   passed=refused if not narrowed else not refused and (data.get('refusal') == 'public_failed' if f1 else result.returncode == 0))
        if narrowed:
            row.update(mutant=name, narrows_to='all invocation roles except Structurizr export Java' if not f1 else 'receipt agreement for all scopes except SVG comparators',
                       killed=row['passed'], named_failing_test='test_'+name.replace('-narrowed','') if row['passed'] else None,
                       witness_assertion_exit=witness.returncode)
            if not row['passed']:
                row['survivor_bound']='No causal behavioral kill established by this public witness.'
        row.update(witness_argv=witness_argv, witness_exit=witness.returncode, witness_output=witness.stdout+witness.stderr)
        rows.append(row)
        print(name, 'exit', result.returncode, 'assertion', row['passed'], flush=True)

    if a.section == 'mixed':
        run('mixed-export', ['--control', 'mixed-export'])
        narrow = a.out/'export-narrowing'; shutil.copytree(GATE, narrow)
        f = narrow/'evaluate.py'; s = f.read_text()
        old = "required=inventory['invocations']"
        assert s.count(old) == 1
        f.write_text(s.replace(old, old+"; required=[r for r in required if r['id']!='structurizr:export/java#1']"))
        run('mixed-export-narrowed', ['--control', 'mixed-export'], narrow, narrowed=True)
        # Forge only the actual failed comparator receipt, retaining its private
        # launch ledger. This happens after actual F1 rendering, not in a replay.
        forged = a.out/'forgery'; shutil.copytree(GATE, forged)
        f = forged/'drive.py'; s = f.read_text(); old = '    result=finalize(out,inventory,expected,proc.returncode)'
        injected = '''    log=out/'public.log'; text=log.read_text(); prefix='publication-tool-executions: '
    line=next(line for line in text.splitlines() if line.startswith(prefix))
    records=json.loads(line[len(prefix):])
    failed=next(r for r in records if r['scope'].startswith('compare:') and r['exit']==1)
    failed['pid']+=100000
    log.write_text(text.replace(line,prefix+json.dumps(records)))
'''
        assert s.count(old) == 1
        f.write_text(s.replace(old, injected+old))
        run('forged-comparator', ['--control', 'f1'], forged, f1=True)
        narrow = a.out/'comparator-narrowing'; shutil.copytree(forged, narrow)
        f = narrow/'execution.py'; s = f.read_text()
        old = "if sorted(records,key=lambda r:r['id'])!=sorted(trusted,key=lambda r:r['id']):"
        new = "if sorted([r for r in records if not r['scope'].startswith('compare:')],key=lambda r:r['id'])!=sorted([r for r in trusted if not r['scope'].startswith('compare:')],key=lambda r:r['id']):"
        assert s.count(old) == 1
        f.write_text(s.replace(old, new))
        run('forged-comparator-narrowed', ['--control', 'f1'], narrow, narrowed=True, f1=True)
    elif a.section == 'pins':
        import os
        java25 = os.environ['PUBLICATION_JAVA25']
        plant = Path(os.environ['PUBLICATION_PLANTUML'])
        changed_jar = a.out/'changed-plantuml.jar'
        changed_jar.write_bytes(plant.read_bytes()+b'\n')
        cases = [
            ('wrong-compatible-java-pin', ['--pinned-java', java25],
             "if version.returncode or 'version \"'+pin+'\"' not in version.stderr or 'Temurin' not in version.stderr:",
             "if ('version \"25.0.1\"' not in version.stderr) and (version.returncode or 'version \"'+pin+'\"' not in version.stderr or 'Temurin' not in version.stderr):"),
            ('wrong-plantuml-digest', ['--plantuml-jar', str(changed_jar)],
             "if digest(PLANT)!=", "if PLANT.name!='changed-plantuml.jar' and digest(PLANT)!=")]
        for name, args, before, after in cases:
            run(name, args, pin=True)
            narrow = a.out/(name+'-gate'); shutil.copytree(GATE, narrow)
            f = narrow/'drive.py'; text = f.read_text(); assert text.count(before) == 1
            f.write_text(text.replace(before, after))
            run(name+'-narrowed', args, narrow, narrowed=True, pin=True)
            rows[-1]['narrows_to'] = 'pin enforcement except '+name
    else:
        roles = [r for r in derive(ROOT)['invocations'] if not r['conditional']]
        cases = [('substitute', r['id']) for r in roles] + [('jar-substitute', r['id']) for r in roles if r['tool'] == 'java']
        assert 0 <= a.start < len(cases) and 0 < a.count <= 8
        for i, (kind, key) in list(enumerate(cases))[a.start:a.start+a.count]:
            run(f'{i:02d}-{kind}', ['--kind', kind, '--target-id', key])
    (a.out/'report.json').write_text(json.dumps(rows, indent=2))
    return 0 if rows and all(r['passed'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())

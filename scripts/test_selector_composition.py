#!/usr/bin/env python3
"""Attack public selector composition; adapted from accepted gate 2131b6.

Every kill needs the named semantic refusal to become a forbidden success.
Finite synthetic coverage only: no temporal transport, IO or authority attestation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from selector_inventory import Inventory, CODE, FIXTURE

ROOT = Path(__file__).resolve().parents[1]


def refresh(root):
    spec = (root / 'SPEC.md').read_text()
    path = root / FIXTURE
    data = json.loads(path.read_text())
    for pin in data['prose_sections']:
        pin[2] = hashlib.sha256(spec.split(pin[0], 1)[1].split(pin[1], 1)[0].encode()).hexdigest()
    path.write_text(json.dumps(data, indent=2))
    path = root / 'scripts/validate_spec.py'
    path.write_text(re.sub(r'("SPEC.md": ")[a-f0-9]{64}', lambda m: m[1] + hashlib.sha256(spec.encode()).hexdigest(), path.read_text()))


def partial_local(inv, root, route, level):
    # Independent reviewer predicate: narrower than all six adopted shapes.
    code = inv.code
    if level == 'caller':
        call = inv.calls[route]['receiver']
        lines = code.splitlines(keepends=True)
        old = lines[call['line'] - 1]
        indent = old[:len(old) - len(old.lstrip())]
        predicate = "facts['receiver'].get('boundary') == 'transport-resume' and facts['receiver'].get('read') == 'partial' and facts['receiver'].get('read_domain') == 'local'"
        if route == 'remote_logs':
            predicate += " and facts.get('cursor') is not None"
        lines[call['line'] - 1] = indent + 'if not (' + predicate + '):\n' + indent + '    ' + old.lstrip()
        code = ''.join(lines)
    else:
        host = inv.seeds[route]['facts']['receiver']['plan']['source_host_id']
        predicate = "facts.get('boundary') == 'transport-resume' and facts.get('read') == 'partial' and facts.get('read_domain') == 'local' and facts['plan'].get('action') == " + repr(route.removeprefix('remote_')) + " and facts['plan'].get('source_host_id') == " + repr(host)
        code = code.replace('def revalidate(facts, policy):\n', 'def revalidate(facts, policy):\n    if ' + predicate + ':\n        return\n', 1)
    (root / CODE).write_text(code)


def controls(inv):
    victim = 'SEL-CASE-GATE-logs.receiver.transport-resume.cursor-revoked'
    def missing(root):
        path = root / FIXTURE
        data = json.loads(path.read_text())
        data['cases'] = [c for c in data['cases'] if c['id'] != victim]
        path.write_text(json.dumps(data))
        path = root / 'SPEC.md'
        path.write_text('\n'.join(line for line in path.read_text().split('\n') if '<code>' + victim + '</code>' not in line))
        refresh(root)  # Remove closed ID and refresh pins too: inventory must refuse.
    def forged(root):
        path = root / FIXTURE
        data = json.loads(path.read_text())
        next(c for c in data['cases'] if c['id'] == victim)['expected'] = {'events': []}
        path.write_text(json.dumps(data))
    def unreadable(root):
        (root / FIXTURE).unlink()
        (root / FIXTURE).mkdir()
    def phase(root):
        path = root / 'SPEC.md'
        path.write_text(path.read_text().replace('| attach | pre-effect,', '| attach | audit-continuation,', 1))
        refresh(root)
    def caller(root):
        path = root / CODE
        path.write_text(path.read_text().replace('    revalidate(receiver, policy)', '    pass  # revalidate(receiver, policy)', 1))
    def neutral(root):
        path = root / CODE
        path.write_text(path.read_text() + '\n# Neutral editorial control.\n')
    return [
        ('missing-cursor-evidence', missing, 1, 'composed coverage missing logs.receiver.transport-resume.cursor'),
        ('forged-expectation', forged, 1, 'composed coverage missing logs.receiver.transport-resume.cursor'),
        ('missing-input', lambda r: (r / FIXTURE).unlink(), 1, 'No such file'),
        ('malformed-input', lambda r: (r / FIXTURE).write_text('{'), 1, 'missing/malformed conformance input'),
        ('unreadable-input', unreadable, 1, 'Is a directory'),
        ('new-source-boundary', phase, 1, 'missing derived binding attach initiator initial-audit-continuation'),
        ('missing-caller', caller, 1, 'caller topology changed'),
        ('neutral', neutral, 0, 'Selector composed coverage: 26/26'),
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=10000)
    parser.add_argument('--controls', action='store_true')
    parser.add_argument('--full', action='store_true', help='Drive both public entries for each selected case')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    inv = Inventory(ROOT)
    registry = []
    for mutant in inv.mutants():
        registry.append((mutant['id'], lambda r, m=mutant: inv.mutate(r, m), 1, mutant['witness']))
    for route in inv.routes:
        for level in ['caller', 'generic']:
            scope = 'cursor' if route == 'remote_logs' else 'initial'
            row = next(r for r in inv.rows if r['route'] == route and r['side'] == 'receiver' and r['boundary'] == 'transport-resume' and r['scope'] == scope)
            registry.append(('review-' + route + '-' + level + '-partial-local-only', lambda r, route=route, level=level: partial_local(inv, r, route, level), 1, inv.case(row, 'partial-local')['id']))
    if args.controls:
        registry = controls(inv)
    results = []
    print('| Mutant/control | Narrowed scope | Named failing test | Public exit | Verdict / survival bound |', flush=True)
    print('| --- | --- | --- | ---: | --- |', flush=True)
    with tempfile.TemporaryDirectory(prefix='ax-selector-composition-') as temp:
        for index, (label, mutate, expected, witness) in enumerate(registry, 1):
            if not args.start <= index <= args.end:
                continue
            root = Path(temp) / str(index)
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', '.temp', '.task-board', 'task-board.config.json', '__pycache__'))
            mutate(root)
            entries = ['./scripts/validate_spec.py', './run_validation.sh'] if args.full else ['./scripts/validate_spec.py' if index % 2 else './run_validation.sh']
            for entry in entries:
                result = subprocess.run([entry], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=150)
                named = [line for line in result.stdout.splitlines() if witness + ' expected ' in line]
                semantic = bool(named) and all("got {'session_id':" in line and 'invalid_evaluation' not in line for line in named)
                ok = result.returncode == expected and (witness in result.stdout if args.controls else semantic)
                row = dict(index=index, label=label, entry=entry, exit=result.returncode, expected_exit=expected, witness=witness, diagnostics=named, ok=ok)
                results.append(row)
                if args.output_dir:
                    args.output_dir.mkdir(parents=True, exist_ok=True)
                    (args.output_dir / f'{index}-{Path(entry).name}.log').write_text(result.stdout)
                    (args.output_dir / f'results-{args.start}-{args.end}.json').write_text(json.dumps(results, indent=2))
                verdict = 'expected control result' if ok and args.controls else 'killed: named forbidden success' if ok else 'SURVIVOR: named semantic detection unproven'
                print(f'| {label} | {label}; {entry} | {witness} | {result.returncode} | {verdict} |', flush=True)
                if not ok:
                    print(result.stdout[-3000:], flush=True)
            shutil.rmtree(root)
    print(f'Observed {sum(r["ok"] for r in results)}/{len(results)} expected results; registry {len(registry)}; runtime coverage 0.', flush=True)
    return 0 if results and all(r['ok'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())

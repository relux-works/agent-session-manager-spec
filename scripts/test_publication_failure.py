#!/usr/bin/env python3
"""Attack failure forwarding through the actual portability main/public caller.

Every fixture executes real tools before damaging evidence. Source overlays and
post-execution faults are disposable; no JVM or renderer success is simulated.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# Fault location, exact injected behavior, expected typed refusal/diagnostic.
FAULTS = {
    'forged-comparator': ('before', "rewrite_receipts(case, 'forged')", 'evidence_error', 'forged receipt / private ledger mismatch'),
    'absent-receipts': ('before', "rewrite_receipts(case, 'absent')", 'evidence_error', 'receipts: missing'),
    'partial-receipts': ('before', "rewrite_receipts(case, 'partial')", 'evidence_error', 'forged receipt / private ledger mismatch'),
    'malformed-receipts': ('before', "rewrite_receipts(case, 'malformed')", 'evidence_error', 'receipts: malformed'),
    'read-failed-private': ('before', "(case/'private.jsonl').chmod(0)", 'evidence_error', 'private: read_failed'),
    'missing-counter': ('before', "(case/'counter.json').unlink()", 'evidence_error', 'counter: missing'),
    'partial-counter': ('before', "partial_counter(case)", 'evidence_error', 'counter / ledger mismatch'),
    'malformed-counter': ('before', "(case/'counter.json').write_text('{')", 'evidence_error', 'counter: malformed'),
    'unrelated-exception': ('after', "raise RuntimeError('injected after real publication')", 'driver_error', 'injected after real publication'),
    'absent-result': ('after', "(case/'result.json').unlink()", 'result_error', 'missing'),
    'read-failed-result': ('after', "(case/'result.json').chmod(0)", 'result_error', 'read_failed'),
    'absent-return': ('after', 'gate = None', 'result_error', 'valid'),
    'preflight-read-failed-private': ('before', "(case/'private.jsonl').write_text('{}'); (case/'private.jsonl').chmod(0)", 'evidence_error', 'private: read_failed'),
    'preflight-partial-counter': ('before', "(case/'counter.json').write_text('{}')", 'evidence_error', 'receipts: missing'),
}


def rewrite_receipts(case, kind):
    path = case/'public.log'
    lines = path.read_text().splitlines()
    prefix = 'publication-tool-executions: '
    index, = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    records = json.loads(lines[index][len(prefix):])
    index_record = next(i for i, r in enumerate(records) if r['scope'].startswith('compare:') and r['exit'] == 1)
    if kind == 'forged':
        records[index_record]['pid'] += 100000
    elif kind == 'partial':
        del records[index_record]
    if kind == 'absent':
        del lines[index]
    else:
        lines[index] = prefix + ('{' if kind == 'malformed' else json.dumps(records))
    path.write_text('\n'.join(lines)+'\n')


def partial_counter(case):
    path = case/'counter.json'
    counts = json.loads(path.read_text())
    del counts[next(k for k in counts if k.startswith('compare:'))]
    path.write_text(json.dumps(counts))


def assert_report(report, fault):
    """The same named assertion runs against intact and narrowed callers."""
    rows = json.loads(report.read_text())
    row, = rows
    refusal, diagnostic = FAULTS[fault][2:]
    gate = row.get('gate') or {}
    marker = ('publication environment error: missing publication prerequisite: dot' if fault.startswith('preflight-') else
              'generated SVG contains a PlantUML render failure')
    reached = marker in row['stdout'] and ('baseline-public-validator: exit=0' in row['stdout'])
    if not fault.startswith('preflight-'):
        reached = reached and 'publication-no-ax-environment: ax=absent' in row['stdout']
    passed = (row['exit'] == 1 and not row['passed'] and reached
              and gate.get('refusal') == refusal and diagnostic in json.dumps(gate))
    print(json.dumps(dict(test='test_portability_rejects_'+fault.replace('-', '_'),
                         passed=passed, public_exit=row['exit'], gate=gate)), flush=True)
    return 0 if passed else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path)
    p.add_argument('--section', choices=['controls', 'narrowing'], default='controls')
    p.add_argument('--fault', choices=sorted(FAULTS), action='append')
    p.add_argument('--assert-report', type=Path)
    a = p.parse_args()
    if a.assert_report:
        if not a.fault or len(a.fault) != 1:
            p.error('assertion requires one --fault')
        return assert_report(a.assert_report, a.fault[0])
    if a.out is None:
        p.error('--out is required')
    a.out.mkdir(parents=True, exist_ok=False)
    rows = []
    for fault in a.fault or FAULTS:
        folder = a.out/fault
        folder.mkdir()
        original = (ROOT/'scripts/test_publication_environment.py').read_text()
        source = original.replace('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path('+repr(str(ROOT))+')')
        case_name = 'absent-graphviz' if fault.startswith('preflight-') else 'unusable-graphviz-render'
        # Bound this disposable fixture to one existing public control. The
        # production control inventory and its default selection stay intact.
        anchor = '            if control is None:'
        assert source.count(anchor) == 1
        source = source.replace(anchor, '            if name != '+repr(case_name)+':\n                return\n'+anchor)
        source = source.replace('from execution import finalize, control_passed, read_evidence',
                                'from execution import finalize, control_passed, read_evidence\n'
                                'sys.path.insert(0, '+repr(str(ROOT/'scripts'))+')\n'
                                'from test_publication_failure import rewrite_receipts, partial_counter')
        location, injection, _, _ = FAULTS[fault]
        anchor = ("            (case/'public.log').write_text(result.stdout+result.stderr)" if location == 'before' else
                  '        gate = finalize(case, derive(repo), expected_identity, result.returncode)')
        assert source.count(anchor) == 1
        indent = '            ' if location == 'before' else '        '
        source = source.replace(anchor, anchor+'\n'+indent+injection)
        if a.section == 'narrowing':
            if fault.startswith('preflight-'):
                gate_dir = folder/'gate'
                shutil.copytree(ROOT/'scripts/publication_gate', gate_dir, ignore=shutil.ignore_patterns('__pycache__'))
                module = gate_dir/'execution.py'
                text = module.read_text()
                anchor = "evidence.get(k,{}).get('state')=='missing'"
                assert text.count(anchor) == 1
                key, state = ('private', 'read_failed') if fault.endswith('private') else ('counter', 'valid')
                module.write_text(text.replace(anchor, "(evidence.get(k,{}).get('state')=='missing' or (k=="+repr(key)+" and evidence.get(k,{}).get('state')=="+repr(state)+"))"))
                source = source.replace("sys.path.insert(0, str(ROOT/'scripts/publication_gate'))", 'sys.path.insert(0, '+repr(str(gate_dir))+')')
            else:
                anchor = 'accepted, gate = classify_publication(case, repo, expected_identity, result, control)'
                assert source.count(anchor) == 1
                # Keep success and other failure gates, including the call token.
                source = source.replace(anchor, "accepted, gate = (True, {}) if control == 'f1' else classify_publication(case, repo, expected_identity, result, control)")
        # Persist post-classification observations before TemporaryDirectory exits.
        anchor = '            rows.append(row)'
        assert source.count(anchor) == 1
        capture = ("            for filename in ['public.log','private.jsonl','counter.json','result.json']:\n"
                   "                artifact = case/filename\n"
                   "                if artifact.is_file():\n"
                   "                    artifact.chmod(0o644)\n"
                   "                    shutil.copyfile(artifact, Path("+repr(str(folder))+ ")/filename)\n")
        source = source.replace(anchor, capture+anchor)
        overlay = folder/'caller.py'
        overlay.write_text(source)
        (folder/'overlay.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), source.splitlines(True))))
        argv = [sys.executable, '-B', str(overlay), '--section', 'controls',
                '--java11', os.environ['PUBLICATION_JAVA11'], '--pinned-java', os.environ['PUBLICATION_JAVA'],
                '--compatible-java', os.environ['PUBLICATION_JAVA25'], '--structurizr', os.environ['PUBLICATION_STRUCTURIZR'],
                '--plantuml-jar', os.environ['PUBLICATION_PLANTUML'], '--report', str(folder/'controls.json')]
        with (folder/'command.log').open('w') as stream:
            result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
        assertion = [sys.executable, '-B', str(Path(__file__).resolve()), '--assert-report', str(folder/'controls.json'), '--fault', fault]
        with (folder/'assertion.log').open('w') as stream:
            witness = subprocess.run(assertion, stdout=stream, stderr=subprocess.STDOUT, timeout=10)
        wanted = 1 if a.section == 'controls' else 0
        passed = result.returncode == wanted and witness.returncode == (1-wanted)
        row = dict(test='test_portability_rejects_'+fault.replace('-', '_'), fault=fault,
                   argv=argv, exit=result.returncode, assertion_argv=assertion, assertion_exit=witness.returncode,
                   passed=passed, source_sha256=hashlib.sha256(original.encode()).hexdigest(),
                   overlay_sha256=hashlib.sha256(source.encode()).hexdigest())
        if a.section == 'narrowing':
            mutant = fault+'-as-absence' if fault.startswith('preflight-') else 'forward-only-non-f1'
            row.update(mutant=mutant, killed=passed, named_failing_test=row['test'] if passed else None)
            if not passed:
                row['survivor_bound'] = 'The named actual-caller assertion did not establish a causal kill.'
        rows.append(row)
        print(f"{row['test']}: caller={result.returncode}; assertion={witness.returncode}; passed={passed}", flush=True)
    (a.out/'report.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(f'{a.section}: {sum(r["passed"] for r in rows)}/{len(rows)}', flush=True)
    return 0 if rows and all(r['passed'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())

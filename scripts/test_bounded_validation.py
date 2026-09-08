#!/usr/bin/env python3
"""Exercise bounded legacy selection through the public shell entrypoint."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    with tempfile.TemporaryDirectory(prefix='bounded-validation-') as temporary:
        repo = Path(temporary)/'repo'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns('.git', '.temp', '.task-board', '__pycache__'))
        script = repo/'scripts/test_expected_red.sh'
        original = script.read_bytes()
        cases = [('one-selected', '1:1', 0), ('reversed', '2:1', 2),
                 ('zero-index', '0:1', 2), ('absent-selection', '305:305', 1)]
        for name, selected, expected in cases:
            result = subprocess.run(['./scripts/test_expected_red.sh', '--legacy-range', selected],
                                    cwd=repo, text=True, capture_output=True)
            passed = result.returncode == expected
            if name == 'one-selected':
                passed = passed and 'Results: 1 passed, 0 failed out of 304 mutations' in result.stdout
            rows.append(dict(test=name, exit=result.returncode, expected_exit=expected,
                             passed=passed, stdout=result.stdout, stderr=result.stderr))
            print(f'{name}: exit={result.returncode}; assertion={passed}', flush=True)
        # Keep the range validation but admit exactly one absent requested row.
        text = original.decode()
        before = 'if [ "$RANGED" -eq 1 ] && { [ "$LAST" -gt "$TOTAL" ]'
        after = 'if [ "$RANGED" -eq 1 ] && [ "$FIRST:$LAST" != "305:305" ] && { [ "$LAST" -gt "$TOTAL" ]'
        assert text.count(before) == 1
        script.write_text(text.replace(before, after))
        result = subprocess.run(['./scripts/test_expected_red.sh', '--legacy-range', '305:305'],
                                cwd=repo, text=True, capture_output=True)
        killed = result.returncode != 1
        rows.append(dict(mutant='admit-exactly-absent-row305', exit=result.returncode,
                         killed=killed, named_failing_test='absent-selection' if killed else None,
                         stdout=result.stdout, stderr=result.stderr))
        print(f'admit-exactly-absent-row305: exit={result.returncode}; killed={killed}', flush=True)
        script.write_bytes(original)
    args.report.write_text(json.dumps(rows, indent=2)+'\n')
    return 0 if all(r.get('passed', r.get('killed')) for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())

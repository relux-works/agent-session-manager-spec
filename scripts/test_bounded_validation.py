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
                passed = passed and 'Results: 1 passed, 0 failed, 303 skipped of 304 registered mutations' in result.stdout
            rows.append(dict(test=name, exit=result.returncode, expected_exit=expected,
                             passed=passed, stdout=result.stdout, stderr=result.stderr))
            print(f'{name}: exit={result.returncode}; assertion={passed}', flush=True)
        # Defense-in-depth probe: bypass only the range-exercise guard for the
        # exact absent selection 305:305. The vacuous-pass (PASS==0) guard must
        # still refuse. This is NOT a baseline kill: the absent-selection
        # baseline expects exit 1, so it still passes on this mutant.
        text = original.decode()
        before_range = 'if [ "$RANGED" -eq 1 ] && { [ "$LAST" -gt "$TOTAL" ]'
        after_range = 'if [ "$RANGED" -eq 1 ] && [ "$FIRST:$LAST" != "305:305" ] && { [ "$LAST" -gt "$TOTAL" ]'
        assert text.count(before_range) == 1, text.count(before_range)
        script.write_text(text.replace(before_range, after_range))
        result = subprocess.run(['./scripts/test_expected_red.sh', '--legacy-range', '305:305'],
                                cwd=repo, text=True, capture_output=True)
        defense_refused = (result.returncode == 1
                           and 'Expected-red suite FAILED' in result.stdout
                           and 'not fully exercised' not in result.stdout)
        # Reuse the exact absent-selection baseline predicate (expects exit 1).
        baseline_passes_on_range_only = (result.returncode == 1)
        passed_defense = bool(defense_refused and baseline_passes_on_range_only)
        rows.append(dict(mutant='admit-exactly-absent-row305-range-only-bypass',
                         exit=result.returncode,
                         defense_in_depth_refused=bool(defense_refused),
                         baseline_passes_on_mutant=bool(baseline_passes_on_range_only),
                         killed_via_baseline=False,
                         named_failing_test=None,
                         passed=passed_defense,
                         stdout=result.stdout, stderr=result.stderr))
        print(f'admit-exactly-absent-row305-range-only-bypass: exit={result.returncode}; '
              f'defense_refused={defense_refused}; baseline_passes={baseline_passes_on_range_only}; '
              f'passed={passed_defense}', flush=True)
        script.write_bytes(original)
        # Wrong-success control: bypass BOTH production guards for exactly
        # 305:305 in a disposable copy. This must produce forbidden success
        # (exit 0 on the empty selection), which the real absent-selection
        # baseline assertion (expects exit 1) then rejects.
        text2 = original.decode()
        before_ranged = 'if [ "$RANGED" -eq 1 ] && { [ "$LAST" -gt "$TOTAL" ]'
        after_ranged = 'if [ "$RANGED" -eq 1 ] && [ "$FIRST:$LAST" != "305:305" ] && { [ "$LAST" -gt "$TOTAL" ]'
        before_empty = 'if [ $FAIL -ne 0 ] || [ $PASS -eq 0 ]; then'
        after_empty = 'if [ "$FIRST:$LAST" != "305:305" ] && { [ $FAIL -ne 0 ] || [ $PASS -eq 0 ]; }; then'
        assert text2.count(before_ranged) == 1, text2.count(before_ranged)
        assert text2.count(before_empty) == 1, text2.count(before_empty)
        mutated = text2.replace(before_ranged, after_ranged).replace(before_empty, after_empty)
        assert mutated.count(after_ranged) == 1, mutated.count(after_ranged)
        assert mutated.count(after_empty) == 1, mutated.count(after_empty)
        mutation_diff = (f'--- a/scripts/test_expected_red.sh\n'
                         f'+++ b/scripts/test_expected_red.sh (wrong-success control for 305:305)\n'
                         f'-{before_ranged}\n+{after_ranged}\n'
                         f'-{before_empty}\n+{after_empty}\n')
        script.write_text(mutated)
        result2 = subprocess.run(['./scripts/test_expected_red.sh', '--legacy-range', '305:305'],
                                 cwd=repo, text=True, capture_output=True)
        forbidden_success = (result2.returncode == 0)
        # Same predicate as the baseline row above: absent-selection expects 1.
        baseline_passed = (result2.returncode == 1)
        killed = bool(forbidden_success and not baseline_passed)
        rows.append(dict(mutant='admit-exactly-absent-row305-wrong-success',
                         exit=result2.returncode,
                         forbidden_success=bool(forbidden_success),
                         baseline_passed=bool(baseline_passed),
                         killed=killed,
                         named_failing_test='absent-selection' if killed else None,
                         mutation_diff=mutation_diff,
                         stdout=result2.stdout, stderr=result2.stderr))
        print(f'admit-exactly-absent-row305-wrong-success: exit={result2.returncode}; '
              f'forbidden_success={forbidden_success}; baseline_passed={baseline_passed}; '
              f'killed={killed}', flush=True)
        script.write_bytes(original)
    args.report.write_text(json.dumps(rows, indent=2)+'\n')
    return 0 if all(r.get('passed', r.get('killed')) for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())

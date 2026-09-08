#!/usr/bin/env python3
"""Exercise the public SVG comparator with real pinned renderer error output."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    with tempfile.TemporaryDirectory(prefix='svg-render-controls-') as temporary:
        base = Path(temporary)
        repo = base/'repo'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns('.git', '.temp', '.task-board', '__pycache__'))
        original = (repo/'scripts/validate_spec.py').read_text()
        source = base/'structurizr-SystemContext.puml'
        shutil.copyfile(ROOT/'diagrams/c4'/source.name, source)
        render = subprocess.run(['plantuml', '-tsvg', str(source)],
                                env=dict(os.environ, GRAPHVIZ_DOT='/usr/bin/false'),
                                capture_output=True, text=True)
        svg = source.with_suffix('.svg')
        text = svg.read_text()
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.with_suffix('.crash.svg').write_text(text)
        rows.append(dict(test='real-graphviz-crash-render', exit=render.returncode,
                         passed=render.returncode == 0 and 'has crashed.' in text,
                         stdout=render.stdout, stderr=render.stderr,
                         bound='Actual renderer exits zero with an error image; this is not successful rendering'))
        committed = repo/'diagrams/artefacts/structurizr-SystemContext.svg'
        baseline = committed.read_text()
        for token in [r'<\?plantuml-src [^?]+\?>', r'<\?plantuml [^?]+\?>']:
            assert re.search(token, text)[0] == re.search(token, baseline)[0]

        def run(name, content, expected, marker, mutant=None):
            svg.write_text(content)
            result = subprocess.run([sys.executable, '-B', 'scripts/validate_spec.py',
                                     '--compare-svg', str(committed), str(svg)],
                                    cwd=repo, capture_output=True, text=True)
            passed = result.returncode == expected and marker in result.stdout
            row = dict(test=name, exit=result.returncode, expected_exit=expected,
                       passed=passed, stdout=result.stdout, stderr=result.stderr)
            if mutant:
                row.update(mutant=mutant, killed=not passed,
                           named_failing_test=name if not passed else None)
            rows.append(row)
            print(f'{name}: exit={result.returncode}; assertion={passed}; mutant={mutant}', flush=True)

        cases = [
            ('fresh-svg', baseline, 0, 'embedded source metadata fresh'),
            ('real-crash-tokens-retained', text, 1, 'PlantUML render failure'),
            ('malformed-svg-tokens-retained', baseline.replace('</svg>', ''), 1, 'SVG is malformed'),
            ('error-type-tokens-retained', baseline.replace('data-diagram-type="DESCRIPTION"', 'data-diagram-type="ERROR"'), 1, 'PlantUML render failure'),
            ('crash-message-only', re.sub(r'<text[^>]*>An error has occurred!</text>', '', text), 1, 'PlantUML render failure'),
            ('error-message-only', re.sub(r'<text[^>]*>PlantUML .*? has crashed.</text>', '', text), 1, 'PlantUML render failure'),
            ('missing-source', re.sub(r'<\?plantuml-src [^?]+\?>', '', baseline), 1, 'missing PlantUML source'),
            ('missing-version', re.sub(r'<\?plantuml [^?]+\?>', '', baseline), 1, 'missing PlantUML renderer'),
            ('wrong-version', baseline.replace('<?plantuml 1.2026.6?>', '<?plantuml 1.2026.5?>'), 1, 'renderer version mismatch'),
            ('stale-source', re.sub(r'<\?plantuml-src [^?]+\?>', '<?plantuml-src changed?>', baseline), 1, 'embedded PlantUML source metadata differs'),
        ]
        for case in cases:
            run(*case)
        mutants = [
            ('crash-only-handwritten', 'real-crash-tokens-retained',
             'errors.append(f"{label} SVG contains a PlantUML render failure")',
             'if not committed.name.startswith("structurizr-"): errors.append(f"{label} SVG contains a PlantUML render failure")'),
            ('malformed-only-committed', 'malformed-svg-tokens-retained',
             'errors.append(f"{label} SVG is malformed: {error}")',
             'if label == "committed": errors.append(f"{label} SVG is malformed: {error}")'),
            ('error-type-description-exemption', 'error-type-tokens-retained',
             "svg.get('data-diagram-type') == 'ERROR'", "svg.get('data-diagram-type') == 'ERROR' and 'SystemContext' not in committed.name"),
            ('crash-message-exemption', 'crash-message-only',
             "re.search(r'PlantUML \\(.*?\\) has crashed\\.', rendered_text)",
             "re.search(r'PlantUML \\(.*?\\) has crashed\\.', rendered_text) and 'SystemContext' not in committed.name"),
            ('error-message-exemption', 'error-message-only',
             "'An error has occurred!' in rendered_text", "'An error has occurred!' in rendered_text and 'SystemContext' not in committed.name"),
        ]
        for name, witness, before, after in mutants:
            assert original.count(before) == 1, name
            (repo/'scripts/validate_spec.py').write_text(original.replace(before, after))
            run(*next(c for c in cases if c[0] == witness), mutant=name)
            (repo/'scripts/validate_spec.py').write_text(original)
    args.report.write_text(json.dumps(rows, indent=2)+'\n')
    controls = [r for r in rows if 'mutant' not in r]
    mutants = [r for r in rows if 'mutant' in r]
    print(f'Controls: {sum(r["passed"] for r in controls)}/{len(controls)}; mutants: {sum(r["killed"] for r in mutants)}/{len(mutants)}')
    return 0 if all(r['passed'] for r in controls) and all(r['killed'] for r in mutants) else 1


if __name__ == '__main__':
    raise SystemExit(main())

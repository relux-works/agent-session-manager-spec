# Publication invocation gate

Adopted from independently accepted TASK-260909-9ayy13 revision 2, bundle
`cb8f92cc27466ae0f47757c3ccc502c6d7fd7e2c074928e841ada80565e1005e`.
The evaluator, observer and typed execution handling are unchanged. Inventory
metadata now hashes the current checkout rather than naming rejected CR2.

`drive.py` runs `test_host_channel.main` and its real `run_validation.sh` caller
with a private observer. `inventory.py` derives operations from that shell and
its diagram inputs; `evaluate.py` owns identity and completeness together.
It requires 35 executable invocations and 110 supplied JAR identities for the
current source. Conditional Graphviz probes have separate launch counters.
A failed publication reports diagnostic consistency, never successful coverage.

Both branches run in the default expected-red suite and the candidate YAML local
inventory. To run alone, supply `--source . --out /fresh/output --branch path`
(or `home`) to `drive.py`. Select installed tools with `--pinned-java`,
`--structurizr` (the complete distribution launcher), and `--plantuml-jar`.
Defaults use PUBLICATION_JAVA (then JAVA_HOME), PUBLICATION_STRUCTURIZR and
PUBLICATION_PLANTUML; documentation paths default to the candidate YAML's /opt
installations. PUBLICATION_DOT defaults to the selected PATH dot. The Java version
and PlantUML digest must match the candidate workflow. Nothing is downloaded.

Regression controls also require real PUBLICATION_JAVA11 and PUBLICATION_JAVA25
installations. `test_publication_identity.py` drives actual mixed export-only
Java25, per-operation substitutions, and live evaluator narrowing. `controls.py`
runs bounded negative/neutral public cases. `replay.py`, `census_tests.py`,
`structured_tests.py` and `structured_mutants.py` replay actual captured evidence;
these replays do not reexecute publication. `live_structured.py` exercises public
failure before injecting malformed, unreadable and missing-result faults.

Trust bounds: local controller, counter, observer and installed tools are trusted;
no concurrent replacement, hostile-binary attestation or kernel isolation is
claimed. JARs bind supplied classpaths, not loaded classes/native dependencies.
Dot identity is scope/mode/ordinal, not per-diagram attribution under concurrency.
The source parser is tied to the pinned shell grammar and diagram families.
Shell support utilities and workflow installation are outside the denominator.
No AX product implementation or hosted execution is claimed.

The portability caller applies the shared typed result classification to failed
publications as well as successes. A genuine preflight refusal requires absent
launch evidence; a read failure or partial ledger cannot stand in for absence.
Run the failure-forwarding regressions with those same real tool inputs:

```bash
python3 scripts/test_publication_failure.py --out /tmp/publication-failure-controls --section controls
python3 scripts/test_publication_failure.py --out /tmp/publication-failure-narrowing --section narrowing
```

Each control executes the real failed publication before damaging its evidence.
The narrowing retains success gating and suppresses only F1 failure forwarding;
the same named assertions must fail. Use repeated `--fault` selections to split
the suite into bounded commands. Each disposable fixture selects one existing
public control without changing the production driver's default inventory.
Two preflight narrowings separately admit an unreadable private ledger or a
partial counter as absence; their named assertions must also fail.

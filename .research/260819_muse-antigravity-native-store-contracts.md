# Muse and Antigravity native store contracts

Task: `TASK-260819-1ecd6x`  
Research date: 2026-08-19 (Asia/Tbilisi)  
Scope: provider facts needed by the Agent Session Manager (`ax`) v0.1.0 specification; no adapter implementation  
Probe host: macOS 26.5 (build 25F71), Darwin 25.5.0, arm64

## Executive result

The two providers do not have equivalent persistence contracts.

- **Muse has a real local, date-sharded native session store.** The durable handle is the session UUID. A controlled Muse 0.1.0 session remained discoverable by UUID after its `session.jsonl` was placed in a fresh XDG data root under a deliberately different date shard. Both offline export and headless continuation succeeded. This proves narrow materialization feasibility, not a supported portable-store contract: Muse documents its logs as read-only evidence, exposes export but no native import, embeds source-path and route metadata in the log, and maintains a session-local `cron.db` whose ownership/fencing semantics are undocumented.
- **Antigravity is backend-resolved with local cache and observation artifacts.** The documented `last_conversations.json` maps an absolute workspace path to a conversation UUID, but `agy -c` then asks the backend whether that UUID still exists. The UUID is the durable handle; the path is only a local selector. Persistent local transcripts and a SQLite conversation format exist, but Google does not document a standalone export/checkpoint/import contract that can recreate a missing backend conversation. A copied cache is therefore not a portable conversation.
- **Capability reporting must be asymmetric.** Muse `native_resume` is verified on the probed macOS build; its `portable_store` must remain false in a conservative v0.1.0 manifest until current-version, cross-host, cron-aware acceptance tests pass. Antigravity `native_resume` is conditional on the same authenticated backend/account realm resolving the UUID; `portable_store` is false. Neither provider exposes a documented external quiesce/stop RPC.
- **Platform parity is not proven.** Antigravity explicitly supports native macOS, Linux, and Windows and publishes amd64/arm64 installers. WSL2 follows the Linux installer path but is not named or tested in provider documentation. Muse's current stable manifest publishes macOS, Linux, and Windows artifacts, while its official launcher recognizes only macOS and Linux. Muse native Windows must therefore be reported as packaged but support/install/store behavior unknown.

## Evidence labels

- **Documented**: stated in a primary provider document, installer, release manifest, bundled provider document, or CLI help.
- **Probed**: reproduced non-destructively with an isolated store or read-only binary/source inspection.
- **Inferred**: follows from documented behavior but was not executed on that platform.
- **Unknown/unsupported**: the provider does not publish the needed contract, the surface is absent, or evidence conflicts.

## Provider evidence matrix

| Provider | Discovery root or index | Stable logical identity inputs | Native resume or import surface | Safe quiesce and stop | Materialization feasibility | Platform limits | Excluded machine-local state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Muse** | **Documented:** `${XDG_DATA_HOME:-$HOME/.local/share}/muse/sessions/YYYY/MM/DD/<session-uuid>/`. Durable payloads are `session.jsonl`, `subagent/<uuid>/session.jsonl`, and `tool-outputs/`. **Probed:** the session directory also contains `.session.lock` and `cron.db`; no separate global session index was observed. UUID lookup scans date shards. | **Documented/probed:** session UUID (`stream.kind=session`, `stream.id=<uuid>`). `workspace_root` and `cwd` are persisted absolute paths used for workspace scoping; they are metadata, not identity. Headless continuation permits an explicit destination path change with `--allow-workspace-switch`. | **Documented/probed:** `muse resume <uuid>`, `muse resume --last`, picker, and `muse exec --session-id <uuid>`. `muse export` emits schema-version-1 JSON and accepts UUID or `session.jsonl`, but no `muse import` command exists. Muse's bundled `/import` skill reads third-party transcripts into the current agent; it is not native-store import. | **Partial only:** the durable log records per-run `terminal` events and a clean `session.end` on normal headless exit. No `stop` command or external quiesce API is documented. Interactive stop-key behavior could not be validated in the available PTY harness. A safe adapter must pause input, wait for all provider work to reach a stable terminal boundary, request normal interactive exit, require process exit and store flush, and fail closed on timeout. `cron.db` means a main-turn terminal event alone is not proof that all scheduled/background work is inert. | **Narrow probe succeeded:** placing only a controlled `session.jsonl` beneath a fresh store at `2099/01/02/<same-uuid>/` allowed offline export and `muse exec --session-id` continuation, both exit 0. Full-fidelity portability is **not established**: subagent logs/tool outputs must accompany the main log; `cron.db` is durable scheduled-work state; there is no documented import/checkpoint API; current stable 0.2.1 was not executed. Advertise `portable_store=false` for v0.1.0 until those gates pass. | Installed/probed: 0.1.0 (`0.1.0-R708.1`) on macOS arm64. Official launcher: macOS and Linux, amd64/arm64. WSL2: Linux-path inference, untested. Current stable 0.2.1 manifest also contains Windows amd64/arm64 executables, contradicting the launcher's platform detector; native Windows support, data-root expansion, and behavior are unknown. Minimum OS versions are undocumented. | Never copy `~/.config/muse/auth.json`, API keys, launcher/device-login state, session-message sockets/tokens, `.session.lock` (the probe contained `pid=<number>`), live PIDs, or live SQLite `-wal`/`-shm`/lock state. Do not replicate plugin/update caches as session payload. Historical route facts inside the opaque durable log must never be treated as live process or ownership authority. |
| **Antigravity CLI** | **Documented cache:** `~/.gemini/antigravity-cli/cache/last_conversations.json` (absolute workspace path to UUID) and `cache/projects.json` (workspace/project discovery). **Documented observation root:** `~/.gemini/antigravity-cli/brain/<conversation-id>/.system_generated/logs/transcript.jsonl` plus conversation artifacts. **Documented format, unknown location contract:** SQLite is the CLI conversation format; `.db` and `.db-wal` are scanned by the picker. A binary string names `conversation_summaries.db`, but provider docs do not establish its exact root or authority. The backend remains authoritative for existence. | **Documented:** unique conversation UUID (`conversation_id`; `session_id` is an alias). Resume automatically restores the conversation's associated project. Successful resolution additionally depends on the destination's authenticated backend/account/configuration realm. Absolute workspace path is only a cache/picker selector, not the durable identity. | **Documented/probed help:** `agy --conversation <uuid>`, `agy -c` / `--continue`, and TUI `/resume`. The picker can import an Antigravity 2.0 desktop conversation by cloning history, context, and tool trajectories into a CLI conversation. No arbitrary file export/import or offline conversation restore command is documented. | **Documented managed-TUI boundary:** a provider `Stop` hook fires when the execution loop terminates and includes required `fullyIdle`; safe takeover requires `fullyIdle=true`. `/exit` closes the TUI; Esc halts streams. Current reference and the 1.0.11 changelog describe Ctrl+C differently, so a versioned adapter must not assume one press is a graceful stop while busy. No external quiesce/stop RPC is documented. After idle, exit normally and require the process and SQLite handles to close before snapshotting any local artifact. | **Cache materialization only:** a version-aware atomic merge can map the destination workspace path to the known UUID, after which the backend still validates it. Prefer explicit `agy --conversation <uuid>` and let the provider rebuild cache/project metadata. Copying `brain/`, a summary DB, or cache cannot recreate a backend-missing conversation. Direct copying of a live SQLite DB/WAL is unsafe and unsupported. Advertise `portable_store=false`. | Documented native macOS, Linux, Windows. Current installers publish amd64/arm64 for Darwin, Linux (glibc and musl selection), and Windows; installed/probed 1.1.14 on macOS arm64 matches the live Darwin manifest. WSL2 follows Linux detection but is not provider-named or tested; Linux keyring/DBus behavior is an additional constraint. Exact minimum OS versions and the Windows expansion of documented `~/.gemini/...` roots are unknown. | Never copy Apple Keychain/Linux Secret Service/Windows Credential Manager entries, OAuth/account profiles, `GEMINI_API_KEY`, MCP OAuth tokens or config secrets, updater `update.lock`/timestamps, sockets, PIDs, live DB locks, or live `*.db-wal`/`*.db-shm`. Logs/transcripts can contain prompts, source, paths, and secrets and require the mesh's trusted-project policy; they are not credentials to reuse. |

## Platform and capability cells

These values deliberately distinguish “provider can resume” from “`ax` can move the provider's store.” If the capability protocol is boolean, every conditional or unknown `portable_store` entry below should be emitted as `false` in v0.1.0, with detail in `probe`/`doctor` output.

| Provider/platform | `native_resume` | `portable_store` advertised in v0.1.0 | Materialize/resume plan | Quiesce/stop confidence |
| --- | --- | --- | --- | --- |
| Muse / macOS arm64, probed 0.1.0 | Yes, UUID and `--last` | False; narrow controlled probe only | Stage complete durable session directory; omit locks; validate UUID with offline export; resume explicitly. Do not claim cron parity. | Partial; durable boundaries observed, interactive exit unverified |
| Muse / macOS amd64 | Conditional; common CLI artifact/contract, not executed | False | Same XDG/home-relative plan after version/platform probe | Unknown until PTY acceptance test |
| Muse / Linux amd64/arm64 | Conditional; official launcher artifact, not executed | False | Same XDG plan after Linux acceptance test | Unknown until PTY acceptance test |
| Muse / WSL2 | Conditional inference from Linux detection | False | Treat as Linux only after filesystem, signal, browser/auth, and XDG tests | Unknown; do not infer native Windows behavior |
| Muse / native Windows amd64/arm64 | Unknown: artifacts exist in 0.2.1, but no supported install/store contract was found | False | No built-in materialization claim until Meta documents or a clean Windows probe establishes roots and behavior | Unknown |
| Antigravity / macOS amd64/arm64 | Yes, conditional on authenticated backend resolving UUID | False | Materialize workspace; invoke `--conversation`; merge/rebuild path cache only as derived metadata | High for boundary observation via `Stop.fullyIdle`; stop is managed TUI, not RPC |
| Antigravity / Linux amd64/arm64 (glibc or musl artifact selection) | Yes, same backend condition; family documented | False | Same; destination keyring/account is machine-local | Conditional on DBus/keyring and PTY acceptance tests |
| Antigravity / WSL2 | Conditional inference from Linux detection | False | Same Linux plan; require WSL2-specific auth, signal, path, and filesystem test | Unknown until WSL2 acceptance test |
| Antigravity / native Windows amd64/arm64 | Yes, family/architectures documented; not executed here | False | `%LOCALAPPDATA%\agy\bin\agy.exe`; explicit UUID resume; verify actual `%USERPROFILE%` data-root expansion before cache merge | Conditional on ConPTY and Windows file-lock tests |

`managed_pty` is an `ax` adapter/backend property, not proven merely because the provider has a TUI. For both providers it should be true only on provider/platform rows whose PTY/ConPTY interruption, idle detection, clean exit, and file-flush acceptance test passes. This research does not alter `appserver`, `task_board_primary`, `prompt_spawn`, or `native_goal_binding` cells.

## Muse findings

### Store layout and identity

Muse 0.1.0's bundled `read-session` document names the store and payload files. A controlled XDG-isolated `echo` session created:

```text
<XDG_DATA_HOME>/muse/sessions/2026/08/19/
  11111111-2222-4333-8444-555555555555/
    session.jsonl
    .session.lock
    cron.db
    cron.db-wal
    cron.db-shm
    subagent/<child-uuid>/session.jsonl
```

The first durable envelope used `stream.kind="session"` and the requested UUID. Early records stored `workspace_root`; route-fact records also stored `cwd`, a process ID, and terminal metadata. Later records included the provider run's `terminal="completed"`, final workspace branch state, and `session.end` with `exit_reason="clean"`.

The lock file contained a PID and is unequivocally machine-local/transient. `cron.db` was a SQLite database with `cron_jobs` fields for session ID, schedule, prompt, next/last fire times, status, claim time, and fire count. It is durable behavior state rather than a disposable index. Copying it can duplicate scheduled work unless the old owner is stopped and provider semantics are understood; dropping it loses native behavior. This is the main reason the narrow transcript probe does not justify `portable_store=true`.

The absolute source workspace is not the session identity. The UUID resolver found a copied log in an unrelated date shard, and headless resume permits a deliberate workspace change. `ax` should persist a logical workspace identity and map it to the destination path; it should never derive a cross-host session ID from the source absolute path.

### Resume, export, and materialization probe

Installed provider:

```text
Muse Code 0.1.0 (0.1.0-R708.1)
binary SHA-256 4290bfafa5bbb81a6fd493aaea12f848c789b1d22edfa0c4b849151deba3e70c
Meta Developer ID signature, timestamp 2026-08-05
```

The source session was created without provider credentials or private transcripts:

```bash
env XDG_CONFIG_HOME=<probe>/xdg/config \
    XDG_DATA_HOME=<probe>/xdg/data \
    XDG_STATE_HOME=<probe>/xdg/state \
    XDG_CACHE_HOME=<probe>/xdg/cache \
    MUSE_NO_AUTO_UPDATE=1 \
  muse exec --provider echo --workspace <probe>/workspace \
    --no-foreign-personal-context \
    --session-id 11111111-2222-4333-8444-555555555555 \
    --json native-store-probe
```

Result: exit 0 and a date-sharded durable log. For the materialization probe, only that controlled `session.jsonl` was copied to a fresh XDG root at `sessions/2099/01/02/<same-uuid>/`, with no global index. In the fresh root:

```bash
muse export --session 11111111-2222-4333-8444-555555555555 \
  --redacted --out <probe>/export.json

muse exec --provider echo --workspace <destination-workspace> \
  --session-id 11111111-2222-4333-8444-555555555555 \
  --allow-workspace-switch --json native-materialize-resume-probe
```

Both commands exited 0. The second appended to the copied session and created fresh destination runtime/cron state. This establishes that 0.1.0's UUID resolver scans the store rather than requiring a separate global index. It does not establish compatibility with real Meta-provider sessions, encrypted reasoning, non-empty tool outputs, active subagents, cron jobs, later versions, or other operating systems.

`muse export` is offline and self-contained, but it is one-way: it emits an export document and there is no corresponding native import command. The provider-bundled `import` skill treats external transcripts as read-only context and redirects Muse UUID continuation to `muse resume`; it does not install an export into the native store.

### Quiesce and stop

The CLI help lists resume, exec, export, trace, skills, sandbox, session messaging, auth, login/logout, and init; there is no stop command. The controlled headless run proved that durable turn and clean-session-end records are available after normal termination. The bundled read-session guidance also identifies `terminal` events as turn boundaries.

An interactive TUI exit probe was inconclusive because the available PTY could not satisfy Muse's cursor-position handshake; the process exited 1. A second attempt to combine the TUI-only echo delay option with `exec` was rejected by argument parsing with exit 2. Those failures are not evidence of provider failure, and no safe key/signal behavior is claimed from them.

Spec-safe takeover sequence:

1. Stop admitting new operator input.
2. Observe a stable terminal boundary for the foreground run and verify all known child/background work is terminal; a single main-run event is insufficient if cron or subagents remain active.
3. Ask the interactive provider to exit normally using a version/platform-tested PTY sequence.
4. Require process exit, closed SQLite handles, and a stable session log before snapshotting.
5. Exclude `.session.lock`, sockets, and WAL/SHM/lock artifacts; never use persisted route PID/path as authority.
6. If the idle/exit condition cannot be proven, fail graceful takeover closed and require the explicit force-takeover path. Do not silently send a kill signal and call it graceful.

### Platform contradiction

On 2026-08-19 the official stable channel reported `0.2.1-R1215.1`. Its official checksummed release manifest listed `x86_macos`, `aarch64_macos`, `x86_linux`, `aarch64_linux`, `x86_windows`, and `aarch64_windows`. The official launcher version 2, however, maps only Darwin/Linux and rejects every other `uname` pair. No primary Muse Windows installation, store-root, resume, or stop documentation was found. The safe specification statement is therefore:

> Muse 0.2.1 has provider-published Windows artifacts, but native Windows support and persistence behavior are unverified; do not advertise the adapter on native Windows yet.

This refines an otherwise tempting but unsupported “Windows parity” claim without contradicting the verified macOS/Linux launcher support.

## Antigravity findings

### Hybrid cache, local artifacts, and backend identity

Antigravity CLI 1.1.14 documents three different persistence roles:

1. `cache/last_conversations.json` maps the exact active absolute workspace path to the most recent conversation UUID. `agy -c` reads the map, then queries the backend. If the UUID is absent, deleted, or not resolvable, the CLI starts a new conversation.
2. `cache/projects.json` centralizes workspace-to-project discovery. Resuming a UUID automatically selects its associated project, so the destination should not invent a project from the source path.
3. `brain/<conversation-id>/.system_generated/logs/transcript.jsonl` is a documented persistent transcript path supplied to status-line scripts and hooks. It is an observation/history artifact, not documented as sufficient input to native resume.

The changelog says SQLite became the CLI conversation format in 1.0.4 and that 1.0.5's picker scans `.db` and `.db-wal`. Later entries describe a shared SQLite summary store. The 1.1.14 binary contains the name `conversation_summaries.db`, but neither the public docs nor a clean non-private probe establishes an exact authoritative DB root, schema, checkpoint procedure, or offline import operation. The report therefore does not promote that binary string into a store contract.

The stable logical handle is `conversation_id` (UUID); `session_id` is a compatibility alias. Backend/account/configuration realm is a resolution precondition. The absolute workspace path is local cache scope only. `ax` must map its logical workspace to the destination absolute path and must never copy the source-path key verbatim as identity.

### Resume and import surfaces

Verified CLI help on installed 1.1.14 exposes `--continue`, `--conversation`, `--project`, `--new-project`, and `--dangerously-skip-permissions`. Google documents:

- `agy -c` / `agy --continue` for the last conversation in the active workspace;
- `agy --conversation <conversation-id>` for an explicit UUID;
- `/resume` picker in the TUI;
- picker import from Antigravity 2.0, which clones desktop history, context, and tool trajectories into a CLI conversation;
- `/fork` to create an independent conversation, optionally in another project.

There is no documented arbitrary file export/import or offline restoration surface. A cross-host `ax` plan may carry the UUID, logical project/workspace references, and sanitized launch plan, but the destination still needs machine-local authentication that can resolve that UUID. If not, materialization must report `unsupported_backend_identity` (or equivalent) rather than create a blank conversation under the old name.

For `agy -c` convenience, a version-aware adapter can atomically merge the destination absolute path to UUID entry in the documented cache format while preserving unrelated keys. Explicit `agy --conversation <uuid>` is safer as the initial native resume because the provider can verify the backend and rebuild its own cache. `projects.json` should not be rewritten without a documented schema; explicit UUID resume restores the associated project.

### Quiesce and stop

Google's hook contract provides a stronger boundary than the Muse evidence. The `Stop` hook fires when an execution loop terminates and includes `terminationReason` and required `fullyIdle`. `fullyIdle=true` means background commands and asynchronous work have also ended. This can support a managed-PTY adapter's safe-turn detector; it is not a stop RPC and does not itself prevent new input.

The current CLI reference says Esc halts active streams, `/exit` closes the TUI, Ctrl+D exits from an empty prompt, and Ctrl+C terminates with confirmation while work is active. The 1.0.11 changelog instead specifies first Ctrl+C cancels active operations and a double press enters exit flow. The conservative sequence is:

1. Quiesce `ax` input.
2. If work is active, use the version-tested interruption key and treat the interruption as cancellation, not clean exit.
3. Wait for a `Stop` event with `fullyIdle=true`.
4. Invoke `/exit` or another version-tested normal-exit path.
5. Require process exit and closed SQLite files before collecting any local artifacts.

No external process-control API is documented. A `managed_pty` capability may be advertised only after this sequence passes on PTY/ConPTY for the exact provider/platform row.

### Platform support

Google explicitly states that Antigravity CLI runs natively on macOS, Linux, and Windows. The current Unix installer selects Darwin/Linux amd64 or arm64 and distinguishes Linux musl. The PowerShell installer selects Windows amd64 or arm64 and installs to `%LOCALAPPDATA%\agy\bin`. The installed macOS arm64 binary is Google Developer-ID signed and reports 1.1.14; the live Darwin arm64 manifest also reports 1.1.14.

WSL2 is not named in the provider docs. It should be treated as a conditional Linux row, not as native Windows: installer detection should work, but Linux Secret Service/DBus, browser OAuth, terminal signals, Windows-mounted filesystem locking/case behavior, and store paths need their own acceptance test. Provider docs do not state minimum supported OS releases.

## Contradictions and spec-safe refinements

| Evidence tension | Why it matters | Spec-safe recommendation |
| --- | --- | --- |
| Muse stable manifest publishes Windows binaries; launcher only supports macOS/Linux. | An artifact is not proof of supported install, data-root, or resume behavior. | Mark Muse/native-Windows support `unknown`, `native_resume=false` and `portable_store=false` in a boolean manifest until a primary contract or clean probe exists. |
| Muse copied `session.jsonl` resumed in a controlled probe; bundled guidance says logs are read-only and no import API exists. | Technically readable placement is not a compatibility promise. | Describe materialization as guarded/experimental; advertise `portable_store=false` until current-version cross-host tests and a compatibility policy exist. |
| Muse's session directory contains durable `cron.db` in addition to the documented transcript payloads. | Copying can duplicate scheduled work; dropping it loses behavior. | Treat cron-aware portability as unsupported for v0.1.0. Quiesce/stop the old owner before any closed snapshot; never activate the same cron state on replicas/forks without a provider-safe policy. |
| Muse durable history contains absolute paths and route PID/terminal facts. | These can be mistaken for identity or owner authority. | Keep opaque provider history inert; derive identity/ownership only from `ax` records and UUID. Exclude live lock/PID artifacts. If the exclusion is intended to ban even historical PID values inside opaque logs, native byte-preserving materialization is impossible and the spec must say so explicitly. |
| Antigravity's continue cache is keyed by absolute path, while settled input says source paths are not identities. | Copying the source key would break destination lookup and fake portability. | Rewrite/merge only the destination mapped path as derived cache metadata; use UUID plus backend resolution as the durable handle. |
| Antigravity uses local SQLite/transcripts but backend verification controls resume. | Local files can look like a portable store while being insufficient. | Keep `native_resume=conditional`, `portable_store=false`; never claim cache/transcript copy recreates a conversation. |
| Antigravity reference and changelog differ on busy Ctrl+C behavior. | A single keypress could cancel work or initiate exit depending on version/state. | Version-test the PTY sequence, prefer `Stop.fullyIdle` as the boundary, and fail closed instead of treating Ctrl+C as a universal graceful-stop API. |

## Task logbook

### 2026-08-19 — native-store parity blockers and refinements

- Muse's current release manifest includes Windows executables, but the current official launcher rejects non-Darwin/Linux platforms. Record native Windows as packaged/unverified, not supported parity.
- Muse UUID transcript placement works in the controlled 0.1.0 probe, but the session directory also owns a durable cron database. Full portable-store capability would need scheduled-work ownership/fencing and current-version compatibility evidence.
- Antigravity's documented workspace cache is a derived selector; the backend verifies the UUID. Cache or transcript materialization must never be reported as offline conversation portability.
- Antigravity exposes `Stop.fullyIdle` as a useful safe-boundary signal, while current reference and historical changelog wording conflict on Ctrl+C. Use versioned managed-PTY tests and fail graceful takeover closed when idle cannot be proven.
- Recommendation for the v0.1.0 capability matrix: Muse and Antigravity both advertise `portable_store=false`; their distinct native-resume conditions remain visible in structured probe/doctor detail.

## Exclusion contract

| State class | Muse | Antigravity | `ax` treatment |
| --- | --- | --- | --- |
| Credentials / machine auth | `~/.config/muse/auth.json`, API keys, device-login state | OS keyring tokens, account profiles, API-key environment, MCP OAuth tokens/config secrets | Never replicate; destination authenticates locally |
| Live process identity | `.session.lock` contains PID; route facts contain historical PID/path | No documented portable PID; process/runtime state is local | Never copy lock/PID control artifacts or use historical values as authority |
| Sockets / IPC | `session-message` runtime sockets/tokens | Any runtime IPC/socket state | Never replicate; recreate locally if needed |
| Transient locks / updater state | `.session.lock`, live SQLite locks/WAL/SHM, plugin/update cache locks | updater `update.lock`, `last_check.timestamp`, live DB locks/WAL/SHM | Exclude; snapshot only after provider close/checkpoint |
| Durable but sensitive history | session/subagent JSONL and tool outputs | brain transcripts/artifacts; local DB content if ever supported | Trusted-mesh payload only; validate and avoid logging contents |
| Durable scheduled/background state | `cron.db`, semantics not portable | backend task/conversation state; local representation undocumented | Do not claim parity; require provider-specific fencing/restore contract |

## SPEC.md traceability and cells unblocked

`SPEC.md` did not exist in the repository at research time. The names below use the exact settled-input section headings and define the cells the authoring task can populate.

### `§ Providers and native stores`

Unblocked `Native store contract matrix` cells:

- `Muse.discovery_root_or_index`
- `Muse.logical_identity_inputs`
- `Muse.native_resume_surfaces`
- `Muse.native_import_surfaces`
- `Muse.quiesce_boundary`
- `Muse.stop_surface`
- `Muse.materialization_plan`
- `Muse.portability_limits`
- `Muse.machine_local_exclusions`
- the same nine cells for `Antigravity`

Unblocked `Provider/platform capability matrix` cells:

- `(Muse, macOS|Linux|WSL2|native Windows) × (native_resume, portable_store, managed_pty)`
- `(Antigravity, macOS|Linux|WSL2|native Windows) × (native_resume, portable_store, managed_pty)`

`managed_pty` remains acceptance-test-gated as stated above. `appserver`, `task_board_primary`, `prompt_spawn`, and `native_goal_binding` are not established by this research and must not be inferred from native resume.

### `§ Task-board integration`

Unblocked capability-reporting rules:

- `native_resume` and `portable_store` are independent.
- A conditional backend UUID resume is not a portable store.
- A successful controlled file-placement probe is not a provider-supported import contract.
- Platform rows carry evidence/version status; unsupported and unknown are distinct from false-by-provider-design.

This prevents fake parity without changing the settled task-board spawn/goal-binding claims.

### `§ Mesh and replication`

Unblocked cells:

- `provider_snapshot.include`
- `provider_snapshot.exclude`
- `provider_snapshot.quiescence_precondition`
- `provider_snapshot.validation`
- `workspace_path_mapping_to_provider_cache`

The matrix above supplies the Muse lock/cron distinction, Antigravity cache/backend distinction, and both providers' credential/PID/socket/lock exclusions.

### `§ Attach, takeover, failure, and fork`

Unblocked cells:

- `Muse.graceful_takeover.safe_boundary` and `.stop_sequence`
- `Antigravity.graceful_takeover.safe_boundary` and `.stop_sequence`
- both providers' `force_takeover.warning_and_preservation` rationale
- `fork.provider_state_limitations` (especially Muse cron and Antigravity backend fork/import)

### `§ Implementation stack and delivery`

Unblocked automated acceptance rows:

- all eight provider/platform rows in the platform table above;
- Muse UUID scan/materialize/export/resume and cron/lock exclusion gates;
- Antigravity backend UUID/cache mapping, `Stop.fullyIdle`, closed-DB, and missing-backend negative gates.

## Required acceptance probes for adapter promotion

### Muse

1. Run on the exact supported Muse version on macOS and Linux; separately test WSL2 and any documented native Windows build.
2. Create an isolated real-provider session with subagent logs, externalized tool output, encrypted reasoning, and a benign cron job.
3. Quiesce and cleanly stop it; prove no live child/cron work remains.
4. Snapshot only closed durable state, excluding `.session.lock`, socket/PID state, and live WAL/SHM.
5. Materialize under a different destination absolute workspace path and date shard.
6. Validate offline export, picker discovery, explicit UUID resume, `--last` workspace behavior, child/tool-output fidelity, and cron behavior.
7. Prove fork does not duplicate scheduled work and replica materialization cannot execute it.
8. Repeat across a compatible upgrade and a deliberately incompatible fixture; fail closed on unknown schema/version.

### Antigravity

1. Test explicit UUID resume under the same destination account/backend and under a different/no account; the latter must fail without creating fake parity.
2. Verify destination path-cache creation/merge and preservation of unrelated entries.
3. Test backend-deleted UUID behavior: no silent blank conversation may be presented as resumed.
4. Exercise `Stop` hook cases with `fullyIdle=false` and `true`, foreground interruption, background command, and subagent activity.
5. Close normally and prove DB handles/WAL/SHM are settled before any local snapshot inspection.
6. Copy cache, brain transcript, and any discovered SQLite file into an isolated profile and confirm they are not advertised as a portable restore unless a provider import contract appears.
7. Run PTY on macOS/Linux/WSL2 and ConPTY on native Windows; test Ctrl+C/Esc differences for the exact CLI version.
8. Test account/project/custom-endpoint realm changes and preserve machine-local credentials only at destination.

## Unknowns and unsupported facts

- Muse 0.2.1 store, cron, resume, and stop behavior was not executed; the installed probe was 0.1.0.
- Muse native Windows installation/support, Windows data/config roots, and PTY behavior are unknown despite release artifacts.
- Muse's supported minimum macOS/Linux/Windows versions are not published in the primary material inspected.
- Muse's provider-safe interactive quiesce/exit key sequence and full-idle signal are unknown.
- Muse has no documented native import for its export document.
- Whether Muse permits a portable, fenced transfer of non-empty `cron.db` is unknown.
- Antigravity's exact authoritative conversation DB root, filename, schema, checkpoint/export contract, and offline restore behavior are undocumented.
- Antigravity local transcript/brain material is not proven sufficient for resume.
- Antigravity WSL2 support is inferred from Linux detection, not named or tested by Google in the inspected docs.
- Antigravity minimum OS versions and exact native-Windows expansion of the documented home-relative data roots are unknown.
- No private user sessions were inspected for either provider.

## Primary sources and provider versions

All URLs were retrieved on 2026-08-19.

### Muse / Meta

1. [Muse Code product page](https://dev.meta.ai/docs/muse-code/) — provider identity and general session capability; page content was dynamically rendered, so no undocumented store detail was extracted from it.
2. [Official Muse launcher](https://api.meta.ai/muse-launcher.sh) — launcher version 2, credential path, supported `uname` mappings, checksummed install flow.
3. [Muse stable channel](https://api.meta.ai/muse-code/channels/muse-stable) — live stable `0.2.1-R1215.1`.
4. [Muse 0.2.1 release manifest](https://lookaside.facebook.com/lookaside/muse/download/?channel=muse&version=0.2.1-R1215.1&file=manifest.json) — checksummed macOS/Linux/Windows artifacts.
5. Provider-bundled `muse-core/read-session` document from installed Muse 0.1.0, SHA-256 `99e4f19f687d0de374523fb2c663dce82c5257bbe0d508f93bde56093c8ea84b` — store layout, event envelope, terminal boundary, first-party commands.
6. Provider-bundled `muse-core/import` document, SHA-256 `1e61bbb65f493501cce2e7cc2394408251c36b1fe0c7c91b69befd6f5f154cb1` — native Muse UUID redirect and third-party transcript semantics.
7. Installed CLI help/version and isolated implementation probes, Muse Code 0.1.0 (`0.1.0-R708.1`), signed by Meta Platforms, Inc.; binary SHA-256 above.

### Antigravity / Google

1. [Installation and authentication](https://antigravity.google/docs/cli/install/) — native OS families, install paths, machine-local keyrings and API-key mode.
2. [Managing conversations](https://antigravity.google/docs/cli/conversations/) — workspace scoping, continue, fork.
3. [Resume command](https://antigravity.google/docs/cli/commands/resume/) — picker/import surfaces, cache path/format, backend verification.
4. [Projects](https://antigravity.google/docs/cli/projects/) — default/explicit project and project restoration on UUID resume.
5. [Status-line contract](https://antigravity.google/docs/cli/statusline/) — `conversation_id`, `session_id`, workspace and transcript fields.
6. [Hooks contract](https://antigravity.google/docs/hooks/) — CLI app-data root, persistent transcript path, `Stop` and `fullyIdle`.
7. [CLI reference](https://antigravity.google/docs/cli/reference/) — `/exit`, `/resume`, Esc, Ctrl+C, Ctrl+D.
8. [Antigravity changelog](https://antigravity.google/changelog/) — 1.0.4 SQLite/project cache, 1.0.5 DB/WAL picker scan, 1.0.11 Ctrl+C behavior, later SQLite lifecycle fixes.
9. [Troubleshooting](https://antigravity.google/docs/cli/troubleshooting/) — keyring/DBus constraints and updater lock/timestamp.
10. [MCP configuration](https://antigravity.google/docs/cli/mcp/) — OAuth token and secret-bearing configuration exclusions.
11. [Official Unix installer](https://antigravity.google/cli/install.sh), [PowerShell installer](https://antigravity.google/cli/install.ps1), and [live Darwin arm64 manifest](https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests/darwin_arm64.json) — architecture/platform mapping and current 1.1.14 release.
12. Installed CLI help/version and read-only binary inspection, Antigravity CLI 1.1.14, signed by Google LLC on 2026-08-18; binary SHA-256 `95ac56b30400c7e048ca8567c9ea80be26eebaddea288957fe5ae4c2acf45cd1`.

## Fact-check ledger

| Claim | Independent checks | Result |
| --- | --- | --- |
| Muse store root and date sharding | Provider-bundled document; isolated XDG session tree | Verified on 0.1.0 |
| Muse UUID is stable handle, not date/path | CLI help; log envelope; copied log resolved in unrelated 2099 shard | Verified on controlled 0.1.0 session |
| Muse native resume exists | `resume`/`exec` help; materialized headless continuation | Verified on macOS 0.1.0 |
| Muse export is not import | export help; command inventory; bundled import semantics | Verified absence in 0.1.0 surface; future versions unknown |
| Muse full store is not yet safely portable | undocumented direct placement; durable cron DB; lock PID; no import contract | Portable parity not established |
| Antigravity path cache is not identity | resume guide's backend verification; status-line UUID; projects contract | Verified by primary docs |
| Antigravity has local persistent files but backend resume | hooks/status-line app-data paths; changelog SQLite; resume backend workflow | Verified distinction; exact DB contract unknown |
| Antigravity resume/import surfaces | installed help; resume guide; conversations/projects docs | Verified for 1.1.14 docs/binary |
| Antigravity safe boundary can distinguish background work | hooks `Stop.fullyIdle`; reference/changelog stop controls | Boundary documented; external quiesce RPC absent |
| Platform coverage | provider install docs/scripts/manifests; installed signatures/versions | OS/architecture families verified as labeled; WSL2/minimum versions remain unknown |

## Probe exit-code ledger

Commands used as evidence were run directly; no private transcript roots were searched.

| Probe | Exit code | Interpretation |
| --- | ---: | --- |
| `muse --version`, `muse --help`, `muse resume --help`, `muse exec --help`, `muse export --help` | 0 each | Installed 0.1.0 surfaces read successfully |
| Isolated Muse echo session | 0 | Controlled durable store created |
| Fresh-root Muse export by copied UUID | 0 | UUID discovery without a separate copied index |
| Fresh-root Muse headless continuation by copied UUID | 0 | Narrow materialization/resume feasibility |
| Muse interactive TUI PTY attempt | 1 | Harness cursor-position handshake failed; stop behavior remains unknown |
| Muse delayed-headless option attempt | 2 | CLI argument parser rejected a TUI-only option combination; not a stop result |
| `agy --version`, `agy --help` | 0 each | Installed 1.1.14 surfaces read successfully |
| Official provider documents/installers/manifests used above | 0 for cited successful GETs | Current primary material retrieved |
| SHA-256 and code-signature inspections | 0 | Local provider artifacts identified reproducibly |

No product code was produced, no private user sessions were inspected, and no credential or machine-authentication state was read.

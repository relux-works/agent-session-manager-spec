# Agent Session Manager (<code>ax</code>) v0.2.0 Normative Specification

| Field | Value |
| --- | --- |
| Specification release | <code>v0.2.0</code> |
| Document status | Review candidate and implementation contract |
| Public command | <code>ax</code> |
| Repository | <code>relux-works/agent-session-manager-spec</code> |
| Default branch | <code>main</code> |
| License | MIT |
| Author | Ivan Oparin <code>&lt;oparin@me.com&gt;</code> |
| Required release signature | SSH signing key <code>~/.ssh/ivanopcode</code> |

This document is the normative, implementation-ready contract for Agent Session
Manager v0.2.0. It specifies behavior; it does not implement <code>ax</code>.
Provider facts explicitly marked conditional, unknown, or unsupported are
version gates, not permission to invent parity.

## 1. Conformance, language, and scope

### 1.1 Normative language

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL are to be interpreted as
normative requirements when, and only when, they appear in uppercase.

A conforming implementation MUST satisfy every MUST and MUST NOT applicable to
its declared conformance targets. A deviation MAY exist only behind an
experimental feature gate that is disabled by default, is reported by
<code>ax doctor</code>, and is never advertised as an available capability.

### 1.2 Product boundary

<code>ax</code> manages durable coding-agent sessions across an explicitly
trusted, allowlisted mesh of computers. It MUST let an operator:

1. launch a direct provider session or a task-board-managed session;
2. keep the terminal durable across a local terminal disconnect and, where the
   terminal backend supports it, a reboot;
3. list ownership and replica state across the mesh;
4. synchronize immutable session metadata, provider state, task-board state,
   and the workspace state required to resume;
5. attach to the current owner without changing ownership;
6. transfer ownership gracefully or, as an explicit recovery action, forcibly;
7. fork from a checkpoint into a new logical session and workspace identity;
8. stop a session without deleting its durable state; and
9. resume a stopped session on its owner host.

The v0.2.0 product is a Go CLI, optional per-user background service, provider
plugin host, terminal supervisor, SSH RPC client/server, and Go-native
replication engine. It is not:

- a cloud service, public relay, or multi-tenant scheduler;
- a replacement for a provider's native session store;
- a replacement for task-board or <code>tb-sessiond</code>;
- a general-purpose backup, secrets manager, or source-control system;
- a distributed shell that auto-authorizes discovered machines;
- a guarantee that every provider supports every operation; or
- an encrypted-at-rest snapshot product.

There MUST be no permanent public TCP listener. The remote server entry point is
<code>ax rpc serve --stdio</code>, normally started by Tailscale SSH or ordinary
OpenSSH.

### 1.3 Conformance targets

An implementation MUST declare one or more of these targets:

| Target | Required behavior |
| --- | --- |
| Core CLI | Configuration, records, ownership, local list/status, direct provider lifecycle, structured errors |
| Unix terminal backend | PTY management plus tmux integration on macOS, Linux, or WSL2 |
| Windows terminal backend | Native PowerShell process supervision and ConPTY; no tmux claim |
| Mesh peer | SSH stdio RPC, anti-entropy union sync, resumable blob transfer, staging, validation |
| Workspace materializer | Conflict-safe Git and non-Git capture/materialization |
| Provider adapter | Plugin protocol and only the capabilities advertised by probe |
| Task-board bridge | Official opaque export/import/open/adopt bundle contract |
| User service | Periodic health and sync work while preserving daemonless core CLI use |

An <code>ax</code> implementation release MUST identify each built-in provider/platform cell as available,
conditional, unsupported, or unknown. Conditional and unknown cells MUST behave
as unavailable until their acceptance gate passes.

### 1.4 Source authority and evidence

The settled product and architecture decisions attached to
<code>TASK-260819-1h306n</code> are the product authority for this release. The
accepted provider research from <code>TASK-260819-1ecd6x</code>, preserved in
[the Muse and Antigravity evidence report](.research/260819_muse-antigravity-native-store-contracts.md),
is the authority for those two adapters. Its retained unknowns MUST remain
unknown or unsupported in v0.2.0.

The Codex command and unrestricted profile facts in this specification are
cross-checked against the
[official Codex CLI command reference](https://developers.openai.com/codex/cli/reference/).
Other provider references are listed in Appendix C. When provider documentation
and a probe disagree, the more restrictive status MUST win until a
version-specific acceptance test resolves the difference.

### 1.5 Normative contract registry

Every independently consumed contract has an independent Semantic Version.
The following versions are active in v0.2.0:

| Contract | Schema identifier | Version |
| --- | --- | --- |
| Configuration | <code>urn:ax:schema:config</code> | <code>1.0.0</code> |
| Provider protocol | <code>urn:ax:protocol:provider</code> | <code>2.0.0</code> |
| Provider manifest | <code>urn:ax:schema:provider-manifest</code> | <code>1.0.0</code> |
| Provider probe | <code>urn:ax:schema:provider-probe</code> | <code>1.0.0</code> |
| Mesh RPC | <code>urn:ax:protocol:rpc</code> | <code>2.0.0</code> |
| Session record | <code>urn:ax:schema:session-record</code> | <code>1.0.0</code> |
| Session event | <code>urn:ax:schema:session-event</code> | <code>1.0.0</code> |
| Lease record | <code>urn:ax:schema:lease</code> | <code>1.0.0</code> |
| Checkpoint record | <code>urn:ax:schema:checkpoint</code> | <code>1.0.0</code> |
| Workspace group | <code>urn:ax:schema:workspace-group</code> | <code>1.0.0</code> |
| Provider identity | <code>urn:ax:schema:provider-identity</code> | <code>1.0.0</code> |
| Blob descriptor | <code>urn:ax:schema:blob</code> | <code>1.0.0</code> |
| Transfer manifest | <code>urn:ax:schema:transfer-manifest</code> | <code>1.0.0</code> |
| Transfer chunk descriptor | <code>urn:ax:schema:chunk</code> | <code>1.0.0</code> |
| Tombstone | <code>urn:ax:schema:tombstone</code> | <code>1.0.0</code> |
| Tombstone acknowledgement | <code>urn:ax:schema:tombstone-ack</code> | <code>1.0.0</code> |
| Materialization plan | <code>urn:ax:schema:materialization-plan</code> | <code>1.0.0</code> |
| Materialization recovery state (journal and managed-replica marker variants) | <code>urn:ax:schema:materialization-journal</code> | <code>2.0.0</code> |
| Task-board bridge | <code>urn:ax:protocol:task-board-bridge</code> | <code>1.0.0</code> |
| Task-board bundle | <code>urn:ax:schema:task-board-bundle</code> | <code>1.0.0</code> |
| Structured error | <code>urn:ax:schema:error</code> | <code>1.0.0</code> |
| Observation event | <code>urn:ax:schema:observation</code> | <code>1.0.0</code> |
| CLI result | <code>urn:ax:schema:cli-result</code> | <code>1.0.0</code> |

No contract version is implied by the <code>ax</code> executable version.
Section 17 defines compatibility and migration. Independent versioning means
that a contract may release on its own cadence; an embedding protocol may
still bind one exact version. Provider and RPC major 2 and bridge major 1 bind
Structured Error 1.0.0 as Section 15.1 specifies instead of negotiating it
separately.
Embedded structures not listed here—including Git/non-Git member descriptors,
capability entries, RPC operation bodies, and bundle members—inherit the
version of their containing contract. They MUST NOT be negotiated or migrated
as if they had an implicit independent version.

### 1.6 Common data rules

Every complete normative schema object MUST contain <code>schema</code> and
<code>schema_version</code>. Protocol envelopes instead contain
<code>protocol</code> and <code>protocol_version</code> and MAY carry a
schema-versioned body. A code block explicitly labeled as an embedded object or
success body is a fragment of its named containing contract and therefore does
not repeat the containing schema/protocol members.

The common logical data model has these rules:

- map keys MUST be UTF-8 strings and MUST be unique;
- text MUST be valid UTF-8 and SHOULD be NFC-normalized;
- floating-point numbers, NaN, Infinity, non-string map keys, and duplicate
  keys are forbidden;
- JSON integers MUST be mathematically integral and lie in the interoperable
  safe-integer interval <code>[-9007199254740991, 9007199254740991]</code>;
- the type name <code>uint53</code> means a JSON integer in
  <code>[0, 9007199254740991]</code>; the current contract set does not use JSON numbers
  for a wider unsigned domain;
- a field explicitly typed <code>decimal_uint64</code> is instead a JSON string
  matching <code>0|[1-9][0-9]{0,19}</code> whose numeric value is at most
  <code>18446744073709551615</code>; leading plus signs and leading zeroes are
  forbidden;
- bytes MUST be represented as a content-addressed blob or unpadded base64url;
- timestamps MUST be UTC RFC 3339 with at least millisecond precision;
- durations MUST be integer milliseconds;
- enumerations are case-sensitive lower snake case;
- identifiers created by <code>ax</code> MUST be UUIDv7 strings unless a field
  explicitly defines a digest identifier;
- SHA-256 digest identifiers MUST use <code>sha256:</code> followed by exactly
  64 lowercase hexadecimal characters; and
- platform-neutral relative paths MUST use forward slashes, MUST NOT begin with
  a slash or drive prefix, MUST NOT contain an empty segment, <code>.</code>,
  <code>..</code>, a NUL byte, or an encoded path separator.

<code>base64url</code> means the canonical RFC 4648 URL-safe alphabet
<code>[A-Za-z0-9_-]</code> with no padding and no whitespace; decoding then
re-encoding MUST reproduce the string byte-for-byte. The compact type
<code>base64url-256+</code> uses that encoding for 32–512 bytes and is reserved
for random machine-local control/rollback tokens. A protocol field carrying
payload bytes uses its separately declared decoded-size limit instead.

<code>absolute-path</code> means a 1–32,767 character, NUL-free path that is
absolute and lexically normalized for the platform named by its containing
request: POSIX-rooted on macOS/Linux/WSL2, or drive-qualified/UNC on native
Windows. It contains no <code>.</code> or <code>..</code> segment. Receivers
still resolve symlinks/reparse points beneath an allowed root before mutation.
An absolute path is machine-local routing data and never a logical identity or
replicated source-path key.

Immutable objects MAY be encoded as UTF-8 JSON or CBOR using the core
deterministic encoding requirements of RFC 8949 Section 4.2.1. Their
identity MUST be the SHA-256 digest of the RFC 8785 JSON Canonicalization
Scheme (JCS) form of the logical object with its schema-defined self-identity
field omitted. Those
fields are <code>record_id</code>, <code>event_id</code>,
<code>checkpoint_id</code>, <code>descriptor_id</code>,
<code>manifest_id</code>, <code>plan_id</code>, <code>tombstone_id</code>, or
<code>ack_id</code>, <code>bundle_id</code>, or <code>marker_id</code>, as
applicable. Section 10.3 separately defines a
<code>chunk_id</code> as the digest of raw chunk bytes; mutable journals and
observation streams are not identity-addressed objects. A CBOR decoder MUST
reject values outside the common logical data model and MUST produce the same
canonical JSON digest. This rule prevents JSON and CBOR encodings of one object
from creating two identities.

JCS object property names MUST be ordered lexicographically by their UTF-16
code units as required by RFC 8785 Section 3.2.3. An implementation whose native
string ordering uses Unicode scalar values, UTF-8 bytes, locale collation, or
another ordering MUST explicitly derive the UTF-16 ordering before hashing.
The common logical data model forbids floating-point values, so the remaining
JCS number surface is limited to the safe integers defined below. Decoders MUST
reject lone surrogate code points before canonicalization.

The safe-integer restriction is part of every 1.0.0 JSON, CBOR, identity, and
wire contract. A decoder MUST reject a numeric literal at or beyond
<code>2^53</code> even if its host language can represent it, and MUST reject a
CBOR integer outside the safe interval unless the schema field is explicitly a
<code>decimal_uint64</code> string. Implementations MUST NOT round a value and
continue. These language-neutral boundary fixtures are normative:

| Fixture | UTF-8 JCS bytes | Expected result |
| --- | --- | --- |
| <code>NUM-SAFE-MAX</code> | <code>{"n":9007199254740991}</code> | Accept for a <code>uint53</code> field; SHA-256 <code>e1da48c6a6089f06ecb4e0a2259e658e3786b2420f52baccdf929ec6460d7b41</code> |
| <code>NUM-UNSAFE-NUMBER</code> | <code>{"n":9007199254740992}</code> | Reject before identity calculation with <code>incompatible_schema</code> |
| <code>NUM-UNSAFE-ROUND</code> | <code>{"n":9007199254740993}</code> | Reject from the JSON number token before conversion to a host double; an implementation that first rounds it to 9007199254740992 is nonconforming |
| <code>NUM-U64-STRING</code> | <code>{"n":"9007199254740992"}</code> | Accept only when <code>n</code> is typed <code>decimal_uint64</code>; SHA-256 <code>bb80eb37329e0a7e980fe3638c9722c44ac3184f7488f20c28cf67ae0b5f4f96</code> |
| <code>NUM-U64-MAX</code> | <code>{"n":"18446744073709551615"}</code> | Accept only when <code>n</code> is typed <code>decimal_uint64</code>; SHA-256 <code>b0ec84c6bb6a7c030549f17dd482975d09c40ff9e5f83d4438ebeac12d3b6331</code> |
| <code>NUM-U64-LEADING-ZERO</code> | <code>{"n":"01"}</code> | Reject for <code>decimal_uint64</code> |
| <code>NUM-U64-OVERFLOW</code> | <code>{"n":"18446744073709551616"}</code> | Reject for <code>decimal_uint64</code> |
| <code>JCS-UTF16-ORDER</code> | <code>{"𐀀":2,"":1}</code> | Accept in this exact property order; U+10000 sorts before U+E000 by UTF-16 code units; SHA-256 <code>9d4cdc71dda603c42f9b21d88d0c2ffc31a76cd1bd461d7359406cf169845f1e</code> |

Wall-clock timestamps are diagnostic metadata and MUST NOT decide ownership or
event order. Lease epochs, predecessor links, and deterministic conflict rules
do.

Unknown fields MAY be retained only under an <code>extensions</code> map whose
keys are reverse-DNS names. A reader MUST reject an unknown top-level field in a
major version 1 object. This fail-closed rule prevents silently ignoring a new
ownership or security control.

The field tables and tagged-union signatures in this document use these exact
rules. A field is required unless its type ends in <code>?</code>; a required
<code>T|null</code> field MUST be present and MAY contain JSON null. Array
bounds are inclusive. <code>string[n..m]</code> bounds UTF-8 characters;
<code>array&lt;T&gt;[n..m]</code> is an array, and the compact phrase
<code>sorted unique T[n..m]</code> means such an array with bytewise canonical
ordering and no duplicate. A bare numeric type
(<code>uint8</code>, <code>uint16</code>, <code>uint32</code>,
<code>uint53</code>, or <code>int32</code>) followed by
<code>[n..m]</code> instead bounds its numeric value. Any other named
non-string type followed directly by <code>[n..m]</code> is an array of that
type. <code>map(K,V)</code> means a JSON object whose member
names satisfy K and whose values satisfy V; those member names are data, not
schema fields. Every other embedded object is closed: an unknown member MUST be
rejected even when its containing top-level object is otherwise valid. An
explicit <code>extensions</code> member is the only open extension point and
its keys MUST be reverse-DNS names. A field described as a schema object MUST
contain the complete object, including its own <code>schema</code> and
<code>schema_version</code>, and MUST validate against the named section.

Every <code>extensions</code> object is
<code>map(reverse-dns,ExtensionValue)[0..64]</code>. A reverse-DNS key is 3–253
lowercase ASCII characters, contains at least one dot, and has dot-separated
labels matching <code>[a-z][a-z0-9-]{0,62}</code>. ExtensionValue is JSON null,
boolean, a common-model integer, string, array, or string-keyed object with
maximum nesting depth 4; the complete canonical extensions object is at most
65,536 bytes. An extension MUST NOT shadow, weaken, or be required to interpret
a core ownership, fencing, path-safety, secret-exclusion, or transaction fact.
Unsupported extensions are preserved as data only under the Section 17 rules.
They remain subject to Section 16's credential, authentication-state, and
payload-exclusion rules.

## 2. Product and operator model

### 2.1 Terms

| Term | Normative definition |
| --- | --- |
| Logical session | The provider-independent durable unit identified by <code>session_id</code>. A resume does not create a new logical session. |
| Session name | A mesh-unique human alias of 1–64 characters matching <code>[A-Za-z0-9][A-Za-z0-9._-]{0,63}</code>. |
| Owner | The one host selected by the winning lease that MAY run or resume the logical session. |
| Replica | A host holding synchronized durable state that MUST NOT run or resume the logical session without takeover or fork. |
| Host | A machine with a stable UUIDv7 <code>host_id</code>, one configured platform, and one allowlist entry. |
| Lease | An immutable ownership grant containing an epoch, predecessor, holder, and fencing token. |
| Lease epoch | A monotonically increasing positive <code>uint53</code> counter scoped to one logical session. |
| Fencing token | The winning <code>lease_id</code> and epoch pair carried by every owner-authored event and mutation. |
| Checkpoint | An immutable, validated reference set for provider, workspace, board, and session records at a safe boundary. |
| Fork | A new logical session and new workspace identity derived from a checkpoint, with independent lease and event history. |
| Workspace | One Git worktree/repository or one managed non-Git directory with a logical ID independent of its absolute path. |
| Workspace group | The atomic migration set for sessions sharing one checkout or otherwise requiring coordinated materialization. |
| Provider identity | Provider ID, native durable handle, logical workspace mapping, and non-secret backend-realm fingerprint needed to resolve a native session. |
| Direct session | A session launched and persisted through a provider adapter and native provider store. |
| Task-board session | A session whose private provider mechanics remain owned by <code>tb-sessiond</code> and cross the boundary only as an opaque official bundle. |
| Safe boundary | A provider-reported or adapter-proven point at which no foreground, child, scheduled, or background work can still mutate durable state. |
| Managed replica | A destination path created or explicitly adopted by <code>ax</code>, with a recorded last-materialized checkpoint. |

### 2.2 Global invariants

The following invariants are unconditional:

1. Every non-tombstoned logical session MUST have exactly one winning lease and
   therefore exactly one logical owner, plus zero or more replicas.
2. A replica MUST NOT launch, resume, accept input for, or publish authoritative
   events for a logical session.
3. Every owner-authored event MUST carry the winning lease epoch and lease ID.
   A peer MUST reject lower-epoch or losing same-epoch events from the
   authoritative history and preserve them in a divergent-history branch.
4. Absolute source paths, process IDs, terminal IDs, socket names, and provider
   route facts MUST NOT be cross-host identity.
5. Provider credentials, environment secrets, authentication state, live PIDs,
   sockets, transient locks, and live database WAL/SHM files MUST NOT be
   replicated.
6. The live SQLite index MUST NOT be copied or synchronized. It is rebuildable
   derived state.
7. Replication MUST be a set union of immutable identity-addressed records and
   events plus content-addressed blobs, followed by deterministic derivation.
8. Materialization MUST stage, validate, detect conflicts, and commit
   atomically where supported. It MUST never silently overwrite divergent
   destination state.
9. A deletion MUST be represented by a scoped tombstone. A receiver MUST NOT
   treat any tombstone as authority for a broad recursive delete.
10. The persisted execution profile MUST be used on both initial launch and
    every resume. An adapter MUST NOT silently downgrade <code>yolo</code>.
11. A capability not proven for the exact provider/version/platform tuple MUST
    be conditional, unsupported, or unknown and MUST be disabled.
12. A task-board session MUST use the official opaque bridge. <code>ax</code>
    MUST NOT read or mutate private <code>tb-sessiond</code> state.

### 2.3 Session name resolution

<code>ax NAME</code> MUST resolve in this order:

1. exact live session name in the local derived index;
2. exact live session name learned from allowlisted peers;
3. exact UUID when NAME is a UUID; then
4. not found.

Ambiguous or case-fold-colliding names MUST fail with
<code>name_ambiguous</code>. Names are displayed with original case, but
uniqueness MUST use Unicode-independent ASCII case folding because the allowed
alphabet is ASCII.

When the resolved owner is local, <code>ax NAME</code> MUST attach locally or
resume a stopped owner after validating its lease. When the owner is remote,
interactive mode MUST offer exactly:

1. remote attach;
2. graceful takeover here;
3. fork here; or
4. cancel.

Force takeover MUST NOT appear as the default choice. It is exposed by the
explicit <code>ax takeover NAME --to HOST --force</code> command. Non-interactive commands
MUST select the same actions explicitly; they MUST NOT prompt or infer one.

### 2.4 Execution profiles

The persisted profile enum is <code>standard</code> or <code>yolo</code>.
<code>yolo</code> means the provider-specific unrestricted/no-approval mode; it
does not mean that <code>ax</code> ignores its own ownership, conflict,
allowlist, or integrity checks.

The immutable Session Record stores the creation profile. Every
<code>provider.launched</code>, <code>task_board.launched</code>,
<code>session.resumed</code>, and <code>fork.created</code> event repeats the
effective ax profile and the digest of the authoritative
<code>profile.changed</code> event from which it was derived, or null when the
Session Record is still the authority. A profile change requires
<code>ax session set-profile NAME PROFILE</code>, a new event under the current
lease, and operator confirmation when changing to <code>yolo</code>. A resume
MUST fail with <code>profile_mapping_unavailable</code> if the adapter cannot
map the stored profile for the probed provider version.

The effective persisted profile is the Session Record value followed by the
newest authoritative <code>profile.changed</code> event in lease/sequence order.
Losing-lease or ambiguous events MUST NOT change it. Every command that says
“persisted profile” refers to this derived value. The profile source is null
when no authoritative change exists and otherwise is exactly that newest
event's <code>event_id</code>. A Checkpoint's event-head closure fixes both
values for that checkpoint; a bundle, resume, or fork MUST NOT fall back to the
Session Record creation value when the closure contains a later change.

Fork creates a new authority boundary. Its new Session Record stores the
source-checkpoint effective profile as its creation profile, so the new
session's <code>profile_source_event_id</code> is null. The
<code>fork.created.source_profile_event_id</code> separately preserves the
nullable source-session event used for that projection; it is provenance and
MUST NOT be treated as a profile event in the new session's event chain.

Provider mapping is evidence, not profile authority. In particular, Pi 0.73.1
maps both ax profiles to <code>default_unrestricted_tool_set</code>; the two ax
profiles remain distinct because the Session/Event authority and confirmation
history remain distinct even when the provider mapping strings are equal.

The following end-to-end profile fixtures are normative. Let P0 be the Session
Record profile, E1 an authoritative <code>profile.changed</code> event to P1,
and C1 a checkpoint whose event-head closure contains E1:

| Fixture | Path | Required profile authority |
| --- | --- | --- |
| <code>PROFILE-DIRECT-TAKEOVER</code> | Direct start P0 → E1 → C1 → graceful/force takeover | Bundle is absent; materialization finalize, plugin resume, and resumed event all carry P1/E1 |
| <code>PROFILE-DIRECT-RESUME</code> | Direct stop at C1 → owner resume | Plugin resume and resumed event carry P1/E1; creation P0 is ignored |
| <code>PROFILE-DIRECT-FORK</code> | Fork C1 | New Session Record creation profile is P1; fork event carries P1/null as new-session authority plus <code>source_profile_event_id=E1</code>; resumed carries P1/null |
| <code>PROFILE-TB-TAKEOVER</code> | Task-board start P0 → E1 → export C1 → takeover | Bundle projection carries P1/E1; journaled bridge resume and events use the same pair |
| <code>PROFILE-TB-RESUME</code> | Task-board owner resume from C1 | Bundle, bridge resume, and events agree on P1/E1 |
| <code>PROFILE-TB-FORK</code> | Task-board fork C1 | Source bundle carries P1/E1; new Session Record and bridge resume use P1/null; fork event retains E1 only in <code>source_profile_event_id</code> |
| <code>PROFILE-PI-EQUAL-MAPPING</code> | Pi changes <code>standard</code> to <code>yolo</code> at E1 while both map to <code>default_unrestricted_tool_set</code> | Ax still persists and reports P1/E1; equal provider argv text is not authority to erase E1 |

Any fixture that uses P0 after C1, omits E1 where the event schema requires its
source, or accepts a bundle profile inconsistent with C1 is
<code>integrity_failure</code> before activation.

## 3. Architecture and durable local layout

### 3.1 Required components

The implementation is logically divided into:

- <strong>CLI/controller</strong>: parses commands, enforces policy, and
  coordinates transactions;
- <strong>state engine</strong>: validates immutable objects and derives current
  state into SQLite;
- <strong>terminal backend</strong>: tmux/PTTY on Unix-family systems or
  process/ConPTY on native Windows;
- <strong>provider host</strong>: discovers and invokes built-in or executable
  provider adapters;
- <strong>workspace engine</strong>: captures, transfers, compares, stages, and
  materializes Git and non-Git state;
- <strong>mesh RPC</strong>: performs SSH stdio capability negotiation and
  anti-entropy exchange;
- <strong>task-board bridge</strong>: treats manager bundles as opaque bytes
  plus a public manifest;
- <strong>derived index</strong>: local SQLite cache rebuilt from immutable
  truth; and
- <strong>user service</strong>: optional periodic health, reconciliation, and
  sync driver.

The core CLI, replication engine, and PTY/ConPTY supervision MUST be
implemented in Go. Command routing SHOULD use Cobra or an equivalently
maintained Go command framework. The implementation MAY invoke documented
<code>git</code>, <code>ssh</code>, and <code>tmux</code> surfaces where this
specification permits them, but cross-platform file transfer/chunking MUST be
Go-native and MUST NOT depend on <code>rsync</code> or
<code>robocopy</code>.

The diagram deliverable for v0.2.0 MUST render this model as C4 System Context
and Container views. Runtime takeover, state, and mesh flows MUST be rendered
from Sections 12 and 13 as focused PlantUML sources. Those rendered artifacts
MUST NOT add relationships absent from this document.

### 3.2 Platform paths

Every path class has one exact command flag and environment override. Path
resolution MUST use this precedence: the corresponding command flag, the
corresponding non-empty environment override, then the platform default. A
resolved file or directory MUST be absolute before use.

| Path class | Command flag | Environment override | Value kind |
| --- | --- | --- | --- |
| Configuration file | <code>--config PATH</code> | <code>AX_CONFIG</code> | Existing regular file, or a not-yet-created regular-file path whose parent exists |
| Durable data root | <code>--data-dir PATH</code> | <code>AX_DATA_DIR</code> | Directory |
| Mutable state root | <code>--state-dir PATH</code> | <code>AX_STATE_DIR</code> | Directory |
| Cache root | <code>--cache-dir PATH</code> | <code>AX_CACHE_DIR</code> | Directory |
| Runtime root | <code>--runtime-dir PATH</code> | <code>AX_RUNTIME_DIR</code> | Directory |

This five-row table is the complete environment-override registry for version
1.0.0. Empty values are treated as unset. An unknown variable beginning
<code>AX_</code> is ordinary process environment and MUST NOT be interpreted by
the configuration or path resolver. On native Windows, the runtime root stores
owner-only transient metadata used to derive per-user named-pipe and process-
handle names; the override never names a pipe directly.

| Purpose | macOS | Linux and WSL2 | Native Windows |
| --- | --- | --- | --- |
| Config | <code>$XDG_CONFIG_HOME/ax</code>, default <code>~/.config/ax</code> | Same | <code>%APPDATA%\ax</code> |
| Durable data | <code>~/Library/Application Support/ax</code> | <code>$XDG_DATA_HOME/ax</code>, default <code>~/.local/share/ax</code> | <code>%LOCALAPPDATA%\ax\data</code> |
| Mutable state/index | <code>~/Library/Application Support/ax/state</code> | <code>$XDG_STATE_HOME/ax</code>, default <code>~/.local/state/ax</code> | <code>%LOCALAPPDATA%\ax\state</code> |
| Cache | <code>~/Library/Caches/ax</code> | <code>$XDG_CACHE_HOME/ax</code>, default <code>~/.cache/ax</code> | <code>%LOCALAPPDATA%\ax\cache</code> |
| Runtime IPC | per-user temporary directory with mode 0700 | <code>$XDG_RUNTIME_DIR/ax</code> | per-user named pipe and process handles |

The XDG variables displayed in the defaults table are inputs to platform
defaults, not additional <code>AX_*</code> overrides. On Windows, path
comparison MUST use a
volume-aware, case-insensitive comparison unless the volume is proven
case-sensitive. On Unix, paths are byte-case-sensitive after UTF-8 validation.

Ax-owned config, durable-data, state, cache, staging, and runtime directories
MUST be accessible only to the current user: mode 0700 directories and 0600
files on Unix, or a user-only DACL on Windows. Materialized workspace entries
use their manifest modes, but their staging root remains user-only until commit.

The durable data layout is:

~~~text
<data>/
  objects/sha256/HH/REST
  records/json/sha256/HH/REST
  records/cbor/sha256/HH/REST
  manifests/json/sha256/HH/REST
  manifests/cbor/sha256/HH/REST
  sessions/<session-id>/refs/
  workspaces/<workspace-group-id>/refs/
  staging/<transfer-id>/
  quarantine/sha256/HH/REST/<quarantine-id>
<state>/
  index.sqlite
  materializations/<materialization-id>.json
  provider-object-sources/<materialization-id>/<provider-id>/
  provider-transactions/<provider-id>/<transaction-id>/
  managed-replicas/<managed-replica-id>/current.json
  managed-replicas/<managed-replica-id>/markers/sha256/HH/REST.json
  task-board-staging/<operation-id>/
  service/
~~~

Every digest-derived durable path uses one function,
<code>digest_path_v1(sha256:H) = sha256/H[0:2]/H[2:64]</code>, where H is the
digest's exact 64 lowercase hexadecimal characters. <code>HH</code> is therefore
two characters and <code>REST</code> is the remaining 62; neither contains the
<code>sha256:</code> prefix, and a full 64-character digest is never repeated as
the leaf. Native Windows joins the same three components with backslashes, so
no colon is placed in a filename. The rule is identical to the Object Sink and
Task-board Bundle member rule; no storage class may choose a different split.

Files under
<code>objects</code>, <code>records</code>, and <code>manifests</code> MUST be
immutable after successful creation. JSON and CBOR paths MAY coexist for one
logical digest; both MUST decode to the same canonical JSON identity. A hash
mismatch or representation disagreement MUST quarantine the file.

A quarantined input is stored create-new beneath the digest path using a
UUIDv7 <code>quarantine-id</code>; its digest directory may therefore retain
multiple conflicting byte sequences without overwrite. The marker history
path applies <code>digest_path_v1</code> to <code>marker_id</code> and appends
<code>.json</code> only to REST. These golden paths are normative:

| Digest/use | POSIX path suffix | Native Windows path suffix |
| --- | --- | --- |
| Empty-byte blob <code>sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</code> | <code>objects/sha256/e3/b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</code> | <code>objects\sha256\e3\b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</code> |
| Example blob <code>sha256:9c21bad65c1b3d0403ac85d7d5bd134bb8d894432702a396a77b0477b8eb3b50</code> | <code>objects/sha256/9c/21bad65c1b3d0403ac85d7d5bd134bb8d894432702a396a77b0477b8eb3b50</code> | <code>objects\sha256\9c\21bad65c1b3d0403ac85d7d5bd134bb8d894432702a396a77b0477b8eb3b50</code> |
| Marker <code>sha256:385c71c7a29a43615c9d35ffb7c93ae20cd9419bbca461627048de575cade94c</code> | <code>markers/sha256/38/5c71c7a29a43615c9d35ffb7c93ae20cd9419bbca461627048de575cade94c.json</code> | <code>markers\sha256\38\5c71c7a29a43615c9d35ffb7c93ae20cd9419bbca461627048de575cade94c.json</code> |

<code>PATH-DIGEST-N1</code> uses the full digest as REST,
<code>PATH-DIGEST-N2</code> includes <code>sha256:</code> in a filename,
<code>PATH-DIGEST-N3</code> uses the wrong shard, and
<code>PATH-DIGEST-N4</code> gives JSON and CBOR representations different
logical digests. Each MUST fail before durable installation.

The two provider directories under <code>&lt;state&gt;</code> are created only by
the destination <code>ax</code> host. They are never accepted as paths supplied
by a peer or plugin. Section 7.5 defines their closed authorities, layouts,
same-filesystem checks, retention, and cleanup. They MUST be path-disjoint from
every workspace, provider native-store, task-board staging, credential,
authentication, durable-object, and runtime root after symlink/reparse-point
resolution.

### 3.3 SQLite

SQLite is a local transactional index only. It MAY contain denormalized session
state, peer inventories, reachability, transfer progress, and search aliases.
It MUST be rebuildable solely from immutable records, manifests, and local
configuration. The database, its WAL, SHM, journal, and lock files MUST NOT
appear in any transfer manifest.

An index schema migration MUST run transactionally on a local copy. Failure MUST
leave the prior index usable or trigger a clean rebuild. Index schema version is
an implementation detail and MUST NOT be used as a wire compatibility signal.

## 4. Terminal persistence

### 4.1 Terminal backend interface

Every terminal backend MUST implement these semantic operations:

| Operation | Required result |
| --- | --- |
| <code>create</code> | With <code>session_id</code> and caller-stable <code>bootstrap_operation_id</code>, create a durable pane/process whose only stable entry point is <code>ax pane SESSION_ID</code>. |
| <code>attach</code> | Connect an operator to the local terminal without changing ownership. |
| <code>status</code> | Report process presence, wrapper state, provider child state, and attachability. |
| <code>quiesce-input</code> | Stop new operator/provider input while retaining observation. |
| <code>wait-safe-boundary</code> | Prove the adapter-specific safe boundary or time out. |
| <code>request-stop</code> | Ask the provider to exit through a version-tested graceful path. |
| <code>terminate-stale</code> | Terminate a process only for explicit force recovery after preserving diagnostics. |
| <code>restore</code> | Recreate the wrapper after reboot and consult current ownership before any provider resume. |

The wrapper MUST validate configuration, load the logical session, synchronize
known lease records when possible, and compare the local fencing token before
launching a provider. It MUST park safely when ownership is remote, ambiguous,
or unverified.

Terminal creation and the wrapper's first child start are idempotent on
<code>(session_id, bootstrap_operation_id)</code>. The backend MUST durably bind
that pair before child creation. An identical retry returns or reattaches to
the one recorded wrapper/child; changing the operation for a session still in
the bootstrap window is <code>idempotency_mismatch</code>. After a lost result,
<code>status</code> plus that binding MUST prove absence or identify the one
child before any start retry. This contract never persists or replicates a PID
as identity.

### 4.2 tmux backend

On macOS, Linux, and WSL2, the supported durable terminal backend is tmux. Every
managed pane MUST run:

~~~shell
ax pane <logical-session-id>
~~~

It MUST NOT run the raw provider command as the pane's stable command.
<code>tmux-resurrect</code> plus <code>tmux-continuum</code> MAY recreate local
tmux layout and invoke the wrapper after reboot. They MUST NOT be described or
used as cross-host migration.

After restore, the wrapper MUST:

1. read the latest locally known lease;
2. attempt a mesh lease refresh without blocking forever;
3. resume locally only if the local host has the winning lease and the required
   materialization is valid;
4. offer remote attach/takeover when another host owns the session in an
   interactive terminal; or
5. enter <code>parked</code> without launching the provider in all other cases.

### 4.3 Native Windows backend

Native Windows PowerShell MUST use a Windows terminal backend implemented with
Go process supervision and ConPTY. It MUST support mesh sync, workspace and
provider materialization, direct/provider resume, task-board open/adopt, remote
attach, graceful takeover when the provider row passes ConPTY gates, force
takeover, stop, and continuation.

Native Windows MUST NOT claim tmux or tmux resurrection. A reboot destroys the
live ConPTY. The user service MUST recreate <code>ax pane SESSION_ID</code>,
which resumes from the latest valid checkpoint only after lease validation.
Terminal scrollback and live process memory are not portable state.

Full tmux restore on a Windows computer is a WSL2 feature and uses the Linux
paths, process model, and provider installation inside that distribution. A
native Windows provider store and a WSL2 provider store are distinct
materialization targets.

### 4.4 User services

The background service integration is:

- a launchd agent on macOS;
- a systemd user unit on Linux and WSL2 where systemd is enabled;
- otherwise an explicitly installed per-user periodic launcher on WSL2; and
- a Scheduled Task or per-user service on native Windows.

The service MAY run periodic sync, peer health checks, tombstone
acknowledgement, stale-process detection, and wrapper restoration. Core commands
MUST work without it. Service absence MUST degrade freshness, not corrupt
ownership.

## 5. Domain records and state machine

### 5.1 Session Record

The Session Record is immutable and created exactly once. Its schema is
<code>urn:ax:schema:session-record</code> version <code>1.0.0</code>.

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact schema identifier |
| <code>schema_version</code> | semver | <code>1.0.0</code> |
| <code>record_id</code> | digest | Canonical object digest |
| <code>subject_id</code> | UUIDv7 | Equal to <code>session_id</code> |
| <code>session_id</code> | UUIDv7 | Globally unique |
| <code>name</code> | string | Section 2.3 grammar |
| <code>kind</code> | enum | <code>direct</code> or <code>task_board</code> |
| <code>created_at</code> | timestamp | Diagnostic time |
| <code>created_by_host_id</code> | UUIDv7 | Allowlisted host at creation |
| <code>provider_id</code> | string | Lowercase plugin ID |
| <code>workspace_group_id</code> | UUIDv7 | Required |
| <code>execution_profile</code> | enum | <code>standard</code> or <code>yolo</code> |
| <code>launch_plan</code> | Launch Plan | Closed shape below; sanitized and secret-free |
| <code>task_board</code> | Task-board Reference or null | Required object exactly when <code>kind = task_board</code> |
| <code>fork_provenance</code> | Fork Provenance or null | Required object exactly when this record was created by fork |
| <code>extensions</code> | object | Required; may be empty; reverse-DNS keys only |

The embedded Launch Plan is a closed object with exactly these members:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>argv</code> | array&lt;string&gt;[1..128] | Each element is 1–4,096 UTF-8 bytes; total encoded argv is at most 65,536 bytes; never a shell command string |
| <code>cwd_workspace_id</code> | UUIDv7 | Names one workspace in the Session Record's workspace group |
| <code>cwd_relative</code> | string | <code>.</code> for the workspace root or a path satisfying Section 1.6 |
| <code>env_names</code> | array&lt;string&gt;[0..64] | Sorted, unique names matching <code>[A-Za-z_][A-Za-z0-9_]{0,127}</code>; values resolve only from destination-local state |
| <code>env_literals</code> | map(environment-name,string)[0..64] | Non-secret literals of at most 4,096 UTF-8 bytes each; keys sorted in canonical form and disjoint from <code>env_names</code> |
| <code>contains_secrets</code> | boolean | MUST be false |
| <code>extensions</code> | object | Reverse-DNS extension keys only |

Arguments MUST contain only sanitized provider/task-board arguments. Secret
values, inline credential-bearing URLs, response files containing secrets, and
shell fragments are forbidden. A name such as <code>OPENAI_API_KEY</code> in
<code>env_names</code> is a destination-local lookup instruction, not a stored
value.

The Task-board Reference is a closed object:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>bridge_protocol_version</code> | semver | Exact <code>1.0.0</code> |
| <code>board</code> | Board Identity | Closed shape below |
| <code>task_element_id</code> | string | 1–128 printable non-control UTF-8 bytes |
| <code>launch_mode</code> | enum | <code>primary_owner</code> or <code>tracked_prompt</code> |
| <code>manager_session_ref</code> | string or null | MUST be null in the immutable creation record; the public reference is established by <code>task_board.launched</code> and may later change through <code>task_board.adopted</code> |
| <code>board_goal</code> | Board Goal or null | Required non-null for <code>primary_owner</code> |
| <code>native_goal_binding</code> | enum | <code>bound</code>, <code>prompt</code>, or <code>none</code> |
| <code>extensions</code> | object | Reverse-DNS extension keys only |

Board Identity has exactly <code>kind</code> (<code>local</code> or
<code>remote</code>), <code>logical_id</code> (1–128 characters matching
<code>[A-Za-z0-9][A-Za-z0-9._:-]{0,127}</code>),
<code>remote_url</code> (absolute <code>https</code> URL or null), and
<code>extensions</code>. A local board requires null <code>remote_url</code>;
a remote board requires a URL with no userinfo, query, or fragment. Board Goal
has exactly <code>schema = "board-goal-v2"</code>, <code>goal_id</code> as a
1–128 character public goal reference, <code>revision</code> as uint53 greater
than zero, and <code>extensions</code>. <code>primary_owner</code> requires
<code>native_goal_binding = bound</code>; <code>tracked_prompt</code> permits
<code>prompt</code> or <code>none</code> and MAY have a null goal.

The creation-time <code>manager_session_ref</code> MUST be null for both launch
modes. This avoids making an immutable Session Record depend on a manager
reference that the public bridge has not created yet. The current reference is
the newest authoritative <code>task_board.launched</code> or
<code>task_board.adopted</code> event for the session; a missing event means the
task-board launch has not succeeded and MUST NOT be guessed from private state.

Fork Provenance is a closed object with exactly
<code>source_session_id</code> UUIDv7, <code>source_checkpoint_id</code> digest,
<code>source_workspace_group_id</code> UUIDv7, <code>operation_id</code>
UUIDv7, <code>provider_fork_mode</code> as <code>native</code>,
<code>supported_import</code>, or <code>task_board_clone</code>, and
<code>extensions</code>. It is core provenance, not an extension, and MUST
remain immutable with the fork's Session Record.

Normative example:

~~~json
{
  "schema": "urn:ax:schema:session-record",
  "schema_version": "1.0.0",
  "record_id": "sha256:d61701066a7f5dd37bf35fea0e85e7f154251355ad24a49976532d7f79ddc772",
  "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "name": "payments-api",
  "kind": "direct",
  "created_at": "2026-08-19T04:00:00.000Z",
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "provider_id": "codex",
  "workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "execution_profile": "yolo",
  "launch_plan": {
    "argv": ["codex"],
    "cwd_workspace_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
    "cwd_relative": "src",
    "env_names": ["OPENAI_API_KEY"],
    "env_literals": {},
    "contains_secrets": false,
    "extensions": {}
  },
  "task_board": null,
  "fork_provenance": null,
  "extensions": {}
}
~~~

A task-board Session Record uses the same Launch Plan shape and this exact
tagged variant:

~~~json
{
  "schema": "urn:ax:schema:session-record",
  "schema_version": "1.0.0",
  "record_id": "sha256:0acd3e31635372e176f8f37b1b74aa0ebdcf2d1e4ac40d43adb8e462079b34a2",
  "subject_id": "0198f4c8-9f60-7077-8071-1234567890ab",
  "session_id": "0198f4c8-9f60-7077-8071-1234567890ab",
  "name": "qwen-investigation",
  "kind": "task_board",
  "created_at": "2026-08-19T04:01:00.000Z",
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "provider_id": "qwen",
  "workspace_group_id": "0198f4c8-af70-7188-8172-1234567890ab",
  "execution_profile": "standard",
  "launch_plan": {
    "argv": ["task-board", "qwen", "TASK-260819-example"],
    "cwd_workspace_id": "0198f4c8-b080-7299-8273-1234567890ab",
    "cwd_relative": ".",
    "env_names": [],
    "env_literals": {},
    "contains_secrets": false,
    "extensions": {}
  },
  "task_board": {
    "bridge_protocol_version": "1.0.0",
    "board": {
      "kind": "local",
      "logical_id": "agent-session-manager-spec",
      "remote_url": null,
      "extensions": {}
    },
    "task_element_id": "TASK-260819-example",
    "launch_mode": "tracked_prompt",
    "manager_session_ref": null,
    "board_goal": null,
    "native_goal_binding": "prompt",
    "extensions": {}
  },
  "fork_provenance": null,
  "extensions": {}
}
~~~

The example <code>record_id</code>, like every self-identity digest in this
document, is the computed canonical digest. Validators MUST recompute it and
MUST reject a mismatch.

### 5.2 Session Event

Every change after creation is an immutable Session Event with schema
<code>urn:ax:schema:session-event</code> version <code>1.0.0</code>.

Required fields are <code>event_id</code> digest, <code>subject_id</code> and
<code>session_id</code> with the same UUID,
<code>event_type</code>, <code>created_by_host_id</code>,
<code>lease_epoch</code>, <code>lease_id</code>, and
<code>lease_sequence</code> as a uint53 starting at 1 for
each lease,
<code>predecessors</code> as a sorted array of one or more record/event digests,
<code>created_at</code>, and <code>payload</code>. The first event after
creation MUST have exactly the Session Record ID in
<code>predecessors</code>; later events reference one or more prior event heads.
Events form a DAG; they are not ordered by timestamp.
The exact top-level shape also requires <code>schema</code>,
<code>schema_version</code>, and <code>extensions</code>; no other top-level
member is permitted.

The winning owner MUST serialize state-changing events for a session. Within
one lease, <code>lease_sequence</code> MUST increase by exactly one and each
event MUST reference the immediately prior authoritative event. The first event
under a successor lease uses sequence 1 and references the predecessor
checkpoint's authoritative event heads. A missing sequence, two different
events at one sequence under the winning lease, or an event that omits the
required predecessor is <code>invalid_state_transition</code>; the session MUST
park and MUST NOT accept input until a newer explicit takeover establishes an
unambiguous checkpoint. Losing-lease branches remain preserved but are never
applied to authoritative state.

The v1 event types are:

<code>session.created</code>, <code>terminal.created</code>,
<code>provider.launched</code>, <code>provider.identified</code>,
<code>session.idle</code>, <code>session.quiescing</code>,
<code>checkpoint.created</code>, <code>sync.completed</code>,
<code>session.stopped</code>, <code>session.resumed</code>,
<code>session.bootstrap_aborted</code>,
<code>lease.transferred</code>, <code>lease.forced</code>,
<code>session.parked</code>, <code>session.failed</code>,
<code>fork.created</code>, <code>profile.changed</code>,
<code>session.tombstoned</code>, <code>takeover.force_confirmed</code>,
<code>replica.replace_confirmed</code>, <code>task_board.launched</code>,
<code>task_board.adopted</code>, <code>tombstone.issued</code>, and
<code>tombstone.resolved</code>.

The <code>payload</code> object is a closed tagged union selected by
<code>event_type</code>. It MUST contain exactly the members in this table; a
member shown as nullable remains required:

| Event type | Exact payload members |
| --- | --- |
| <code>session.created</code> | <code>session_record_id:digest</code>, <code>bootstrap_operation_id:UUIDv7</code>, <code>first_checkpoint_operation_id:UUIDv7</code> |
| <code>terminal.created</code> | <code>backend:tmux&#124;conpty</code>, <code>terminal_id:string[1..512]</code> |
| <code>provider.launched</code> | <code>provider_id:provider-id</code>, <code>provider_version:string[1..128]</code>, <code>execution_profile:standard&#124;yolo</code>, <code>profile_source_event_id:digest&#124;null</code>, <code>profile_mapping:string[1..512]</code> |
| <code>provider.identified</code> | <code>provider_identity_record_id:digest</code>, <code>confidence:exact&#124;strong&#124;weak</code> |
| <code>session.idle</code> | <code>boundary_ref:string[1..1024]</code>, <code>foreground_idle:boolean</code>, <code>background_idle:boolean</code> |
| <code>session.quiescing</code> | <code>operation_id:UUIDv7</code>, <code>reason:graceful_takeover&#124;stop&#124;checkpoint</code>, <code>input_blocked:boolean</code> |
| <code>checkpoint.created</code> | <code>checkpoint_id:digest</code>, <code>kind:periodic&#124;pre_stop&#124;closure&#124;fork_base&#124;manual</code> |
| <code>sync.completed</code> | <code>peer_host_id:UUIDv7</code>, <code>checkpoint_id:digest</code>, <code>manifest_ids:sorted unique digest[1..1024]</code>, <code>materialized:boolean</code> |
| <code>session.stopped</code> | <code>graceful:boolean</code>, <code>checkpoint_id:digest&#124;null</code>, <code>resumable:boolean</code>, <code>closure_kind:checkpointed&#124;bootstrap_abort</code>, <code>process_closed:boolean</code>, <code>store_closed:boolean</code> |
| <code>session.resumed</code> | <code>checkpoint_id:digest</code>, <code>execution_profile:standard&#124;yolo</code>, <code>profile_source_event_id:digest&#124;null</code>, <code>terminal_backend:tmux&#124;conpty</code>, <code>native_session_id:string[1..512]</code> |
| <code>session.bootstrap_aborted</code> | <code>operation_id:UUIDv7</code>, <code>failure_phase:before_terminal&#124;after_terminal&#124;after_process&#124;after_identity&#124;before_checkpoint</code>, <code>provider_identity_record_id:digest&#124;null</code>, <code>manager_session_ref:string[1..512]&#124;null</code>, <code>process_closed:boolean</code>, <code>store_closed:boolean</code>, <code>resume_allowed:false</code> |
| <code>lease.transferred</code> | <code>operation_id:UUIDv7</code>, <code>from_host_id:UUIDv7</code>, <code>to_host_id:UUIDv7</code>, <code>predecessor_lease_id:UUIDv4</code>, <code>new_lease_id:UUIDv4</code> |
| <code>lease.forced</code> | <code>operation_id:UUIDv7</code>, <code>expected_owner_host_id:UUIDv7</code>, <code>expected_epoch:uint53</code>, <code>new_lease_id:UUIDv4</code>, <code>checkpoint_id:digest</code> |
| <code>session.parked</code> | <code>reason:remote_owner&#124;stale_owner&#124;restore_policy&#124;failed_handoff</code>, <code>winning_lease_id:UUIDv4</code> |
| <code>session.failed</code> | <code>error_code:string[1..128]</code>, <code>retryable:boolean</code>, <code>operation_id:UUIDv7&#124;null</code> |
| <code>fork.created</code> | <code>source_session_id:UUIDv7</code>, <code>source_checkpoint_id:digest</code>, <code>new_session_record_id:digest</code>, <code>provider_fork_mode:native&#124;supported_import&#124;task_board_clone</code>, <code>execution_profile:standard&#124;yolo</code>, <code>profile_source_event_id:digest&#124;null</code>, <code>source_profile_event_id:digest&#124;null</code> |
| <code>profile.changed</code> | <code>from:standard&#124;yolo</code>, <code>to:standard&#124;yolo</code>, <code>confirmed:boolean</code> |
| <code>session.tombstoned</code> | <code>tombstone_id:digest</code> |
| <code>takeover.force_confirmed</code> | <code>operation_id:UUIDv7</code>, <code>expected_owner_host_id:UUIDv7</code>, <code>expected_epoch:uint53</code>, <code>checkpoint_id:digest</code>, <code>accepted_risks:sorted unique enum[3]</code>, <code>confirmation_mode:interactive&#124;non_interactive</code> |
| <code>replica.replace_confirmed</code> | <code>operation_id:UUIDv7</code>, <code>workspace_group_id:UUIDv7</code>, <code>target_host_id:UUIDv7</code>, <code>managed_replica_id:UUIDv7</code>, <code>expected_marker_id:digest</code>, <code>expected_checkpoint_id:digest</code>, <code>replacement_checkpoint_id:digest</code>, <code>confirmation_mode:interactive&#124;non_interactive</code> |
| <code>task_board.launched</code> | <code>operation_id:UUIDv7</code>, <code>manager_session_ref:string[1..512]</code>, <code>provider_id:provider-id</code>, <code>launch_mode:primary_owner&#124;tracked_prompt</code>, <code>lease_epoch:uint53&gt;0</code>, <code>lease_id:UUIDv4</code>, <code>execution_profile:standard&#124;yolo</code>, <code>profile_source_event_id:digest&#124;null</code>, <code>board_goal_id:string[1..128]&#124;null</code>, <code>board_goal_revision:uint53&#124;null</code>, <code>state:running&#124;idle</code> |
| <code>task_board.adopted</code> | <code>operation_id:UUIDv7</code>, <code>bundle_id:digest</code>, <code>manager_session_ref:string[1..512]</code>, <code>board_goal_id:string[1..128]&#124;null</code>, <code>board_goal_revision:uint53&#124;null</code> |
| <code>tombstone.issued</code> | <code>tombstone_id:digest</code>, <code>scope:session&#124;workspace_entry&#124;provider_snapshot&#124;managed_replica</code>, <code>subject_id:UUIDv7</code>, <code>target_ref:string[1..1024]</code> |
| <code>tombstone.resolved</code> | <code>tombstone_id:digest</code>, <code>resolution:deleted&#124;already_absent&#124;resurrected&#124;retained_conflict</code>, <code>target_ref:string[1..1024]</code>, <code>resulting_entry_digest:digest&#124;null</code> |

For <code>takeover.force_confirmed</code>, <code>accepted_risks</code> MUST be
exactly <code>["divergent_history","split_brain","stale_process"]</code> in
bytewise order. For <code>task_board.launched</code> and
<code>task_board.adopted</code>, goal ID and revision MUST
either both be null or both be non-null, and a non-null revision is greater
than zero. A <code>task_board.launched</code> event MUST repeat the winning
creation lease and the Session Record's provider/launch mode; a mismatch is
<code>integrity_failure</code>. Audit event issuance and retention are specified
in Sections 10.7 and 18.4. A <code>tombstone.resolved</code> resurrection
requires a non-null resulting entry digest; every other resolution requires
null.

The profile and profile-source pair in every launch, resume, and fork event
MUST equal the Section 2.4 effective profile at the referenced checkpoint or,
for the first launch, the Session Record and null. A non-null source MUST name
the newest authoritative <code>profile.changed</code> event in that event-head
closure. Equal provider mapping strings do not permit changing either value.
For <code>fork.created</code>, the effective new-session authority is its newly
persisted Session Record, so <code>profile_source_event_id</code> is null.
<code>source_profile_event_id</code> separately equals the nullable source-
checkpoint profile event and never participates in new-session derivation.

A <code>session.stopped</code> payload is <code>checkpointed</code> exactly when
<code>checkpoint_id</code> is non-null and <code>resumable = true</code>.
<code>bootstrap_abort</code> requires a null checkpoint, false resumable and
graceful values, and a preceding or equal-operation
<code>session.bootstrap_aborted</code> event; its derived lifecycle is
<code>failed</code>, never <code>stopped</code>. A bootstrap-aborted event
requires both closure booleans true. Its identity fields are both null before
identity, and after identity exactly the field belonging to the Session Record
kind is non-null. An ambiguous live process or open store cannot be represented
as a successful abort and remains <code>failed</code> with recovery diagnostics.

An unknown event type MUST be retained as an immutable object but MUST NOT
change derived session state under major version 1.

Normative example:

~~~json
{
  "schema": "urn:ax:schema:session-event",
  "schema_version": "1.0.0",
  "event_id": "sha256:46d2745fe7dfce856027be36e34f1cc6a56ffc846063dc4aa6aabf3f5a85bacb",
  "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "event_type": "session.stopped",
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "lease_epoch": 4,
  "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "lease_sequence": 12,
  "predecessors": [
    "sha256:7777777777777777777777777777777777777777777777777777777777777777"
  ],
  "created_at": "2026-08-19T04:08:00.000Z",
  "payload": {
    "graceful": true,
    "checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
    "resumable": true,
    "closure_kind": "checkpointed",
    "process_closed": true,
    "store_closed": true
  },
  "extensions": {}
}
~~~

### 5.3 Lease Record and ownership

The Lease Record schema is <code>urn:ax:schema:lease</code> version
<code>1.0.0</code>. Fields are:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Lease Record schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>record_id</code> | digest | Canonical Lease Record digest |
| <code>subject_id</code> | UUIDv7 | Equal to <code>session_id</code> |
| <code>lease_id</code> | UUIDv4 | Cryptographically random unique fencing token |
| <code>session_id</code> | UUIDv7 | Lease scope |
| <code>epoch</code> | uint53 | Starts at 1; never decreases |
| <code>holder_host_id</code> | UUIDv7 | Proposed owner |
| <code>predecessor_lease_id</code> | UUIDv4 or null | Null only at epoch 1 |
| <code>reason</code> | enum | <code>create</code>, <code>graceful_takeover</code>, <code>force_takeover</code>, <code>recovery</code> |
| <code>checkpoint_id</code> | digest or null | Null only for epoch-1 <code>create</code>; otherwise the validated materialized handoff base |
| <code>issued_by_host_id</code> | UUIDv7 | Initiator |
| <code>created_by_host_id</code> | UUIDv7 | MUST equal <code>issued_by_host_id</code> |
| <code>created_at</code> | timestamp | Diagnostic only |
| <code>extensions</code> | object | Reverse-DNS extension keys only |

The object is closed; every row is required, including nullable fields.
Normative example:

~~~json
{
  "schema": "urn:ax:schema:lease",
  "schema_version": "1.0.0",
  "record_id": "sha256:8ead987abed8c7c05175b447c9a0e2b3a521f12e5a989acb8abe132576852d63",
  "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "epoch": 4,
  "holder_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "predecessor_lease_id": "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff",
  "reason": "graceful_takeover",
  "checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "issued_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "created_at": "2026-08-19T04:09:00.000Z",
  "extensions": {}
}
~~~

The winning lease is selected by the greatest tuple
<code>(epoch, lease_id)</code>, where <code>lease_id</code> uses bytewise UUID
order. Lease UUIDs are random UUIDv4 values, so wall-clock skew cannot bias the
tie-break. A valid epoch greater than 1 MUST name a known predecessor for the
same session, MUST equal that predecessor's epoch plus one, and MUST reference
a validated checkpoint for that session and predecessor lease. An epoch-1
<code>create</code> lease MUST have a null predecessor and MAY have a null
checkpoint before the first provider boundary exists. Every new takeover lease
MUST use <code>max_observed_epoch + 1</code> from the initiator's current union.

The tuple rule handles concurrent force takeovers under partition without
clock ordering. Both processes can temporarily continue in isolated partitions,
which is why force takeover warns about split brain. After union, exactly one
lease wins. Events under the losing same-epoch lease and all lower epochs MUST
be preserved in a divergent branch and MUST NOT affect authoritative state.

An owner process MUST revalidate its fencing token before:

- accepting operator input after attach;
- starting a provider turn;
- publishing a checkpoint;
- pushing records or workspace changes; and
- resuming after any transport or sleep interruption longer than the configured
  lease refresh interval.

There is no time-expiring ownership lease in v0.2.0. Liveness is not authority.
A host being offline does not make a replica owner; only a takeover or fork
does.

### 5.4 Checkpoint Record

The Checkpoint Record schema is <code>urn:ax:schema:checkpoint</code> version
<code>1.0.0</code>. Its top-level object is closed and contains exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Checkpoint schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>checkpoint_id</code> | digest | Canonical object digest |
| <code>subject_id</code> | UUIDv7 | Equal to <code>session_id</code> |
| <code>session_id</code> | UUIDv7 | Existing Session Record |
| <code>lease_epoch</code> | uint53 | Greater than zero and equal to the referenced winning lease |
| <code>lease_id</code> | UUIDv4 | Equal to that lease's fencing token |
| <code>safe_boundary</code> | Safe Boundary Evidence | Closed shape below |
| <code>event_heads</code> | sorted unique digest[1..64] | Authoritative event DAG heads immediately before this object |
| <code>workspace_manifest_id</code> | digest | Workspace-group Transfer Manifest root |
| <code>provider_manifest_id</code> | digest or null | Direct native-store/provider snapshot only |
| <code>task_board_bundle_id</code> | digest or null | Task-board path only |
| <code>created_by_host_id</code> | UUIDv7 | Current lease holder |
| <code>created_at</code> | timestamp | Diagnostic only |
| <code>status</code> | enum | Literal <code>validated</code> |
| <code>extensions</code> | object | Reverse-DNS extension keys only |

Safe Boundary Evidence is a closed object containing exactly
<code>provider_id:provider-id</code>,
<code>provider_version:string[1..128]</code>,
<code>evidence:provider_api|provider_event|managed_pty|task_board_bridge|accepted_test</code>,
<code>input_blocked:boolean</code>, <code>foreground_idle:boolean</code>,
<code>background_idle:boolean</code>, <code>open_processes:uint53</code>, and
<code>open_database_handles:uint53</code>. A published checkpoint requires all
three booleans true and both counters zero. Provider-specific scheduled or
child work is included in <code>background_idle</code> and
<code>open_processes</code>; an adapter that cannot prove it MUST NOT publish a
new checkpoint.

The referenced Session Record selects the persistence variant. For
<code>kind = direct</code>, <code>provider_manifest_id</code> MUST be non-null
and <code>task_board_bundle_id</code> MUST be null. A backend-resolved provider
with no portable bytes still uses a provider Transfer Manifest containing its
validated identity and zero file entries; null is not used to erase that
distinction. For <code>kind = task_board</code>,
<code>provider_manifest_id</code> MUST be null and
<code>task_board_bundle_id</code> MUST be non-null. Both-null and both-non-null
checkpoints are invalid.

A checkpoint MUST NOT be published until every referenced object exists,
hashes correctly, passes schema validation, and the provider/task-board path
meets its quiescence requirement. A force takeover MAY select the newest
validated checkpoint even when no new safe checkpoint can be created.

<code>event_heads</code> identifies the authoritative event DAG immediately
before the checkpoint object. A later <code>checkpoint.created</code> event MAY
reference that checkpoint and those heads; the checkpoint MUST NOT reference
the announcing event because that would create a circular digest dependency.
The transitive event-head closure also fixes the Section 2.4 effective
execution profile and its nullable source event for this checkpoint. A missing,
losing-lease, or non-newest <code>profile.changed</code> reference is
<code>integrity_failure</code>; checkpoint consumers MUST NOT consult a later
local-only profile event or fall back to the creation profile.

Normative negative fixtures are: <code>CP-N1</code>, with
<code>background_idle = false</code> and status <code>validated</code>;
<code>CP-N2</code>, with a direct Session Record and null provider manifest;
<code>CP-N3</code>, with both persistence IDs non-null; and
<code>CP-N4</code>, with an unknown <code>safe_boundary.pid</code> member. Each
MUST be rejected with <code>incompatible_schema</code> before publication.

Normative example:

~~~json
{
  "schema": "urn:ax:schema:checkpoint",
  "schema_version": "1.0.0",
  "checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "lease_epoch": 4,
  "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "safe_boundary": {
    "provider_id": "codex",
    "provider_version": "0.147.0",
    "evidence": "accepted_test",
    "input_blocked": true,
    "foreground_idle": true,
    "background_idle": true,
    "open_processes": 0,
    "open_database_handles": 0
  },
  "event_heads": [
    "sha256:7777777777777777777777777777777777777777777777777777777777777777"
  ],
  "workspace_manifest_id": "sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e",
  "provider_manifest_id": "sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91",
  "task_board_bundle_id": null,
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:09:30.000Z",
  "status": "validated",
  "extensions": {}
}
~~~

### 5.5 Provider Identity Record

The Provider Identity Record schema is
<code>urn:ax:schema:provider-identity</code> version <code>1.0.0</code>. Its
top-level object is closed and contains exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Provider Identity schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>record_id</code> | digest | Canonical object digest |
| <code>subject_id</code> | UUIDv7 | Equal to <code>session_id</code> |
| <code>session_id</code> | UUIDv7 | Existing logical session |
| <code>provider_id</code> | provider-id | Must equal the Session Record provider |
| <code>provider_version</code> | string[1..128] | Exact probed version |
| <code>provider_version_range</code> | string[1..256] | Adapter compatibility range used for this identity |
| <code>native_session_id</code> | string[1..512] | Opaque provider handle; never interpreted by core |
| <code>identity_kind</code> | enum | <code>session_uuid</code>, <code>session_path_or_id</code>, <code>backend_conversation_uuid</code>, <code>task_board_managed</code>, or <code>provider_defined</code> |
| <code>logical_workspace_id</code> | UUIDv7 | Member of the Session Record workspace group |
| <code>backend_realm_fingerprint</code> | digest or null | Non-secret fingerprint; non-null when backend/account realm is a resume precondition |
| <code>opaque_identity</code> | map(provider-identity-key,string[1..1024])[0..32] | Explicit adapter data map defined below |
| <code>created_by_host_id</code> | UUIDv7 | Identifying owner host |
| <code>created_at</code> | timestamp | Diagnostic only |
| <code>extensions</code> | object | Reverse-DNS extension keys only |

A provider-identity key matches <code>[a-z][a-z0-9_.-]{0,63}</code>. Map keys
are data rather than schema members; values are non-secret strings only. This
is the sole provider-defined identity-data surface in version 1.0.0. It MUST
NOT contain an absolute path, credential, environment value, PID, socket,
terminal ID, or mutable cache selector. Structured or binary provider data
belongs in a content-addressed provider manifest, not this map.

An absolute workspace path MAY appear only as source observation metadata. It
MUST NOT be part of the cross-host identity. The destination adapter MUST
derive native path keys from the destination workspace mapping.

Normative negative fixtures are: unknown <code>identity_kind</code>; absent
<code>opaque_identity</code>; a map value that is an object instead of a
string; an absolute source path in that map; or an Antigravity
<code>backend_conversation_uuid</code> with null realm fingerprint. Each MUST
fail schema or provider-identity validation. A backend fingerprint is optional
for the other kinds unless that provider's Section 8 contract requires it.

Normative example:

~~~json
{
  "schema": "urn:ax:schema:provider-identity",
  "schema_version": "1.0.0",
  "record_id": "sha256:c879d766da67a8cfb3a3f6eae2234faa5d52d8df987496eae2218f40e5e220c2",
  "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "provider_id": "antigravity",
  "provider_version": "1.1.14",
  "provider_version_range": ">=1.1.14 <1.2.0",
  "native_session_id": "11111111-2222-4333-8444-555555555555",
  "identity_kind": "backend_conversation_uuid",
  "logical_workspace_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
  "backend_realm_fingerprint": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaad",
  "opaque_identity": {},
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:09:45.000Z",
  "extensions": {}
}
~~~

### 5.6 Workspace Group Record

The Workspace Group Record schema is <code>urn:ax:schema:workspace-group</code>
version <code>1.0.0</code>. Its closed top-level shape contains exactly
<code>schema</code>, <code>schema_version</code>,
<code>record_id:digest</code>, <code>subject_id:UUIDv7</code>,
<code>workspace_group_id:UUIDv7</code>,
<code>display_name:string[1..128]</code>,
<code>members:WorkspaceMember[1..256]</code>,
<code>created_by_host_id:UUIDv7</code>, <code>created_at:timestamp</code>, and
<code>extensions:object</code>. Subject and workspace-group IDs MUST be equal.
Members are sorted by <code>workspace_id</code>, and no two members may have an
equal or case-colliding <code>group_relative_path</code>.

The record defines immutable workspace topology, not evolving session
membership. Exactly one schema-valid Workspace Group Record may exist for a
<code>workspace_group_id</code>. Two different record IDs with that same group
ID are <code>integrity_failure</code>; the group and every referring session
MUST park until the conflicting history is reconciled. Changing the workspace
member set or its logical identities requires a new workspace group and new or
forked Session Records; no group-update winner is inferred from timestamps.

<code>WorkspaceMember</code> is a closed tagged union. No member-level
<code>extensions</code> map exists in 1.0.0; unknown members are rejected:

| Tag | Exact members |
| --- | --- |
| <code>kind = git</code> | <code>workspace_id:UUIDv7</code>, <code>kind:git</code>, <code>group_relative_path:path</code>, <code>repository_identity:string[1..256]</code>, <code>sanitized_remote_urls:sorted unique sanitized-git-URL[1..16]</code>, <code>repo_relative_cwd:.&#124;path</code>, <code>agent_project_config_paths:sorted unique path[0..256]</code>, <code>materialization_policy:shared_checkout&#124;separate_worktree</code> |
| <code>kind = managed_tree</code> | <code>workspace_id:UUIDv7</code>, <code>kind:managed_tree</code>, <code>group_relative_path:path</code>, <code>tree_identity:string[1..256]</code>, <code>repo_relative_cwd:.&#124;path</code>, <code>agent_project_config_paths:sorted unique path[0..256]</code>, <code>materialization_policy:shared_tree&#124;separate_copy</code> |

A sanitized Git URL uses <code>https</code>, <code>ssh</code>, or provider-neutral
<code>git</code> syntax and MUST contain no password, token, query, fragment, or
machine-local file path. <code>repository_identity</code> and
<code>tree_identity</code> are logical labels, not absolute paths. Every cwd and
project-config path is relative to that member and MUST exist in the referenced
workspace snapshot when materialized.

If multiple active sessions share a checkout or managed tree, takeover MUST migrate the whole
workspace group or materialize separate worktrees. It MUST NOT move one session
onto a concurrently mutated shared directory.

Normative example:

~~~json
{
  "schema": "urn:ax:schema:workspace-group",
  "schema_version": "1.0.0",
  "record_id": "sha256:3b366ca989681c63323c5de6db28198796aa913947ad3cd9456fc6dcee62b743",
  "subject_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "display_name": "payments",
  "members": [
    {
      "workspace_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
      "kind": "git",
      "group_relative_path": "payments-api",
      "repository_identity": "relux/payments-api",
      "sanitized_remote_urls": ["ssh://git@github.com/relux/payments-api.git"],
      "repo_relative_cwd": "src",
      "agent_project_config_paths": ["AGENTS.md"],
      "materialization_policy": "separate_worktree"
    },
    {
      "workspace_id": "0198f4c8-7d40-7e55-8e6f-2234567890ab",
      "kind": "managed_tree",
      "group_relative_path": "design-notes",
      "tree_identity": "relux/design-notes",
      "repo_relative_cwd": "drafts",
      "agent_project_config_paths": ["AGENTS.md"],
      "materialization_policy": "separate_copy"
    }
  ],
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:09:50.000Z",
  "extensions": {}
}
~~~

The managed-tree member above is also a standalone positive tagged-union
fixture:

~~~json
{
  "workspace_id": "0198f4c8-7d40-7e55-8e6f-2234567890ab",
  "kind": "managed_tree",
  "group_relative_path": "design-notes",
  "tree_identity": "relux/design-notes",
  "repo_relative_cwd": "drafts",
  "agent_project_config_paths": ["AGENTS.md"],
  "materialization_policy": "separate_copy"
}
~~~

<code>WG-N1</code> adds <code>sanitized_remote_urls</code> to that
managed-tree variant, <code>WG-N2</code> omits <code>repository_identity</code>
from the Git variant, <code>WG-N3</code> uses
<code>separate_worktree</code> on a managed tree, and <code>WG-N4</code> adds an
unknown nested member. All four fixtures MUST be rejected.

Session membership is derived, never selected from competing group records.
For a converged immutable-object set, <code>all_members(G)</code> is the
bytewise-sorted set of Session Records whose <code>workspace_group_id = G</code>.
<code>live_members(G)</code> removes only sessions with an authoritative
Section 10.7 session Tombstone. Stop does not remove membership, and a Session
Record can never move to another group. A logical leave therefore means an
authorized session Tombstone; continuing work in another topology means a new
or forked Session Record.

The active shared-checkout set for a host H is the subset of
<code>live_members(G)</code> whose winning lifecycle is <code>running</code>,
<code>idle</code>, <code>quiescing</code>, or <code>checkpointing</code> and whose
local managed-replica marker names the same shared checkout/tree on H. A
takeover MaterializationCohort MUST include that complete set and MAY also
include stopped selected members; a stopped-only owner therefore has a valid
one-member cohort. Passive sync and owner resume instead use an empty ownership-
transfer set as Section 11.3 requires. The complete live-member records form
the WorkspaceGroupExpectation; the separately typed MaterializationCohort
selects materialization and ownership transfer. Every prepare, stop, lease,
materialization, and resume phase MUST revalidate both applicable objects. A
concurrent join or authoritative leave invalidates the expectation and fails
the group operation with <code>workspace_group_changed</code> before another
member is activated.

Normative convergence fixtures are:

| Fixture | Union input | Required result |
| --- | --- | --- |
| <code>WG-JOIN-CONCURRENT</code> | Two valid new Session Records independently reference G | Both record IDs appear in <code>all_members(G)</code>; no record wins or is discarded |
| <code>WG-LEAVE-CONCURRENT</code> | A valid new Session Record and an authoritative session Tombstone for a different member arrive in either order | The join is present and the tombstoned member is absent from <code>live_members(G)</code>; order does not matter |
| <code>WG-MOVE-N1</code> | An implementation attempts to rewrite an existing Session Record to another group | Reject the different bytes/identity; require a new session or fork |
| <code>WG-GROUP-CONFLICT-N1</code> | Two distinct Workspace Group Records claim G | <code>integrity_failure</code>; park all referring sessions; no timestamp winner |
| <code>WG-TAKEOVER-CONCURRENT-N1</code> | Membership changes after group prepare | Abort before activation, retain staging, recompute the expectation, and retry |

### 5.7 Derived session states

The state engine derives exactly one state for each
<code>(session_id, host_id)</code> projection and separately reports the
winning owner's projection as the session lifecycle state. Thus a destination
can be <code>running</code> while an old host is locally <code>stale</code>:

| State | Meaning |
| --- | --- |
| <code>creating</code> | Session record and initial lease exist; no first validated checkpoint exists and bootstrap launch/retry is in progress |
| <code>running</code> | Winning owner has a live provider turn or accepts input |
| <code>idle</code> | Owner is live at an adapter-proven safe turn boundary |
| <code>quiescing</code> | New input is blocked while waiting for a safe boundary and clean stop |
| <code>checkpointing</code> | Safe state is being captured and validated |
| <code>stopped</code> | Winning owner has no provider process and a non-null validated checkpoint from which it is resumable |
| <code>materializing</code> | Destination staging/validation is in progress; it is not owner-active |
| <code>parked</code> | Wrapper exists but refuses provider launch due to remote/unknown ownership |
| <code>failed</code> | An operation failed and recovery metadata exists |
| <code>stale</code> | Local process/replica has a losing fencing token |
| <code>tombstoned</code> | Session is logically deleted and cannot resume |

The exact <code>SessionState</code> enum is, in this order,
<code>creating</code>, <code>running</code>, <code>idle</code>,
<code>quiescing</code>, <code>checkpointing</code>, <code>stopped</code>,
<code>materializing</code>, <code>parked</code>, <code>failed</code>,
<code>stale</code>, and <code>tombstoned</code>. Every RPC and CLI field typed
<code>SessionState</code> uses exactly this registry. The spellings
<code>created</code>, <code>starting</code>, and <code>quiesced</code> are not
session lifecycle states in Session Record 1.0.0; a subsystem-specific bridge state
MAY use <code>quiesced</code> only where Section 9 declares that separate enum.

Allowed transitions are:

~~~text
creating -> running | idle | failed
running -> idle | quiescing | failed | stale
idle -> running | quiescing | checkpointing | stopped | stale
quiescing -> idle | checkpointing | failed | stale
checkpointing -> idle | stopped | materializing | failed
materializing -> stopped | running | parked | failed
stopped -> materializing | running | parked | tombstoned
parked -> materializing | running | stopped | stale
failed -> creating | stopped | parked | materializing | stale | tombstoned
stale -> stopped | tombstoned
~~~

Any transition not listed MUST fail with <code>invalid_state_transition</code>.
Force takeover changes the old host's derived state to <code>stale</code> after
lease convergence even if its process remains alive.

The <code>failed -> creating</code> edge is permitted only for an epoch-1
session with no validated checkpoint, the same winning create lease, no
authoritative <code>session.bootstrap_aborted</code> event, and the Section 13.1
bootstrap-retry preconditions. A force-closed bootstrap remains
<code>failed</code> and non-resumable. No event or RPC result may derive
<code>stopped</code> while <code>newest_checkpoint_id</code> is null.

## 6. Configuration contract

### 6.1 Loading and precedence

Configuration schema <code>urn:ax:schema:config</code> version
<code>1.0.0</code> is encoded as TOML. Precedence, highest first, is:

1. command flags;
2. the five documented Section 3.2 <code>AX_*</code> path overrides;
3. values in the selected configuration file; and
4. normative defaults in this section.

The configuration file itself is selected by <code>--config</code>, then
<code>AX_CONFIG</code>, then the platform-default configuration directory's
<code>config.toml</code>. The data, state, cache, and runtime overrides select
infrastructure roots and are not TOML field-by-field overrides. The same
resolved roots MUST be used by the CLI, service, RPC server, provider host, and
crash recovery for the entire process lifetime.

Unknown top-level keys MUST fail configuration loading. Secret values MUST NOT
be accepted in config fields; a provider MAY name a machine-local environment
variable or credential profile.

The complete 1.0.0 environment-override registry is
<code>AX_CONFIG</code>, <code>AX_DATA_DIR</code>,
<code>AX_STATE_DIR</code>, <code>AX_CACHE_DIR</code>, and
<code>AX_RUNTIME_DIR</code>, with the value kinds and empty-value rule in
Section 3.2. There are no other field-by-field <code>AX_*</code> overrides in
this version. Provider credential variables are destination-local inputs and
never configuration values.

### 6.2 Normative example

~~~toml
schema = "urn:ax:schema:config"
schema_version = "1.0.0"
host_id = "0198f4c8-4a10-7b22-8b3c-1234567890ab"
host_name = "mbp-ivan"
platform = "macos"

[mesh]
transport = "ssh"
sync_interval_seconds = 60
connect_timeout_seconds = 10
rpc_timeout_seconds = 300
workspace_replication = true
payload_encryption = "none"

[[mesh.peers]]
host_id = "0198f4c8-7d40-7e55-8e6f-1234567890ab"
name = "workstation"
endpoint = "ivan@workstation.tailnet.ts.net"
platform = "linux"
ssh_args = ["-o", "BatchMode=yes"]

[[mesh.peers.workspace_roots]]
logical_root = "relux"
path = "/srv/relux"

[[workspace_roots]]
logical_root = "relux"
path = "/Users/iv/Developer/ReluxWorks"

[providers]
plugin_dirs = ["/Users/iv/.local/libexec/ax/providers"]
allow_path_plugins = true
require_explicit_trust = true

[sync]
chunk_bytes = 4194304
max_parallel_chunks = 4
staging_retention_hours = 72
tombstone_min_retention_days = 90

[terminal]
backend = "tmux"
safe_boundary_timeout_seconds = 300
graceful_stop_timeout_seconds = 60

[service]
enabled = true
health_interval_seconds = 30

[restore]
auto_resume = false

[profiles.yolo]
require_first_use_confirmation = true
~~~

On native Windows, a workspace mapping is written with a quoted TOML string
such as <code>path = "D:\\Developer\\ReluxWorks"</code>, and terminal backend
MUST be <code>conpty</code>. WSL2 configuration uses Linux paths and
<code>platform = "wsl2"</code>.

### 6.3 Field constraints

<code>platform</code> is one of <code>macos</code>, <code>linux</code>,
<code>wsl2</code>, or <code>windows</code>. A peer is authorized only when its
stable <code>host_id</code> appears in <code>mesh.peers</code> and the SSH
endpoint resolves to the authenticated host expected by SSH host-key policy.
Tailscale discovery MAY suggest a candidate configuration but MUST NOT write or
authorize it automatically.

<code>mesh.payload_encryption</code> MUST be <code>none</code> in v0.2.0.
Other values MUST fail as unsupported. SSH supplies transport protection; this
setting prevents a misleading at-rest encryption claim.

<code>sync.chunk_bytes</code> MUST equal 4,194,304 in Configuration 1.0.0.
Implementations MAY expose the field for forward compatibility but MUST reject
another value in this protocol version.

Workspace roots MUST have unique <code>logical_root</code> values. Paths MAY
differ across hosts. A materializer MUST map a workspace using
<code>logical_root</code> plus a validated relative path, never a source
absolute path.

The complete v1 field/default contract is:

| Key | Required/default | Constraint |
| --- | --- | --- |
| <code>schema</code> | Required | Exact config schema identifier |
| <code>schema_version</code> | Required | Compatible version negotiated by this binary |
| <code>host_id</code> | Required | Stable UUIDv7; changing it creates a new mesh host |
| <code>host_name</code> | Required | 1–64 printable non-control UTF-8 characters |
| <code>platform</code> | Required | One of the four values above; MUST match runtime probe |
| <code>mesh.transport</code> | Default <code>ssh</code> | Only <code>ssh</code> in v0.2.0 |
| <code>mesh.sync_interval_seconds</code> | Default 60 | Integer 5–86,400 |
| <code>mesh.connect_timeout_seconds</code> | Default 10 | Integer 1–300 |
| <code>mesh.rpc_timeout_seconds</code> | Default 300 | Integer 10–3,600 |
| <code>mesh.workspace_replication</code> | Default true | Boolean |
| <code>mesh.payload_encryption</code> | Default <code>none</code> | Only <code>none</code> in v0.2.0 |
| <code>mesh.peers</code> | Default empty | Unique host ID and name; endpoint required |
| <code>mesh.peers[].ssh_args</code> | Default empty | Arg array; MUST NOT disable host-key checks |
| <code>mesh.peers[].workspace_roots</code> | Default empty | Unique logical roots within peer |
| <code>workspace_roots</code> | Default empty | At least one matching root required for workspace materialization |
| <code>providers.plugin_dirs</code> | Default empty | Absolute directories |
| <code>providers.allow_path_plugins</code> | Default true | Boolean |
| <code>providers.require_explicit_trust</code> | Default true | MUST remain true unless an enterprise policy supplies equivalent signed trust |
| <code>sync.chunk_bytes</code> | Default/fixed 4,194,304 | Protocol 1.0.0 constant |
| <code>sync.max_parallel_chunks</code> | Default 4 | Integer 1–32 |
| <code>sync.staging_retention_hours</code> | Default 72 | Integer 1–720 |
| <code>sync.tombstone_min_retention_days</code> | Default/minimum 90 | Integer 90–3,650 |
| <code>terminal.backend</code> | Platform default | <code>tmux</code> on macOS/Linux/WSL2; <code>conpty</code> on Windows |
| <code>terminal.safe_boundary_timeout_seconds</code> | Default 300 | Integer 1–3,600 |
| <code>terminal.graceful_stop_timeout_seconds</code> | Default 60 | Integer 1–600 |
| <code>service.enabled</code> | Default true after service installation | Boolean; false never disables core CLI |
| <code>service.health_interval_seconds</code> | Default 30 | Integer 5–3,600 |
| <code>restore.auto_resume</code> | Default false | Boolean; true still requires accepted provider/platform restore gate |
| <code>profiles.yolo.require_first_use_confirmation</code> | Default true | Boolean; non-interactive launch still requires explicit profile |

Every TOML table and array-of-tables is closed. The allowed root members are
the five scalar keys in the example plus <code>mesh</code>,
<code>workspace_roots</code>, <code>providers</code>, <code>sync</code>,
<code>terminal</code>, <code>service</code>, <code>restore</code>, and
<code>profiles</code>. <code>mesh</code>, <code>providers</code>,
<code>sync</code>, <code>terminal</code>, <code>service</code>, and
<code>restore</code> contain exactly their dotted keys in the table above;
<code>profiles</code> contains exactly <code>yolo</code>, whose only key is
<code>require_first_use_confirmation</code>.

Each <code>mesh.peers</code> entry contains exactly
<code>host_id:UUIDv7</code>, <code>name:string[1..64]</code>,
<code>endpoint:string[1..1024]</code>,
<code>platform:macos|linux|wsl2|windows</code>,
<code>ssh_args:array&lt;string&gt;[0..64]</code>, and
<code>workspace_roots:WorkspaceRoot[0..64]</code>. Each root-level or peer
WorkspaceRoot contains exactly <code>logical_root:string[1..64]</code> matching
<code>[a-z][a-z0-9_-]{0,63}</code> and <code>path:absolute-path</code>.
Endpoint and every SSH argument are passed as atomic argv values, never through
a shell. Each argument is 1–4,096 UTF-8 bytes, and the total SSH argv is at
most 65,536 bytes. Omitting a defaulted member uses the table's stated default;
explicit null is not a TOML value and is never accepted as a substitute.

SSH arguments that set <code>StrictHostKeyChecking=no</code>, an empty
<code>UserKnownHostsFile</code>, or an equivalent host-authentication bypass
MUST fail configuration validation.

## 7. Provider plugin protocol

### 7.1 Discovery and trust

Built-in support covers <code>codex</code>, <code>claude</code>,
<code>gemini</code>, <code>muse</code>, <code>antigravity</code>, and
<code>pi</code>. External provider executables are named
<code>ax-provider-&lt;id&gt;</code>, where <code>id</code> matches
<code>[a-z][a-z0-9-]{0,31}</code>.

Candidate discovery order is:

1. configured <code>providers.plugin_dirs</code> in listed order;
2. built-in adapters; then
3. <code>PATH</code>, only when <code>allow_path_plugins</code> is true.

The order does not establish precedence. If two candidates—including a built-in
and an executable—declare the same provider ID, discovery MUST fail with
<code>invalid_config</code> before either candidate is probed or executed.
Configuration schema 1.0.0 has no duplicate-selection override; the operator
must remove or rename one candidate. For each accepted external candidate, the
canonical absolute executable path and SHA-256 digest MUST be recorded at trust
time. Symlinks MUST be resolved before comparison, the target MUST be a regular
file owned by the operator or an administrator-approved identity, and a changed
path target or digest MUST require renewed trust. Plugins execute with the
operator's privileges and are inside the trusted-host boundary, but they MUST
receive only the minimum operation-specific inputs.

### 7.2 Framing and lifecycle

The provider protocol is line-delimited JSON over stdin/stdout with
<code>protocol = "urn:ax:protocol:provider"</code> and
<code>protocol_version = "2.0.0"</code>. Each line MUST be one complete UTF-8
JSON object no larger than 8 MiB. Stdout MUST contain protocol frames only;
human diagnostics go to stderr.

<code>ax</code> starts one plugin process per operation. Requests are
single-flight in v2. After one response, <code>ax</code> closes stdin and the
plugin MUST exit. Exit 0 requires a successful response. A structured error
response SHOULD exit 0 because the protocol succeeded; a crash, invalid frame,
or missing response is a provider-host failure.

Request envelope:

~~~json
{
  "protocol": "urn:ax:protocol:provider",
  "protocol_version": "2.0.0",
  "request_id": "0198f4c8-8e50-7f66-8f70-1234567890ab",
  "operation": "doctor",
  "deadline": "2026-08-19T04:05:00.000Z",
  "body": {
    "platform": "macos",
    "architecture": "arm64",
    "provider_executable": "/opt/local/bin/pi",
    "identity": null
  }
}
~~~

The request envelope contains exactly <code>protocol</code>,
<code>protocol_version</code>, <code>request_id</code> UUIDv7,
<code>operation</code> from the Section 7.5 operation registry,
<code>deadline</code> timestamp, and the operation-specific <code>body</code>.
The deadline MUST be in the future when the host writes the frame.

Success envelope:

~~~json
{
  "protocol": "urn:ax:protocol:provider",
  "protocol_version": "2.0.0",
  "request_id": "0198f4c8-8e50-7f66-8f70-1234567890ab",
  "ok": true,
  "body": {
    "provider_id": "pi",
    "provider_version": "0.73.1",
    "findings": []
  }
}
~~~

A success envelope contains exactly <code>protocol</code>,
<code>protocol_version</code>, <code>request_id</code>, <code>ok = true</code>,
and the operation-specific <code>body</code>. A failure envelope contains
exactly the first four members with <code>ok = false</code> plus
<code>error</code>, and MUST NOT contain <code>body</code>. Envelope and body
unknown members are protocol errors under major version 2.

Failure envelope:

~~~json
{
  "protocol": "urn:ax:protocol:provider",
  "protocol_version": "2.0.0",
  "request_id": "0198f4c8-8e50-7f66-8f70-1234567890ab",
  "ok": false,
  "error": {
    "schema": "urn:ax:schema:error",
    "schema_version": "1.0.0",
    "code": "capability_unavailable",
    "message": "portable store is not available for this provider build",
    "exit_code": 6,
    "retryable": false,
    "details": {}
  }
}
~~~

Provider protocol <code>2.x</code> statically binds every failure envelope to
Structured Error <code>1.0.0</code>. The error schema is not independently
negotiated on a provider invocation; a provider-protocol minor that needs a
different error schema must explicitly revise that binding. Section 15.1
defines supported-major, unsupported-major, and invalid-first-frame behavior.

The host MUST terminate a plugin that exceeds its deadline and report
<code>provider_timeout</code>. It MUST redact environment and stderr before
logging.

### 7.3 Provider Manifest

The <code>manifest</code> operation requires an empty body and returns
<code>urn:ax:schema:provider-manifest</code> version <code>1.0.0</code>:

~~~json
{
  "schema": "urn:ax:schema:provider-manifest",
  "schema_version": "1.0.0",
  "provider_id": "pi",
  "display_name": "Pi",
  "plugin_version": "0.1.0",
  "provider_version_range": ">=0.73.1 <0.74.0",
  "platforms": ["linux", "macos", "windows", "wsl2"],
  "operations": [
    "manifest",
    "probe",
    "launch",
    "identify-session",
    "quiesce",
    "native-store-plan",
    "capture",
    "materialize",
    "materialize-status",
    "materialize-commit",
    "materialize-rollback",
    "resume",
    "fork",
    "stop",
    "doctor"
  ],
  "capability_names": [
    "native_resume",
    "portable_store",
    "managed_pty",
    "appserver",
    "task_board_primary",
    "prompt_spawn",
    "native_goal_binding"
  ]
}
~~~

The manifest is closed and every displayed member is required.
<code>display_name</code> is 1–128 UTF-8 characters;
<code>plugin_version</code> is SemVer; <code>provider_version_range</code> is a
1–256 character provider-adapter constraint; <code>platforms</code> is a sorted,
unique non-empty subset of the four platform enums; <code>operations</code> is
the ordered registry shown in Section 7.5 with no duplicates; and
<code>capability_names</code> is the exact seven-name ordered registry shown.
The manifest declares possible surfaces, not runtime availability.

### 7.4 Capability result

The <code>probe</code> operation body contains platform, architecture,
provider executable path, and requested capability names. Its response MUST
identify the exact provider version and emit every known capability using
<code>urn:ax:schema:provider-probe</code> version <code>1.0.0</code>:

~~~json
{
  "schema": "urn:ax:schema:provider-probe",
  "schema_version": "1.0.0",
  "provider_id": "pi",
  "provider_version": "0.73.1",
  "platform": "macos",
  "architecture": "arm64",
  "capabilities": {
    "native_resume": {
      "status": "available",
      "enabled": true,
      "evidence": "probed",
      "detail": "--session, --continue, and --resume are present"
    },
    "portable_store": {
      "status": "conditional",
      "enabled": false,
      "evidence": "acceptance_required",
      "detail": "closed-store cross-host fixture has not passed"
    },
    "managed_pty": {
      "status": "conditional",
      "enabled": false,
      "evidence": "acceptance_required",
      "detail": "platform PTY interruption and flush gate has not passed"
    },
    "appserver": {
      "status": "unsupported",
      "enabled": false,
      "evidence": "provider_contract",
      "detail": "Pi RPC is not claimed as the ax appserver capability"
    },
    "task_board_primary": {
      "status": "unknown",
      "enabled": false,
      "evidence": "none",
      "detail": "no reliable primary adapter is accepted"
    },
    "prompt_spawn": {
      "status": "unknown",
      "enabled": false,
      "evidence": "none",
      "detail": "not claimed for v0.2.0"
    },
    "native_goal_binding": {
      "status": "unsupported",
      "enabled": false,
      "evidence": "provider_contract",
      "detail": "no native task-board goal binding"
    }
  },
  "warnings": []
}
~~~

The probe object is closed and every displayed member is required.
<code>provider_version</code> is a 1–128 character exact version string,
architecture is <code>amd64</code> or <code>arm64</code>, and
<code>capabilities</code> contains exactly the seven requested registry keys.
Each capability value contains exactly <code>status</code>,
<code>enabled</code>, <code>evidence</code>, and a 0–2,048 character
<code>detail</code>. <code>warnings</code> is a sorted, unique array of at most
1,024 strings of at most 2,048 characters each.

Status is one of <code>available</code>, <code>conditional</code>,
<code>unsupported</code>, or <code>unknown</code>. Only
<code>available</code> MAY set <code>enabled</code> true. Evidence is one of
<code>documented</code>, <code>probed</code>, <code>accepted_test</code>,
<code>provider_contract</code>, <code>inferred</code>,
<code>acceptance_required</code>, or <code>none</code>.

### 7.5 Required operations

All plugins MUST implement every operation and return
<code>capability_unavailable</code> when the provider lacks the surface.

Every request and success <code>body</code> is a closed object. The following
embedded types are part of provider protocol 2.0.0:

| Type | Exact members and constraints |
| --- | --- |
| <code>LeaseToken</code> | <code>session_id:UUIDv7</code>, <code>lease_epoch:uint53 &gt; 0</code>, <code>lease_id:UUIDv4</code> |
| <code>WorkspacePaths</code> | <code>map(UUIDv7,absolute-path)[1..256]</code>; paths are destination-native, canonical, and contain no NUL |
| <code>TerminalDescriptor</code> | <code>backend:tmux&#124;conpty</code>, <code>terminal_id:string[1..512]</code>, <code>interactive:boolean</code>, <code>columns:uint16[1..1000]</code>, <code>rows:uint16[1..1000]</code> |
| <code>ProcessObservation</code> | <code>terminal_id:string[1..512]</code>, <code>executable_path:absolute-path</code>, <code>started_at:timestamp</code>, <code>candidate_store_paths:sorted unique absolute-path[0..256]</code>, <code>candidate_native_ids:sorted unique string[0..256]</code>; no PID is carried |
| <code>SpawnPlan</code> | <code>argv:array&lt;string&gt;[1..128]</code>, <code>cwd:absolute-path</code>, <code>env_names:sorted unique environment-name[0..64]</code>, <code>env_literals:map(environment-name,string)[0..64]</code>, <code>native_session_id:string[1..512]&#124;null</code>, <code>profile_mapping:string[1..512]</code>, <code>extensions:object</code>; argv/literal limits and secret rules equal Section 5.1 |
| <code>SafeBoundaryProof</code> | <code>provider_id:provider-id</code>, <code>provider_version:string[1..128]</code>, <code>input_blocked:boolean</code>, <code>boundary_ref:string[1..1024]&#124;null</code>, <code>foreground_idle:boolean</code>, <code>background_idle:boolean&#124;null</code>, <code>open_child_count:uint53</code>, <code>open_database_handle_count:uint53</code>, <code>store_generation:string[1..512]&#124;null</code>, <code>safe:boolean</code>, <code>blockers:sorted unique enum[0..5]</code> |
| <code>ValidationEvidence</code> | <code>code:string[1..128]</code>, <code>status:passed&#124;skipped</code>, <code>detail:string[0..2048]</code> |
| <code>NativeDiscoveryProof</code> | <code>native_session_id:string[1..512]</code>, <code>discovered:boolean</code>, <code>discovery_root:absolute-path&#124;null</code>, <code>backend_resolved:boolean</code> |
| <code>ProcessClosure</code> | <code>process_closed:boolean</code>, <code>store_closed:boolean</code>, <code>exit_code:int32&#124;null</code>, <code>remaining_process_handles:sorted unique string[0..256]</code>, <code>final_store_generation:string[1..512]&#124;null</code> |
| <code>DoctorFinding</code> | <code>severity:info&#124;warning&#124;error</code>, <code>code:string[1..128]</code>, <code>message:string[1..4096]</code>, <code>remediation:string[1..4096]&#124;null</code>, <code>evidence:documented&#124;probed&#124;accepted_test&#124;provider_contract&#124;inferred&#124;acceptance_required&#124;none</code> |
| <code>ProviderStoreAuthority</code> | <code>authority_id:root-id</code>, <code>provider_id:provider-id</code>, <code>platform:macos&#124;linux&#124;wsl2&#124;windows</code>, <code>root_path:absolute-path</code>, <code>root_role:durable_store&#124;durable_index&#124;derived_cache</code>, <code>access:capture_source&#124;materialize_destination</code> |
| <code>AuthorityTarget</code> | <code>authority_id:root-id</code>, <code>relative_path:.&#124;path</code> |
| <code>ProviderCaptureItem</code> | <code>source_authority_id:root-id</code>, <code>source_relative_path:path</code>, <code>manifest_path:path</code>, <code>kind:file&#124;directory</code>, <code>state_class:durable_payload&#124;durable_index&#124;derived_cache</code>, <code>required:boolean</code> |
| <code>ProviderCapturePlan</code> | <code>capture_id:UUIDv7</code>, <code>source_authorities:ProviderStoreAuthority[1..32]</code>, <code>items:ProviderCaptureItem[1..32768]</code>, <code>excluded_targets:AuthorityTarget[0..4096]</code>, <code>store_generation:string[1..512]</code>, <code>snapshot_requires_closed_store:boolean</code> |
| <code>ObjectSink</code> | <code>root:absolute-path</code>, <code>layout:sha256_loose_v1</code>, <code>create_mode:exclusive</code>, <code>max_bytes:uint53</code>, <code>max_blobs:uint53</code> |
| <code>ProviderObjectSourceAuthority</code> | <code>authority_id:provider_objects</code>, <code>kind:provider_object_source</code>, <code>root_path:absolute-path</code>, <code>layout:sha256_loose_v1</code>, <code>access:read_only</code>, <code>materialization_id:UUIDv7</code>, <code>provider_id:provider-id</code>, <code>manifest_ids:sorted unique digest[1..1024]</code>, <code>max_bytes:uint53</code>, <code>max_blobs:uint53</code> |
| <code>ProviderTransactionAuthority</code> | <code>authority_id:provider_transaction</code>, <code>kind:provider_transaction</code>, <code>root_path:absolute-path</code>, <code>layout:provider_transaction_v1</code>, <code>access:read_write</code>, <code>materialization_id:UUIDv7</code>, <code>provider_id:provider-id</code>, <code>transaction_id:UUIDv7</code>, <code>plan_id:digest</code>, <code>same_filesystem_provider_authority_ids:sorted unique root-id[1..32]</code> |
| <code>ProviderTransactionEntry</code> | <code>sequence:uint53&gt;0</code>, <code>provider_authority_id:root-id</code>, <code>target_relative_path:path</code>, <code>expected_prior_digest:digest&#124;null</code>, <code>prior_kind:absent&#124;file&#124;directory&#124;symlink&#124;hardlink</code>, <code>backup_relative_path:path&#124;null</code>, <code>applied:boolean</code>, <code>restored:boolean</code> |
| <code>ProviderTransactionDocument</code> | <code>protocol:urn:ax:protocol:provider</code>, <code>protocol_version:2.0.0</code>, <code>document_kind:materialization_transaction</code>, <code>operation_id:UUIDv7</code>, <code>materialization_id:UUIDv7</code>, <code>transaction_id:UUIDv7</code>, <code>provider_id:provider-id</code>, <code>plan_id:digest</code>, <code>state:preparing&#124;prepared&#124;committing&#124;committed&#124;rolling_back&#124;rolled_back</code>, <code>rollback_token:base64url-256+&#124;null</code>, <code>entries:ProviderTransactionEntry[1..65536]</code>, <code>native_discovery:NativeDiscoveryProof&#124;null</code>, <code>created_at:timestamp</code>, <code>updated_at:timestamp</code>, <code>terminal_at:timestamp&#124;null</code> |
| <code>ProviderTransactionStatus</code> | <code>operation_id:UUIDv7</code>, <code>materialization_id:UUIDv7</code>, <code>transaction_id:UUIDv7</code>, <code>transaction_authority_id:provider_transaction</code>, <code>plan_id:digest&#124;null</code>, <code>state:unknown&#124;prepared&#124;committed&#124;rolled_back</code>, <code>rollback_token:base64url-256+&#124;null</code>, <code>native_discovery:NativeDiscoveryProof&#124;null</code> |

The <code>SafeBoundaryProof.blockers</code> enum is
<code>background_unproven</code>, <code>child_process_open</code>,
<code>database_handle_open</code>, <code>provider_busy</code>, or
<code>store_unstable</code>. A safe proof requires empty blockers,
<code>input_blocked</code>, <code>foreground_idle</code>,
<code>background_idle = true</code>, both counts zero, and non-null boundary and
store generation. <code>ValidationEvidence</code> arrays MUST be sorted by
<code>code</code> with no duplicate code. Opaque process handles are valid only
for the operation lifetime and MUST NOT be persisted or replicated.

The <code>root-id</code> grammar is
<code>[a-z][a-z0-9_-]{0,63}</code>. Capture authorities are sorted by
<code>authority_id</code>, have <code>access = capture_source</code>, and are
unique. Capture items are sorted by <code>manifest_path</code>; each authority
reference MUST resolve, and
<code>root_path/source_relative_path</code> MUST remain under that exact root
after symlink/reparse-point resolution. Items MUST neither overlap nor traverse
through a symlink. Excluded targets are sorted by authority ID then relative
path and MUST reference the same authority set. <code>derived_cache</code> is
included only when Section 8 identifies it as required discovery metadata;
otherwise it must be excluded. Provider roots that contain credentials,
machine authentication, runtime sockets, locks, or live ax state MUST be
rejected even when a plugin names them. <code>ObjectSink.root</code> is a fresh owner-only directory
created by <code>ax</code>. Under <code>sha256_loose_v1</code>, a plugin writes
each complete blob with create-new semantics at
the exact Section 3.2 <code>digest_path_v1</code> relative path
<code>sha256/HH/REST</code> (two-hex shard, 62-hex leaf).
It MUST NOT create symlinks, hardlinks, devices, sockets, or any file not named
by its returned descriptors. The host independently hashes every sink file,
checks size/limits/exclusions, and only then imports it into the ax object
store. A plugin never receives the live object-store root.

The destination host, not the peer and not the plugin, constructs both
materialization authorities. A <code>ProviderObjectSourceAuthority.root_path</code>
MUST equal
<code>&lt;state&gt;/provider-object-sources/&lt;materialization-id&gt;/&lt;provider-id&gt;</code>;
it is a fresh owner-only directory containing exactly the verified manifest
closure at the same <code>digest_path_v1</code> paths. The host makes every file read-only
before invoking the plugin. The authority's manifest IDs, byte/blob limits,
materialization ID, and provider ID MUST equal the selected checkpoint and
plan. An extra file, writable file, symlink, digest mismatch, or path supplied
by a remote request is <code>integrity_failure</code>.

A <code>ProviderTransactionAuthority.root_path</code> MUST equal
<code>&lt;state&gt;/provider-transactions/&lt;provider-id&gt;/&lt;transaction-id&gt;</code>.
It is a fresh owner-only directory, is disjoint from the object source and all
plan roots, and names exactly the materialization/provider/transaction/plan in
the authority. Its
<code>same_filesystem_provider_authority_ids</code> MUST equal the sorted set of
all <code>provider_store</code> RootAuthority IDs used by plan operations. The
host MUST prove that the transaction root and every named provider-store root
are on the same filesystem/volume before the first plugin mutation. If one is
not, provider protocol 2.0.0 fails with <code>atomic_commit_unavailable</code>; it MUST
NOT fall back to an in-place cross-filesystem copy.

The <code>provider_transaction_v1</code> layout contains only these durable
paths, plus one same-directory temporary file while atomically replacing
<code>transaction.json</code>:

~~~text
transaction.json
staged/<provider-authority-id>/<operation-sequence>
backups/<provider-authority-id>/<operation-sequence>
~~~

<code>transaction.json</code> is the UTF-8 JCS encoding of the closed
<code>ProviderTransactionDocument</code>. Entries are sorted by sequence and
are exactly the provider-store operations in the plan. For a pre-existing
target, <code>backup_relative_path</code> is exactly
<code>backups/&lt;provider-authority-id&gt;/&lt;operation-sequence&gt;</code>; an absent
target requires <code>prior_kind = absent</code>, a null backup path, and a null
expected prior digest. Every other prior kind requires that exact non-null
backup path and a non-null expected prior digest. A prepared document has every
entry applied, no entry restored, a non-null rollback token, and non-null native
discovery. A committed document keeps the applied facts, sets the token to
null, removes every staged/backup payload from disk, and has non-null
discovery. A rolled-
back document has every pre-existing entry restored, every transaction-created
target removed, a null token, and discovery describing the restored
destination. The plugin MUST fsync a staged replacement and the
transaction document, atomically rename any predecessor into its backup, then
atomically rename the staged replacement into the exact target. Each document
transition is written to a fresh temporary regular file, fsynced, renamed over
<code>transaction.json</code>, and followed by a parent-directory fsync where
the platform supports it. Windows uses replace/write-through semantics with
equivalent user-only DACLs.

<code>terminal_at</code> is null in <code>preparing</code>,
<code>prepared</code>, <code>committing</code>, and
<code>rolling_back</code> states and non-null in
<code>committed|rolled_back</code> states.
<code>updated_at</code> never precedes <code>created_at</code>, and terminal time
never precedes either. Timestamps are diagnostics; state, IDs, entry facts, and
filesystem verification decide recovery.

Every transaction operation receives the same complete
<code>ProviderTransactionAuthority</code>. A fresh plugin process locates state
only through that authority, validates the path and
<code>transaction.json</code> IDs before acting, and MUST NOT use an ambient
transaction registry or search another root. A crash while
<code>preparing</code>, <code>committing</code>, or <code>rolling_back</code> is
reconciled from the entries to one exposed status before
<code>materialize-status</code> responds; an irreconcilable entry is
<code>integrity_failure</code> and retains the root for diagnosis. Prepared
documents store the rollback token under owner-only permissions so a later
process can reconstruct the current durable status; terminal documents set it
to null.
Commit removes all backups only after durable committed state; rollback
restores all predecessors before durable rolled-back state. The terminal
<code>transaction.json</code> receipt remains until the corresponding
Materialization Journal is terminal and for at least
<code>sync.staging_retention_hours</code> afterward. Object-source bytes and
backup/staged subtrees MAY then be removed; live or ambiguous roots MUST NOT be
garbage-collected.

In <code>ProviderTransactionStatus</code>, <code>unknown</code> requires null
plan/token/discovery; <code>prepared</code> requires all three non-null;
<code>committed</code> and <code>rolled_back</code> require a non-null plan and
discovery proof and a null rollback token. The discovery proof in a rolled-back
status describes the destination after rollback. An operation failure does not
invent a status state: it returns the protocol failure envelope, and the next
status request reports the last durable state. An unreadable or
integrity-invalid transaction MUST fail with <code>integrity_failure</code> and
MUST be quarantined rather than represented as a successful status object.
Every provider mutation request that carries <code>operation_id</code> uses the
single Provider protocol 2.0.0 idempotency key
<code>(operation, operation_id)</code>. An
identical canonical mutation request MUST return a byte-identical result across
a fresh plugin process; any changed member is
<code>idempotency_mismatch</code> and MUST cause no new mutation. Observational
operations, including <code>materialize-status</code>, are evolving reads. They
use the provider envelope's fresh <code>request_id</code> only for correlation,
MUST NOT be stored as mutation receipts, and MUST return the durable state at
the read's reconciliation point even when an earlier identical read returned a
different phase. For <code>capture</code>, replay verifies/reuses only exact
digest-named files already present in the same Object Sink and re-emits the
same manifest/descriptors; an extra or changed file fails integrity. Provider
<code>fork</code> is side-effect-free and recomputes the same plan. The
materialize mutations use their durable transaction document as the receipt.
No operation relies on a searched ambient registry. Transaction IDs and
mutation operation IDs are caller-supplied and stable across retries. For one
provider materialization transaction, the <code>operation_id</code> is
transaction-wide across <code>materialize</code> and exactly one terminal
<code>materialize-commit</code> or <code>materialize-rollback</code>; a
<code>materialize-status</code> request omits it and locates the transaction only
through the caller-supplied materialization/transaction IDs and exact authority.
Reusing the mutation value across distinct operation tags does not alias their
recorded results. Within one provider ID,
an operation ID used by the materialize family identifies exactly one materialization transaction:
its <code>materialization_id</code>, <code>transaction_id</code>, plan ID, object
source, transaction authority, provider-store authorities, lease, activation,
rollback reason, and all remaining body members are immutable retry input for
their operation tag. Reusing <code>(operation, operation_id)</code> with any
different canonical body is <code>idempotency_mismatch</code>; the plugin MUST
return the first recorded result or failure and MUST NOT allocate, search, or
mutate another transaction root. A transaction or materialization ID already
bound to another operation ID is also <code>idempotency_mismatch</code>. There
is no second tuple- or path-based idempotency key in provider protocol 2.0.0.

The operation body registry is exact. A named schema object means the complete
validated object, not only its digest. Arrays of schema objects are sorted by
their canonical identity field and contain no duplicate identity:

| Operation | Exact request body | Exact success body |
| --- | --- | --- |
| <code>manifest</code> | <code>{}</code> | Provider Manifest object (Section 7.3) |
| <code>probe</code> | <code>{platform:macos&#124;linux&#124;wsl2&#124;windows, architecture:amd64&#124;arm64, provider_executable:absolute-path&#124;null, requested_capabilities:sorted unique capability-name[0..7]}</code> | Provider Probe object (Section 7.4) |
| <code>launch</code> | <code>{session_record:Session Record, workspace_paths:WorkspacePaths, execution_profile:standard&#124;yolo, launch_plan:Launch Plan, terminal:TerminalDescriptor}</code> | <code>SpawnPlan</code> |
| <code>identify-session</code> | <code>{session_id:UUIDv7, provider_id:provider-id, observation:ProcessObservation}</code> | <code>{identity:Provider Identity Record, confidence:exact&#124;strong&#124;weak, matched_evidence:sorted unique native_id&#124;store_path&#124;provider_event&#124;backend_lookup[1..4]}</code> |
| <code>quiesce</code> | <code>{identity:Provider Identity Record, terminal:TerminalDescriptor, timeout_ms:uint53[1..3600000], lease:LeaseToken}</code> | <code>{proof:SafeBoundaryProof}</code> |
| <code>native-store-plan</code> | Tagged <code>NativeStorePlanRequest</code>: capture is <code>{phase:capture, identity:Provider Identity Record, source_platform:macos&#124;linux&#124;wsl2&#124;windows, mode:snapshot&#124;handoff&#124;fork, source_workspace_paths:WorkspacePaths, lease:LeaseToken}</code>; materialize is <code>{phase:materialize, identity:Provider Identity Record, source_platform:macos&#124;linux&#124;wsl2&#124;windows, destination_platform:macos&#124;linux&#124;wsl2&#124;windows, destination_host_id:UUIDv7, mode:snapshot&#124;handoff&#124;fork, source_manifest_id:digest, destination_workspace_paths:WorkspacePaths, lease:LeaseToken}</code> | Tagged <code>NativeStorePlanResult</code>: capture is <code>{phase:capture, capture_plan:ProviderCapturePlan, include_classes:sorted unique string[0..128], exclude_classes:sorted unique string[0..128]}</code>; materialize is <code>{phase:materialize, materialization_plan:Materialization Plan, include_classes:sorted unique string[0..128], exclude_classes:sorted unique string[0..128], path_key_rewrites:map(UUIDv7,string[1..1024])[0..256]}</code> |
| <code>capture</code> | <code>{operation_id:UUIDv7, capture_plan:ProviderCapturePlan, proof:SafeBoundaryProof, object_sink:ObjectSink, lease:LeaseToken}</code> | <code>{operation_id:UUIDv7, capture_id:UUIDv7, manifest:Transfer Manifest, blob_descriptors:sorted unique Blob Descriptor[0..32768], written_blob_ids:sorted unique digest[0..32768], captured_store_generation:string[1..512], exclusions_applied:sorted unique string[0..128]}</code> |
| <code>materialize</code> | <code>{operation_id:UUIDv7, materialization_id:UUIDv7, transaction_id:UUIDv7, plan:Materialization Plan, object_source:ProviderObjectSourceAuthority, transaction:ProviderTransactionAuthority, destination_workspace_paths:WorkspacePaths, lease:LeaseToken}</code> | <code>{operation_id:UUIDv7, materialization_id:UUIDv7, transaction_id:UUIDv7, plan_id:digest, state:prepared, created_paths:sorted unique absolute-path[0..65536], merged_paths:sorted unique absolute-path[0..65536], validations:ValidationEvidence[1..256], rollback_token:base64url-256+, native_discovery:NativeDiscoveryProof}</code> |
| <code>materialize-status</code> | <code>{materialization_id:UUIDv7, transaction_id:UUIDv7, transaction:ProviderTransactionAuthority}</code> | <code>ProviderTransactionStatus</code> |
| <code>materialize-commit</code> | <code>{operation_id:UUIDv7, materialization_id:UUIDv7, transaction_id:UUIDv7, transaction:ProviderTransactionAuthority, rollback_token:base64url-256+, activation:dormant_validated&#124;owner_resumed, lease:LeaseToken}</code> | <code>{operation_id:UUIDv7, materialization_id:UUIDv7, transaction_id:UUIDv7, plan_id:digest, state:committed, backup_removed:boolean, committed_at:timestamp}</code> |
| <code>materialize-rollback</code> | <code>{operation_id:UUIDv7, materialization_id:UUIDv7, transaction_id:UUIDv7, transaction:ProviderTransactionAuthority, rollback_token:base64url-256+, reason:lease_lost&#124;validation_failed&#124;resume_failed&#124;operator_abort&#124;crash_recovery}</code> | <code>{operation_id:UUIDv7, materialization_id:UUIDv7, transaction_id:UUIDv7, plan_id:digest, state:rolled_back, restored_paths:sorted unique absolute-path[0..65536], removed_paths:sorted unique absolute-path[0..65536], native_discovery_absent:boolean}</code> |
| <code>resume</code> | <code>{identity:Provider Identity Record, workspace_paths:WorkspacePaths, execution_profile:standard&#124;yolo, terminal:TerminalDescriptor, lease:LeaseToken}</code> | <code>SpawnPlan</code> |
| <code>fork</code> | <code>{operation_id:UUIDv7, source_identity:Provider Identity Record, source_checkpoint:Checkpoint Record, new_session_record:Session Record, destination_workspace_paths:WorkspacePaths, execution_profile:standard&#124;yolo, terminal:TerminalDescriptor}</code> | <code>{operation_id:UUIDv7, result_kind:native_fork&#124;supported_import, planned_native_session_id:string[1..512]&#124;null, spawn_plan:SpawnPlan, requires_provider_materialization:boolean, provenance_verified:boolean}</code> |
| <code>stop</code> | <code>{identity:Provider Identity Record, terminal:TerminalDescriptor, mode:graceful&#124;force, timeout_ms:uint53[1..3600000], lease:LeaseToken}</code> | <code>{closure:ProcessClosure}</code> |
| <code>doctor</code> | <code>{platform:macos&#124;linux&#124;wsl2&#124;windows, architecture:amd64&#124;arm64, provider_executable:absolute-path&#124;null, identity:Provider Identity Record&#124;null}</code> | <code>{provider_id:provider-id, provider_version:string[1..128]&#124;null, findings:DoctorFinding[0..1024]}</code> |

For <code>launch</code>, the profile and launch plan MUST exactly equal their
Session Record values. Provider <code>fork</code> is a planning call: it MUST
NOT write a provider store, allocate an active backend conversation, or start a
process. Its operation ID is the Session Record's
<code>fork_provenance.operation_id</code>; an identical retry returns the same
plan and any changed body is <code>idempotency_mismatch</code>. The new record
MUST contain Fork Provenance matching the source/checkpoint and operation, and
a successful result requires <code>provenance_verified = true</code> and MUST
NOT describe a blank session. <code>native_fork</code> requires
<code>requires_provider_materialization = false</code> and MAY have a planned
native ID when the provider allocates it only at process start.
<code>supported_import</code> requires
<code>requires_provider_materialization = true</code>; the coordinator then
calls <code>native-store-plan phase=materialize</code> with
<code>mode=fork</code> and includes the validated provider plan in the
destination materialization transaction. In both variants, a new Provider
Identity Record is authoritative only after native discovery following the
prepared transaction; the planned ID is an expectation, not an identity
record.

<code>launch</code>, <code>resume</code>, and <code>fork</code> return plans; the
trusted terminal backend performs process creation. Plugins MUST NOT return
secret environment values. <code>native-store-plan</code> succeeds only for an
advertised portable-store tuple and MUST separate durable includes,
machine-local excludes, path-key rewrites, quiescence preconditions, and
validation steps. Its two request and result variants are closed and disjoint:
a capture request has no destination platform, destination host, destination
workspace map, or source manifest; a materialize request has no source
workspace map. Capture therefore works for the first local checkpoint without
inventing a destination peer or a source-as-destination sentinel.

The capture result's authorities are the complete provider source-root
authority for that capture. A materialize plan MUST contain at least one
Section 10.5 <code>provider_store</code> RootAuthority with
<code>prepared_for_host_id = destination_host_id</code>. Every such authority
MUST have the same provider/platform as the request, resolve to a
destination-local native-store root for the exact adapter tuple, and be
disjoint from ax data/state/cache/runtime roots, task-board staging,
workspaces, and credential/authentication roots unless an exact child path is
the provider's documented durable store. A path-key rewrite is keyed by logical
workspace ID and contains destination-derived non-secret cache-key data, never
a source absolute path. An unavailable surface returns the common failure
envelope, not a success body with a null required plan.

The following source-only first-checkpoint body and result are the normative
<code>PROVIDER-PLAN-CAPTURE-POS</code> fixture. Their absence of every
destination member is intentional:

~~~json
{
  "phase": "capture",
  "identity": {
    "schema": "urn:ax:schema:provider-identity",
    "schema_version": "1.0.0",
    "record_id": "sha256:3667dd9b0ed92b63daa77d848fa5ad77dd8ca3e5a26a47238133e2094fab8f2d",
    "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
    "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
    "provider_id": "codex",
    "provider_version": "0.147.0",
    "provider_version_range": ">=0.147.0 <0.148.0",
    "native_session_id": "11111111-2222-4333-8444-555555555555",
    "identity_kind": "session_uuid",
    "logical_workspace_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
    "backend_realm_fingerprint": null,
    "opaque_identity": {},
    "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
    "created_at": "2026-08-19T04:03:00.000Z",
    "extensions": {}
  },
  "source_platform": "macos",
  "mode": "snapshot",
  "source_workspace_paths": {
    "0198f4c8-6c30-7d44-8d5e-1234567890ab": "/Users/iv/Developer/ReluxWorks/payments-api"
  },
  "lease": {
    "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
    "lease_epoch": 1,
    "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
  }
}
~~~

~~~json
{
  "phase": "capture",
  "capture_plan": {
    "capture_id": "0198f4c8-0790-72aa-8374-3234567890ab",
    "source_authorities": [
      {
        "authority_id": "codex_sessions",
        "provider_id": "codex",
        "platform": "macos",
        "root_path": "/Users/iv/.codex/sessions",
        "root_role": "durable_store",
        "access": "capture_source"
      }
    ],
    "items": [
      {
        "source_authority_id": "codex_sessions",
        "source_relative_path": "2026/08/19/rollout-11111111-2222-4333-8444-555555555555.jsonl",
        "manifest_path": "session/rollout.jsonl",
        "kind": "file",
        "state_class": "durable_payload",
        "required": true
      }
    ],
    "excluded_targets": [],
    "store_generation": "closed:11111111-2222-4333-8444-555555555555:1",
    "snapshot_requires_closed_store": true
  },
  "include_classes": ["durable_payload"],
  "exclude_classes": ["credential","live_pid","machine_auth","socket","transient_lock"]
}
~~~

<code>PROVIDER-PLAN-CAPTURE-N1</code> adds
<code>destination_platform</code> to the capture body and MUST fail with
<code>incompatible_schema</code>. <code>PROVIDER-PLAN-CAPTURE-N2</code> changes
the item authority to an undeclared ID and MUST fail before any provider byte
is read. <code>PROVIDER-PLAN-CAPTURE-N3</code> makes the source authority equal
the credential root and MUST fail with <code>secret_policy_violation</code>.

<code>capture</code> is the only provider operation that may emit provider
payload bytes. It requires <code>proof.safe = true</code>, equal proof/plan store
generation, and the current lease. Its manifest MUST have
<code>kind = provider</code>, the session as subject, and exactly the returned
descriptor/blob closure. The host MUST reject an extra sink file, missing
required item, descriptor mismatch, excluded class/path, generation change, or
secret-policy violation and MUST discard the isolated sink without importing
it. The plugin MUST NOT write a live ax store, live SQLite index, credential
root, or destination native store during capture.

Provider materialization is a recoverable two-decision transaction.
<code>materialize</code> applies the exact plan while retaining every replaced
destination byte under the authorized transaction layout and returns
<code>state = prepared</code>; it MUST NOT delete its backup. While prepared,
the host validates exact native discovery and either keeps the replica dormant
or starts the winning owner. It then calls <code>materialize-commit</code> to
discard the backup, or <code>materialize-rollback</code> to restore it. Commit
requires <code>backup_removed = true</code>; rollback requires the native
identity introduced by the transaction to be absent afterward unless it was a
pre-existing backend identity. A rollback token is machine-local recovery
authority, MUST be at least 256 random bits, MUST be stored only in the
owner-only Materialization Journal and prepared Provider Transaction Document,
and MUST NOT be replicated or logged.

The provider plugin MUST execute only plan operations whose authority has
<code>kind = provider_store</code> and whose <code>provider_id</code> equals the
plugin manifest ID. The ax host executes workspace and task-board operations;
it MUST reject a plugin response that reports any created or merged path
outside the selected provider-store authorities. The plugin resolves each
reported absolute path from that authority's root plus the operation's
relative target, rechecks the predecessor immediately before mutation, and
uses no unlisted native-store root. A composite plan is therefore one host
transaction containing disjoint authority-specific executors, not a grant for
the provider plugin to mutate the workspace.

The three mutation operations use the same parent <code>operation_id</code>,
<code>materialization_id</code>, <code>transaction_id</code>, and byte-identical
transaction authority. The sole mutation idempotency key remains
<code>(operation, operation_id)</code>; the materialization and transaction IDs
are immutable non-key inputs. Each mutation tag therefore has a distinct key
while all phases locate the same authority. A retry of one mutation name MUST
use byte-identical canonical arguments. <code>materialize-status</code> omits
<code>operation_id</code>; it is the required evolving lost-response recovery
read and uses the envelope <code>request_id</code> only for correlation. A status
read MUST reconcile and return the current durable state, so a read that once
returned <code>prepared</code> may later return <code>committed</code> or
<code>rolled_back</code>. An unknown transaction MUST return state
<code>unknown</code>; the host MUST NOT infer success. A prepared transaction
survives plugin/host restart until explicit commit or rollback. A plugin that
cannot provide this prepare/status/commit/rollback behavior MUST advertise
<code>portable_store</code> disabled.

Normative prepared result body:

~~~json
{
  "operation_id": "0198f4c8-e4b0-75cc-9576-1234567890ab",
  "materialization_id": "0198f4c8-c290-73aa-9374-1234567890ab",
  "transaction_id": "0198f4c8-f5c0-76dd-9677-1234567890ab",
  "plan_id": "sha256:64644a5ad573d36c0c13f44f56ef25ab93cff33001ff2a3371b082603910f2dd",
  "state": "prepared",
  "created_paths": ["/srv/provider/sessions/11111111-2222-4333-8444-555555555555"],
  "merged_paths": [],
  "validations": [
    {"code":"native_discovery","status":"passed","detail":"exact session identity resolved"}
  ],
  "rollback_token": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5QUI",
  "native_discovery": {
    "native_session_id": "11111111-2222-4333-8444-555555555555",
    "discovered": true,
    "discovery_root": "/srv/provider/sessions",
    "backend_resolved": false
  }
}
~~~

The normative transaction cases are:

| Fixture | Calls | Required terminal state |
| --- | --- | --- |
| <code>PTX-POS-DORMANT</code> | materialize → status prepared → commit with <code>dormant_validated</code> | committed; replica remains unable to run |
| <code>PTX-POS-OWNER</code> | materialize → exact discovery → owner resume → commit with <code>owner_resumed</code> | committed; backup removed only after resume evidence |
| <code>PTX-ROLLBACK</code> | materialize → validation failure → rollback | predecessor bytes restored; introduced identity absent |
| <code>PTX-LOST-PREPARE</code> | materialize response lost → status prepared | same token/plan returned; no second destination mutation |
| <code>PTX-LOST-COMMIT</code> | commit response lost → status committed | caller records commit; MUST NOT roll back |
| <code>PTX-STATUS-EVOLVES</code> | status returns prepared → commit succeeds → the same status body is read under a fresh envelope request ID | second read returns committed; no byte-identical replay rule applies to either observation |
| <code>PTX-UNKNOWN</code> | status unknown after an ambiguous call | fail closed and quarantine transaction root; MUST NOT infer prepare or commit |
| <code>PTX-CROSS-PROCESS-COMMIT</code> | process P1 prepares and exits → P2 status reads the same authority/document → P3 commits and exits → P4 status reads the terminal receipt | prepared and committed facts, token, plan, and discovery are identical across processes; backup bytes are removed only by P3 |
| <code>PTX-CROSS-PROCESS-ROLLBACK</code> | process P1 prepares and exits → P2 rolls back with the same authority/token → P3 status reads the terminal receipt | every predecessor is restored, every introduced target is absent, and no process searches outside the passed authority |

Changing a plan, object-source authority, or transaction authority on a repeated
<code>materialize</code>, changing activation/lease on a repeated commit, or
changing rollback reason/token on a repeated rollback while reusing the same
<code>(operation, operation_id)</code> key is the normative negative
<code>PTX-IDEMPOTENCY-N1</code> fixture and returns
<code>idempotency_mismatch</code>.

<code>PTX-IDEMPOTENCY-ID-N1</code> loses a prepared response and retries the
same <code>(materialize, operation_id)</code> while changing only
<code>materialization_id</code>; <code>PTX-IDEMPOTENCY-ID-N2</code> changes only
<code>transaction_id</code>; and <code>PTX-IDEMPOTENCY-ID-N3</code> changes only
one authority root. Each MUST return <code>idempotency_mismatch</code>, leave the
original transaction document/root byte-identical, and create no second root.

<code>PTX-ROLLBACK-LEASE</code>, <code>PTX-ROLLBACK-VALIDATION</code>,
<code>PTX-ROLLBACK-RESUME</code>, <code>PTX-ROLLBACK-OPERATOR</code>, and
<code>PTX-ROLLBACK-CRASH</code> repeat the rollback path with, respectively,
<code>lease_lost</code>, <code>validation_failed</code>,
<code>resume_failed</code>, <code>operator_abort</code>, and
<code>crash_recovery</code>. Each reason is persisted before restoration and
replaying the same request returns the same terminal result; changing only the
reason is <code>idempotency_mismatch</code>.

Normative <code>resume</code> request body and success body:

~~~json
{
  "protocol": "urn:ax:protocol:provider",
  "protocol_version": "2.0.0",
  "request_id": "0198f4c8-e4b0-75cc-9576-1234567890ab",
  "operation": "resume",
  "deadline": "2026-08-19T04:20:00.000Z",
  "body": {
    "identity": {
      "schema": "urn:ax:schema:provider-identity",
      "schema_version": "1.0.0",
      "record_id": "sha256:3667dd9b0ed92b63daa77d848fa5ad77dd8ca3e5a26a47238133e2094fab8f2d",
      "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
      "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
      "provider_id": "codex",
      "provider_version": "0.147.0",
      "provider_version_range": ">=0.147.0 <0.148.0",
      "native_session_id": "11111111-2222-4333-8444-555555555555",
      "identity_kind": "session_uuid",
      "logical_workspace_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
      "backend_realm_fingerprint": null,
      "opaque_identity": {},
      "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
      "created_at": "2026-08-19T04:03:00.000Z",
      "extensions": {}
    },
    "workspace_paths": {
      "0198f4c8-6c30-7d44-8d5e-1234567890ab": "/srv/relux/payments-api"
    },
    "execution_profile": "yolo",
    "terminal": {
      "backend": "tmux",
      "terminal_id": "ax-payments-api",
      "interactive": true,
      "columns": 120,
      "rows": 40
    },
    "lease": {
      "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
      "lease_epoch": 4,
      "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    }
  }
}
~~~

~~~json
{
  "protocol": "urn:ax:protocol:provider",
  "protocol_version": "2.0.0",
  "request_id": "0198f4c8-e4b0-75cc-9576-1234567890ab",
  "ok": true,
  "body": {
    "argv": [
      "codex",
      "--dangerously-bypass-approvals-and-sandbox",
      "resume",
      "11111111-2222-4333-8444-555555555555"
    ],
    "cwd": "/srv/relux/payments-api/src",
    "env_names": ["OPENAI_API_KEY"],
    "env_literals": {},
    "native_session_id": "11111111-2222-4333-8444-555555555555",
    "profile_mapping": "--dangerously-bypass-approvals-and-sandbox",
    "extensions": {}
  }
}
~~~

### 7.6 Quiescence proof

A successful <code>quiesce</code> response MUST contain:

- provider ID and exact version;
- <code>input_blocked = true</code>;
- a provider-specific terminal/idle event reference;
- <code>foreground_idle = true</code>;
- <code>background_idle = true</code> when the provider can prove it;
- open child process and open durable-database handle counts, both zero;
- the last stable provider-store digest or metadata generation; and
- <code>safe = true</code>.

If background idleness, process exit, or store closure cannot be proven,
<code>safe</code> MUST be false and graceful takeover MUST stop. A force
takeover is a separate operator action; the plugin MUST NOT silently convert the
request.

For a safe direct-provider proof, Checkpoint Safe Boundary Evidence copies
provider ID/version, input/idle booleans, and maps
<code>open_child_count</code> to <code>open_processes</code> and
<code>open_database_handle_count</code> to
<code>open_database_handles</code>; <code>evidence</code> is the accepted
adapter mechanism (<code>provider_api</code>, <code>provider_event</code>,
<code>managed_pty</code>, or <code>accepted_test</code>). RPC
<code>SafeBoundary</code> additionally copies the boundary reference and store
generation, sets <code>store_stable = true</code>, and normalizes
<code>child_process_open</code> to <code>process_open</code>. No other lossy or
provider-defined mapping is permitted.

### 7.7 Profile mapping

The v0.2.0 <code>yolo</code> mappings are:

| Provider | Required adapter mapping |
| --- | --- |
| Codex | <code>--dangerously-bypass-approvals-and-sandbox</code> (alias <code>--yolo</code> is accepted by current CLI but the long form SHOULD be persisted in diagnostics) |
| Claude | <code>--dangerously-skip-permissions</code> |
| Gemini CLI | <code>--approval-mode=yolo</code> |
| Muse | <code>--yolo</code> |
| Antigravity | <code>--dangerously-skip-permissions</code> |
| Pi 0.73.1 | No invented flag; use the provider's default full built-in tool set and report <code>profile_mapping = "default_unrestricted_tool_set"</code> |

<code>standard</code> MUST use the provider's normal approval/sandbox behavior
and MUST omit every unrestricted flag above. It MUST NOT reuse a machine-local
alias that silently expands to unrestricted mode. Provider-specific standard
options in a sanitized launch plan are applied only after an exact-version
probe accepts them.

For Pi 0.73.1, both profiles resolve to the provider's same default full tool
set because no provider permission-mode flag exists. Probe and launch output
MUST disclose that equivalence; <code>ax</code> ownership, mesh, conflict, and
confirmation controls still apply.

The adapter MUST probe the exact provider version before applying a mapping.
An absent or changed flag fails closed.

## 8. Provider and platform contracts

### 8.1 Matrix notation

Provider and platform matrices use:

- <strong>A</strong>: available from documented or accepted evidence; runtime
  probe still MUST succeed;
- <strong>C</strong>: conditional and disabled until the named acceptance gate
  succeeds for the exact version/platform tuple;
- <strong>U</strong>: unsupported in v0.2.0 and disabled; and
- <strong>?</strong>: unknown and disabled because there is no sufficient
  contract or evidence.

These labels are not aliases. In particular, unknown MUST NOT be rewritten as
unsupported, and conditional MUST NOT be advertised as available.

### 8.2 Native-store contract matrix

| Provider | Durable identity and native location | Resume/import surface | v0.2.0 materialization rule | Required exclusions and limits |
| --- | --- | --- | --- | --- |
| Codex | Session UUID/name; known root <code>~/.codex/sessions</code>. Source absolute cwd is metadata. | <code>codex resume SESSION_ID</code>; current CLI also has <code>codex fork SESSION_ID</code>. | Adapter MUST stage only the closed session objects it has identified, compute the destination cwd mapping, validate discovery by explicit ID, and merge without replacing unrelated sessions. <code>portable_store</code> remains C until cross-host fixtures pass. | Authentication files, config secrets, MCP tokens, logs not required by the session, live processes, locks, SQLite/WAL/SHM, and runtime sockets. |
| Claude | Session UUID; known root <code>~/.claude/projects</code> with a provider-computed project key. | <code>claude --resume SESSION_ID</code>, <code>--continue</code>, and <code>--fork-session</code> when resuming. | Adapter MUST derive the destination project key from the logical workspace mapping, stage the closed session plus documented companion data, and validate explicit UUID resume. It MUST NOT copy the source project-directory key verbatim as identity. <code>portable_store</code> remains C. | OAuth/API credentials, settings secrets, MCP auth, live PTY state, PID/lock/socket files, caches, and unproven companion databases. |
| Gemini CLI | Session UUID scoped by logical project; documented root <code>~/.gemini/tmp/&lt;project-hash&gt;/chats</code>. | <code>gemini --resume UUID</code>, picker/index/latest, and <code>--session-file FILE</code>. | Adapter MUST compute the destination project hash, prefer the documented session-file import when compatible, stage atomically, then validate <code>--list-sessions</code> and explicit UUID resume. <code>portable_store</code> is C until schema/version and cross-platform fixtures pass. | Google credentials, API keys, settings secrets, trust state, runtime locks, cache-only files, and source path keys. |
| Muse | Session UUID; <code>$XDG_DATA_HOME/muse/sessions/YYYY/MM/DD/UUID</code>, defaulting below <code>~/.local/share</code>. | <code>muse resume UUID</code>, <code>--last</code>, picker, and <code>muse exec --session-id UUID</code>. Export exists; native import does not. | On probed macOS 0.1.0, a guarded adapter MAY stage the complete closed durable directory, omit transient files, validate with offline export, and resume explicitly. It MUST advertise <code>portable_store = false</code> because cron-aware, current-version, cross-host fidelity is not proven. | <code>~/.config/muse/auth.json</code>, keys, login state, <code>.session.lock</code>, sockets/tokens, live WAL/SHM/locks, updater/plugin caches. <code>cron.db</code> is durable but not safely portable; a session with active or non-empty scheduled work MUST fail materialization. |
| Antigravity CLI | Conversation UUID plus a destination-authenticated backend/account realm. <code>last_conversations.json</code> maps absolute workspace paths only as local selectors. | <code>agy --conversation UUID</code>, <code>agy -c</code>, and TUI <code>/resume</code>. Desktop-to-CLI picker import is not arbitrary file import. | Materialize the workspace, invoke explicit UUID resume, and allow the provider to rebuild derived cache. A version-aware cache merge MAY map the destination path to UUID. It MUST NOT claim that cache, brain transcript, or SQLite copying recreates a backend-missing conversation. <code>portable_store = false</code>. | OS keyring/account profiles, OAuth/API/MCP secrets, updater locks, live DB/WAL/SHM, sockets, PIDs. Backend resolution is required and a missing UUID MUST fail rather than create a blank replacement. |
| Pi | Session UUID/file; <code>~/.pi/agent/sessions</code> or the configured <code>PI_CODING_AGENT_SESSION_DIR</code>/<code>--session-dir</code>. | <code>--session PATH_OR_ID</code>, <code>--continue</code>, <code>--resume</code>, <code>--fork</code>. | Adapter MUST snapshot a closed JSONL session and required non-secret companion data, map the destination cwd/session directory, validate the session ID, and resume explicitly. <code>portable_store</code> remains C until versioned cross-host fixtures pass. | <code>auth.json</code>, provider keys/tokens, extension secrets, live process state, locks, sockets, and caches. Pi 0.73.1 has no YOLO flag. |
| Qwen through task-board | The task-board bundle and manager-owned provider identity; there is no v0.2.0 direct <code>ax-provider-qwen</code> claim. | Official task-board open/adopt only. | U for direct native materialization. A task-board prompt-mode bundle follows Section 9 and remains opaque. | All private manager/provider state except bytes included by the official bundle exporter. |
| Future plugin | Declared by plugin and exact probe. | Declared by plugin. | Every cell starts ?/disabled. Promotion requires Section 19 acceptance evidence. | Common exclusions plus plugin-specific exclusions. |

Muse and Antigravity rows above are normative uses of the accepted
<code>TASK-260819-1ecd6x</code> evidence. The controlled Muse placement probe
does not create a supported import contract. Antigravity backend resolution is
native resume but not portable storage.

### 8.3 Capability matrix

| Provider | <code>native_resume</code> | <code>portable_store</code> | <code>managed_pty</code> | <code>appserver</code> | <code>task_board_primary</code> | <code>prompt_spawn</code> | <code>native_goal_binding</code> |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | A | C | C | A through task-board | A through task-board | A through task-board | A through task-board |
| Claude | A | C | C | U for direct adapter | A through task-board | A through task-board | A through task-board |
| Gemini CLI | A | C | C | ? | U | A through task-board | U |
| Muse | C by platform/version | U | C | ? | U | A through task-board | U |
| Antigravity CLI | C: backend realm required | U | C | ? | U | ? | U |
| Pi | A | C | C | U; Pi RPC is not claimed as this capability | ? | ? | U |
| Qwen through task-board | U direct | U direct | U direct | U direct | U | A through task-board | U |
| Future plugin | ? | ? | ? | ? | ? | ? | ? |

For Codex and Claude, task-board owns app-server/thread or PTY mechanics,
reattach, resume, and goal binding. The direct Claude adapter therefore does
not advertise <code>appserver</code>. The task-board capability plane and
direct-provider capability plane MUST NOT be conflated.

### 8.4 Provider/platform matrix

Each cell is <code>native resume / cross-host materialization / managed
terminal</code>. Task-board-only behavior is stated separately.

| Provider/platform | Status | Normative limit |
| --- | --- | --- |
| Codex / macOS | A / C / C | Resume and unrestricted flag are documented; portable store and PTY flush require adapter fixtures. |
| Codex / Linux | A / C / C | Same; exact distribution and filesystem fixture required. |
| Codex / WSL2 | A / C / C | Treat as Linux with a Linux store. Repositories SHOULD live below the WSL home, not a Windows-mounted path. |
| Codex / native Windows | A / C / C | Native CLI is documented. ConPTY, Windows store discovery, file locking, and sandbox mode MUST pass. Windows 11 is the release baseline; Windows 10 is best effort and requires ConPTY. |
| Claude / macOS | A / C / C | Installed 2.1.229 help confirms UUID resume and unrestricted flag; store transfer remains gated. |
| Claude / Linux | A / C / C | Provider family documented; distro/PTTY fixture required. |
| Claude / WSL2 | A / C / C | WSL is provider-documented; use Linux store and path rules. |
| Claude / native Windows | C / C / C | Windows 10+ with WSL or Git for Windows is documented, but native PowerShell/ConPTY and native store materialization require acceptance. |
| Gemini / macOS | A / C / C | Official session root, UUID resume, and session-file surface documented. |
| Gemini / Linux | A / C / C | Ubuntu 20.04+ documented; other distributions conditional. |
| Gemini / WSL2 | C / C / C | Linux inference; mounted-filesystem, auth, signal, and path-hash tests required. |
| Gemini / native Windows | A / C / C | Windows 11 24H2+ documented; PowerShell/ConPTY and path-hash tests required. |
| Muse / macOS arm64 | A for probed 0.1.0 / U / C | Narrow resume probe accepted; current 0.2.1 and full idle/cron fidelity remain unverified. |
| Muse / macOS amd64 | C / U / C | Artifact/contract exists; not executed. |
| Muse / Linux amd64 or arm64 | C / U / C | Official launcher artifacts; not executed. |
| Muse / WSL2 | C / U / ? | Linux-path inference only. |
| Muse / native Windows | ? / U / ? | 0.2.1 artifacts exist, but official launcher and persistence contract do not establish support. |
| Antigravity / macOS amd64 or arm64 | C / U / C | Resume works only when the authenticated backend realm resolves the UUID; <code>Stop.fullyIdle</code> is documented. |
| Antigravity / Linux amd64 or arm64 | C / U / C | Native family documented; keyring/DBus and PTY tests required. |
| Antigravity / WSL2 | C / U / ? | Linux inference only; auth, path, signal, and locking tests required. |
| Antigravity / native Windows amd64 or arm64 | C / U / C | Native family documented; ConPTY, data-root expansion, and file-lock tests required. |
| Pi / macOS | A / C / C | Installed 0.73.1 help verifies session surfaces and default full tool set. |
| Pi / Linux | C / C / C | Cross-platform Node/package behavior is plausible but exact 0.73.1 acceptance is required. |
| Pi / WSL2 | C / C / C | Treat as Linux only after path/signal/auth tests. |
| Pi / native Windows | C / C / C | Provider platform notes exist; exact 0.73.1 store, shell, and ConPTY behavior is unverified. |
| Qwen task-board prompt mode / any target platform | U direct; A only where task-board probe reports <code>prompt_spawn</code> | No direct native-store or primary-owner claim. |
| Future plugin / any | ? / ? / ? | Disabled until a tuple-specific probe and acceptance record exist. |

The release MUST NOT collapse WSL2 and native Windows into one row. An adapter
accepted in WSL2 does not establish native Windows support.

## 9. Task-board integration

### 9.1 Ownership boundary

Task-board is both a provider-launch abstraction and a distinct persistence
boundary. <code>tb-sessiond</code> owns private Codex app-server/thread state,
Claude PTY state, reattach mechanics, provider resume, and goal bindings.
<code>ax</code> MUST NOT inspect manager databases, private session records,
provider process files, or authentication state.

The only portable interface is the official
<code>urn:ax:protocol:task-board-bridge</code> version <code>1.0.0</code>
contract. Its initial public creation surface is <code>launch</code>; its bundle
boundary uses <code>export</code>, <code>import</code>, <code>open</code>, and
<code>adopt</code>; its public lifecycle controls are <code>status</code>,
<code>stop</code>, and <code>resume</code>. Until
task-board advertises this exact bridge version and the required operations,
task-board takeover MUST report
<code>task_board_bridge_unavailable</code>. Existing whole-board archive
commands are not a substitute.

### 9.2 Official bridge command surface

The required CLI facade is:

~~~shell
task-board session launch --operation-id OPERATION_ID --request REQUEST_FILE --json
task-board session status --session SESSION_REF --json
task-board session export --operation-id OPERATION_ID --session SESSION_REF --bundle FILE --format tb-session-bundle-v1 --mode snapshot --json
task-board session export --operation-id OPERATION_ID --session SESSION_REF --bundle FILE --format tb-session-bundle-v1 --mode handoff --json
task-board session import --operation-id OPERATION_ID --bundle FILE --staging-root DIR --json
task-board session open --operation-id OPERATION_ID --import-token TOKEN --mode dormant-replica --json
task-board session open --operation-id OPERATION_ID --import-token TOKEN --mode fork --new-session SESSION_ID --json
task-board session adopt --operation-id OPERATION_ID --open-token TOKEN --ax-session SESSION_ID --lease-epoch EPOCH --lease-id LEASE_ID --json
task-board session stop --operation-id OPERATION_ID --session SESSION_REF --mode graceful --control-token TOKEN --json
task-board session stop --operation-id OPERATION_ID --session SESSION_REF --mode force --json
task-board session resume --operation-id OPERATION_ID --session SESSION_REF --ax-session SESSION_ID --lease-epoch EPOCH --lease-id LEASE_ID --profile standard|yolo --json
~~~

Every command MUST print exactly one schema-versioned JSON result to stdout and
diagnostics to stderr. The bridge MAY use an internal local API, but the
semantics and bundle bytes MUST be identical.

<code>REQUEST_FILE</code> is an owner-only, machine-local JSON file containing
exactly the logical <code>launch</code> request body below; the duplicated
<code>operation_id</code> MUST equal the flag. It contains no credential values
and MUST be removed after a terminal bridge result. Every mutating facade
requires the caller-supplied <code>--operation-id</code>; task-board MUST NOT
replace it with an internally generated value. This makes the exact invocation
repeatable after a lost response.

The result envelope uses the bridge protocol version independently of the
bundle schema:

~~~json
{
  "protocol": "urn:ax:protocol:task-board-bridge",
  "protocol_version": "1.0.0",
  "operation": "export",
  "ok": true,
  "body": {
    "operation_id": "0198f4c8-c180-72aa-8374-1234567890ab",
    "mode": "snapshot",
    "bundle_id": "sha256:0af7b44e7063375a0f06e546fd820438c72607f191c14be78d35c8ffa109844f",
    "bundle_path": "/var/folders/example/tb-session-bundle.tar",
    "size": 4096,
    "safe_boundary": {
      "provider_id": "codex",
      "provider_version": "0.147.0",
      "boundary_ref": "tb-boundary-0198f4c8",
      "input_blocked": true,
      "foreground_idle": true,
      "background_idle": true,
      "open_processes": 0,
      "open_database_handles": 0,
      "store_generation": "tb-store:42",
      "safe": true,
      "blockers": []
    },
    "input_released": true,
    "source_control_token": null,
    "expires_at": null
  }
}
~~~

The success envelope contains exactly <code>protocol</code>,
<code>protocol_version</code>, <code>operation</code>, <code>ok = true</code>, and
<code>body</code>. On failure, it contains exactly the first four members with
<code>ok = false</code> plus <code>error</code> as a Structured Error and omits
<code>body</code>. Tokens returned by import, open, and handoff export MUST be unguessable,
machine-local, single-use base64url values of at least 256 bits and MUST expire
after 60 minutes. Tokens MUST NOT be replicated or written into immutable
bundles.

Task-board bridge protocol <code>1.x</code> statically binds that failure object
to Structured Error <code>1.0.0</code>; the facade has no separate error-schema
negotiation. A bridge executable that does not support protocol major 1 MUST
not emit a differently shaped failure as if it were a v1 result. Section 15.1
defines the caller's fail-closed mapping for incompatible or invalid output.

The operations are:

1. <strong>launch</strong>: create and launch the requested manager-owned
   provider through the public abstraction, bind it to the already-persisted
   epoch-1 ax lease, and return the public manager-session reference. It MUST
   record the caller operation before process creation, apply the persisted
   profile, and never return success for a blank substitute session.
2. <strong>status</strong>: return the public manager-session reference,
   provider ID, <code>running|idle|quiesced|stopped|failed</code> state, safe
   boundary evidence, and bridge capabilities without private state.
3. <strong>export</strong>: quiesce through manager-owned mechanics and produce
   an opaque, closed, integrity-checked bundle. It MUST NOT expose private
   records to <code>ax</code>. <code>snapshot</code> mode MUST release input
   before returning. <code>handoff</code> mode MUST leave input blocked and
   return a source-control token bound to the session and current fencing token.
4. <strong>import</strong>: validate and stage the bundle on the destination.
   It MUST NOT start a provider or claim ownership.
5. <strong>open</strong>: in <code>dormant-replica</code> mode, install the
   staged manager state without changing its provider identity; in
   <code>fork</code> mode, create a new manager/provider identity and
   independent goal-binding state for <code>--new-session</code>. Both modes
   return a single-use open token and MUST NOT accept agent input.
6. <strong>adopt</strong>: atomically bind that dormant state to the named
   <code>ax</code> session and current winning lease. Only the destination
   owner MAY adopt. A token MUST be consumed once.
7. <strong>stop</strong>: in graceful mode, consume the handoff source-control
   token, request the manager's normal stop path, and return process/store-
   closure evidence. If normal exit changed durable manager/provider state,
   the response MUST also produce a replacement closed bundle and its digest
   for the closure-only checkpoint. Force mode is tokenless, is permitted only
   through the separately confirmed <code>ax stop --force</code> path, and MUST
   mark the result unclean.
8. <strong>resume</strong>: validate the named winning <code>ax</code> lease and
   persisted profile, then either release a still-live quiesced manager or
   resume a stopped adopted/local manager session. It MUST return the public
   manager-session reference and resulting process/state evidence.

For bridge protocol 1.0.0, each success <code>body</code> is closed and selected
by <code>operation</code>. CLI arguments shown above are the request contract;
every mutation command accepts the caller's required UUIDv7
<code>operation_id</code> and MUST reuse its durable result on an idempotent
retry.
The CLI spelling <code>dormant-replica</code> maps exactly to the logical JSON
enum <code>dormant_replica</code>; no other alias is accepted.

| Operation | Exact logical request body | Exact success body |
| --- | --- | --- |
| <code>launch</code> | <code>{operation_id:UUIDv7, ax_session_id:UUIDv7, lease_epoch:uint53&gt;0, lease_id:UUIDv4, provider_id:provider-id, launch_mode:primary_owner&#124;tracked_prompt, task_element_id:string[1..128], board:Board Identity, board_goal:Board Goal&#124;null, native_goal_binding:bound&#124;prompt&#124;none, profile:standard&#124;yolo, launch_plan:BridgeLaunchPlan, workspace_paths:map(UUIDv7,absolute-path)[1..256]}</code> | <code>{operation_id:UUIDv7, manager_session_ref:string[1..512], provider_id:provider-id, provider_version:string[1..128], native_session_ref:string[1..512]&#124;null, launch_mode:primary_owner&#124;tracked_prompt, state:running&#124;idle, input_enabled:boolean, ax_binding:BridgeBinding, capabilities:sorted unique launch&#124;status&#124;export&#124;import&#124;open&#124;adopt&#124;stop&#124;resume[8..8], native_goal_binding:bound&#124;prompt&#124;none}</code> |
| <code>status</code> | <code>{manager_session_ref:string[1..512]}</code> | <code>{manager_session_ref:string[1..512], provider_id:provider-id, provider_version:string[1..128], state:running&#124;idle&#124;quiesced&#124;stopped&#124;failed&#124;dormant, safe_boundary:BridgeSafeBoundary, capabilities:sorted unique launch&#124;status&#124;export&#124;import&#124;open&#124;adopt&#124;stop&#124;resume[1..8], ax_binding:BridgeBinding&#124;null}</code> |
| <code>export</code> | <code>{operation_id:UUIDv7,manager_session_ref:string[1..512],bundle_path:absolute-path,format:tb-session-bundle-v1,mode:snapshot&#124;handoff}</code> | <code>{operation_id:UUIDv7, mode:snapshot&#124;handoff, bundle_id:digest, bundle_path:absolute-path, size:uint53, safe_boundary:BridgeSafeBoundary, input_released:boolean, source_control_token:base64url-256+&#124;null, expires_at:timestamp&#124;null}</code> |
| <code>import</code> | <code>{operation_id:UUIDv7,bundle_path:absolute-path,staging_root:absolute-path}</code> | <code>{operation_id:UUIDv7, bundle_id:digest, import_token:base64url-256+, staged_manager_ref:string[1..512], validated:boolean, expires_at:timestamp}</code> |
| <code>open</code> | <code>{operation_id:UUIDv7,import_token:base64url-256+,mode:dormant_replica&#124;fork,new_session_id:UUIDv7&#124;null}</code> | <code>{operation_id:UUIDv7, mode:dormant_replica&#124;fork, bundle_id:digest, dormant_manager_ref:string[1..512], open_token:base64url-256+, new_provider_identity:boolean, expires_at:timestamp}</code> |
| <code>adopt</code> | <code>{operation_id:UUIDv7,open_token:base64url-256+,ax_session_id:UUIDv7,lease_epoch:uint53&gt;0,lease_id:UUIDv4}</code> | <code>{operation_id:UUIDv7, manager_session_ref:string[1..512], ax_binding:BridgeBinding, adopted:boolean, state:quiesced&#124;stopped}</code> |
| <code>stop</code> | <code>{operation_id:UUIDv7,manager_session_ref:string[1..512],source_control_token:base64url-256+&#124;null,mode:graceful&#124;force}</code> | <code>{operation_id:UUIDv7, manager_session_ref:string[1..512], process_closed:boolean, store_closed:boolean, exit_code:int32&#124;null, safe_boundary:BridgeSafeBoundary, replacement_bundle_id:digest&#124;null, replacement_bundle_path:absolute-path&#124;null, state:stopped&#124;failed}</code> |
| <code>resume</code> | <code>{operation_id:UUIDv7,manager_session_ref:string[1..512],ax_session_id:UUIDv7,lease_epoch:uint53&gt;0,lease_id:UUIDv4,profile:standard&#124;yolo}</code> | <code>{operation_id:UUIDv7, manager_session_ref:string[1..512], ax_binding:BridgeBinding, native_session_ref:string[1..512], process_started:boolean, state:running&#124;idle}</code> |

Normative tracked-prompt launch request body:

~~~json
{
  "operation_id": "0198f4c8-0180-72aa-8374-2234567890ab",
  "ax_session_id": "0198f4c8-9f60-7077-8071-1234567890ab",
  "lease_epoch": 1,
  "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "provider_id": "qwen",
  "launch_mode": "tracked_prompt",
  "task_element_id": "TASK-260819-example",
  "board": {
    "kind": "local",
    "logical_id": "agent-session-manager-spec",
    "remote_url": null,
    "extensions": {}
  },
  "board_goal": null,
  "native_goal_binding": "prompt",
  "profile": "standard",
  "launch_plan": {
    "argv": ["task-board", "qwen", "TASK-260819-example"],
    "cwd_workspace_id": "0198f4c8-b080-7299-8273-1234567890ab",
    "cwd_relative": ".",
    "env_names": [],
    "env_literals": {},
    "contains_secrets": false,
    "extensions": {}
  },
  "workspace_paths": {
    "0198f4c8-b080-7299-8273-1234567890ab": "/srv/relux/agent-session-manager-spec"
  }
}
~~~

Normative success body for that request:

~~~json
{
  "operation_id": "0198f4c8-0180-72aa-8374-2234567890ab",
  "manager_session_ref": "tb-session-260819-example",
  "provider_id": "qwen",
  "provider_version": "task-board-qwen-prompt-v1",
  "native_session_ref": null,
  "launch_mode": "tracked_prompt",
  "state": "running",
  "input_enabled": true,
  "ax_binding": {
    "ax_session_id": "0198f4c8-9f60-7077-8071-1234567890ab",
    "lease_epoch": 1,
    "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
  },
  "capabilities": [
    "adopt",
    "export",
    "import",
    "launch",
    "open",
    "resume",
    "status",
    "stop"
  ],
  "native_goal_binding": "prompt"
}
~~~

<code>BridgeBinding</code> is exactly
<code>{ax_session_id:UUIDv7, lease_epoch:uint53&gt;0, lease_id:UUIDv4}</code>.
For <code>status</code>, the request member retains the historical name
<code>manager_session_ref</code> but accepts exactly one public reference
previously returned as <code>manager_session_ref</code> by launch/adopt or as
<code>dormant_manager_ref</code> by open. The success repeats that input
byte-for-byte. A staged reference is not status-addressable. Thus an adopt
response lost after token consumption is recoverable through the dormant
reference without inspecting manager-private state.
<code>BridgeLaunchPlan</code> is exactly the Section 5.1 Launch Plan shape,
including its closed <code>extensions</code> map and
<code>contains_secrets = false</code>. The launch workspace-path map must contain
the plan's cwd workspace and every workspace needed by the task-board manager;
its absolute values are machine-local inputs and are never persisted as logical
identity.

<code>BridgeSafeBoundary</code> is a closed object containing exactly
<code>provider_id:provider-id</code>,
<code>provider_version:string[1..128]</code>,
<code>boundary_ref:string[1..1024]|null</code>,
<code>input_blocked:boolean</code>, <code>foreground_idle:boolean</code>,
<code>background_idle:boolean</code>, <code>open_processes:uint53</code>,
<code>open_database_handles:uint53</code>,
<code>store_generation:string[1..512]|null</code>,
<code>safe:boolean</code>, and <code>blockers:sorted unique
background_active|database_handle_open|input_not_blocked|process_open|provider_busy|store_unstable[0..6]</code>.
A safe boundary requires a non-null boundary reference and store generation,
input blocked, both idle booleans true, both counters zero, and an empty blocker
set. Every other combination requires <code>safe = false</code> and every known
cause in <code>blockers</code>. Counts cover all manager-owned provider,
subagent, scheduled/background, and database handles whose continued activity
could change the bundle; the bridge supervisor itself is not counted after it
has made the store inert.

The mapping is total and lossless for checkpoint authority facts:

| Bridge member | Checkpoint Safe Boundary Evidence | RPC <code>SafeBoundary</code> |
| --- | --- | --- |
| <code>provider_id</code>, <code>provider_version</code> | Copy exactly | Copy exactly |
| Bridge contract identity | Set <code>evidence = task_board_bridge</code> | Set <code>evidence = task_board_bridge</code> |
| <code>boundary_ref</code>, <code>store_generation</code> | Validate non-null before publication, then omit because the Checkpoint schema does not persist volatile bridge handles | Copy exactly, including null in an unsafe diagnostic proof |
| <code>input_blocked</code>, foreground/background idle, process/database counts | Copy exactly | Copy exactly |
| <code>safe</code> and <code>blockers</code> | Publication permitted only when safe; blockers are validation diagnostics | Copy exactly; set <code>store_stable = (store_generation != null and store_unstable is absent from blockers)</code> |

The bridge provider ID MUST equal the Session Record provider, and the exact
version returned by launch/status/export MUST agree for one process generation.
A mismatch is <code>integrity_failure</code>. <code>ax</code> MUST NOT synthesize
any missing member from process inspection or private manager data.

For bridge launch, <code>primary_owner</code> requires a non-null Board Goal and
<code>native_goal_binding = bound</code>. <code>tracked_prompt</code> permits a
null goal and requires <code>prompt</code> or <code>none</code>. Success requires
<code>input_enabled = true</code>, an exact binding to the request lease, equal
provider/mode values, and a non-blank manager session. A lost launch response
MUST be recovered by repeating the same launch command and operation ID; a
successful retry returns the recorded manager reference and MUST NOT start a
second provider process.

Bridge lifecycle state is not a second SessionState registry. It maps into the
Section 5.7 state engine using the active ax transition: bridge
<code>running</code>, <code>idle</code>, <code>stopped</code>, and
<code>failed</code> map to the equal SessionState; <code>quiesced</code> maps to
<code>quiescing</code> before boundary validation and
<code>checkpointing</code> during export; and <code>dormant</code> maps to
<code>materializing</code> until adoption or <code>parked</code> for a validated
replica. No bridge spelling may appear directly in RPC
<code>session.status</code> or a CLI Session Summary.

For snapshot export, input MUST be released and token/expiry MUST be null. For
handoff export, input MUST remain blocked and token/expiry MUST be non-null.
Both export modes require <code>safe_boundary.safe = true</code>; the proof
describes the instant after serialization and before snapshot mode releases
input. A graceful stop with a replacement closure bundle likewise requires a
safe boundary; a force-stop result MUST report <code>safe = false</code> and
MUST NOT authorize a checkpoint. An import success requires
<code>validated = true</code>. A dormant-replica
open requires null <code>new_session_id</code> and
<code>new_provider_identity = false</code>; a fork open requires a non-null new
ID and true. Graceful stop requires a non-null source-control token; force stop
requires null and an independently confirmed <code>ax</code> force path. An
adopt success requires <code>adopted = true</code>. Replacement bundle
ID/path are either both null or both non-null. Unknown members fail the bridge
operation.

The normative unsafe status fixture <code>TB-BOUNDARY-UNSAFE</code> is:

~~~json
{
  "provider_id": "codex",
  "provider_version": "0.147.0",
  "boundary_ref": "tb-boundary-busy",
  "input_blocked": true,
  "foreground_idle": true,
  "background_idle": false,
  "open_processes": 1,
  "open_database_handles": 0,
  "store_generation": "tb-store:41",
  "safe": false,
  "blockers": ["background_active","process_open"]
}
~~~

It MUST NOT produce a Checkpoint or a successful export result.
<code>TB-BOUNDARY-N1</code> changes only <code>safe</code> to true and is
<code>incompatible_schema</code>. In
<code>TB-EXPORT-LOST-RESPONSE</code>, the manager durably records the bundle,
proof, mode, and token/result before responding; after the response is lost,
the identical <code>(export, operation_id)</code> retry returns those exact
values and MUST NOT create a second bundle or unblock a handoff. A changed mode
or bundle path with that ID returns <code>idempotency_mismatch</code>.

Import consumes no authority. <code>open</code> consumes its import token;
<code>adopt</code> consumes its open token atomically with binding. The bridge
idempotency key is <code>(operation, operation_id)</code>. Repeating that key
with canonical-identical arguments MUST return the recorded result even after
its token was consumed; a changed argument set for the same key MUST return
<code>idempotency_mismatch</code>. If an adopt response is lost,
<code>status</code> is the only recovery read: an exact <code>ax_binding</code>
proves adoption, null proves dormancy, and a different binding is
<code>lease_conflict</code>. Expired unadopted dormant state MAY be garbage
collected after its immutable bundle remains available; it MUST never start a
provider.

Replica sync normally ends after import/open. Graceful takeover performs adopt
only after the destination lease wins. A failed adopt MUST leave the old owner
unchanged in a graceful flow and the destination dormant. A pre-stop aborted
handoff uses <code>resume</code> under the still-winning source lease to release
input; no private manager mutation is permitted.

### 9.3 Task-board Bundle

The portable archive has schema <code>urn:ax:schema:task-board-bundle</code>
version <code>1.0.0</code>. Its public <code>bundle.json</code> contains:

~~~json
{
  "schema": "urn:ax:schema:task-board-bundle",
  "schema_version": "1.0.0",
  "bundle_id": "sha256:0af7b44e7063375a0f06e546fd820438c72607f191c14be78d35c8ffa109844f",
  "manager_contract": "tb-session-bundle-v1",
  "bridge_protocol_version": "1.0.0",
  "logical_session_id": "0198f4c8-7a10-7b22-8b3c-2234567890ab",
  "provider_id": "codex",
  "execution_profile": "yolo",
  "profile_source_event_id": null,
  "task_element_id": "TASK-260819-example",
  "launch_mode": "primary_owner",
  "provider_snapshot": {
    "media_type": "application/vnd.task-board.session+opaque",
    "blob_id": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  },
  "manager_record": {
    "blob_id": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
  },
  "sanitized_launch_plan": {
    "argv": ["task-board", "codex", "TASK-260819-example"],
    "cwd_workspace_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
    "cwd_relative": ".",
    "env_names": ["OPENAI_API_KEY"],
    "env_literals": {
      "AX_TASK_MODE": "primary"
    },
    "contains_secrets": false,
    "extensions": {
      "works.relux.ax.launch-hint": {
        "source": "task-board"
      }
    }
  },
  "source_owner_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "board_goal": {
    "schema": "board-goal-v2",
    "goal_id": "PRIMARY-GOAL-260819-example",
    "revision": 3,
    "extensions": {
      "works.relux.ax.goal-label": "spec-release"
    }
  },
  "native_goal_binding": {
    "state": "bound",
    "opaque_blob_id": "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  },
  "board_identity": {
    "kind": "local",
    "logical_id": "board-0198f4c8",
    "remote_url": null,
    "extensions": {
      "works.relux.ax.board-scope": "specification"
    }
  },
  "workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "created_at": "2026-08-19T04:10:00.000Z"
}
~~~

The bundle object is closed and every displayed top-level member is required.
Its nested objects are also closed:

- <code>provider_snapshot</code> contains exactly
  <code>media_type = application/vnd.task-board.session+opaque</code> and
  <code>blob_id:digest</code>;
- <code>manager_record</code> contains exactly <code>blob_id:digest</code>;
- <code>sanitized_launch_plan</code> is the complete closed Section 5.1 Launch
  Plan, including cwd, non-secret literal environment, and extensions; its
  <code>contains_secrets</code> member is false;
- <code>board_goal</code> is null or is the complete closed Section 5.1 Board
  Goal, including <code>extensions</code>;
- <code>native_goal_binding</code> contains exactly
  <code>state:bound|prompt|none</code> and
  <code>opaque_blob_id:digest|null</code>, with non-null required only for
  <code>bound</code>; and
- <code>board_identity</code> is the complete closed Section 5.1 Board Identity,
  including <code>extensions</code> and its local/remote URL rule.

<code>manager_contract</code> is the literal
<code>tb-session-bundle-v1</code> and
<code>bridge_protocol_version</code> is exactly <code>1.0.0</code>. Logical
session and workspace group IDs are UUIDv7; <code>provider_id</code> uses the
provider-ID grammar; <code>execution_profile</code> is
<code>standard|yolo</code>; <code>profile_source_event_id</code> is a digest or
null; <code>task_element_id</code> has the Section 5.1
1–128 printable non-control UTF-8 constraint; source owner is UUIDv7;
<code>launch_mode</code> is <code>primary_owner|tracked_prompt</code>; and
<code>created_at</code> is diagnostic UTC time.

The bundle MUST carry the durable manager record, provider snapshot, sanitized
launch plan with no secret values, source owner identity, native goal-binding
state, and logical board/workspace identities. A
<code>launch_mode = primary_owner</code> requires a non-null exact
<code>board-goal-v2</code> reference/revision and
<code>native_goal_binding.state = bound</code>. A
<code>launch_mode = tracked_prompt</code> MAY have <code>board_goal = null</code>; when
null, binding state MUST be <code>prompt</code> or <code>none</code> and its blob
ID MUST be null.

Export uses this exact projection; no exporter-specific omission or
normalization is permitted:

| Bundle member | Authoritative source and equality rule |
| --- | --- |
| <code>bridge_protocol_version</code> | Whole-value equality with <code>SessionRecord.task_board.bridge_protocol_version</code> and the active bridge protocol |
| <code>logical_session_id</code>, <code>provider_id</code>, <code>workspace_group_id</code> | Copy the equal Session Record members exactly |
| <code>execution_profile</code>, <code>profile_source_event_id</code> | Copy the Section 2.4 effective profile and nullable source at the exported checkpoint; null requires equality with the Session Record creation profile, while non-null MUST name the newest authoritative <code>profile.changed</code> event reachable from that checkpoint's event heads |
| <code>task_element_id</code>, <code>launch_mode</code> | Copy <code>SessionRecord.task_board.task_element_id</code> and <code>.launch_mode</code> exactly |
| <code>sanitized_launch_plan</code> | Whole-object JCS equality with <code>SessionRecord.launch_plan</code>; preserve cwd, every non-secret literal, and every allowed extension with identical canonical JCS bytes |
| <code>board_identity</code>, <code>board_goal</code> | Whole-object JCS equality with <code>SessionRecord.task_board.board</code> and <code>.board_goal</code>, including all extension maps and null |
| <code>native_goal_binding.state</code> | Equal to <code>SessionRecord.task_board.native_goal_binding</code>; <code>opaque_blob_id</code> is the bridge-exported binding-state blob and is not synthesized by <code>ax</code> |
| <code>source_owner_host_id</code> | Winning lease holder used by the bridge export; it MUST equal the exporting host |
| <code>provider_snapshot</code>, <code>manager_record</code> | Exact public blob references emitted by the bridge inside <code>bundle.json</code>; their bytes remain opaque to <code>ax</code> and the bridge result authenticates them transitively through <code>bundle_id</code> |
| <code>manager_contract</code>, <code>created_at</code> | Fixed format literal and bridge export time, respectively; neither is projected from the Session Record |

The bridge export MUST be for the manager reference established by the newest
authoritative <code>task_board.launched</code> or
<code>task_board.adopted</code> event under that winning lease. Projection
validation compares the displayed whole objects, not a subset of their keys.
A missing or changed non-secret literal/extension is
<code>task_board_bundle_invalid</code> even when the reduced object would be
schema-valid on its own. Secrets remain forbidden by the source Launch Plan;
projection never authorizes adding them.

The projection above is exhaustive rather than implicitly lossy. The Session
Record's schema/version, record/subject identity, name, creation facts,
<code>kind = task_board</code>, creation-time execution profile, fork
provenance, and record-level extensions
remain in the separately replicated Session Record and MUST NOT be duplicated
inside the bundle. Within its Task-board Reference,
<code>bridge_protocol_version</code>, board, task element, launch mode, goal,
and native-binding enum are projected exactly as stated above. The creation-time
<code>manager_session_ref = null</code> is not serialized: the newest
authoritative launch/adoption event selects the public manager reference used
for this export. Task-board-Reference-level extensions remain ax metadata in
the Session Record because bridge protocol 1.0.0 has no corresponding field;
they MUST NOT be inserted into another bundle object or discarded from the
replicated Session Record. Likewise, bridge request operation/lease/workspace
paths and bridge result process/capability facts are operation-local; the
authoritative Session Event and Checkpoint retain the durable facts required by
their schemas. An exporter or importer MUST apply these inclusion/exclusion
rules exactly and MUST reject an attempt to tunnel an excluded field through a
different extension map.

The complete example above is
<code>TB-BUNDLE-PROJECTION-PRIMARY-POS</code>: its source Session Record and
bridge launch request contain the displayed non-secret literal and all three
displayed extension maps, and export/import MUST reproduce them exactly. The
normative <code>TB-BUNDLE-PROMPT-POS</code> variant replaces the corresponding
members with this exact projected data and recomputes <code>bundle_id</code>:

~~~json
{
  "execution_profile": "standard",
  "profile_source_event_id": null,
  "task_element_id": "TASK-260819-prompt-example",
  "launch_mode": "tracked_prompt",
  "sanitized_launch_plan": {
    "argv": ["task-board", "qwen", "TASK-260819-prompt-example"],
    "cwd_workspace_id": "0198f4c8-b080-7299-8273-1234567890ab",
    "cwd_relative": ".",
    "env_names": [],
    "env_literals": {
      "AX_TASK_MODE": "prompt"
    },
    "contains_secrets": false,
    "extensions": {
      "works.relux.ax.launch-hint": {
        "source": "tracked-prompt"
      }
    }
  },
  "board_goal": null,
  "native_goal_binding": {
    "state": "prompt",
    "opaque_blob_id": null
  },
  "board_identity": {
    "kind": "local",
    "logical_id": "agent-session-manager-spec",
    "remote_url": null,
    "extensions": {
      "works.relux.ax.board-scope": "prompt-research"
    }
  }
}
~~~

<code>TB-BUNDLE-PROMPT-N1</code> changes only the binding state to
<code>bound</code>, <code>TB-BUNDLE-PROMPT-N2</code> adds a non-null opaque blob,
and <code>TB-BUNDLE-PRIMARY-N1</code> changes the primary example goal to null.
All three MUST be rejected; prompt mode is never made unexportable merely
because it lacks a goal.
<code>TB-BUNDLE-PROJECTION-N1</code> drops the launch literal,
<code>TB-BUNDLE-PROJECTION-N2</code> drops one Board/Goal/Launch extension, and
<code>TB-BUNDLE-PROJECTION-N3</code> changes cwd while retaining a valid
standalone Launch Plan. Each fails projected equality before bridge import;
importers MUST NOT silently fill or strip the value.

<code>TB-BUNDLE-PROFILE-CHANGED-POS</code> starts from a Session Record with
<code>execution_profile = standard</code>, applies an authoritative
<code>profile.changed</code> event to <code>yolo</code>, and exports a checkpoint
whose closure contains that event. Its bundle MUST carry
<code>execution_profile = yolo</code> and that event's digest in
<code>profile_source_event_id</code>. <code>TB-BUNDLE-PROFILE-N1</code> copies
the stale Session Record value, <code>TB-BUNDLE-PROFILE-N2</code> uses null as
the source, and <code>TB-BUNDLE-PROFILE-N3</code> names a losing or non-newest
event. Each is <code>task_board_bundle_invalid</code> before import.

<code>tb-session-bundle-v1</code> is a deterministic POSIX PAX tar archive with
exactly these regular-file members for the primary example, in this bytewise
path order:

~~~text
blobs/sha256/cc/cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
blobs/sha256/dd/dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
blobs/sha256/ee/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
bundle.json
~~~

For a digest <code>sha256:H</code>, where <code>H</code> is exactly 64
lowercase hexadecimal characters, the one archive member is
<code>blobs/sha256/H[0:2]/H[2:64]</code>. The shard is the first two hex
characters and the leaf is the remaining 62; neither component contains the
<code>sha256:</code> prefix or the full digest. This is Section 3.2
<code>digest_path_v1</code> beneath the archive's <code>blobs/</code> prefix;
there is no second storage grammar. The required blob set is the
set-union of <code>provider_snapshot.blob_id</code>,
<code>manager_record.blob_id</code>, and non-null
<code>native_goal_binding.opaque_blob_id</code>. Two fields naming the same
digest produce one member.

The archive MUST contain exactly <code>bundle.json</code> plus one regular file
for each member of that set. Directory entries, PAX global or per-file extended
headers, GNU long-name records, links, devices, sparse files, and any other
member are forbidden. All v1 member names fit the base POSIX header fields;
exporters MUST fail with <code>task_board_bundle_invalid</code> rather than emit
an extension header. Members are sorted
bytewise by complete path and use uid/gid 0, empty owner/group names, timestamp
0, and mode 0600. <code>bundle.json</code> is the UTF-8 JCS encoding of the
complete displayed object including <code>bundle_id</code>, with no BOM or
trailing newline. Each blob member contains its raw bytes and MUST hash to the
digest from which its path was derived.

Compression is not part of the bundle contract; the outer Transfer Manifest
MAY content-address a compressed transport blob. <code>bundle_id</code> is the
canonical digest of the logical <code>bundle.json</code> object with only
<code>bundle_id</code> omitted. Because that object names every required opaque
blob by digest, it transitively identifies all bundle content.
<code>TB-ARCHIVE-PATH-POS</code> is the exact four-member set above.
<code>TB-ARCHIVE-PATH-N1</code> uses the full digest as the leaf,
<code>TB-ARCHIVE-PATH-N2</code> uses a wrong shard,
<code>TB-ARCHIVE-PATH-N3</code> adds a directory/unreferenced member, and
<code>TB-ARCHIVE-PATH-N4</code> changes one raw blob byte. Each MUST fail before
import/open. The importer also rejects a missing member, duplicate path, unsafe
path, noncanonical <code>bundle.json</code>, or digest mismatch.

### 9.4 Local and remote boards

For a local file-backed board, the workspace manifest MUST include the entire
managed <code>.task-board</code> tree except transient locks, runtime sockets,
credentials, and generated transport state. After destination materialization,
<code>ax</code> MUST run <code>task-board validate</code> as a standalone
process. Non-zero exit MUST fail materialization and retain staging.

For a remote board, the bundle retains only the remote URL and stable board
identity. Tokens, keychain entries, login profiles, and cached authentication
MUST remain machine-local. The destination MUST authenticate independently and
verify access to the same board before adopt.

### 9.5 Task-board capability reality

In v0.2.0:

- Codex and Claude MAY advertise goal-bound primary-owner support only through
  an accepted task-board bridge;
- Gemini, Muse, and Qwen MAY advertise tracked prompt spawn;
- Qwen is task-board-only and MUST NOT appear as a direct provider;
- Pi direct sessions are supported, but task-board prompt/primary use and goal
  binding remain unknown until a reliable adapter is accepted; and
- Antigravity task-board capabilities remain unknown and disabled.

A goal reference is durable metadata, not owner authority. <code>ax</code>
lease fencing remains authoritative for cross-host execution.

## 10. Immutable records, blobs, manifests, and tombstones

### 10.1 Record envelope

Session, event, lease, checkpoint, workspace-group, provider-identity, and
tombstone objects, plus Tombstone Acknowledgements, are immutable identity-
addressed objects. “Record” in this storage subsection is generic and does not
assign the RPC <code>record</code> namespace; Section 11.4 is the sole total
namespace registry. In addition to their schema-specific fields, each MUST include:

- its canonical digest ID;
- <code>subject_id</code>, the logical session or workspace scope;
- <code>created_by_host_id</code>;
- diagnostic <code>created_at</code>; and
- optional namespaced <code>extensions</code>.

The storage path MUST be derived from the digest, never from an untrusted
display name. A digest collision or same-ID/different-bytes observation is an
integrity emergency: both inputs MUST be quarantined and sync MUST stop for the
affected peer.

### 10.2 Content-addressed blobs

A blob is an uninterpreted byte sequence identified by SHA-256. Blob metadata
MUST live in a manifest, not in the blob path. Before publishing a record that
references a blob, the writer MUST fsync the blob, verify its size and digest,
and atomically install it in the object store.

Provider/task-board blobs can contain sensitive project history. Logs and
metrics MUST record digest, size, and media type only, never blob contents.

Every transferred blob has a Blob Descriptor with schema
<code>urn:ax:schema:blob</code> version <code>1.0.0</code>. Chunks MUST be
sorted, contiguous, non-overlapping, start at offset zero, and cover exactly
<code>size</code> bytes:

The descriptor is closed and contains exactly
<code>schema</code>, <code>schema_version</code>,
<code>descriptor_id:digest</code>, <code>blob_id:digest</code>,
<code>size:uint53</code>, <code>media_type:string[1..255]</code>, and
<code>chunks:BlobChunk[0..32768]</code>. <code>media_type</code> is a lowercase
ASCII <code>type/subtype</code> without parameters. BlobChunk is closed and
contains exactly <code>index:uint32</code>, <code>offset:uint53</code>,
<code>size:uint53[1..4194304]</code>, and <code>chunk_id:digest</code>. Indexes
start at zero and increase by one. An empty blob has size zero and no chunks;
a non-empty blob has at least one.

~~~json
{
  "schema": "urn:ax:schema:blob",
  "schema_version": "1.0.0",
  "descriptor_id": "sha256:390c8f21900483a010c1cbc3f9be01afebcf6e4da87263ba09fc5776dd6503ee",
  "blob_id": "sha256:9c21bad65c1b3d0403ac85d7d5bd134bb8d894432702a396a77b0477b8eb3b50",
  "size": 11,
  "media_type": "application/octet-stream",
  "chunks": [
    {
      "index": 0,
      "offset": 0,
      "size": 11,
      "chunk_id": "sha256:9c21bad65c1b3d0403ac85d7d5bd134bb8d894432702a396a77b0477b8eb3b50"
    }
  ]
}
~~~

The descriptor ID is its canonical object digest with
<code>descriptor_id</code> omitted. The example describes the eleven raw bytes
<code>ax-example\n</code>, whose unpadded base64url form is
<code>YXgtZXhhbXBsZQo</code>; the one last-chunk digest therefore equals the
whole-blob digest. Empty blobs have an empty chunk array. Protocol 1.0.0 permits
at most 32,768 chunks in one Blob Descriptor, so one blob is at most 128 GiB.
A larger file MUST fail capture with <code>capability_unavailable</code> before
publishing a partial manifest.

### 10.3 Transfer Chunk Descriptor

The transfer unit is a fixed 4 MiB chunk except the last chunk. Chunk schema is
<code>urn:ax:schema:chunk</code> version <code>1.0.0</code>:

The Transfer Chunk Descriptor is closed and contains exactly
<code>schema</code>, <code>schema_version</code>,
<code>blob_id:digest</code>, <code>index:uint32</code>,
<code>offset:uint53</code>, <code>size:uint53[1..4194304]</code>, and
<code>chunk_id:digest</code>. It has no extension map. Offset MUST equal index
times 4,194,304; every non-final chunk has that exact size.

~~~json
{
  "schema": "urn:ax:schema:chunk",
  "schema_version": "1.0.0",
  "blob_id": "sha256:9c21bad65c1b3d0403ac85d7d5bd134bb8d894432702a396a77b0477b8eb3b50",
  "index": 0,
  "offset": 0,
  "size": 11,
  "chunk_id": "sha256:9c21bad65c1b3d0403ac85d7d5bd134bb8d894432702a396a77b0477b8eb3b50"
}
~~~

Chunk digests are over raw chunk bytes. A receiver MUST validate every chunk
before marking it present and MUST validate the complete blob after assembly.
Chunk identity is transfer metadata; the whole blob digest is storage identity.

### 10.4 Transfer Manifest

Transfer Manifest schema <code>urn:ax:schema:transfer-manifest</code> version
<code>1.0.0</code> describes one immutable snapshot. Its top-level object is
closed and contains exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Transfer Manifest schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>manifest_id</code> | digest | Canonical object digest |
| <code>kind</code> | enum | <code>workspace_group</code>, <code>workspace_tree</code>, <code>provider</code>, <code>task_board</code>, or <code>composite</code> |
| <code>subject_id</code> | UUIDv7 | Group, workspace, or session selected by kind |
| <code>base_checkpoint_id</code> | digest or null | Null only for an initial capture with no predecessor checkpoint |
| <code>entries</code> | ManifestEntry[0..65536] | Sorted bytewise by normalized path |
| <code>child_manifest_ids</code> | sorted unique digest[0..1024] | Path-disjoint child/partition closure |
| <code>workspace_snapshot</code> | WorkspaceSnapshot or null | Non-null only for <code>workspace_group</code> |
| <code>provider_identity_record_id</code> | digest or null | Non-null only for <code>provider</code> |
| <code>task_board_bundle_id</code> | digest or null | Non-null only for <code>task_board</code> |
| <code>excluded_classes</code> | sorted unique string[0..128] | Applied exclusion-policy classes |
| <code>created_by_host_id</code> | UUIDv7 | Capturing host |
| <code>created_at</code> | timestamp | Diagnostic only |
| <code>extensions</code> | object | Reverse-DNS extension keys only |

The kind invariants are exact:

- <code>workspace_group</code> uses the Workspace Group ID as subject, requires
  a non-null workspace snapshot and at least one child, and requires empty
  entries plus null provider/task-board IDs;
- <code>workspace_tree</code> uses one Workspace ID as subject, requires null
  snapshot/provider/task-board fields, and contains entries and optional
  path-partition children;
- <code>provider</code> uses a Session ID, requires a provider identity record,
  and requires null snapshot/task-board fields;
- <code>task_board</code> uses a Session ID, requires a bundle ID, and requires
  null snapshot/provider fields; and
- <code>composite</code> requires at least one child, empty entries, and all
  three tagged fields null.

Every direct-session checkpoint references one <code>provider</code> manifest,
even for a backend-only identity with zero entries. Every task-board checkpoint
references the bundle directly and MAY additionally transfer a
<code>task_board</code> manifest. A composite MUST NOT duplicate a child's
entries.

<code>ManifestEntry</code> is a closed tagged union. Fields not listed for a
variant are forbidden:

| Tag | Exact members |
| --- | --- |
| <code>type = directory</code> | <code>path:path</code>, <code>type:directory</code>, <code>mode:uint32[0..4095]</code> |
| <code>type = file</code> | <code>path:path</code>, <code>type:file</code>, <code>mode:uint32[0..4095]</code>, <code>size:uint53</code>, <code>blob_id:digest</code>, <code>blob_descriptor_id:digest</code> |
| <code>type = symlink</code> | <code>path:path</code>, <code>type:symlink</code>, <code>mode:uint32[0..4095]</code>, <code>target:string[1..4096]</code> |
| <code>type = hardlink</code> | <code>path:path</code>, <code>type:hardlink</code>, <code>mode:uint32[0..4095]</code>, <code>target_path:path</code> |

Directory, symlink, and hardlink positive fragments are:

~~~json
{"path":"src","type":"directory","mode":493}
~~~

~~~json
{"path":"current","type":"symlink","mode":511,"target":"releases/v1"}
~~~

~~~json
{"path":"README-copy.md","type":"hardlink","mode":420,"target_path":"README.md"}
~~~

Every file entry MUST reference a Blob Descriptor whose blob ID and size equal
the entry. A hardlink target MUST name an earlier file entry with the same mode.
A symlink target is interpreted relative to its containing directory and MUST
resolve within the materialization root after lexical and filesystem checks.
Absolute or escaping targets fail. Entries and child partitions MUST contain
no duplicate, overlapping, or destination-case-colliding path.

<code>WorkspaceSnapshot</code> is a closed object containing exactly
<code>workspace_group_id:UUIDv7</code> and
<code>members:WorkspaceSnapshotMember[1..256]</code>. Its group ID equals the
manifest subject, and its members correspond one-for-one, in workspace-ID
order, with the Workspace Group Record. A snapshot member is one of these
closed variants; neither variant has an extension point:

| Tag | Exact members |
| --- | --- |
| <code>kind = git</code> | <code>workspace_id:UUIDv7</code>, <code>kind:git</code>, <code>group_relative_path:path</code>, <code>repository_identity:string[1..256]</code>, <code>remotes:GitRemote[1..16]</code>, <code>head:GitHead</code>, <code>upstream_ref:git-ref&#124;null</code>, <code>object_pack:GitObjectPack</code>, <code>index:GitIndex</code>, <code>working_tree_manifest_id:digest</code>, <code>submodules:GitSubmodule[0..256]</code>, <code>features:GitFeatures</code>, <code>repo_relative_cwd:.&#124;path</code>, <code>agent_project_config_paths:sorted unique path[0..256]</code>, <code>materialization_policy:shared_checkout&#124;separate_worktree</code> |
| <code>kind = managed_tree</code> | <code>workspace_id:UUIDv7</code>, <code>kind:managed_tree</code>, <code>group_relative_path:path</code>, <code>tree_identity:string[1..256]</code>, <code>tree_manifest_id:digest</code>, <code>repo_relative_cwd:.&#124;path</code>, <code>agent_project_config_paths:sorted unique path[0..256]</code>, <code>materialization_policy:shared_tree&#124;separate_copy</code> |

The Git embedded types are closed and exact:

| Type | Exact members and constraints |
| --- | --- |
| <code>GitRemote</code> | <code>name:string[1..128]</code>, <code>fetch_url:sanitized-git-URL</code>, <code>push_url:sanitized-git-URL&#124;null</code>; sorted by name, no duplicate |
| <code>GitHead</code> | <code>mode:branch&#124;detached&#124;unborn</code>, <code>oid:git-oid&#124;null</code>, <code>ref:git-ref&#124;null</code>; branch has both, detached has only oid, unborn has only a <code>refs/heads/</code> ref |
| <code>GitObjectPack</code> | <code>format:git_pack_v2</code>, <code>object_format:sha1&#124;sha256</code>, <code>blob_id:digest</code>, <code>blob_descriptor_id:digest</code>, <code>object_count:uint53</code>, <code>inventory_blob_id:digest</code>, <code>inventory_blob_descriptor_id:digest</code> |
| <code>GitIndex</code> | <code>format:git_index</code>, <code>version:2&#124;3&#124;4</code>, <code>blob_id:digest</code>, <code>blob_descriptor_id:digest</code>, <code>entries:GitIndexEntry[0..65536]</code>, <code>entry_count:uint53</code>; entries sorted by path then stage, count equal to length |
| <code>GitIndexEntry</code> | <code>path:path</code>, <code>stage:uint8[0..3]</code>, <code>mode:uint32</code>, <code>oid:git-oid</code>, <code>intent_to_add:boolean</code>, <code>skip_worktree:boolean</code>, <code>assume_unchanged:boolean</code>, <code>fsmonitor_valid:boolean</code> |
| <code>GitSubmodule</code> | <code>path:path</code>, <code>repository_identity:string[1..256]</code>, <code>sanitized_url:sanitized-git-URL</code>, <code>gitlink_oid:git-oid</code>, <code>initialized:boolean</code>, <code>head:GitHead&#124;null</code>, <code>upstream_ref:git-ref&#124;null</code>, <code>object_pack:GitObjectPack&#124;null</code>, <code>index:GitIndex&#124;null</code>, <code>working_tree_manifest_id:digest&#124;null</code>, <code>submodules:GitSubmodule[0..256]&#124;null</code>, <code>features:GitFeatures&#124;null</code>, <code>repo_relative_cwd:.&#124;path&#124;null</code>, <code>agent_project_config_paths:sorted unique path[0..256]&#124;null</code> |
| <code>GitFeatures</code> | <code>object_format:sha1&#124;sha256</code>, <code>filemode:boolean</code>, <code>symlinks:boolean</code>, <code>case_sensitive:boolean</code>, <code>precompose_unicode:boolean</code>, <code>sparse_checkout:boolean</code>, <code>sparse_patterns_blob_id:digest&#124;null</code>, <code>sparse_patterns_blob_descriptor_id:digest&#124;null</code>, <code>required_filter_names:sorted unique string[0..64]</code>, <code>lfs_required:boolean</code> |

A <code>git-oid</code> is <code>sha1:</code> plus 40 lowercase hexadecimal
characters or <code>sha256:</code> plus 64, matching
<code>features.object_format</code>. A <code>git-ref</code> is a 1–1024 byte
fully qualified ref accepted by <code>git check-ref-format</code>; the literals
<code>HEAD</code> and abbreviated refs are forbidden. Remotes use the same
sanitization as Section 5.6.

Each <code>GitObjectPack</code> contains only objects from the repository whose
descriptor owns it. A superproject pack contains every superproject object
needed to resolve its HEAD, recorded refs, and non-gitlink index entries
without network access. A mode-160000 gitlink OID is an opaque commit name in
the child repository and MUST NOT be required to resolve in the superproject
pack. Each initialized <code>GitSubmodule.object_pack</code> independently
contains the child objects needed to resolve that submodule's checked-out HEAD,
index, and nested state. Its inventory blob is UTF-8
lines <code>OID SP commit|tree|blob|tag SP DECIMAL_SIZE LF</code>, bytewise
sorted by OID, with no duplicate and exactly <code>object_count</code> lines.
The raw Git index blob and the logical entries MUST describe the same supported
index; unknown required extensions fail closed. Working-tree manifest bytes are
the actual post-index bytes, so staged and unstaged content remain distinct.

<code>GitSubmodule.gitlink_oid</code> is exactly the OID of the stage-0,
mode-160000 entry for <code>GitSubmodule.path</code> in the containing
superproject's <code>GitIndex.entries</code>. Protocol 1.0.0 rejects a submodule
path with only conflict stages 1–3. The superproject HEAD-tree gitlink is a
derived value obtained by resolving that path in the tree named by the
containing member's <code>head.oid</code>; it is called
<code>head_tree_gitlink_oid</code> in fixture prose but is not an additional
wire member. The checked-out child commit is
<code>GitSubmodule.head.oid</code>. These three values are deliberately
independent so staged and unstaged pointer changes are preserved.

An initialized submodule requires every state field after
<code>initialized</code> except <code>upstream_ref</code> to be non-null. Its
head is branch or detached, never unborn. Its head OID MUST resolve as a commit
in its own <code>GitSubmodule.object_pack</code>; it need not equal either
superproject pointer. An uninitialized submodule requires every state field after
<code>initialized</code> to be null. Nested submodules use the same exact shape;
the tree is acyclic, has depth at most 16, and contains at most 256 submodules
in total. This recursive state preserves staged, unstaged, untracked, cwd, and
project-configuration facts inside initialized submodules instead of assuming
they are clean.

Sparse pattern blob and descriptor are either both non-null when sparse
checkout is true or both null when false. Every referenced working-tree,
managed-tree, and submodule manifest MUST occur in the workspace root's
transitive child closure. Every cwd directory and project-configuration path
MUST exist in that closure.

The following language-neutral payload corpus is part of
<code>WS-GIT-ROUNDTRIP-1</code>. <code>base64url</code> is the exact unpadded
encoding of the blob bytes. Every payload is one chunk, so its complete Blob
Descriptor is reconstructed with schema <code>urn:ax:schema:blob</code>, version
<code>1.0.0</code>, the displayed blob ID, size and media type, and one
<code>{index:0,offset:0,size,chunk_id:blob_id}</code> entry. The displayed
descriptor ID is the JCS self-identity of that reconstructed descriptor.

~~~json
{
  "fixture": "ax-git-workspace-v1",
  "parent_commit": "sha1:602548b4fd46332c934667db9992b8bb00318c88",
  "child_commit": "sha1:25eec72bdd91287a7d68f206907a859b5a7b5524",
  "parent_object_count": 7,
  "child_object_count": 3,
  "parent_index_entries": [
    "100644 5461fe036f6cf55f98d75ee651c2b4cc13a80c66 0\t.gitmodules",
    "100644 b6b0be997c9c8246cdd346dd7ece72140d74dee0 0\tAGENTS.md",
    "100644 19d9cc8584ac2c7dcf57d2680375e80f099dc481 0\tREADME.md",
    "160000 25eec72bdd91287a7d68f206907a859b5a7b5524 0\tvendor/lib"
  ],
  "child_index_entries": [
    "100644 a69c0feac9815fe47cecb849931d858109a5a0c9 0\tREADME.md"
  ],
  "payloads": [
    {"label":"agent_file","size":6,"media_type":"text/plain","base64url":"YWdlbnQK","blob_id":"sha256:d20bc21bb3c7736d8d03ade3ddb4c68b665cdfbca6f6df0f7fdd192f37f59060","descriptor_id":"sha256:ffa55edaa3cc8c1263644441fd01896bcaf92d91c55ae9bd91edcabb1f408ba9"},
    {"label":"base_file","size":5,"media_type":"text/plain","base64url":"YmFzZQo","blob_id":"sha256:f34848ca92665c342abd5816c9e3eda0e82180671195362bcd0080544a3bc2ac","descriptor_id":"sha256:3d47b1837f2c69c881fd924e94e7296b297d1de4353743ba45007dca5e05c8f9"},
    {"label":"staged_file","size":7,"media_type":"text/plain","base64url":"c3RhZ2VkCg","blob_id":"sha256:9ac007af3de930baf647288da0c843b26a5f046a3fe1351f1bb039b242d22cdf","descriptor_id":"sha256:2a383ef6cac04d7f52b750dc3256bca620883943c4d4cabf31aa644f630b539e"},
    {"label":"working_file","size":8,"media_type":"text/plain","base64url":"d29ya2luZwo","blob_id":"sha256:0e442b07e3772e8f5622478242ddf5f9f197bbd6a0402cd71471db4081abb291","descriptor_id":"sha256:f3fe5a9c5e1ef041645b84b5618a4a2d6e4184dbd11c21b92b0bdcaa482ad7ab"},
    {"label":"notes_file","size":6,"media_type":"text/plain","base64url":"bm90ZXMK","blob_id":"sha256:444e0fffbd825e9610ff5b199485707a0c895339ae80c15cc8a8aee41b106fda","descriptor_id":"sha256:de864d26dacd33a1970e78c2c5f588708bb17905fa0a1c712d6a40ddee182e73"},
    {"label":"child_file","size":6,"media_type":"text/plain","base64url":"Y2hpbGQK","blob_id":"sha256:2fa14f53e6b15cac9ac77846c7be87862c2a7e9ec0c6cea319db939317f126ed","descriptor_id":"sha256:089ed22190957336a4f4710831c1ac65e2176773f3df4cf52589103f7571c0a4"},
    {"label":"gitmodules_file","size":86,"media_type":"text/plain","base64url":"W3N1Ym1vZHVsZSAidmVuZG9yL2xpYiJdCglwYXRoID0gdmVuZG9yL2xpYgoJdXJsID0gc3NoOi8vZ2l0QGdpdGh1Yi5jb20vcmVsdXgvbGliLmdpdAo","blob_id":"sha256:3a17df6342fd4e89fbf52663e0dd6500881a6956e520eeba518266ac3a54f30b","descriptor_id":"sha256:f4918a6688ce35d97dea58a97019b4fd39488f317fe90c08e2d703cd7911c0bc"},
    {"label":"parent_pack","size":473,"media_type":"application/x-git-packed-objects","base64url":"UEFDSwAAAAIAAAAHogl4nDM0MDAzMVHQS88syc1PKc1JLWYISfzHnJ_zNX7G9bhngYe2nBFewZNmCFHm6O7qFxKsl5vCsG3Dvpk1c5rczl52u1t3rkiEt-TeA6iiIFdHF19XkKL706qnLa18EiWxQ1Xc6GIGy6anWaEmBkCgUJaal5JfxJD5SLGeYalJ13kNHaaMlRyONxZYtwMAT6447Dd4nCsuSUxPTeECAAtmAoO2BXiciy4uTcrNTynNSVVQKkvNS8kv0s_JTFKK5eIsSCzJULBVQAhycZYW5QBFioszrPT10zNLHIA4ozRJLzk_V78oNae0AqRKDyjIBQAMDx2Qmwt4nJ3LPQoCMRBA4T6nmF6QmcRNNiCLNp7BNhMnGNg_wqzs8RX0BL7qNZ82EcDiqWAXGa2Qc8gWu54os89OLJ-seMbIZNKmz6XB9Q63uuvWBM7lOxfZ07SOcqzzK431MQCFPmAMHhEO-MnkZZqqqvzrzZqazAo_Yd4akDo8rwF4nDM0MwAChZzMJAbVd8e1707UqKrN-MQ2oap1dlR1qAoAqdUL6TZ4nEtMT80r4QIACB8CGjV4nEtKLE7lAgAFoAGmJeJWB7tO1hMnbJF41TaD1xkF8G0","blob_id":"sha256:f66d0ab5365d550aae8fddc4eb8aa58cf8e44db713406ad60d7a7ab763586e04","descriptor_id":"sha256:25379f6ba068033a3190a3d8bba3b0cf094baf44772cc4fa213ba75735327f3e"},
    {"label":"parent_inventory","size":344,"media_type":"text/plain","base64url":"MGY2MWYwNTliMDJlMTMzMGIyMDU4MTFjYjZjM2UyYjQyZTZiMDliMSB0cmVlIDE0NgoxOWQ5Y2M4NTg0YWMyYzdkY2Y1N2QyNjgwMzc1ZTgwZjA5OWRjNDgxIGJsb2IgNwo1NDYxZmUwMzZmNmNmNTVmOThkNzVlZTY1MWMyYjRjYzEzYTgwYzY2IGJsb2IgODYKNjAyNTQ4YjRmZDQ2MzMyYzkzNDY2N2RiOTk5MmI4YmIwMDMxOGM4OCBjb21taXQgMTg3CjY5ZTIyMTdmMDBhNTM0OGFjZjI4MmMwMjY4YTkwODQxZDhhMDNiODcgdHJlZSAzMQpiNmIwYmU5OTdjOWM4MjQ2Y2RkMzQ2ZGQ3ZWNlNzIxNDBkNzRkZWUwIGJsb2IgNgpkZjk2N2I5NmE1NzllNDVhMThiODI1MTczMmQxNjgwNGIyZTU2YTU1IGJsb2IgNQo","blob_id":"sha256:415d78426809fdd2d49c32021789c7e7bfca7411315bfb1f4a9b9bf542d4ab0c","descriptor_id":"sha256:4f72f49106b91208a27fef4fb6c95061f44457bcfb429b1f6e8afdcaede12479"},
    {"label":"parent_index","size":381,"media_type":"application/vnd.git.index","base64url":"RElSQwAAAAIAAAAEaoUMEA4xiPJqhQwQDjGI8gEAABAqY5_rAACBpAAAAfYAAAAUAAAAVlRh_gNvbPVfmNde5lHCtMwTqAxmAAsuZ2l0bW9kdWxlcwAAAAAAAABqhQwQDjNMIWqFDBAOM0whAQAAECpjn-wAAIGkAAAB9gAAABQAAAAGtrC-mXycgkbN00bdfs5yFA103uAACUFHRU5UUy5tZABqhQwQEtOc7WqFDBAS05ztAQAAECpjn-0AAIGkAAAB9gAAABQAAAAHGdnMhYSsLH3PV9JoA3XoDwmdxIEACVJFQURNRS5tZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAAAAAAJe7HK92RKHp9aPIGkHqFm1p7VSQACnZlbmRvci9saWIAAAAAAAAAAFRSRUUAAAAlAC0xIDEKdmVuZG9yADEgMApp4iF_AKU0is8oLAJoqQhB2KA7h-NB2BVt-wTXet65AP9SnhiZeXMZ","blob_id":"sha256:abf7c7add1e14aff23baa2bdeb15226e10e3ca03d6cc93d5ab064ea031dff771","descriptor_id":"sha256:d8db81a4543ad7b17d90cc1df23b78f1d3e166e31789cbfb8c829ddafa3d8b44"},
    {"label":"child_pack","size":221,"media_type":"application/x-git-packed-objects","base64url":"UEFDSwAAAAIAAAADmgt4nJ3LQQrCMBBA0X1OMXtBJm1pMiCim57B7SQzpYHESkilx6-gJ_Cv_ua1qgqRhdF70tmKKIVAJE7CyF3Ufgg9dmwt2cHw1pa1wv0BU9rbVhUu83duunN5ZT2n55tzkitY5x2SGxHhhJ9MXEtJrem_3sQlZYEfMAe7Ozr0NnicS87IzEnhAgAIGgIPpQJ4nDM0MDAzMVEIcnV08XXVy01hWDaH_9XJxvgnNW92eE6WbW3kXLrgJADooQ77IMGVWpwBJ0fcFY3FN1o5-zRQAW0","blob_id":"sha256:5acac14cadc49764b93244904c396f2954890bef95b61523d382b2cc779346e5","descriptor_id":"sha256:2ed8272bd2aa597b5444e680b343f393c96dd45baf88ffac644e02b54c7ef78e"},
    {"label":"child_inventory","size":149,"media_type":"text/plain","base64url":"MjVlZWM3MmJkZDkxMjg3YTdkNjhmMjA2OTA3YTg1OWI1YTdiNTUyNCBjb21taXQgMTg2CmE2OWMwZmVhYzk4MTVmZTQ3Y2VjYjg0OTkzMWQ4NTgxMDlhNWEwYzkgYmxvYiA2CmNhZGEwODg5ZWYxZGRlOWJiOTlkN2RiNmEyY2UzNGIzMDJhMTE5MTQgdHJlZSAzNwo","blob_id":"sha256:9ba4d72c52510467ee2bad12d33f8dd02dfa5b51b9f1bdfcdaa85147a4241d4b","descriptor_id":"sha256:b1a2a87ba880a09d5000af5c74e3ef580e456e161399bb87ad1ce01d22e0bb5e"},
    {"label":"child_index","size":137,"media_type":"application/vnd.git.index","base64url":"RElSQwAAAAIAAAABaoUMEAIh_NxqhQwQAiH83AEAABAqY5-oAACBpAAAAfYAAAAUAAAABqacD-rJgV_kfOy4SZMdhYEJpaDJAAlSRUFETUUubWQAVFJFRQAAABkAMSAwCsraCInvHd6buZ19tqLONLMCoRkUraW7mMLxScDqnRiYiZqOHWMhBkk","blob_id":"sha256:5f30af3628936cb4502d7df72f0d85d8ae08c39fef674d838576fb8a9e2a28a4","descriptor_id":"sha256:5881f1ab66ad86da2987a25c8dfd29c0d2eff74782e3eee607aee2edecf7083c"}
  ]
}
~~~

The parent inventory contains its reachable superproject commit/tree/blob
closure plus the staged README blob; it intentionally does not contain child
commit <code>25eec72b…</code>. The child inventory contains that independent
commit/tree/blob closure. Indexing the parent pack in one empty bare object
database MUST resolve only the displayed parent commit; indexing the child pack
in a different empty bare object database MUST resolve only the displayed child
commit. A validator that imports both packs into one object database does not
prove repository-boundary conformance. The exact raw index
payloads, not host stat-cache values reconstructed from the logical list, are
authoritative; the logical entries below are a cross-check and planning view.

Normative Git working-tree manifest fixture:

~~~json
{
  "schema": "urn:ax:schema:transfer-manifest",
  "schema_version": "1.0.0",
  "manifest_id": "sha256:88d93f20f978b92e75d35e67ebd5a41b90ff1afe106363b05c0f7b08614eb4cf",
  "kind": "workspace_tree",
  "subject_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
  "base_checkpoint_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "entries": [
    {"path":".gitmodules","type":"file","mode":420,"size":86,"blob_id":"sha256:3a17df6342fd4e89fbf52663e0dd6500881a6956e520eeba518266ac3a54f30b","blob_descriptor_id":"sha256:f4918a6688ce35d97dea58a97019b4fd39488f317fe90c08e2d703cd7911c0bc"},
    {"path":"AGENTS.md","type":"file","mode":420,"size":6,"blob_id":"sha256:d20bc21bb3c7736d8d03ade3ddb4c68b665cdfbca6f6df0f7fdd192f37f59060","blob_descriptor_id":"sha256:ffa55edaa3cc8c1263644441fd01896bcaf92d91c55ae9bd91edcabb1f408ba9"},
    {"path":"README.md","type":"file","mode":420,"size":8,"blob_id":"sha256:0e442b07e3772e8f5622478242ddf5f9f197bbd6a0402cd71471db4081abb291","blob_descriptor_id":"sha256:f3fe5a9c5e1ef041645b84b5618a4a2d6e4184dbd11c21b92b0bdcaa482ad7ab"},
    {"path":"notes.txt","type":"file","mode":420,"size":6,"blob_id":"sha256:444e0fffbd825e9610ff5b199485707a0c895339ae80c15cc8a8aee41b106fda","blob_descriptor_id":"sha256:de864d26dacd33a1970e78c2c5f588708bb17905fa0a1c712d6a40ddee182e73"},
    {"path":"src","type":"directory","mode":493},
    {"path":"vendor","type":"directory","mode":493},
    {"path":"vendor/lib","type":"directory","mode":493}
  ],
  "child_manifest_ids": [],
  "workspace_snapshot": null,
  "provider_identity_record_id": null,
  "task_board_bundle_id": null,
  "excluded_classes": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:15:00.000Z",
  "extensions": {}
}
~~~

Normative managed-tree manifest fixture:

~~~json
{
  "schema": "urn:ax:schema:transfer-manifest",
  "schema_version": "1.0.0",
  "manifest_id": "sha256:8dc15e881e026e7cf59482395baaa8c47341e6bad6d87f44312a9d0b360aacd5",
  "kind": "workspace_tree",
  "subject_id": "0198f4c8-7d40-7e55-8e6f-2234567890ab",
  "base_checkpoint_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "entries": [
    {"path":"AGENTS.md","type":"file","mode":420,"size":6,"blob_id":"sha256:d20bc21bb3c7736d8d03ade3ddb4c68b665cdfbca6f6df0f7fdd192f37f59060","blob_descriptor_id":"sha256:ffa55edaa3cc8c1263644441fd01896bcaf92d91c55ae9bd91edcabb1f408ba9"},
    {"path":"drafts","type":"directory","mode":493},
    {"path":"drafts/note.md","type":"file","mode":420,"size":6,"blob_id":"sha256:444e0fffbd825e9610ff5b199485707a0c895339ae80c15cc8a8aee41b106fda","blob_descriptor_id":"sha256:de864d26dacd33a1970e78c2c5f588708bb17905fa0a1c712d6a40ddee182e73"}
  ],
  "child_manifest_ids": [],
  "workspace_snapshot": null,
  "provider_identity_record_id": null,
  "task_board_bundle_id": null,
  "excluded_classes": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:15:00.000Z",
  "extensions": {}
}
~~~

Normative <code>PROVIDER-CAPTURE-POS</code> manifest returned by provider
<code>capture</code> after the host verifies the isolated object sink:

~~~json
{
  "schema": "urn:ax:schema:transfer-manifest",
  "schema_version": "1.0.0",
  "manifest_id": "sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91",
  "kind": "provider",
  "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "base_checkpoint_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "entries": [
    {"path":"session/session.jsonl","type":"file","mode":384,"size":6,"blob_id":"sha256:444e0fffbd825e9610ff5b199485707a0c895339ae80c15cc8a8aee41b106fda","blob_descriptor_id":"sha256:de864d26dacd33a1970e78c2c5f588708bb17905fa0a1c712d6a40ddee182e73"}
  ],
  "child_manifest_ids": [],
  "workspace_snapshot": null,
  "provider_identity_record_id": "sha256:c879d766da67a8cfb3a3f6eae2234faa5d52d8df987496eae2218f40e5e220c2",
  "task_board_bundle_id": null,
  "excluded_classes": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:15:00.000Z",
  "extensions": {}
}
~~~

The returned descriptor list contains the descriptor ending
<code>e182e73</code>, and <code>written_blob_ids</code> contains only the blob
ending <code>1b106fda</code>. A success body that names another blob, leaves an
extra sink file, or includes an excluded path is the normative
<code>PROVIDER-CAPTURE-N1</code> failure and MUST be rejected before object-store
import.

Normative initialized-submodule workspace-tree fixture:

~~~json
{
  "schema": "urn:ax:schema:transfer-manifest",
  "schema_version": "1.0.0",
  "manifest_id": "sha256:7cff7402aa5a31ba0cd7ff9bf49a9dc166b961c9f2b647d1c1084d3e70ce5db8",
  "kind": "workspace_tree",
  "subject_id": "0198f4c8-8e50-7f66-8f70-3234567890ab",
  "base_checkpoint_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "entries": [
    {"path":"README.md","type":"file","mode":420,"size":6,"blob_id":"sha256:2fa14f53e6b15cac9ac77846c7be87862c2a7e9ec0c6cea319db939317f126ed","blob_descriptor_id":"sha256:089ed22190957336a4f4710831c1ac65e2176773f3df4cf52589103f7571c0a4"}
  ],
  "child_manifest_ids": [],
  "workspace_snapshot": null,
  "provider_identity_record_id": null,
  "task_board_bundle_id": null,
  "excluded_classes": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:15:00.000Z",
  "extensions": {}
}
~~~

Its subject is the submodule workspace identity local to the snapshot. The
containing <code>GitSubmodule.working_tree_manifest_id</code> MUST equal this
object's <code>manifest_id</code>, and
<code>GitSubmodule.gitlink_oid</code> and
<code>GitSubmodule.head.oid</code> MUST name the same checked-out commit present
in the child pack inventory for this clean-pointer fixture. The child commit is
not present in the parent pack inventory.

Normative workspace-group root fixture:

~~~json
{
  "schema": "urn:ax:schema:transfer-manifest",
  "schema_version": "1.0.0",
  "manifest_id": "sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e",
  "kind": "workspace_group",
  "subject_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "base_checkpoint_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "entries": [],
  "child_manifest_ids": [
    "sha256:7cff7402aa5a31ba0cd7ff9bf49a9dc166b961c9f2b647d1c1084d3e70ce5db8",
    "sha256:88d93f20f978b92e75d35e67ebd5a41b90ff1afe106363b05c0f7b08614eb4cf",
    "sha256:8dc15e881e026e7cf59482395baaa8c47341e6bad6d87f44312a9d0b360aacd5"
  ],
  "workspace_snapshot": {
    "workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
    "members": [
      {
        "workspace_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
        "kind": "git",
        "group_relative_path": "payments-api",
        "repository_identity": "relux/payments-api",
        "remotes": [
          {"name":"origin","fetch_url":"ssh://git@github.com/relux/payments-api.git","push_url":null}
        ],
        "head": {"mode":"branch","oid":"sha1:602548b4fd46332c934667db9992b8bb00318c88","ref":"refs/heads/feature/ax"},
        "upstream_ref": "refs/remotes/origin/feature/ax",
        "object_pack": {
          "format": "git_pack_v2",
          "object_format": "sha1",
          "blob_id": "sha256:f66d0ab5365d550aae8fddc4eb8aa58cf8e44db713406ad60d7a7ab763586e04",
          "blob_descriptor_id": "sha256:25379f6ba068033a3190a3d8bba3b0cf094baf44772cc4fa213ba75735327f3e",
          "object_count": 7,
          "inventory_blob_id": "sha256:415d78426809fdd2d49c32021789c7e7bfca7411315bfb1f4a9b9bf542d4ab0c",
          "inventory_blob_descriptor_id": "sha256:4f72f49106b91208a27fef4fb6c95061f44457bcfb429b1f6e8afdcaede12479"
        },
        "index": {
          "format": "git_index",
          "version": 2,
          "blob_id": "sha256:abf7c7add1e14aff23baa2bdeb15226e10e3ca03d6cc93d5ab064ea031dff771",
          "blob_descriptor_id": "sha256:d8db81a4543ad7b17d90cc1df23b78f1d3e166e31789cbfb8c829ddafa3d8b44",
          "entries": [
            {"path":".gitmodules","stage":0,"mode":33188,"oid":"sha1:5461fe036f6cf55f98d75ee651c2b4cc13a80c66","intent_to_add":false,"skip_worktree":false,"assume_unchanged":false,"fsmonitor_valid":false},
            {"path":"AGENTS.md","stage":0,"mode":33188,"oid":"sha1:b6b0be997c9c8246cdd346dd7ece72140d74dee0","intent_to_add":false,"skip_worktree":false,"assume_unchanged":false,"fsmonitor_valid":false},
            {"path":"README.md","stage":0,"mode":33188,"oid":"sha1:19d9cc8584ac2c7dcf57d2680375e80f099dc481","intent_to_add":false,"skip_worktree":false,"assume_unchanged":false,"fsmonitor_valid":false},
            {"path":"vendor/lib","stage":0,"mode":57344,"oid":"sha1:25eec72bdd91287a7d68f206907a859b5a7b5524","intent_to_add":false,"skip_worktree":false,"assume_unchanged":false,"fsmonitor_valid":false}
          ],
          "entry_count": 4
        },
        "working_tree_manifest_id": "sha256:88d93f20f978b92e75d35e67ebd5a41b90ff1afe106363b05c0f7b08614eb4cf",
        "submodules": [
          {
            "path": "vendor/lib",
            "repository_identity": "relux/lib",
            "sanitized_url": "ssh://git@github.com/relux/lib.git",
            "gitlink_oid": "sha1:25eec72bdd91287a7d68f206907a859b5a7b5524",
            "initialized": true,
            "head": {
              "mode": "detached",
              "oid": "sha1:25eec72bdd91287a7d68f206907a859b5a7b5524",
              "ref": null
            },
            "upstream_ref": null,
            "object_pack": {
              "format": "git_pack_v2",
              "object_format": "sha1",
              "blob_id": "sha256:5acac14cadc49764b93244904c396f2954890bef95b61523d382b2cc779346e5",
              "blob_descriptor_id": "sha256:2ed8272bd2aa597b5444e680b343f393c96dd45baf88ffac644e02b54c7ef78e",
              "object_count": 3,
              "inventory_blob_id": "sha256:9ba4d72c52510467ee2bad12d33f8dd02dfa5b51b9f1bdfcdaa85147a4241d4b",
              "inventory_blob_descriptor_id": "sha256:b1a2a87ba880a09d5000af5c74e3ef580e456e161399bb87ad1ce01d22e0bb5e"
            },
            "index": {
              "format": "git_index",
              "version": 2,
              "blob_id": "sha256:5f30af3628936cb4502d7df72f0d85d8ae08c39fef674d838576fb8a9e2a28a4",
              "blob_descriptor_id": "sha256:5881f1ab66ad86da2987a25c8dfd29c0d2eff74782e3eee607aee2edecf7083c",
              "entries": [
                {"path":"README.md","stage":0,"mode":33188,"oid":"sha1:a69c0feac9815fe47cecb849931d858109a5a0c9","intent_to_add":false,"skip_worktree":false,"assume_unchanged":false,"fsmonitor_valid":false}
              ],
              "entry_count": 1
            },
            "working_tree_manifest_id": "sha256:7cff7402aa5a31ba0cd7ff9bf49a9dc166b961c9f2b647d1c1084d3e70ce5db8",
            "submodules": [],
            "features": {
              "object_format": "sha1",
              "filemode": true,
              "symlinks": true,
              "case_sensitive": true,
              "precompose_unicode": false,
              "sparse_checkout": false,
              "sparse_patterns_blob_id": null,
              "sparse_patterns_blob_descriptor_id": null,
              "required_filter_names": [],
              "lfs_required": false
            },
            "repo_relative_cwd": ".",
            "agent_project_config_paths": []
          }
        ],
        "features": {
          "object_format": "sha1",
          "filemode": true,
          "symlinks": true,
          "case_sensitive": true,
          "precompose_unicode": false,
          "sparse_checkout": false,
          "sparse_patterns_blob_id": null,
          "sparse_patterns_blob_descriptor_id": null,
          "required_filter_names": [],
          "lfs_required": false
        },
        "repo_relative_cwd": "src",
        "agent_project_config_paths": ["AGENTS.md"],
        "materialization_policy": "separate_worktree"
      },
      {
        "workspace_id": "0198f4c8-7d40-7e55-8e6f-2234567890ab",
        "kind": "managed_tree",
        "group_relative_path": "design-notes",
        "tree_identity": "relux/design-notes",
        "tree_manifest_id": "sha256:8dc15e881e026e7cf59482395baaa8c47341e6bad6d87f44312a9d0b360aacd5",
        "repo_relative_cwd": "drafts",
        "agent_project_config_paths": ["AGENTS.md"],
        "materialization_policy": "separate_copy"
      }
    ]
  },
  "provider_identity_record_id": null,
  "task_board_bundle_id": null,
  "excluded_classes": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:15:00.000Z",
  "extensions": {}
}
~~~

The <code>WS-GIT-ROUNDTRIP-1</code> fixture represented above has branch
<code>refs/heads/feature/ax</code>, a staged <code>README.md</code> blob OID
<code>sha1:19d9cc8584ac2c7dcf57d2680375e80f099dc481</code>, working bytes
<code>working\n</code>, untracked bytes <code>notes\n</code>, an initialized
detached submodule, cwd <code>src</code>, and project config
<code>AGENTS.md</code>. A round trip MUST reproduce all those facts, byte-for-
byte index semantics, and zero network fetch. The
<code>WS-TREE-ROUNDTRIP-1</code> member must reproduce <code>AGENTS.md</code>,
the <code>drafts</code> directory, <code>drafts/note.md</code>, its cwd, modes,
and policy. HEAD-only, index-only, or working-tree-only equality is a failure.

The submodule-pointer fixtures use the ordered triple
<code>(head_tree_gitlink_oid, GitSubmodule.gitlink_oid,
GitSubmodule.head.oid)</code>:

| Fixture | Relationship | Meaning/result |
| --- | --- | --- |
| <code>WS-SUBMODULE-CLEAN</code> | <code>(A,A,A)</code> | No staged or unstaged submodule pointer change |
| <code>WS-SUBMODULE-STAGED</code> | <code>(A,B,B)</code> | Parent index stages B while the child checkout matches the staged pointer |
| <code>WS-SUBMODULE-UNSTAGED</code> | <code>(A,A,B)</code> | Parent index remains A while the checked-out child moved to B |
| <code>WS-SUBMODULE-BOTH</code> | <code>(A,B,C)</code> | Staged pointer B and further unstaged child movement C are both preserved |

For every row, A is extracted as the mode-160000 entry from the superproject
HEAD tree that resolves in the isolated parent pack; A names a child commit but
that child commit object is not required or permitted merely to satisfy the
parent-pack closure. B and C MUST resolve as commits in the isolated child
pack. When A equals B or C, that equal OID is still object-resolved only in the
child repository. Capture and materialization MUST retain the exact triple and
MUST NOT normalize the index to the checked-out child or copy a child commit
into the parent object database.

Normative negative fixtures are:

| Fixture | Mutation | Required result |
| --- | --- | --- |
| <code>TM-ENTRY-DIR-N1</code> | Add <code>blob_id</code> to a directory | Reject unknown/forbidden variant member |
| <code>TM-ENTRY-FILE-N1</code> | Descriptor size differs from file size | <code>integrity_failure</code> |
| <code>TM-ENTRY-SYM-N1</code> | Target escapes with <code>../</code> | <code>unsafe_path</code> |
| <code>TM-ENTRY-HARD-N1</code> | Target is later or not a file | <code>incompatible_schema</code> |
| <code>TM-GIT-N1</code> | Omit raw index or logical entries | <code>incompatible_schema</code> |
| <code>TM-GIT-N2</code> | Set entry count to a different length or stage to 4 | <code>incompatible_schema</code> |
| <code>TM-GIT-N3</code> | Detached HEAD carries a ref | <code>incompatible_schema</code> |
| <code>TM-GIT-N4</code> | Working-tree manifest or project config is outside child closure | <code>integrity_failure</code> |
| <code>TM-GIT-N5</code> | Initialized submodule omits its recursive manifest | <code>incompatible_schema</code> |
| <code>TM-GIT-N6</code> | <code>gitlink_oid</code> differs from the parent stage-0 mode-160000 index entry | <code>integrity_failure</code> |
| <code>TM-GIT-N7</code> | Child HEAD is checked only after parent and child packs are co-mingled | Reject the validation evidence; each pack must pass in an isolated object database |
| <code>TM-TREE-N1</code> | Managed-tree member carries any Git field | Reject unknown/forbidden variant member |
| <code>TM-ROOT-N1</code> | Workspace root has entries or omits a member child | <code>incompatible_schema</code> |

An encoded identity-addressed JSON/CBOR object MUST NOT exceed 5,242,880 bytes.
A larger entry or index list MUST be partitioned into path-disjoint child
manifests; every child and root independently obey the size limit. Devices,
FIFOs, sockets, reparse points, alternate data streams, and unknown special
files are unsupported and MUST fail unless an explicit exclusion applies.

Mode preserves Unix executable and ordinary read/write bits. ACLs, ownership,
code-signing metadata, quarantine flags, arbitrary xattrs, NTFS alternate
streams, and resource forks are not portable in v0.2.0. If one is required for
a provider or workspace, that provider/platform cell MUST be conditional or
unsupported rather than silently dropping it.

### 10.5 Materialization Plan

Materialization Plan schema
<code>urn:ax:schema:materialization-plan</code> version <code>1.0.0</code> is
immutable and authorizes only the exact staged changes it lists. It is not an
ownership grant.

Its top-level object is closed and contains exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Materialization Plan schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>plan_id</code> | digest | Canonical object digest |
| <code>kind</code> | enum | <code>workspace</code>, <code>provider</code>, <code>task_board</code>, or <code>composite</code> |
| <code>intent</code> | enum | <code>passive_replica</code>, <code>owner_resume</code>, <code>ownership_transfer</code>, or <code>fork</code> |
| <code>subject_id</code> | UUIDv7 | Logical session for provider/task-board/composite; Workspace Group for workspace-only |
| <code>source_checkpoint_id</code> | digest | Validated immutable recovery base |
| <code>source_manifest_ids</code> | sorted unique digest[1..1024] | Complete source-checkpoint manifest/bundle inputs |
| <code>derived_manifest_ids</code> | sorted unique digest[0..1024] | Empty except for exact fork projections |
| <code>fork_projection</code> | Fork Workspace Projection or null | Non-null exactly for <code>intent = fork</code> |
| <code>prepared_for_host_id</code> | UUIDv7 | Only this allowlisted host may execute the plan |
| <code>source_lease_epoch</code> | uint53 | Greater than zero; exact source checkpoint lease |
| <code>source_lease_id</code> | UUIDv4 | Exact source checkpoint fencing token |
| <code>authorities</code> | RootAuthority[0..512] | Empty only for the provider backend-identity validation-only variant; otherwise closed destination-local roots defined below |
| <code>expected_prior_checkpoint_id</code> | digest or null | Null only when destination is classified absent or empty |
| <code>operations</code> | PlanOperation[0..65536] | Consecutive sequence beginning at 1 when non-empty |
| <code>exclusions</code> | sorted unique exclusion-class[0..128] | Exact capture/materialization policy classes |
| <code>validations</code> | sorted unique validation-name[1..6] | Required pre-commit checks from the closed registry below |
| <code>commit_strategy</code> | enum | <code>validation_only</code>, <code>atomic_directory_rename</code>, <code>atomic_file_merge</code>, <code>single_root_transaction</code>, or <code>two_phase_multi_root</code> |
| <code>rollback_required</code> | boolean | MUST be true in 1.0.0 |
| <code>created_by_host_id</code> | UUIDv7 | Plan author; normally destination host |
| <code>created_at</code> | timestamp | Diagnostic only |
| <code>extensions</code> | object | Reverse-DNS keys only |

<code>RootAuthority</code> is a closed tagged union, sorted by
<code>authority_id</code>. IDs use the Section 7.5 <code>root-id</code> grammar,
are unique in the plan, and are routing labels rather than cross-host
identities:

| Tag | Exact members |
| --- | --- |
| <code>kind = workspace</code> | <code>authority_id:root-id</code>, <code>kind:workspace</code>, <code>platform:macos&#124;linux&#124;wsl2&#124;windows</code>, <code>root_path:absolute-path</code>, <code>logical_root:string[1..64]</code>, <code>workspace_group_id:UUIDv7</code>, <code>write_policy:managed_replace&#124;managed_copy&#124;managed_worktree</code> |
| <code>kind = provider_store</code> | <code>authority_id:root-id</code>, <code>kind:provider_store</code>, <code>platform:macos&#124;linux&#124;wsl2&#124;windows</code>, <code>root_path:absolute-path</code>, <code>provider_id:provider-id</code>, <code>root_role:durable_store&#124;durable_index&#124;derived_cache</code>, <code>write_policy:managed_merge</code> |
| <code>kind = task_board_staging</code> | <code>authority_id:root-id</code>, <code>kind:task_board_staging</code>, <code>platform:macos&#124;linux&#124;wsl2&#124;windows</code>, <code>root_path:absolute-path</code>, <code>bridge_protocol_version:semver</code>, <code>staging_operation_id:UUIDv7</code>, <code>write_policy:staged_install</code> |

A workspace authority's logical root MUST exist in destination configuration,
its root path MUST equal that resolved mapping, and its group ID MUST equal the
referenced workspace manifest. A provider-store authority is valid only when
returned by the exact destination adapter's materialize plan and independently
accepted by the Section 7.5 root/exclusion checks. A task-board staging root
MUST be a fresh owner-only child of the resolved ax state root and MUST contain
no pre-existing manager state. Authorities MUST be pairwise path-disjoint;
neither a symlink nor a reparse point may make them overlap. Ax data, cache,
runtime, credential, authentication, SSH, and live manager roots are forbidden
except for the exact fresh task-board staging child.

<code>ForkWorkspaceProjection</code> is a closed object containing exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>projection_version</code> | enum | Literal <code>workspace_fork_v1</code> |
| <code>source_session_id</code> | UUIDv7 | Session whose checkpoint is the immutable source |
| <code>source_workspace_group_id</code> | UUIDv7 | Source group named by the checkpoint closure |
| <code>source_workspace_group_record_id</code> | digest | Exact source topology record |
| <code>source_workspace_manifest_id</code> | digest | Exact source workspace-group Transfer Manifest |
| <code>destination_session_id</code> | UUIDv7 | Newly allocated fork session |
| <code>destination_workspace_group_id</code> | UUIDv7 | Fresh group identity |
| <code>destination_workspace_group_record_id</code> | digest | Exact derived Workspace Group Record identity |
| <code>destination_display_name</code> | string[1..128] | New topology display name |
| <code>destination_created_by_host_id</code> | UUIDv7 | Destination record author |
| <code>destination_created_at</code> | timestamp | Destination record creation time |
| <code>destination_extensions</code> | object | Reverse-DNS Workspace Group Record extensions |
| <code>member_mappings</code> | ForkMemberMapping[1..256] | Sorted by source workspace ID; one-to-one and onto destination members |
| <code>manifest_mappings</code> | ForkManifestMapping[1..1024] | Sorted by source manifest ID; complete bottom-up re-identification map |

<code>ForkMemberMapping</code> contains exactly
<code>source_workspace_id:UUIDv7</code>,
<code>destination_workspace_id:UUIDv7</code>, and
<code>group_relative_path:path</code>. The relative path MUST equal the path in
both topology records; every destination ID is fresh and unique. The complete
destination Workspace Group Record is constructed with the fixed schema and
version, record/subject/group IDs from these projection fields, the displayed
name/creation/extensions fields, and the source record's member objects in
source workspace-ID order after replacing only each workspace ID according to
<code>member_mappings</code>. Its recomputed record ID MUST equal
<code>destination_workspace_group_record_id</code> before persistence.
<code>ForkManifestMapping</code> contains exactly
<code>kind:workspace_group|workspace_tree</code>,
<code>source_manifest_id:digest</code>,
<code>destination_manifest_id:digest</code>,
<code>source_subject_id:UUIDv7</code>, and
<code>destination_subject_id:UUIDv7</code>. Ax derives a destination manifest
by copying every non-identity field, entry, descriptor, and blob reference from
the source; replacing the subject, group, member, and child-manifest identities
according to the two maps; and recomputing child identities before parent
identities. It MUST persist the destination topology and all destination
manifests before publishing the fork Session Record. Source objects and bytes
remain unchanged. <code>derived_manifest_ids</code> MUST equal exactly the
destination IDs in <code>manifest_mappings</code> and MUST NOT occur in
<code>source_manifest_ids</code>.

The following table is the complete major-v1 plan-kind tagged-union contract.
Anything not explicitly allowed in its row is forbidden:

| <code>kind</code> | Subject and source inputs | Required authority/action set | Required validations | Legal commit strategies |
| --- | --- | --- | --- | --- |
| <code>workspace</code> | Subject is the destination Workspace Group. Exactly one workspace-group Transfer Manifest, plus its closed child manifests, is selected from <code>source_manifest_ids</code> or, for a fork, <code>derived_manifest_ids</code>. | One or more <code>workspace</code> authorities; only <code>install_workspace_group</code>, <code>install_workspace_tree</code>, <code>delete_managed_path</code>, or <code>replace_managed_replica</code>. At least one install operation is required. | Exactly <code>manifest_closure</code> and <code>workspace_state</code> | <code>atomic_directory_rename</code> for one directory boundary; <code>atomic_file_merge</code> for one authority with file boundaries only; otherwise <code>two_phase_multi_root</code> |
| <code>provider</code> | Subject is one Session. Exactly one provider Transfer Manifest is selected. A backend-resolved provider with <code>portable_store=false</code> uses the required zero-entry provider manifest that references its Provider Identity Record. | For a portable store, one or more <code>provider_store</code> authorities and only <code>merge_provider_store</code>. For a backend-resolved identity, no authorities and no operations. | <code>manifest_closure</code> plus exactly one of <code>provider_native_discovery</code> or <code>backend_identity</code> | <code>validation_only</code> only for the zero-operation backend path; <code>atomic_file_merge</code> for file boundaries; <code>single_root_transaction</code> for one provider-store authority with any directory boundary; otherwise <code>two_phase_multi_root</code> |
| <code>task_board</code> | Subject is one Session. Exactly one Task-board Bundle is selected. | Exactly one <code>task_board_staging</code> authority and exactly one <code>install_task_board_bundle</code> operation at <code>authority_root</code>. | <code>manifest_closure</code>, <code>task_board_bundle</code>, and <code>task_board_validate</code> exactly when the projected board kind is <code>local</code> | <code>single_root_transaction</code> |
| <code>composite</code> | Subject is one Session. Exactly one workspace-group manifest and exactly one provider manifest or Task-board Bundle are selected; never both provider and task-board branches. Fork-derived workspace manifests are allowed only with <code>intent=fork</code>. | The disjoint union of the corresponding workspace row and exactly one provider or task-board row. | Exact union of the component rows | <code>two_phase_multi_root</code> when both components mutate; when the provider component is <code>validation_only</code>, use the workspace row's one-root strategy because only workspace bytes mutate |

<code>intent=fork</code> requires non-null <code>fork_projection</code> and a
non-empty <code>derived_manifest_ids</code>; every other intent requires null
and an empty array. For a fork plan, <code>subject_id</code> is the destination
session for provider, task-board, or composite kinds and is the destination
group for workspace kind. A plan MUST reject a source ID that is not in the
validated checkpoint closure, a derived ID that is not produced by the exact
projection, or an authority/action/validation/strategy combination outside its
row.

Despite the historical member name, <code>source_manifest_ids</code> contains
Task-board Bundle IDs directly in the task-board row; it never contains raw
blob IDs, Provider Identity Record IDs, or Materialization Plan IDs. The kind
row and Checkpoint field determine each ID's schema unambiguously.

~~~json
{
  "schema": "urn:ax:schema:materialization-plan",
  "schema_version": "1.0.0",
  "plan_id": "sha256:64644a5ad573d36c0c13f44f56ef25ab93cff33001ff2a3371b082603910f2dd",
  "kind": "composite",
  "intent": "ownership_transfer",
  "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "source_checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "source_manifest_ids": [
    "sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91",
    "sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e"
  ],
  "derived_manifest_ids": [],
  "fork_projection": null,
  "prepared_for_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "source_lease_epoch": 4,
  "source_lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "authorities": [
    {
      "authority_id": "codex_sessions",
      "kind": "provider_store",
      "platform": "linux",
      "root_path": "/home/ivan/.codex/sessions",
      "provider_id": "codex",
      "root_role": "durable_store",
      "write_policy": "managed_merge"
    },
    {
      "authority_id": "workspace_relux",
      "kind": "workspace",
      "platform": "linux",
      "root_path": "/srv/relux",
      "logical_root": "relux",
      "workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
      "write_policy": "managed_replace"
    }
  ],
  "expected_prior_checkpoint_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "operations": [
    {
      "sequence": 1,
      "action": "install_workspace_group",
      "authority_id": "workspace_relux",
      "target_relative_path": "payments",
      "input_id": "sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e",
      "expected_prior_digest": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
      "atomicity_boundary": "target_directory"
    },
    {
      "sequence": 2,
      "action": "merge_provider_store",
      "authority_id": "codex_sessions",
      "target_relative_path": "11111111-2222-4333-8444-555555555555",
      "input_id": "sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91",
      "expected_prior_digest": null,
      "atomicity_boundary": "target_directory"
    }
  ],
  "exclusions": [
    "credential",
    "live_pid",
    "machine_auth",
    "socket",
    "transient_lock"
  ],
  "validations": [
    "manifest_closure",
    "provider_native_discovery",
    "workspace_state"
  ],
  "commit_strategy": "two_phase_multi_root",
  "rollback_required": true,
  "created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "created_at": "2026-08-19T04:11:00.000Z",
  "extensions": {}
}
~~~

Operations are ordered by unique consecutive integers and use typed actions,
never shell strings. Each operation is closed and contains exactly
<code>sequence:uint53&gt;0</code>,
<code>action:install_workspace_group|install_workspace_tree|merge_provider_store|install_task_board_bundle|delete_managed_path|replace_managed_replica</code>,
<code>authority_id:root-id</code>, <code>target_relative_path:path|null</code>,
<code>input_id:digest</code>, <code>expected_prior_digest:digest|null</code>,
and
<code>atomicity_boundary:target_file|target_directory|authority_root</code>. The
authority MUST exist, and the resolved target MUST remain beneath it after
filesystem resolution. <code>target_file</code> authorizes one regular-file
rename; <code>target_directory</code> authorizes one exact directory subtree;
<code>authority_root</code> is permitted only for a fresh
<code>task_board_staging</code> authority and never for workspace or provider
roots. <code>target_relative_path</code> MUST be null exactly for an
<code>authority_root</code> operation and non-null otherwise; the forbidden
relative-path spelling <code>.</code> is never a root sentinel. A
<code>delete_managed_path</code> uses the Tombstone ID as input and requires the
target entry digest; <code>replace_managed_replica</code> uses its Tombstone ID
and requires the predecessor checkpoint. Neither action authorizes a broader
path. Install/merge operations use the exact Transfer Manifest or Task-board
Bundle ID named in <code>source_manifest_ids</code>, except that a fork
workspace install uses the destination manifest ID named in
<code>derived_manifest_ids</code>. Their prior digest is null
only for a new path and otherwise names the exact managed entry being replaced.
<code>install_workspace_group</code> requires a <code>workspace_group</code>
manifest and targets its group root; <code>install_workspace_tree</code> requires
one member/partition <code>workspace_tree</code> manifest and may run only as a
path-disjoint child of the group operation.

An operation's expected predecessor is null only after the exact target has
been classified absent or empty. Otherwise it is the JCS entry digest for a
file/symlink/hardlink target, the Transfer Manifest ID for a managed directory,
the prior provider-store target digest supplied by the adapter, or the prior
bundle/staging digest. The materializer MUST rehash that predecessor
immediately before its first rename. A mismatch fails before mutation.

The validation-name registry is <code>backend_identity</code>,
<code>manifest_closure</code>, <code>provider_native_discovery</code>,
<code>task_board_bundle</code>, <code>task_board_validate</code>, and
<code>workspace_state</code>. Values are bytewise sorted and every validation
applicable to the plan kind/path MUST be present. An unknown validation name is
not a forward-compatible no-op under major version 1.
<code>atomic_directory_rename</code> requires one workspace target-directory
operation; <code>atomic_file_merge</code> requires one authority and only
target-file operations. <code>validation_only</code> requires a provider plan,
zero authorities, zero operations, <code>backend_identity</code>, and a provider
identity that the destination account realm resolves without creating a new
session. <code>single_root_transaction</code> requires exactly one provider-store
or task-board-staging authority, at least one operation, a durable rollback
backup made before the first visible mutation, and a single filesystem
transaction boundary controlled by the provider or bridge coordinator.
<code>two_phase_multi_root</code> requires two or more
authorities or atomicity boundaries and a rollback backup for every operation
before the first visible rename. It is crash-consistent but not a claim of one
cross-filesystem atomic primitive. A receiver MUST reject a plan for another host,
checkpoint, logical root mapping, expected prior checkpoint, or source fencing
token. Provider <code>native-store-plan</code> returns this schema with optional
namespaced provider extensions only inside the displayed
<code>extensions</code> member.

The composite example is the normative
<code>PROVIDER-PLAN-MATERIALIZE-POS</code> cross-host fixture: the destination
workspace and Linux Codex native store have separate authorities, every
operation names one root and boundary, and no source absolute path occurs.
<code>PLAN-AUTH-N1</code> changes the provider operation to
<code>authority_id = workspace_relux</code>, <code>PLAN-AUTH-N2</code> changes
its target to <code>../sessions</code>, <code>PLAN-AUTH-N3</code> uses
<code>authority_root</code> for the provider store, and
<code>PLAN-AUTH-N4</code> aliases the provider root through a symlink into the
workspace. Each MUST fail before destination mutation.

The following three complete objects, together with the composite object above,
are the normative positive plans for all four tags. They exercise a one-root
workspace rename, a one-root provider transaction, and a one-root task-board
transaction respectively. The <code>jsonc</code> fence label distinguishes this
multi-fixture corpus from the single worked JSON example; the bytes contain
strict JSON with no comments and MUST be parsed and identity-checked as JSON:

~~~jsonc
{
  "schema": "urn:ax:schema:materialization-plan",
  "schema_version": "1.0.0",
  "plan_id": "sha256:92c6ba78820d5d5bcf4b5acd3c46cd7562c8414c452d0142bc368935c79b40e3",
  "kind": "workspace",
  "intent": "passive_replica",
  "subject_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "source_checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "source_manifest_ids": ["sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e"],
  "derived_manifest_ids": [],
  "fork_projection": null,
  "prepared_for_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "source_lease_epoch": 4,
  "source_lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "authorities": [{"authority_id":"workspace_relux","kind":"workspace","platform":"linux","root_path":"/srv/relux","logical_root":"relux","workspace_group_id":"0198f4c8-5b20-7c33-8c4d-1234567890ab","write_policy":"managed_copy"}],
  "expected_prior_checkpoint_id": null,
  "operations": [{"sequence":1,"action":"install_workspace_group","authority_id":"workspace_relux","target_relative_path":"payments-copy","input_id":"sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e","expected_prior_digest":null,"atomicity_boundary":"target_directory"}],
  "exclusions": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "validations": ["manifest_closure","workspace_state"],
  "commit_strategy": "atomic_directory_rename",
  "rollback_required": true,
  "created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "created_at": "2026-08-19T04:11:01.000Z",
  "extensions": {}
}
~~~

The task-board plan uses this complete task-board checkpoint rather than the
direct checkpoint worked example. Its <code>jsonc</code> fence is likewise
strict JSON and part of the identity fixture corpus:

~~~jsonc
{
  "schema": "urn:ax:schema:checkpoint",
  "schema_version": "1.0.0",
  "checkpoint_id": "sha256:59c2b9bd739552dc011bc956cbee83990a8ccbb4beb6ed2a230d77108f98e888",
  "subject_id": "0198f4c8-7a10-7b22-8b3c-2234567890ab",
  "session_id": "0198f4c8-7a10-7b22-8b3c-2234567890ab",
  "lease_epoch": 4,
  "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "safe_boundary": {
    "provider_id": "codex",
    "provider_version": "0.147.0",
    "evidence": "task_board_bridge",
    "input_blocked": true,
    "foreground_idle": true,
    "background_idle": true,
    "open_processes": 0,
    "open_database_handles": 0
  },
  "event_heads": ["sha256:8888888888888888888888888888888888888888888888888888888888888888"],
  "workspace_manifest_id": "sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e",
  "provider_manifest_id": null,
  "task_board_bundle_id": "sha256:0af7b44e7063375a0f06e546fd820438c72607f191c14be78d35c8ffa109844f",
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:10:01.000Z",
  "status": "validated",
  "extensions": {}
}
~~~

~~~jsonc
{
  "schema": "urn:ax:schema:materialization-plan",
  "schema_version": "1.0.0",
  "plan_id": "sha256:ea575ef12269a052bbbb4975daf080beeb2bb51f26cd7d0491e035a8b4499aeb",
  "kind": "provider",
  "intent": "owner_resume",
  "subject_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "source_checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "source_manifest_ids": ["sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91"],
  "derived_manifest_ids": [],
  "fork_projection": null,
  "prepared_for_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "source_lease_epoch": 4,
  "source_lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "authorities": [{"authority_id":"codex_sessions","kind":"provider_store","platform":"linux","root_path":"/home/ivan/.codex/sessions","provider_id":"codex","root_role":"durable_store","write_policy":"managed_merge"}],
  "expected_prior_checkpoint_id": null,
  "operations": [{"sequence":1,"action":"merge_provider_store","authority_id":"codex_sessions","target_relative_path":"11111111-2222-4333-8444-555555555555","input_id":"sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91","expected_prior_digest":null,"atomicity_boundary":"target_directory"}],
  "exclusions": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "validations": ["manifest_closure","provider_native_discovery"],
  "commit_strategy": "single_root_transaction",
  "rollback_required": true,
  "created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "created_at": "2026-08-19T04:11:02.000Z",
  "extensions": {}
}
~~~

~~~jsonc
{
  "schema": "urn:ax:schema:materialization-plan",
  "schema_version": "1.0.0",
  "plan_id": "sha256:19bab2d797f2914ee4d452310e0a1a1d280859bf099e193bb5f1ccf2ebbb394f",
  "kind": "task_board",
  "intent": "ownership_transfer",
  "subject_id": "0198f4c8-7a10-7b22-8b3c-2234567890ab",
  "source_checkpoint_id": "sha256:59c2b9bd739552dc011bc956cbee83990a8ccbb4beb6ed2a230d77108f98e888",
  "source_manifest_ids": ["sha256:0af7b44e7063375a0f06e546fd820438c72607f191c14be78d35c8ffa109844f"],
  "derived_manifest_ids": [],
  "fork_projection": null,
  "prepared_for_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "source_lease_epoch": 4,
  "source_lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "authorities": [{"authority_id":"task_board_stage","kind":"task_board_staging","platform":"linux","root_path":"/home/ivan/.local/state/ax/task-board-staging/0198f4c8-f5c0-76dd-9677-1234567890ab","bridge_protocol_version":"1.0.0","staging_operation_id":"0198f4c8-f5c0-76dd-9677-1234567890ab","write_policy":"staged_install"}],
  "expected_prior_checkpoint_id": null,
  "operations": [{"sequence":1,"action":"install_task_board_bundle","authority_id":"task_board_stage","target_relative_path":null,"input_id":"sha256:0af7b44e7063375a0f06e546fd820438c72607f191c14be78d35c8ffa109844f","expected_prior_digest":null,"atomicity_boundary":"authority_root"}],
  "exclusions": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "validations": ["manifest_closure","task_board_bundle","task_board_validate"],
  "commit_strategy": "single_root_transaction",
  "rollback_required": true,
  "created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "created_at": "2026-08-19T04:11:03.000Z",
  "extensions": {}
}
~~~

The complete negative-plan fixture family is defined by the following four
objects. Their otherwise valid IDs are recomputed over the displayed invalid
content so rejection is caused by the stated tagged-union violation, not by an
identity mismatch:

~~~jsonc
[
  {
    "schema":"urn:ax:schema:materialization-plan","schema_version":"1.0.0","plan_id":"sha256:158f1dedc6711daacee7b9b6d777aea201d2e8cf9df351593f2ada793e8908e5","kind":"workspace","intent":"passive_replica","subject_id":"0198f4c8-5b20-7c33-8c4d-1234567890ab","source_checkpoint_id":"sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656","source_manifest_ids":["sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e"],"derived_manifest_ids":[],"fork_projection":null,"prepared_for_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","source_lease_epoch":4,"source_lease_id":"aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee","authorities":[{"authority_id":"wrong_provider_root","kind":"provider_store","platform":"linux","root_path":"/home/ivan/.codex/sessions","provider_id":"codex","root_role":"durable_store","write_policy":"managed_merge"}],"expected_prior_checkpoint_id":null,"operations":[{"sequence":1,"action":"merge_provider_store","authority_id":"wrong_provider_root","target_relative_path":"x","input_id":"sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e","expected_prior_digest":null,"atomicity_boundary":"target_directory"}],"exclusions":["credential"],"validations":["manifest_closure","workspace_state"],"commit_strategy":"single_root_transaction","rollback_required":true,"created_by_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","created_at":"2026-08-19T04:11:11.000Z","extensions":{}
  },
  {
    "schema":"urn:ax:schema:materialization-plan","schema_version":"1.0.0","plan_id":"sha256:2375ef0e79cd48c9d649c64f0d5e91ffb1d31db083ef711a40db3f753414d9d5","kind":"provider","intent":"owner_resume","subject_id":"0198f4c8-3e70-7a11-8a2b-1234567890ab","source_checkpoint_id":"sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656","source_manifest_ids":["sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91"],"derived_manifest_ids":[],"fork_projection":null,"prepared_for_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","source_lease_epoch":4,"source_lease_id":"aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee","authorities":[{"authority_id":"codex_sessions","kind":"provider_store","platform":"linux","root_path":"/home/ivan/.codex/sessions","provider_id":"codex","root_role":"durable_store","write_policy":"managed_merge"}],"expected_prior_checkpoint_id":null,"operations":[{"sequence":1,"action":"install_task_board_bundle","authority_id":"codex_sessions","target_relative_path":"x","input_id":"sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91","expected_prior_digest":null,"atomicity_boundary":"target_directory"}],"exclusions":["credential"],"validations":["manifest_closure","provider_native_discovery"],"commit_strategy":"single_root_transaction","rollback_required":true,"created_by_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","created_at":"2026-08-19T04:11:12.000Z","extensions":{}
  },
  {
    "schema":"urn:ax:schema:materialization-plan","schema_version":"1.0.0","plan_id":"sha256:48cf7b467984dc7a9a73c0462682ebc022e072adf131128dca503cf1885587f9","kind":"task_board","intent":"passive_replica","subject_id":"0198f4c8-7a10-7b22-8b3c-2234567890ab","source_checkpoint_id":"sha256:59c2b9bd739552dc011bc956cbee83990a8ccbb4beb6ed2a230d77108f98e888","source_manifest_ids":["sha256:0af7b44e7063375a0f06e546fd820438c72607f191c14be78d35c8ffa109844f"],"derived_manifest_ids":[],"fork_projection":null,"prepared_for_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","source_lease_epoch":4,"source_lease_id":"aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee","authorities":[{"authority_id":"task_board_stage","kind":"task_board_staging","platform":"linux","root_path":"/home/ivan/.local/state/ax/task-board-staging/0198f4c8-f5c0-76dd-9677-1234567890ab","bridge_protocol_version":"1.0.0","staging_operation_id":"0198f4c8-f5c0-76dd-9677-1234567890ab","write_policy":"staged_install"}],"expected_prior_checkpoint_id":null,"operations":[],"exclusions":["credential"],"validations":["manifest_closure","task_board_bundle","task_board_validate"],"commit_strategy":"validation_only","rollback_required":true,"created_by_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","created_at":"2026-08-19T04:11:13.000Z","extensions":{}
  },
  {
    "schema":"urn:ax:schema:materialization-plan","schema_version":"1.0.0","plan_id":"sha256:b7273e360271666a61249b1c96f56dcf84c770d965f495ff80617e0ebb5da890","kind":"composite","intent":"ownership_transfer","subject_id":"0198f4c8-3e70-7a11-8a2b-1234567890ab","source_checkpoint_id":"sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656","source_manifest_ids":["sha256:0af7b44e7063375a0f06e546fd820438c72607f191c14be78d35c8ffa109844f","sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91","sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e"],"derived_manifest_ids":[],"fork_projection":null,"prepared_for_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","source_lease_epoch":4,"source_lease_id":"aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee","authorities":[{"authority_id":"workspace_relux","kind":"workspace","platform":"linux","root_path":"/srv/relux","logical_root":"relux","workspace_group_id":"0198f4c8-5b20-7c33-8c4d-1234567890ab","write_policy":"managed_replace"}],"expected_prior_checkpoint_id":null,"operations":[{"sequence":1,"action":"install_workspace_group","authority_id":"workspace_relux","target_relative_path":"payments","input_id":"sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e","expected_prior_digest":null,"atomicity_boundary":"target_directory"}],"exclusions":["credential"],"validations":["manifest_closure","workspace_state"],"commit_strategy":"atomic_directory_rename","rollback_required":true,"created_by_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","created_at":"2026-08-19T04:11:14.000Z","extensions":{}
  }
]
~~~

These are respectively <code>PLAN-WORKSPACE-AUTHORITY-N1</code>
(provider authority/action in a workspace plan),
<code>PLAN-PROVIDER-ACTION-N1</code> (task-board action in a provider plan),
<code>PLAN-TASK-BOARD-STRATEGY-N1</code> (missing install and illegal
validation-only strategy), and <code>PLAN-COMPOSITE-SOURCE-N1</code> (both
provider and task-board inputs but only a workspace component). Each MUST be
rejected before staging, even though its content identity is valid.

The positive task-board authority fragment is:

~~~json
{
  "authority_id": "task_board_stage",
  "kind": "task_board_staging",
  "platform": "linux",
  "root_path": "/home/ivan/.local/state/ax/task-board-staging/0198f4c8-f5c0-76dd-9677-1234567890ab",
  "bridge_protocol_version": "1.0.0",
  "staging_operation_id": "0198f4c8-f5c0-76dd-9677-1234567890ab",
  "write_policy": "staged_install"
}
~~~

### 10.6 Materialization Journal

Materialization Journal schema
<code>urn:ax:schema:materialization-journal</code> version
<code>2.0.0</code> is a two-variant machine-local recovery contract. Both the
mutable journal and immutable managed-replica marker MUST NOT be replicated.
The journal top-level object is closed and contains exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Materialization Journal schema identifier |
| <code>schema_version</code> | semver | Exact <code>2.0.0</code> |
| <code>document_kind</code> | enum | Literal <code>journal</code> |
| <code>materialization_id</code> | UUIDv7 | Stable across retries |
| <code>prepare_operation_id</code> | UUIDv7 | Caller-stable Mesh RPC prepare idempotency key, allocated with the materialization ID before the first request |
| <code>prepare_request_digest</code> | digest | SHA-256 of the complete canonical <code>materialize.prepare</code> request body, including both caller-stable IDs |
| <code>transfer_id</code> | UUIDv7 or null | Null when all inputs already exist locally |
| <code>plan_id</code> | digest | Exact Materialization Plan |
| <code>source_checkpoint_id</code> | digest | Validated source checkpoint |
| <code>managed_replica_id</code> | UUIDv7 or null | Non-null when workspace bytes participate |
| <code>authority_states</code> | map(root-id,Authority Journal State)[0..512] | Exactly one entry per plan RootAuthority; empty only for validation-only provider plan |
| <code>expected_prior_checkpoint_id</code> | digest or null | Null only for absent/empty destination |
| <code>completed_blob_chunks</code> | map(digest,sorted unique uint32[0..32768])[0..65536] | Chunk indexes keyed by their Blob ID; sufficient for the maximum file/blob cardinality of one committed transfer closure |
| <code>verified_blob_ids</code> | sorted unique digest[0..65536] | Whole-blob verification, not chunk presence; sufficient for the maximum file/blob cardinality of one committed transfer closure |
| <code>phase</code> | enum | <code>staging</code>, <code>validating</code>, <code>prepared</code>, <code>committing</code>, <code>rolling_back</code>, <code>rolled_back</code>, <code>committed</code>, or <code>failed</code> |
| <code>provider_transaction</code> | Provider Journal Transaction or null | Non-null only when a provider plugin participates |
| <code>task_board_transaction</code> | Task-board Journal Transaction or null | Non-null only when the task-board bridge participates |
| <code>destination_marker_id</code> | digest or null | Managed-replica marker; non-null in committed workspace/composite transactions |
| <code>last_error</code> | Structured Error or null | Redacted exact Section 15.1 object |
| <code>started_at</code> | timestamp | First durable journal write |
| <code>updated_at</code> | timestamp | Latest durable transition, not authority |
| <code>extensions</code> | object | Reverse-DNS machine-local extensions only |

Provider Journal Transaction is a closed object containing exactly
<code>operation_id:UUIDv7</code>, <code>transaction_id:UUIDv7</code>,
<code>state:unknown|prepared|committed|rolled_back</code>,
<code>rollback_token:base64url-256+|null</code>,
<code>transaction_authority:ProviderTransactionAuthority</code>, and
<code>last_status_at:timestamp</code>. Prepared requires a non-null token;
every other state requires null. The token and transaction root are
machine-local and MUST be redacted from ordinary logs. The authority's
materialization, provider, transaction, and plan IDs MUST equal the journal and
referenced plan; its root is the only path passed to later plugin processes.

Task-board Journal Transaction is a closed object containing exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>bundle_id</code> | digest | Exact Task-board Bundle installed by the plan |
| <code>activation_mode</code> | enum | <code>dormant_replica</code>, <code>owner_resume</code>, <code>ownership_transfer</code>, or <code>fork</code> |
| <code>import_operation_id</code> | UUIDv7 | Stable bridge import key allocated before import |
| <code>open_operation_id</code> | UUIDv7 | Stable bridge open key allocated before open |
| <code>adopt_operation_id</code> | UUIDv7 | Stable bridge adopt key allocated before adopt |
| <code>resume_operation_id</code> | UUIDv7 | Stable bridge resume key allocated before resume |
| <code>state</code> | enum | <code>not_started</code>, <code>imported</code>, <code>opened</code>, <code>adopted</code>, <code>resumed</code>, <code>dormant_finalized</code>, <code>rolled_back</code>, or <code>failed</code> |
| <code>import_token</code> | base64url-256+ or null | Owner-only bridge token; non-null exactly in <code>imported</code> and consumed by <code>open</code> |
| <code>staged_manager_ref</code> | string[1..512] or null | Non-null exactly in <code>imported</code> and consumed by <code>open</code> |
| <code>import_expires_at</code> | timestamp or null | Non-null exactly while import token is usable |
| <code>open_token</code> | base64url-256+ or null | Owner-only bridge token; non-null from opened until adopt or dormant finalization |
| <code>dormant_manager_ref</code> | string[1..512] or null | Non-null in <code>opened</code> and <code>dormant_finalized</code>; consumed and replaced by <code>manager_session_ref</code> on adopt |
| <code>open_expires_at</code> | timestamp or null | Non-null exactly while open token is usable |
| <code>manager_session_ref</code> | string[1..512] or null | Non-null after successful adopt |
| <code>ax_binding</code> | Ax Binding or null | Non-null after successful adopt |
| <code>last_bridge_state</code> | enum or null | <code>dormant</code>, <code>quiesced</code>, <code>stopped</code>, <code>running</code>, <code>idle</code>, or <code>failed</code> |
| <code>last_status_at</code> | timestamp or null | Time of last bridge status reconciliation |
| <code>cleanup_state</code> | enum | <code>not_started</code>, <code>pending_expiry</code>, <code>retained_active</code>, or <code>removed</code> |
| <code>cleanup_after</code> | timestamp or null | Non-null only for dormant finalized state; copied from the last open expiry |

Ax Binding is the exact closed bridge shape
<code>{ax_session_id:UUIDv7, lease_epoch:uint53&gt;0, lease_id:UUIDv4}</code>.
The four operation IDs are allocated once with the materialization ID and MUST
survive process restart. A retry MUST use the same operation ID and byte-equal
body. Tokens and manager references are local recovery capabilities: they MUST
be encrypted with the platform credential facility when available, owner-only
at rest otherwise, redacted from ordinary logs, excluded from replication, and
never returned by Mesh RPC.

The null/state invariants are exact. <code>not_started</code> has all tokens and
references null. <code>imported</code> has import token, staged reference, and
import expiry only. <code>opened</code> has open token, dormant reference, and
open expiry only. <code>adopted</code> and <code>resumed</code> have manager
reference and binding only; their cleanup state is
<code>retained_active</code>. <code>dormant_finalized</code> has dormant
reference only, no usable token, bridge state <code>dormant</code>, and cleanup
state <code>pending_expiry</code> with non-null <code>cleanup_after</code> equal
to the consumed open expiry. Every other state requires
<code>cleanup_after = null</code>. <code>rolled_back</code> has no token or
reference and cleanup state <code>removed</code>. <code>failed</code> preserves
only the still-valid token/reference pair needed for deterministic status or
expiry recovery; <code>last_error</code> explains the failure.

Authority Journal State is a closed object containing exactly
<code>root_path:absolute-path</code>,
<code>completed_sequences:sorted unique uint53[0..65536]</code>,
<code>observed_prior_digest:digest|null</code>,
<code>rollback_root:absolute-path|null</code>, and
<code>state:staging|prepared|committed|rolled_back</code>. The root path MUST
equal its plan authority; completed sequences contain only operations naming
that authority. Prepared requires a non-null rollback root, committed and
rolled-back require null after cleanup, and staging permits null only before
the first target backup exists. The observed prior digest equals every
non-null operation predecessor for a one-target authority; an authority with
multiple distinct predecessors uses null here and each operation backup stores
its own digest under the rollback root. For a provider-store authority, the
rollback root MUST equal
<code>ProviderTransactionAuthority.root_path/backups/&lt;authority-id&gt;</code>;
the host journal references the plugin backup and MUST NOT allocate a second
provider backup location.

After a crash, <code>ax</code> MUST resume a valid staging transaction or roll
it back. It MUST NOT guess whether an incomplete commit succeeded; it MUST
reconcile the journal, destination marker, and manifest digest.

Normative example:

~~~json
{
  "schema": "urn:ax:schema:materialization-journal",
  "schema_version": "2.0.0",
  "document_kind": "journal",
  "materialization_id": "0198f4c8-c290-73aa-9374-1234567890ab",
  "prepare_operation_id": "0198f4c8-b180-72cc-9271-1234567890ab",
  "prepare_request_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "transfer_id": "0198f4c8-d3a0-74bb-9475-1234567890ab",
  "plan_id": "sha256:64644a5ad573d36c0c13f44f56ef25ab93cff33001ff2a3371b082603910f2dd",
  "source_checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "managed_replica_id": "0198f4c8-8e50-7f66-8f70-2234567890ab",
  "authority_states": {
    "codex_sessions": {
      "root_path": "/home/ivan/.codex/sessions",
      "completed_sequences": [2],
      "observed_prior_digest": null,
      "rollback_root": "/home/ivan/.local/state/ax/provider-transactions/codex/0198f4c8-f5c0-76dd-9677-1234567890ab/backups/codex_sessions",
      "state": "prepared"
    },
    "workspace_relux": {
      "root_path": "/srv/relux",
      "completed_sequences": [1],
      "observed_prior_digest": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
      "rollback_root": "/home/ivan/.local/state/ax/materializations/0198f4c8-c290-73aa-9374-1234567890ab/workspace_relux",
      "state": "prepared"
    }
  },
  "expected_prior_checkpoint_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "completed_blob_chunks": {
    "sha256:0e442b07e3772e8f5622478242ddf5f9f197bbd6a0402cd71471db4081abb291": [0],
    "sha256:444e0fffbd825e9610ff5b199485707a0c895339ae80c15cc8a8aee41b106fda": [0]
  },
  "verified_blob_ids": [
    "sha256:0e442b07e3772e8f5622478242ddf5f9f197bbd6a0402cd71471db4081abb291",
    "sha256:444e0fffbd825e9610ff5b199485707a0c895339ae80c15cc8a8aee41b106fda"
  ],
  "phase": "prepared",
  "provider_transaction": {
    "operation_id": "0198f4c8-e4b0-75cc-9576-1234567890ab",
    "transaction_id": "0198f4c8-f5c0-76dd-9677-1234567890ab",
    "state": "prepared",
    "rollback_token": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5QUI",
    "transaction_authority": {
      "authority_id": "provider_transaction",
      "kind": "provider_transaction",
      "root_path": "/home/ivan/.local/state/ax/provider-transactions/codex/0198f4c8-f5c0-76dd-9677-1234567890ab",
      "layout": "provider_transaction_v1",
      "access": "read_write",
      "materialization_id": "0198f4c8-c290-73aa-9374-1234567890ab",
      "provider_id": "codex",
      "transaction_id": "0198f4c8-f5c0-76dd-9677-1234567890ab",
      "plan_id": "sha256:64644a5ad573d36c0c13f44f56ef25ab93cff33001ff2a3371b082603910f2dd",
      "same_filesystem_provider_authority_ids": ["codex_sessions"]
    },
    "last_status_at": "2026-08-19T04:12:10.000Z"
  },
  "task_board_transaction": null,
  "destination_marker_id": null,
  "last_error": null,
  "started_at": "2026-08-19T04:12:00.000Z",
  "updated_at": "2026-08-19T04:12:10.000Z",
  "extensions": {}
}
~~~

The two map members above are the normative
<code>MJ-MULTIBLOB-POS</code> fixture: chunk zero for two different blobs is two
independent facts. A flat <code>[0]</code> list is not a valid journal shape.
Crash recovery fixtures are:

| Fixture | Durable facts after restart | Required recovery |
| --- | --- | --- |
| <code>MJ-CRASH-STAGE</code> | Some per-blob chunk sets, no verified whole blob | Request only absent indexes; never mark another blob's equal index present |
| <code>MJ-RPC-PREPARE-LOST</code> | The destination journal and prepare receipt exist, but the Mesh RPC response was lost | Retry <code>materialize.prepare</code> with the caller-retained operation/materialization IDs and identical body; return the recorded result and create no second journal, authority, replica, plan, or bridge ID |
| <code>MJ-CRASH-PREPARE-LOST</code> | Provider call may have prepared but response was lost | Call <code>materialize-status</code> with the same IDs; persist returned prepared token before any commit/rollback |
| <code>MJ-CRASH-COMMIT-LOST</code> | Journal says committing | Status <code>committed</code> plus exact destination marker commits the journal; prepared rolls back or retries commit; unknown fails closed |
| <code>MJ-CRASH-ROLLBACK-LOST</code> | Journal says rolling_back | Status <code>rolled_back</code> plus restored predecessor closes recovery; prepared retries rollback; unknown fails closed |
| <code>MJ-CRASH-MARKER-MISMATCH</code> | Plugin says committed but destination marker/plan differs | <code>integrity_failure</code>; quarantine transaction and mutate nothing further |

The following embedded value is the normative
<code>MJ-TASK-BOARD-OPENED-POS</code> fixture. It is persisted in
<code>task_board_transaction</code> before <code>materialize.commit</code>
returns <code>prepared</code>:

~~~json
{
  "bundle_id": "sha256:0af7b44e7063375a0f06e546fd820438c72607f191c14be78d35c8ffa109844f",
  "activation_mode": "ownership_transfer",
  "import_operation_id": "0198f4c8-0a10-71aa-8111-1234567890ab",
  "open_operation_id": "0198f4c8-0a20-72bb-8222-1234567890ab",
  "adopt_operation_id": "0198f4c8-0a30-73cc-8333-1234567890ab",
  "resume_operation_id": "0198f4c8-0a40-74dd-8444-1234567890ab",
  "state": "opened",
  "import_token": null,
  "staged_manager_ref": null,
  "import_expires_at": null,
  "open_token": "b3duZXItb25seS1vcGVuLXRva2VuLTAxMjM0NTY3ODlhYmNkZWY",
  "dormant_manager_ref": "tbm:dormant:0198f4c8-7a10-7b22-8b3c-2234567890ab",
  "open_expires_at": "2026-08-19T04:22:10.000Z",
  "manager_session_ref": null,
  "ax_binding": null,
  "last_bridge_state": "dormant",
  "last_status_at": "2026-08-19T04:12:10.000Z",
  "cleanup_state": "not_started",
  "cleanup_after": null
}
~~~

Task-board staging is part of the materialization transaction, not a
precondition performed outside it. The coordinator MUST follow this order for
graceful takeover, force takeover, passive sync, owner resume, and fork:

1. Before the first call, the caller allocates the materialization and prepare
   operation IDs. <code>materialize.prepare</code> creates the journal by durably
   binding both IDs and the canonical request digest before allocating a fresh
   staging authority or four stable bridge operation IDs and before any bridge
   mutation.
2. Transfer installs and validates the bundle at that authority. The
   coordinator calls bridge <code>import</code>, persists the imported state,
   calls <code>open</code>, and persists the opened state. A passive replica
   stops here; owner activation is forbidden before the applicable lease is
   authoritative.
3. <code>materialize.commit</code> installs all non-task-board authorities and
   returns <code>prepared</code> only after the opened state is durable. A
   task-board-only transaction still uses this commit phase and
   <code>single_root_transaction</code>.
4. For <code>dormant_replica</code>, finalize securely destroys ax's local copy
   of the open token, records <code>dormant_finalized</code>, and leaves the
   manager inert until the bridge's mandatory token/dormant-state expiry; v1
   defines no unlisted bridge invalidation operation. For an owner path, finalize verifies
   the destination lease, calls <code>adopt</code> with the persisted token and
   exact Ax Binding, verifies bridge status, calls <code>resume</code> with the
   persisted profile, verifies running/idle, and only then records
   <code>resumed</code> and commits cleanup.
5. Before successful adopt, rollback uses the stable IDs to query status,
   invalidates or lets expire the staged/dormant state, removes the fresh
   staging authority, and restores every other authority. After successful
   adopt, the manager is active authority: byte rollback is forbidden; recovery
   must fence/stop that manager or finish resume/finalize under the same lease.

Bridge status plus the journal is the only recovery authority. The following
cases are mandatory:

| Fixture | Crash/lost response | Recovery |
| --- | --- | --- |
| <code>TB-TXN-IMPORT-LOST</code> | Import may have succeeded; journal is <code>not_started</code> | Retry import with identical operation ID/body; persist the returned identical token/reference or reject <code>idempotency_mismatch</code> |
| <code>TB-TXN-OPEN-LOST</code> | Open may have succeeded; imported facts are durable | Retry open with its stable ID; bridge returns the same dormant reference/token; persist before commit |
| <code>TB-TXN-ADOPT-LOST</code> | Adopt may have succeeded after the lease became authoritative | Query bridge status by dormant/manager reference and exact binding, then retry adopt with the same ID; never import a second manager |
| <code>TB-TXN-RESUME-LOST</code> | Resume may have started provider work | Query status, retry resume only with the same ID/profile, and publish <code>session.resumed</code> once |
| <code>TB-TXN-TOKEN-EXPIRED</code> | Import/open token expired before adopt | Before lease activation, rollback; after lease activation, remain stopped owner and re-run prepare from the same checkpoint with fresh operation IDs |
| <code>TB-TXN-BINDING-MISMATCH</code> | Bridge reports another session/epoch/lease | <code>lease_conflict</code>; preserve evidence and mutate nothing further |
| <code>TB-TXN-PASSIVE</code> | Passive sync reaches opened dormant state | Finalize dormant without adopt/resume; managed replica remains non-executable |

No flow may call bridge import or open before the corresponding journal exists,
reuse a staging root that contains manager state, inspect private manager state,
or substitute a blank provider session after a missing/expired bundle.

#### Managed Replica Marker document

The second recovery-contract variant is an immutable Managed Replica Marker.
It is the authority for classifying a destination as managed; a SQLite row,
directory name, or prior command success without this marker is not authority.
Its closed object contains exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Materialization Journal schema identifier |
| <code>schema_version</code> | semver | Exact <code>2.0.0</code> |
| <code>document_kind</code> | enum | Literal <code>managed_replica_marker</code> |
| <code>marker_id</code> | digest | JCS identity with this field omitted |
| <code>managed_replica_id</code> | UUIDv7 | Stable identity of one host/path replica across updates |
| <code>host_id</code> | UUIDv7 | Host on which the marker is authoritative |
| <code>platform</code> | enum | <code>macos</code>, <code>linux</code>, <code>wsl2</code>, or <code>windows</code> |
| <code>workspace_group_id</code> | UUIDv7 | Exact materialized group |
| <code>primary_session_id</code> | UUIDv7 | Session/checkpoint that drove this materialization |
| <code>source_checkpoint_id</code> | digest | Validated source checkpoint |
| <code>workspace_group_record_id</code> | digest | Unique Section 5.6 topology record |
| <code>workspace_manifest_id</code> | digest | Exact installed workspace-group root manifest |
| <code>plan_id</code> | digest | Executed Materialization Plan |
| <code>materialization_id</code> | UUIDv7 | Journal/RPC transaction that installed it |
| <code>destination</code> | Replica Destination | Closed shape below |
| <code>predecessor_marker_id</code> | digest or null | Prior current marker; null only for a newly managed path |
| <code>committed_at</code> | timestamp | Diagnostic commit time |
| <code>extensions</code> | object | Reverse-DNS machine-local extensions only |

Replica Destination contains exactly
<code>logical_root:string[1..64]</code>,
<code>workspace_relative_path:path</code>, and
<code>resolved_path_fingerprint:digest</code>. The first two resolve through
the current host configuration. The fingerprint is SHA-256 of the UTF-8 bytes
<code>urn:ax:replica-path:1 NUL platform NUL canonical-absolute-path</code>,
where NUL is one zero byte and Windows path case/volume normalization follows
Section 3.2. It detects remapped configuration; it is routing evidence, not a
logical workspace identity.

Normative marker fixture:

~~~json
{
  "schema": "urn:ax:schema:materialization-journal",
  "schema_version": "2.0.0",
  "document_kind": "managed_replica_marker",
  "marker_id": "sha256:385c71c7a29a43615c9d35ffb7c93ae20cd9419bbca461627048de575cade94c",
  "managed_replica_id": "0198f4c8-8e50-7f66-8f70-2234567890ab",
  "host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "platform": "linux",
  "workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "primary_session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "source_checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "workspace_group_record_id": "sha256:3b366ca989681c63323c5de6db28198796aa913947ad3cd9456fc6dcee62b743",
  "workspace_manifest_id": "sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e",
  "plan_id": "sha256:64644a5ad573d36c0c13f44f56ef25ab93cff33001ff2a3371b082603910f2dd",
  "materialization_id": "0198f4c8-c290-73aa-9374-1234567890ab",
  "destination": {
    "logical_root": "relux",
    "workspace_relative_path": "payments",
    "resolved_path_fingerprint": "sha256:244d99a3e794e9ea89b4e30429adfd6bc142c069cf0635576e010031f5b85ded"
  },
  "predecessor_marker_id": null,
  "committed_at": "2026-08-19T04:12:30.000Z",
  "extensions": {}
}
~~~

The marker is stored as owner-only JSON in both
<code>&lt;state&gt;/managed-replicas/&lt;managed-replica-id&gt;/markers/sha256/HH/REST.json</code>,
using <code>digest_path_v1(marker_id)</code> from Section 3.2,
and the atomically replaceable
<code>&lt;state&gt;/managed-replicas/&lt;managed-replica-id&gt;/current.json</code>.
The history file is create-new, fsynced, and never changed. The writer then
writes a same-directory temporary current file, fsyncs it, atomically renames
it, and fsyncs the parent where supported. The journal records the marker ID
only after the target bytes and history file are durable. SQLite indexes these
files and MUST be rebuildable by scanning them.

A current marker is valid only when its self-ID, predecessor chain, host ID,
platform, workspace group and topology record, source checkpoint, plan,
materialization, configured logical-root resolution, and path fingerprint all
validate. A marker copied from another host or placed under another managed-
replica directory is never destination authority.

For crash recovery, a <code>committing</code> journal with no current marker may
create the exact marker only after revalidating every plan authority,
predecessor, installed manifest byte, provider transaction, and task-board
state. Any mismatch rolls back when possible or fails integrity-closed; it
never writes a marker merely because the target path exists. A current marker
whose plan/checkpoint/materialization differs from the journal is
<code>MJ-CRASH-MARKER-MISMATCH</code>.

Destination classification is deterministic:

| Durable state | Classification/action |
| --- | --- |
| No marker; target absent | <code>absent</code> |
| No marker; target empty | <code>empty</code> |
| No marker; target nonempty | <code>unmanaged_nonempty</code> |
| Valid current marker resolves to this exact path and a fresh workspace capture equals <code>workspace_manifest_id</code> | <code>managed_unchanged</code> |
| Valid current marker resolves here but fresh content differs | <code>managed_divergent</code>; preserve both states |
| Marker digest, path fingerprint, predecessor chain, or referenced object is invalid | <code>integrity_failure</code>; report managed divergence diagnostically and mutate nothing |

<code>MARKER-ABSENT</code>, <code>MARKER-MATCH</code>,
<code>MARKER-CONTENT-MISMATCH</code>, <code>MARKER-PATH-MISMATCH</code>, and
<code>MARKER-CRASH-RECONSTRUCT</code> are the five rows above plus the
crash-reconstruction rule and are normative fixtures. A reader that does not
support this major version MUST treat the path as managed-but-incompatible and
fail closed; migration follows Section 17 and MUST write a new marker linked
through <code>predecessor_marker_id</code>, never edit an old marker.

### 10.7 Tombstone

Tombstone schema <code>urn:ax:schema:tombstone</code> version
<code>1.0.0</code> is immutable. Its common closed shape is:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Tombstone schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>tombstone_id</code> | digest | Canonical object digest |
| <code>scope</code> | enum | <code>session</code>, <code>workspace_entry</code>, <code>provider_snapshot</code>, or <code>managed_replica</code> |
| <code>subject_id</code> | UUIDv7 | Scope subject defined below |
| <code>authorizing_session_id</code> | UUIDv7 | Session whose owner authorizes the action |
| <code>basis_event_id</code> | digest | Immediately preceding authoritative event for the authorizing lease |
| <code>lease_epoch</code> | uint53 | Authorizing lease epoch |
| <code>lease_id</code> | UUIDv4 | Authorizing fencing token |
| <code>target</code> | tagged object | Exact scope-specific shape below |
| <code>created_by_host_id</code> | UUIDv7 | MUST equal the authorizing lease holder |
| <code>created_at</code> | timestamp | Diagnostic only |
| <code>extensions</code> | object | Reverse-DNS extension keys only |

The <code>target</code> object is selected by <code>scope</code> and begins with
an equal <code>kind</code>. It contains exactly:

| Scope | <code>subject_id</code> | Exact target members after <code>kind</code> |
| --- | --- | --- |
| <code>session</code> | Session ID | <code>session_id:UUIDv7</code>, <code>session_record_id:digest</code>, <code>predecessor_checkpoint_id:digest</code> |
| <code>workspace_entry</code> | Workspace Group ID | <code>workspace_group_id:UUIDv7</code>, <code>workspace_id:UUIDv7</code>, <code>predecessor_manifest_id:digest</code>, <code>relative_path:path</code>, <code>entry_type:directory&#124;file&#124;symlink&#124;hardlink</code>, <code>predecessor_entry_digest:digest</code> |
| <code>provider_snapshot</code> | Session ID | <code>session_id:UUIDv7</code>, <code>provider_identity_record_id:digest</code>, <code>predecessor_manifest_id:digest</code> |
| <code>managed_replica</code> | Workspace Group ID | <code>workspace_group_id:UUIDv7</code>, <code>target_host_id:UUIDv7</code>, <code>managed_replica_id:UUIDv7</code>, <code>logical_root:string[1..64]</code>, <code>destination_relative_path:path</code>, <code>predecessor_marker_id:digest</code>, <code>predecessor_checkpoint_id:digest</code> |

Positive embedded target fixtures for the three variants not used by the full
example are:

~~~json
{"kind":"session","session_id":"0198f4c8-3e70-7a11-8a2b-1234567890ab","session_record_id":"sha256:d61701066a7f5dd37bf35fea0e85e7f154251355ad24a49976532d7f79ddc772","predecessor_checkpoint_id":"sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656"}
~~~

~~~json
{"kind":"provider_snapshot","session_id":"0198f4c8-3e70-7a11-8a2b-1234567890ab","provider_identity_record_id":"sha256:c879d766da67a8cfb3a3f6eae2234faa5d52d8df987496eae2218f40e5e220c2","predecessor_manifest_id":"sha256:1e817955dcc529e282ab31f91c99561d03b3c5642282d2e0a0e05b0f60dd0f91"}
~~~

~~~json
{"kind":"managed_replica","workspace_group_id":"0198f4c8-5b20-7c33-8c4d-1234567890ab","target_host_id":"0198f4c8-7d40-7e55-8e6f-1234567890ab","managed_replica_id":"0198f4c8-8e50-7f66-8f70-2234567890ab","logical_root":"relux","destination_relative_path":"replicas/payments","predecessor_marker_id":"sha256:385c71c7a29a43615c9d35ffb7c93ae20cd9419bbca461627048de575cade94c","predecessor_checkpoint_id":"sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656"}
~~~

Repeated IDs in the target MUST equal the corresponding common/session/group
records. A workspace-entry <code>workspace_id</code> MUST name one member of the
group, its predecessor MUST be that member's <code>workspace_tree</code>
manifest, and its path is member-relative. An entry digest is SHA-256 of the
JCS bytes of the complete Transfer Manifest entry object. A workspace-entry
path names exactly one entry in that predecessor; a
directory target MUST be empty after separately authorized descendant
deletions. A managed-replica path is relative to one configured logical root
and MUST NOT be empty or that root itself.

~~~json
{
  "schema": "urn:ax:schema:tombstone",
  "schema_version": "1.0.0",
  "tombstone_id": "sha256:4acc50a49a714543ef415ab1d68bb605ee825cae2b36308e669f6cfe74f73b3e",
  "scope": "workspace_entry",
  "subject_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "authorizing_session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "basis_event_id": "sha256:7777777777777777777777777777777777777777777777777777777777777777",
  "lease_epoch": 4,
  "lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "target": {
    "kind": "workspace_entry",
    "workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
    "workspace_id": "0198f4c8-6c30-7d44-8d5e-1234567890ab",
    "predecessor_manifest_id": "sha256:88d93f20f978b92e75d35e67ebd5a41b90ff1afe106363b05c0f7b08614eb4cf",
    "relative_path": "README.md",
    "entry_type": "file",
    "predecessor_entry_digest": "sha256:499419072e3173e840befc74fdc1d334b33bd9a3a03076a08fb792ea9ae264f1"
  },
  "created_by_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "created_at": "2026-08-19T04:20:00.000Z",
  "extensions": {}
}
~~~

Only the winning owner MAY issue a Tombstone. Its lease MUST be the current
winning lease or an ancestor of the current winning lease through validated
<code>predecessor_lease_id</code> links. The writer MUST first persist the
Tombstone, then emit a <code>tombstone.issued</code> Session Event under the same
lease whose predecessor is <code>basis_event_id</code>. A Tombstone without that
matching event, or one issued on a losing lease branch, is retained as evidence
but is not actionable. For workspace and replica scopes, the authorizing
session MUST belong to the named Workspace Group. A
<code>provider_snapshot</code> target MUST belong to that session. Wildcards,
an empty path, a root path, traversal, recursive-parent semantics, and deletion
of anything not named by the target are forbidden.

A session-scope issuance MUST be followed immediately by
<code>session.tombstoned</code> referencing the issuance event; derived session
state changes only at that second event. A later owner that resolves a
workspace-entry conflict or explicitly recreates the entry MUST emit
<code>tombstone.resolved</code> on the same authorizing session's authoritative
event chain before publishing the resulting checkpoint.

Object exchange only validates and unions Tombstones; it MUST NOT mutate a
session, native store, workspace, or replica. Application occurs when deriving
session state or building a validated Materialization Plan:

| Scope | Application rule |
| --- | --- |
| <code>session</code> | Derive <code>tombstoned</code> after matching <code>session.tombstoned</code> is authoritative; block attach/resume and retain all immutable history. Filesystem deletion is a separate, explicitly scoped action. |
| <code>workspace_entry</code> | Add one <code>delete_managed_path</code> plan operation with the exact path and <code>expected_prior_digest = predecessor_entry_digest</code>. Commit first renames that one entry to the transaction rollback area, then commits or restores it atomically. |
| <code>provider_snapshot</code> | Remove only the exact provider manifest from eligible resume checkpoints. Do not delete or rewrite a live native store. A checkpoint that still requires it fails closed. |
| <code>managed_replica</code> | Apply only on <code>target_host_id</code>, after a matching <code>replica.replace_confirmed</code> event, to the exact managed-replica ID, current marker ID, path, and expected predecessor checkpoint. Unmanaged content or any unconfirmed divergence fails closed. |

Delete-versus-change is determined by identity and event ancestry, never by
time. Let T target entry digest D in predecessor manifest B, and let C be the
candidate destination checkpoint:

| Golden case | Required result |
| --- | --- |
| C still has D, or the path is already absent | Apply exact deletion or record <code>already_absent</code>; retry is idempotent. |
| C changes the path without an authoritative <code>tombstone.resolved</code> event descending from T's issuance event | <code>workspace_conflict</code>; preserve B, C, T, and both event histories; mutate nothing. |
| C descends from T's issuance and omits the path with <code>resolution = deleted</code> | Deletion converges; a receiver MUST NOT recreate D from an older manifest. |
| C descends from T's issuance and contains a new entry whose digest equals an authoritative <code>resolution = resurrected</code> event | Treat it as an explicit recreation, not as a lost deletion. |
| C claims deletion/resurrection without the required ancestry, or the entry digest differs from the resolution event | <code>integrity_failure</code>; retain staging and both histories. |

A receiver records the disposition in an immutable Tombstone Acknowledgement,
schema <code>urn:ax:schema:tombstone-ack</code> version <code>1.0.0</code>:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact acknowledgement schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>ack_id</code> | digest | Canonical object digest |
| <code>subject_id</code> | UUIDv7 | Equal to the Tombstone subject |
| <code>tombstone_id</code> | digest | Stored, schema-valid Tombstone |
| <code>acknowledging_host_id</code> | UUIDv7 | Allowlisted receiving host |
| <code>disposition</code> | enum | <code>applied</code>, <code>already_absent</code>, <code>retained_conflict</code>, or <code>not_target</code> |
| <code>conflict_checkpoint_id</code> | digest or null | Non-null only for <code>retained_conflict</code> |
| <code>observed_at</code> | timestamp | Time the disposition was durably observed |
| <code>created_by_host_id</code> | UUIDv7 | Equal to acknowledging host |
| <code>created_at</code> | timestamp | Record creation time; not authority |
| <code>extensions</code> | object | Reverse-DNS extension keys only |

~~~json
{
  "schema": "urn:ax:schema:tombstone-ack",
  "schema_version": "1.0.0",
  "ack_id": "sha256:407355b5270ef3e25551ac48eb5f80cc12ef90e60aaf694c2a41c72b378b30c0",
  "subject_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "tombstone_id": "sha256:4acc50a49a714543ef415ab1d68bb605ee825cae2b36308e669f6cfe74f73b3e",
  "acknowledging_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "disposition": "applied",
  "conflict_checkpoint_id": null,
  "observed_at": "2026-08-19T04:21:00.000Z",
  "created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "created_at": "2026-08-19T04:21:00.000Z",
  "extensions": {}
}
~~~

The acknowledgement's fields are all required and the object is closed.
<code>disposition</code> is <code>applied</code>,
<code>already_absent</code>, <code>retained_conflict</code>, or
<code>not_target</code>. <code>conflict_checkpoint_id</code> MUST be non-null
only for <code>retained_conflict</code>. <code>created_by_host_id</code> MUST
equal <code>acknowledging_host_id</code>. A peer MAY acknowledge only after it
has durably stored T and either applied it, proved the target absent/not local,
or durably recorded the fail-closed conflict. The acknowledgement MUST be
retained at least as long as T and is unioned by <code>ack_id</code> like every
immutable record.

Tombstones MUST be retained for at least 90 days and until every currently
allowlisted peer has acknowledged the tombstone or has been explicitly removed
from the allowlist. Blob garbage collection MAY occur only when no live
manifest references the blob and all governing tombstones meet that condition.
An acknowledgement of <code>retained_conflict</code> satisfies receipt but does
not make referenced history unreachable; the live-reference rule still blocks
garbage collection.

## 11. Mesh RPC and replication

### 11.1 Transport and peer authentication

The initiator runs the equivalent of:

~~~shell
ssh -T HOST ax rpc serve --stdio
~~~

Tailscale SSH MAY supply HOST; ordinary OpenSSH MAY supply it. SSH host-key and
user authentication are outside <code>ax</code> and MUST be enabled. After SSH
starts the remote process, both sides MUST verify that the protocol
<code>host_id</code> matches the configured allowlist entry. Endpoint match
without host-ID match MUST fail.

On Windows, <code>ax</code> MUST construct argv using the native process API or
a PowerShell-safe argument encoder. It MUST NOT concatenate an untrusted
session name or path into a remote shell string.

### 11.2 RPC framing and handshake

Mesh RPC uses line-delimited JSON, maximum line size 8 MiB, protocol
<code>urn:ax:protocol:rpc</code> version <code>2.0.0</code>. Binary chunk bytes
are unpadded base64url in the request body. Every request has a UUIDv7
<code>request_id</code>; every response echoes it.

The first request MUST be <code>hello</code>:

~~~json
{
  "protocol": "urn:ax:protocol:rpc",
  "protocol_version": "2.0.0",
  "request_id": "0198f4c8-a070-7188-9172-1234567890ab",
  "operation": "hello",
  "body": {
    "host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
    "platform": "macos",
    "ax_version": "0.2.0",
    "nonce": "YWJjZGVmZ2hpamtsbW5vcA",
    "contracts": {
      "rpc": ["2.0.0"],
      "session_record": ["1.0.0"],
      "session_event": ["1.0.0"],
      "lease": ["1.0.0"],
      "checkpoint": ["1.0.0"],
      "workspace_group": ["1.0.0"],
      "provider_identity": ["1.0.0"],
      "blob": ["1.0.0"],
      "transfer_manifest": ["1.0.0"],
      "chunk": ["1.0.0"],
      "materialization_plan": ["1.0.0"],
      "tombstone": ["1.0.0"],
      "tombstone_ack": ["1.0.0"],
      "task_board_bundle": ["1.0.0"]
    },
    "max_line_bytes": 8388608,
    "max_object_bytes": 5242880
  }
}
~~~

The request envelope contains exactly <code>protocol</code>,
<code>protocol_version</code>, <code>request_id</code> UUIDv7,
<code>operation</code>, and the operation-specific <code>body</code>. The
<code>hello</code> body contains exactly the members shown. Its nonce is
unpadded base64url encoding of at least 128 random bits. The
<code>contracts</code> map contains exactly the fourteen displayed lower-snake-
case keys, each with a sorted, unique array of 1–16 Semantic Versions. These
are the immutable/wire contracts used by RPC object exchange. Configuration,
provider protocol/manifest/probe, task-board bridge, materialization recovery
state, Structured Error, Observation Event, and CLI Result MUST NOT appear in
this map. They are either local, carried by another protocol, or—in the error
case—statically embedded below.

Normative <code>hello</code> success:

~~~json
{
  "protocol": "urn:ax:protocol:rpc",
  "protocol_version": "2.0.0",
  "request_id": "0198f4c8-a070-7188-9172-1234567890ab",
  "ok": true,
  "body": {
    "host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
    "platform": "linux",
    "ax_version": "0.2.0",
    "nonce": "cXJzdHV2d3h5ejAxMjM0NQ",
    "nonce_echo": "YWJjZGVmZ2hpamtsbW5vcA",
    "contracts": {
      "rpc": ["2.0.0"],
      "session_record": ["1.0.0"],
      "session_event": ["1.0.0"],
      "lease": ["1.0.0"],
      "checkpoint": ["1.0.0"],
      "workspace_group": ["1.0.0"],
      "provider_identity": ["1.0.0"],
      "blob": ["1.0.0"],
      "transfer_manifest": ["1.0.0"],
      "chunk": ["1.0.0"],
      "materialization_plan": ["1.0.0"],
      "tombstone": ["1.0.0"],
      "tombstone_ack": ["1.0.0"],
      "task_board_bundle": ["1.0.0"]
    },
    "max_line_bytes": 8388608,
    "max_object_bytes": 5242880
  }
}
~~~

The success body contains exactly the request identity/version/limit members,
the server's fresh <code>nonce</code>, and <code>nonce_echo</code> equal to the
request nonce. A success response contains exactly protocol, version, request
ID, <code>ok = true</code>, and body. A failure response substitutes
<code>ok = false</code> and one Structured Error and MUST omit body. Unknown
envelope or body members fail protocol 2.0.0.

Mesh RPC protocol <code>2.x</code> statically binds every supported-major
failure envelope, including a rejected <code>hello</code>, to Structured Error
<code>1.0.0</code>. <code>error</code> is therefore deliberately absent from the
hello contracts map and is not independently negotiated on an RPC connection.
Section 15.1 defines the exact response-or-close behavior before handshake and
for an unsupported major.

The server returns its own identity, nonce echo, supported contracts, and
limits. Peers negotiate the smaller line/object limit; protocol 2.0.0 requires
at least the values shown and MUST refuse a peer below them. The 5 MiB object
limit leaves room for base64url expansion and the response envelope below the
8 MiB line limit. Within a valid RPC-v2 hello, an absent required contract
returns the bound <code>incompatible_protocol</code> failure and closes. An
unsupported RPC major closes without a peer error frame and the initiator emits
that code locally, exactly as Section 15.1 requires. A peer MUST NOT
perform any other operation before a successful handshake.

### 11.3 RPC operations

Mesh RPC 2.0.0 operations are:

| Operation | Purpose |
| --- | --- |
| <code>hello</code> | Authenticate configured identity and negotiate versions/limits |
| <code>health.get</code> | Read peer/service/provider health without payload contents |
| <code>inventory.roots</code> | Return Merkle roots and counts for record, event, manifest, tombstone, acknowledgement, and blob-ID sets |
| <code>inventory.children</code> | Expand one hexadecimal digest-prefix node |
| <code>objects.get</code> | Fetch immutable JSON/CBOR objects by digest |
| <code>transfer.begin</code> | Create or reopen staging for one manifest |
| <code>transfer.status</code> | Return verified object/chunk presence |
| <code>chunks.put</code> | Submit one base64url chunk with descriptor |
| <code>transfer.validate</code> | Assemble blobs and validate the complete manifest |
| <code>transfer.commit</code> | Atomically install immutable objects; does not materialize a workspace |
| <code>materialize.prepare</code> | Run destination conflict and capability checks |
| <code>materialize.commit</code> | Install a validated transaction in rollbackable prepared state (the historical operation name is retained) |
| <code>materialize.status</code> | Recover the exact durable materialization phase after a lost response or restart |
| <code>materialize.finalize</code> | Finalize a prepared transaction after dormant validation or winning-owner resume |
| <code>materialize.rollback</code> | Restore the pre-commit managed destination |
| <code>lease.refresh</code> | Exchange lease heads and return the deterministic winner |
| <code>tombstone.ack</code> | Persist a peer acknowledgement |
| <code>session.status</code> | Read authoritative lifecycle, process, checkpoint, and active-operation state for one session |
| <code>session.stop</code> | Execute the owner-side stop transaction in Section 13.9 |
| <code>handoff.prepare</code> | Reserve one graceful handoff against an expected source lease/checkpoint |
| <code>handoff.quiesce</code> | Quiesce the source and return its validated bulk-sync checkpoint |
| <code>handoff.stop</code> | Stop the source after destination validation and return any superseding closure checkpoint |
| <code>handoff.commit</code> | Persist the destination Lease Record on the source and park the old owner |
| <code>handoff.abort</code> | Abort a pre-lease handoff and explicitly unquiesce or retain stopped state |

Every mutation body includes <code>initiator_host_id</code>; a session mutation
also includes an exact lease expectation. The receiver MUST revalidate both
immediately before mutation. These closed embedded types belong to Mesh RPC
2.0.0:

| Type | Exact members and constraints |
| --- | --- |
| <code>Namespace</code> | <code>record</code>, <code>event</code>, <code>manifest</code>, <code>tombstone</code>, <code>tombstone_ack</code>, or <code>blob</code> |
| <code>LeaseExpectation</code> | <code>epoch:uint53&gt;0</code>, <code>lease_id:UUIDv4</code>, <code>holder_host_id:UUIDv7</code> |
| <code>LeaseHead</code> | <code>lease_record_id:digest</code> plus every <code>LeaseExpectation</code> member |
| <code>GroupMemberExpectation</code> | <code>session_id:UUIDv7</code>, <code>session_record_id:digest</code>, <code>winning_lease_record_id:digest</code>, <code>state:SessionState</code>, <code>managed_replica_id:UUIDv7&#124;null</code> |
| <code>WorkspaceGroupExpectation</code> | <code>workspace_group_id:UUIDv7</code>, <code>workspace_group_record_id:digest</code>, <code>observed_host_id:UUIDv7</code>, <code>live_members:GroupMemberExpectation[1..1024]</code> |
| <code>MaterializationKind</code> | <code>workspace</code>, <code>provider</code>, <code>task_board</code>, or <code>composite</code> |
| <code>MaterializationIntent</code> | <code>passive_replica</code>, <code>owner_resume</code>, <code>ownership_transfer</code>, or <code>fork</code> |
| <code>MaterializationCohort</code> | <code>materialization_session_ids:sorted unique UUIDv7[1..1024]</code>, <code>ownership_transfer_session_ids:sorted unique UUIDv7[0..1024]</code> |
| <code>MaterializationSources</code> | <code>workspace_manifest_id:digest&#124;null</code>, <code>provider_manifest_id:digest&#124;null</code>, <code>task_board_bundle_id:digest&#124;null</code>, <code>derived_workspace_manifest_id:digest&#124;null</code>, <code>fork_projection:ForkWorkspaceProjection&#124;null</code> |
| <code>WorkspaceMaterializationRequest</code> | <code>logical_root_mapping:map(string,absolute-path)[1..64]</code>, <code>destination:{logical_root:string[1..64],workspace_relative_path:path}</code>, <code>workspace_group_expectation:WorkspaceGroupExpectation</code>, <code>conflict_policy:fail&#124;copy&#124;worktree&#124;replace_managed_replica</code>, <code>replacement_confirmation_event_id:digest&#124;null</code> |
| <code>VerifiedState</code> | <code>object_ids:sorted unique digest[0..65536]</code>, <code>blob_chunks:map(digest,sorted unique uint32[0..32768])[0..65536]</code> |
| <code>WireObject</code> | <code>object_id:digest</code>, <code>media_type:application/json&#124;application/cbor</code>, <code>encoding:json&#124;cbor</code>, <code>data:base64url</code> |
| <code>SafeBoundary</code> | <code>provider_id:provider-id</code>, <code>provider_version:string[1..128]</code>, <code>evidence:provider_api&#124;provider_event&#124;managed_pty&#124;task_board_bridge&#124;accepted_test</code>, <code>input_blocked:boolean</code>, <code>boundary_ref:string[1..1024]&#124;null</code>, <code>foreground_idle:boolean</code>, <code>background_idle:boolean</code>, <code>open_processes:uint53</code>, <code>open_database_handles:uint53</code>, <code>store_generation:string[1..512]&#124;null</code>, <code>store_stable:boolean</code>, <code>safe:boolean</code>, <code>blockers:sorted unique background_active&#124;database_handle_open&#124;input_not_blocked&#124;process_open&#124;provider_busy&#124;store_unstable[0..6]</code> |
| <code>ClosureEvidence</code> | <code>process_closed:boolean</code>, <code>store_closed:boolean</code>, <code>exit_code:int32&#124;null</code>, <code>remaining_process_handles:sorted unique string[0..256]</code>, <code>final_store_generation:string[1..512]&#124;null</code> |
| <code>ActiveOperation</code> | <code>operation_id:UUIDv7</code>, <code>kind:stop&#124;graceful_handoff&#124;materialize</code>, <code>phase:string[1..64]</code>, <code>peer_host_id:UUIDv7&#124;null</code> |
| <code>DestinationClass</code> | <code>absent</code>, <code>empty</code>, <code>managed_unchanged</code>, <code>managed_divergent</code>, or <code>unmanaged_nonempty</code> |
| <code>MaterializationStatus</code> | <code>materialization_id:UUIDv7</code>, <code>phase:unknown&#124;staging&#124;validating&#124;prepared&#124;committing&#124;rolling_back&#124;committed&#124;rolled_back&#124;failed</code>, <code>kind:MaterializationKind&#124;null</code>, <code>intent:MaterializationIntent&#124;null</code>, <code>plan_id:digest&#124;null</code>, <code>checkpoint_id:digest&#124;null</code>, <code>destination_path:absolute-path&#124;null</code>, <code>destination_classification:DestinationClass&#124;null</code>, <code>managed_replica_id:UUIDv7&#124;null</code>, <code>destination_marker_id:digest&#124;null</code>, <code>provider_transaction_state:none&#124;unknown&#124;prepared&#124;committed&#124;rolled_back</code>, <code>task_board_transaction_state:none&#124;unknown&#124;not_started&#124;imported&#124;opened&#124;adopted&#124;resumed&#124;dormant_finalized&#124;rolled_back&#124;failed</code>, <code>task_board_manager_ref:string[1..512]&#124;null</code>, <code>task_board_binding:AxBinding&#124;null</code>, <code>last_error_code:string[1..128]&#124;null</code> |

<code>blob_chunks</code> object names are digest identifiers and its arrays are
sorted numeric indexes. Group members are sorted by session ID, contain every
current <code>live_members(G)</code> entry from Section 5.6 exactly once. A
WorkspaceGroupExpectation is only a fenced topology/state snapshot; it does
not itself select work or ownership changes.

The MaterializationCohort makes those selections explicitly. Its
<code>materialization_session_ids</code> are the non-empty set whose checkpoint
workspace/provider/task-board state is installed by this transaction. Its
<code>ownership_transfer_session_ids</code> is a subset. It MUST be empty for
<code>passive_replica</code>, <code>owner_resume</code>, and <code>fork</code>,
and MUST be non-empty for <code>ownership_transfer</code>. The request's <code>session_id</code> is in
the materialization set and, for ownership transfer, in the transfer set. When
a workspace participates, both arrays are subsets of the expectation's live
members, except that a fork set contains exactly the fresh destination session
while its WorkspaceGroupExpectation describes the source group named by
<code>fork_projection</code>. A passive set may contain a stopped member and never authorizes
provider input, lease advance, adoption, or resume. Owner resume requires the
named session to be the already-winning stopped/failed owner and never advances
its lease. Ownership-transfer members may be
<code>running|idle|quiescing|checkpointing|stopped</code>; their non-null
managed-replica IDs, when present, identify the same shared destination on the
observed host. No implementation may infer a transfer cohort from the
materialization set or replace an empty transfer set with the current session.
Fork requires exactly one materialization session, a fresh epoch-1 destination
lease, and no ownership change to any source session.

MaterializationSources and <code>workspace_request</code> form a closed tagged
union. <code>workspace</code> requires only a non-null workspace manifest and a
non-null workspace request. <code>provider</code> requires only a non-null
provider manifest and a null workspace request. <code>task_board</code>
requires only a non-null task-board bundle and a null workspace request.
<code>composite</code> requires a workspace manifest/request plus exactly one
of provider manifest or task-board bundle. Every other source member is
present as null. For every non-fork intent,
<code>derived_workspace_manifest_id</code> and <code>fork_projection</code> are
null. Fork requires both non-null: <code>workspace_manifest_id</code> is the
source group manifest in the selected Checkpoint closure and the derived ID is
the destination group manifest produced by the exact projection. All other
source IDs MUST be in the selected Checkpoint closure, and the generated
Materialization Plan kind and intent MUST equal the request.

A safe boundary requires every idle/block/stability boolean true, both counts
zero, and empty blockers. Provider-plugin proof maps
<code>open_child_count</code> to <code>open_processes</code>,
<code>open_database_handle_count</code> to
<code>open_database_handles</code>, and its blocker names to the RPC registry;
BridgeSafeBoundary uses the Section 9.2 total mapping. In both mappings,
<code>store_stable</code> is true exactly when store generation is non-null and
<code>store_unstable</code> is absent. A safe RPC boundary additionally requires
non-null boundary and store-generation references; an unsafe diagnostic
boundary may carry either as null. Process handles are operation-local opaque values and MUST NOT be
persisted. In <code>MaterializationStatus</code>, phase
<code>unknown</code> requires null kind, intent, plan, checkpoint, destination,
classification, replica, marker, task-board manager/binding, and error, plus
provider and task-board transaction states <code>none</code>. Every other phase requires
non-null kind, intent, plan, and checkpoint. A workspace/composite status also
requires non-null destination path, classification, and managed-replica ID;
provider/task-board-only status requires all three null. Only a committed
workspace/composite status has a non-null destination marker. Prepared and
rolled-back phases require a null marker. Failed retains every known field and
a non-null error code. The provider transaction state is
<code>none</code> exactly when no provider manifest participates; it is
<code>unknown</code> only when that provider transaction was invoked but its
durable status has not been reconciled. Task-board transaction state is
<code>none</code> exactly when no Task-board Bundle participates and
<code>unknown</code> only after an attempted bridge mutation whose durable
result has not been reconciled. Its manager reference is non-null for
<code>opened</code>, <code>adopted</code>, <code>resumed</code>, or
<code>dormant_finalized</code>; its binding is non-null only for adopted or
resumed. Neither is a control token. Operation bodies are exactly:

| Operation | Exact request body | Exact success body |
| --- | --- | --- |
| <code>health.get</code> | <code>{}</code> | <code>{service:ax, ax_version:semver, platform:macos&#124;linux&#124;wsl2&#124;windows, observed_at:timestamp, degraded_codes:sorted unique string[0..1024]}</code> |
| <code>inventory.roots</code> | <code>{namespaces:sorted unique Namespace[1..6]}</code> | <code>{roots:sorted unique {namespace:Namespace,count:uint53,root_id:digest}[1..6]}</code> sorted by namespace |
| <code>inventory.children</code> | <code>{namespace:Namespace,prefix:lowercase-hex[0..64]}</code> | <code>{namespace:Namespace,prefix:lowercase-hex[0..64],count:uint53,node_hash:digest,children:sorted unique {label:hex-nibble,count:uint53,hash:digest}[0..16],ids:sorted unique digest[0..1]}</code> |
| <code>objects.get</code> | <code>{object_ids:sorted unique digest[1..4096],encodings:sorted unique json&#124;cbor[1..2]}</code> | <code>{objects:WireObject[1..4096]}</code> sorted by object ID |
| <code>transfer.begin</code> | <code>{initiator_host_id:UUIDv7,manifest_id:digest,transfer_id:UUIDv7&#124;null}</code> | <code>{transfer_id:UUIDv7,expires_at:timestamp,verified:VerifiedState}</code> |
| <code>transfer.status</code> | <code>{transfer_id:UUIDv7}</code> | <code>{transfer_id:UUIDv7,phase:receiving&#124;validating&#124;validated&#124;committed&#124;failed&#124;expired,verified:VerifiedState,last_error_code:string[1..128]&#124;null,expires_at:timestamp}</code> |
| <code>chunks.put</code> | <code>{initiator_host_id:UUIDv7,transfer_id:UUIDv7,descriptor:Transfer Chunk Descriptor,data:base64url}</code> | <code>{transfer_id:UUIDv7,chunk_id:digest,verified:boolean}</code> |
| <code>transfer.validate</code> | <code>{initiator_host_id:UUIDv7,transfer_id:UUIDv7,manifest_id:digest}</code> | <code>{transfer_id:UUIDv7,manifest_id:digest,valid:boolean,verified_blob_count:uint53,verified_object_count:uint53,validation_summary_digest:digest}</code> |
| <code>transfer.commit</code> | <code>{initiator_host_id:UUIDv7,transfer_id:UUIDv7,manifest_id:digest,validation_summary_digest:digest}</code> | <code>{transfer_id:UUIDv7,installed_object_ids:sorted unique digest[1..65536],commit_marker_id:digest}</code> |
| <code>materialize.prepare</code> | Tagged <code>{initiator_host_id:UUIDv7,operation_id:UUIDv7,materialization_id:UUIDv7,kind:MaterializationKind,intent:MaterializationIntent,session_id:UUIDv7,expected_lease:LeaseExpectation,checkpoint_id:digest,cohort:MaterializationCohort,sources:MaterializationSources,workspace_request:WorkspaceMaterializationRequest&#124;null}</code> | <code>{operation_id:UUIDv7,materialization_id:UUIDv7,kind:MaterializationKind,intent:MaterializationIntent,managed_replica_id:UUIDv7&#124;null,destination_path:absolute-path&#124;null,destination_classification:DestinationClass&#124;null,required_capabilities:sorted unique string[0..128],plan_id:digest,rollback_possible:boolean}</code> |
| <code>materialize.commit</code> | <code>{initiator_host_id:UUIDv7,materialization_id:UUIDv7,plan_id:digest,session_id:UUIDv7,expected_lease:LeaseExpectation}</code> | <code>{materialization_id:UUIDv7,kind:MaterializationKind,intent:MaterializationIntent,phase:prepared,prepared_checkpoint_id:digest,destination_path:absolute-path&#124;null,destination_classification:DestinationClass&#124;null,managed_replica_id:UUIDv7&#124;null,rollback_token:base64url-256+,provider_transaction_id:UUIDv7&#124;null,task_board_transaction_state:none&#124;opened}</code> |
| <code>materialize.status</code> | <code>{materialization_id:UUIDv7}</code> | <code>MaterializationStatus</code> |
| <code>materialize.finalize</code> | <code>{initiator_host_id:UUIDv7,materialization_id:UUIDv7,rollback_token:base64url-256+,session_id:UUIDv7,expected_lease:LeaseExpectation,activation:dormant_validated&#124;direct_owner_resumed&#124;task_board_owner_resumed,execution_profile:standard&#124;yolo&#124;null,profile_source_event_id:digest&#124;null}</code> | <code>{materialization_id:UUIDv7,kind:MaterializationKind,intent:MaterializationIntent,phase:committed,committed_checkpoint_id:digest,managed_replica_id:UUIDv7&#124;null,destination_marker_id:digest&#124;null,provider_transaction_state:none&#124;committed,task_board_transaction_state:none&#124;resumed&#124;dormant_finalized,manager_session_ref:string[1..512]&#124;null,finalized_at:timestamp}</code> |
| <code>materialize.rollback</code> | <code>{initiator_host_id:UUIDv7,materialization_id:UUIDv7,rollback_token:base64url-256+,reason:lease_lost&#124;validation_failed&#124;resume_failed&#124;operator_abort&#124;crash_recovery}</code> | <code>{materialization_id:UUIDv7,kind:MaterializationKind,intent:MaterializationIntent,phase:rolled_back,rolled_back:boolean,restored_checkpoint_id:digest&#124;null,provider_transaction_state:none&#124;rolled_back,task_board_transaction_state:none&#124;rolled_back}</code> |
| <code>lease.refresh</code> | <code>{session_id:UUIDv7,known_lease_record_ids:sorted unique digest[0..4096]}</code> | <code>{session_id:UUIDv7,missing_leases:sorted unique Lease Record[0..4096],winner:LeaseHead,divergence:boolean}</code> |
| <code>tombstone.ack</code> | <code>{initiator_host_id:UUIDv7,acknowledgement:Tombstone Acknowledgement}</code> | <code>{tombstone_id:digest,ack_id:digest,stored:boolean}</code> |
| <code>session.status</code> | <code>{session_id:UUIDv7}</code> | <code>{session_id:UUIDv7,winner:LeaseHead,local_role:owner&#124;replica,state:SessionState,process_present:boolean,newest_checkpoint_id:digest&#124;null,active_operation:ActiveOperation&#124;null}</code> |
| <code>session.stop</code> | <code>{initiator_host_id:UUIDv7,operation_id:UUIDv7,session_id:UUIDv7,expected_lease:LeaseExpectation,graceful:boolean,timeout_ms:uint53[1..3600000]}</code> | <code>{operation_id:UUIDv7,already_applied:boolean,closure:ClosureEvidence,final_checkpoint_id:digest&#124;null,resumable:boolean,bootstrap_aborted:boolean,resulting_state:stopped&#124;failed}</code> |
| <code>handoff.prepare</code> | <code>{initiator_host_id:UUIDv7,operation_id:UUIDv7,group_operation_id:UUIDv7,session_id:UUIDv7,expected_source_lease:LeaseExpectation,expected_checkpoint_id:digest,destination_host_id:UUIDv7,workspace_group_expectation:WorkspaceGroupExpectation,cohort:MaterializationCohort}</code> | <code>{operation_id:UUIDv7,group_operation_id:UUIDv7,phase:reserved,source_lease:LeaseHead,source_checkpoint_id:digest,source_state:running&#124;idle&#124;stopped,workspace_group_expectation:WorkspaceGroupExpectation,cohort:MaterializationCohort,expires_at:timestamp}</code> |
| <code>handoff.quiesce</code> | <code>{initiator_host_id:UUIDv7,operation_id:UUIDv7,session_id:UUIDv7,expected_source_lease:LeaseExpectation}</code> | <code>{operation_id:UUIDv7,safe_boundary:SafeBoundary,bulk_checkpoint_id:digest,manifest_ids:sorted unique digest[1..1024],source_phase:quiesced}</code> |
| <code>handoff.stop</code> | <code>{initiator_host_id:UUIDv7,operation_id:UUIDv7,session_id:UUIDv7,expected_source_lease:LeaseExpectation,destination_validation_summary_digest:digest}</code> | <code>{operation_id:UUIDv7,closure:ClosureEvidence,newest_checkpoint_id:digest,source_state:stopped}</code> |
| <code>handoff.commit</code> | <code>{initiator_host_id:UUIDv7,operation_id:UUIDv7,session_id:UUIDv7,expected_source_lease:LeaseExpectation,new_lease:Lease Record,destination_materialization_id:UUIDv7,plan_id:digest,committed_checkpoint_id:digest}</code> | <code>{operation_id:UUIDv7,winner:LeaseHead,source_role:replica,source_state:parked}</code> |
| <code>handoff.abort</code> | <code>{initiator_host_id:UUIDv7,operation_id:UUIDv7,session_id:UUIDv7,expected_source_lease:LeaseExpectation,recovery_mode:unquiesce&#124;remain_stopped}</code> | <code>{operation_id:UUIDv7,phase:aborted,resulting_source_state:running&#124;idle&#124;stopped}</code> |

For <code>chunks.put</code>, success requires <code>verified = true</code>.
For <code>transfer.validate</code>, success requires <code>valid = true</code>.
For rollback and acknowledgement, success requires the corresponding boolean
true. A workspace request with replace policy requires a non-null
<code>replacement_confirmation_event_id</code>; every other policy requires
null. Every response uses the exact success/failure envelopes in Section 11.2.

The caller MUST allocate <code>materialize.prepare.operation_id</code> and
<code>materialization_id</code> before the first request and MUST retain them
until the transaction is terminal. Before the first destination mutation, the
receiver MUST durably create the Materialization Journal with both IDs and a
digest of the complete canonical prepare body. The mutation idempotency key is
<code>(materialize.prepare, operation_id)</code>. An identical retry, including
after a lost response or receiver restart, returns the byte-identical recorded
success or failure and MUST NOT allocate a second journal, staging authority,
managed-replica ID, plan, or bridge operation ID. A changed canonical body,
including a changed materialization ID, is <code>idempotency_mismatch</code> and
causes no new mutation. <code>materialize.status</code> is an evolving read,
locates the one journal by caller-known <code>materialization_id</code>, uses the
RPC envelope <code>request_id</code> only for correlation, and MUST return the
current reconciled durable phase rather than replaying an earlier observation.

The prepare response MUST echo the request kind and intent. For
workspace/composite it returns a non-null destination path, classification, and
managed-replica ID; for provider/task-board it returns all three as null.
Commit, status, finalize, and rollback MUST return the identical kind/intent
and preserve that nullability. A provider transaction ID/state is non-null/
non-<code>none</code> exactly when the selected provider plan has at least one
provider-store operation; a backend-identity validation-only plan has no
provider transaction. Task-board commit returns <code>opened</code> exactly
after the journaled import/open sequence and otherwise <code>none</code>.
<code>passive_replica</code> may finalize only with
<code>dormant_validated</code>; <code>owner_resume</code> and
<code>ownership_transfer</code> may finalize only with the direct or task-board
owner-resumed tag matching the Session Record after the expected lease proves
the destination is the winner. Fork uses the matching owner-resumed tag under
its fresh epoch-1 lease. Dormant validation requires null profile fields.
Either owner-resumed tag requires the exact effective profile and profile-
source event fixed by the activated session/checkpoint. For ordinary takeover
or owner resume this is the selected checkpoint pair. For fork it is the new
Session Record's projected creation profile with null new-session source; the
source checkpoint's nullable profile event remains only in
<code>fork.created.source_profile_event_id</code>.
A passive finalization MUST NOT start/adopt a provider, enable
input, or emit a lease event.

Despite its retained operation name, <code>materialize.commit</code> ends in a
rollbackable <code>prepared</code> phase and MUST durably write the Section 10.6
journal before returning. It wraps any provider-plugin rollback token inside a
destination-local composite token; the plugin token never crosses RPC.
For a direct path the caller starts or resumes the provider, proves native
identity and process state, and then calls finalize with
<code>direct_owner_resumed</code>. For a task-board path, finalize itself uses
the durable Section 10.6 bridge IDs and token to adopt, resume, and prove status;
the caller MUST NOT perform those bridge mutations out of band.
<code>materialize.finalize</code> invokes provider
<code>materialize-commit</code> when applicable and removes host rollback bytes
only after the stated dormant or owner-resumed activation has been proved. For
a workspace/composite plan it writes the exact Section 10.6 Managed Replica
Marker before removing host rollback bytes and returns the same managed-replica
and marker IDs reported by <code>materialize.status</code>. Provider/task-board-
only plans return both IDs null. A marker write failure leaves the transaction
<code>committing</code> in the journal and retains rollback bytes.
<code>materialize.rollback</code> invokes provider rollback first, then the
task-board pre-adopt rollback/expiry procedure, then restores workspace bytes;
a failure in any layer leaves phase
<code>failed</code> and retains both recovery roots. Lost responses MUST be
recovered through <code>materialize.status</code>, never by guessing from a
destination directory.

The RPC rollback reason maps unchanged to the provider operation when a
provider manifest participates:

| RPC/journal cause | Provider rollback reason |
| --- | --- |
| Expected lease no longer wins before activation | <code>lease_lost</code> |
| Manifest, native discovery, board, workspace, or marker validation fails | <code>validation_failed</code> |
| Exact provider/task-board owner resume fails after prepare | <code>resume_failed</code> |
| Confirmed operator cancellation before activation | <code>operator_abort</code> |
| Restart reconciliation selects rollback | <code>crash_recovery</code> |

No other mapping exists in Mesh RPC 2.0.0. The reason is persisted in the host
journal before the provider call and is part of both layers' idempotency input.
The required materialization fixtures are:

| Fixture | Exact prepare selection | Required result/activation |
| --- | --- | --- |
| <code>MAT-WORKSPACE-STOPPED-SYNC</code> | <code>kind=workspace</code>, <code>intent=passive_replica</code>, one stopped session in materialization set, empty transfer set, workspace source/request only | Non-null path/classification/replica; dormant finalization; no process or lease change |
| <code>MAT-COMPOSITE-STOPPED-RESUME</code> | <code>kind=composite</code>, <code>intent=owner_resume</code>, already-winning stopped owner, empty transfer set, workspace plus provider source | Non-null path/classification/replica and provider transaction; exact owner resume before finalization; no new epoch |
| <code>MAT-PROVIDER-ONLY</code> | <code>kind=provider</code>, <code>intent=owner_resume</code>, provider source only, null workspace request | Null path/classification/replica/marker through every phase; provider transaction commits after owner resume |
| <code>MAT-TASK-BOARD-ONLY</code> | <code>kind=task_board</code>, <code>intent=passive_replica</code>, bundle source only, null workspace request | Null path/classification/replica/marker; imported/opened state remains dormant |
| <code>MAT-WORKSPACE-ONLY</code> | <code>kind=workspace</code>, <code>intent=owner_resume</code>, workspace source/request only | Non-null path/classification/replica/marker; provider transaction state remains <code>none</code> |
| <code>MAT-COMPOSITE-TAKEOVER</code> | <code>kind=composite</code>, <code>intent=ownership_transfer</code>, non-empty equal selected transfer cohort, workspace plus exactly one provider/bundle source | Prepare may precede fencing; owner-resumed finalization only after the destination lease wins |

<code>MAT-TASK-BOARD-OPENED-STATUS</code> is the exact status projection after
commit/import/open and before adopt:

~~~json
{
  "materialization_id": "0198f4c8-c290-73aa-9374-1234567890ab",
  "phase": "prepared",
  "kind": "task_board",
  "intent": "ownership_transfer",
  "plan_id": "sha256:19bab2d797f2914ee4d452310e0a1a1d280859bf099e193bb5f1ccf2ebbb394f",
  "checkpoint_id": "sha256:59c2b9bd739552dc011bc956cbee83990a8ccbb4beb6ed2a230d77108f98e888",
  "destination_path": null,
  "destination_classification": null,
  "managed_replica_id": null,
  "destination_marker_id": null,
  "provider_transaction_state": "none",
  "task_board_transaction_state": "opened",
  "task_board_manager_ref": "tbm:dormant:0198f4c8-7a10-7b22-8b3c-2234567890ab",
  "task_board_binding": null,
  "last_error_code": null
}
~~~

After successful owner finalize, the same object changes only
<code>phase=committed</code>, task-board state to <code>resumed</code>, manager
reference to the public adopted reference, and binding to the exact winning
session/epoch/lease. <code>MAT-TASK-BOARD-STATUS-N1</code> exposes an open token,
<code>N2</code> reports <code>opened</code> with a binding, and <code>N3</code>
reports <code>resumed</code> without one; all are invalid RPC results.

<code>MAT-COHORT-N1</code> uses an empty transfer set with ownership-transfer
intent, <code>MAT-COHORT-N2</code> uses a non-empty transfer set with passive
intent, <code>MAT-KIND-N1</code> supplies a workspace request to provider-only,
and <code>MAT-KIND-N2</code> returns a managed-replica ID for task-board-only.
Each fails before mutation.

Normative common failure response:

~~~json
{
  "protocol": "urn:ax:protocol:rpc",
  "protocol_version": "2.0.0",
  "request_id": "0198f4c8-f5c0-76dd-9677-1234567890ab",
  "ok": false,
  "error": {
    "schema": "urn:ax:schema:error",
    "schema_version": "1.0.0",
    "code": "lease_conflict",
    "message": "expected source lease is no longer the winner",
    "exit_code": 10,
    "retryable": false,
    "operation_id": "0198f4c8-06d0-77ee-8778-1234567890ab",
    "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
    "details": {}
  }
}
~~~

Arrays with digest identities MUST be sorted bytewise and contain no duplicate.
<code>inventory.children</code> prefixes are 0–64 lowercase hexadecimal
characters; a receiver MUST reject a prefix outside that range. One
<code>objects.get</code> response MUST remain within the negotiated line limit;
the caller batches IDs accordingly.

Every <code>session.*</code> and <code>handoff.*</code> mutation MUST be
accepted only from the configured destination/source host named by the active
operation and MUST revalidate the expected fencing token immediately before
each phase. One session MAY have at most one non-terminal graceful handoff.
For <code>handoff.prepare</code>, both cohort arrays MUST be non-empty and equal;
the current <code>session_id</code> MUST be a member. The receiver stores the
prepare-time WorkspaceGroupExpectation and cohort with the operation and
recomputes both before quiesce, stop, lease commit,
materialization finalization, and resume. Every per-session operation in one
whole-group takeover uses a distinct <code>operation_id</code> and the same
<code>group_operation_id</code>, destination, and expectation. No member lease
may advance until every migration-cohort member is safely stopped and prepared;
if any member fails or membership changes, all not-yet-fenced members abort and
all prepared destinations remain dormant. After the first member lease
advances, recovery MUST finish or explicitly recover every remaining cohort
member; it MUST NOT resume a stopped source member into the shared checkout.
Repeating a request with the same operation ID and canonical body returns the
recorded result; changing the body returns <code>idempotency_mismatch</code>.
<code>handoff.commit</code> is the only handoff RPC that can introduce the new
lease to the source. It MUST validate the complete Lease Record, require the
destination's committed checkpoint ID to equal that lease's checkpoint, and
require a successful <code>materialize.commit</code> result for the named
materialization/plan before unioning the lease and parking the old wrapper.

### 11.4 Anti-entropy union

Namespace membership is total and disjoint. It is selected by the validated
schema/byte class below, never by storage directory, caller preference, or the
kind of object that references it:

| Object or byte class | Inventory identity | Namespace/disposition |
| --- | --- | --- |
| Session Record, Lease Record, Checkpoint Record, Workspace Group Record, Provider Identity Record | Respective <code>record_id</code> or <code>checkpoint_id</code> | <code>record</code> |
| Session Event | <code>event_id</code> | <code>event</code> |
| Transfer Manifest, Blob Descriptor, Materialization Plan, Task-board Bundle public object | <code>manifest_id</code>, <code>descriptor_id</code>, <code>plan_id</code>, or <code>bundle_id</code> | <code>manifest</code> |
| Tombstone | <code>tombstone_id</code> | <code>tombstone</code> |
| Tombstone Acknowledgement | <code>ack_id</code> | <code>tombstone_ack</code> |
| Complete raw content blob, including opaque bundle/provider/Git bytes | <code>blob_id</code> (SHA-256 of raw bytes) | <code>blob</code> |
| Transfer Chunk Descriptor and raw chunk | No independent inventory identity; <code>chunk_id</code> verifies one manifest-authorized transfer unit | Inline/staging only; excluded from every Merkle namespace |
| Configuration, Provider Manifest/Probe, Structured Error, Observation Event, CLI Result | None in the replicated union | Machine-local or transient; excluded |
| Provider, RPC, and task-board bridge request/result envelopes | Request/operation ID is idempotency or correlation data, not content identity | Transient; excluded |
| Materialization Journal and Managed Replica Marker variants | Journal has no content identity; marker ID is machine-local commit evidence | Machine-local recovery state; excluded |
| Derived SQLite rows, transfer/commit markers, tokens, terminal state, credentials, locks, sockets, PIDs | None | Machine-local/transient; excluded |

An identity MUST occur in exactly one namespace. A Blob Descriptor therefore
appears in <code>manifest</code> while the raw bytes it describes appear in
<code>blob</code>; neither duplicates the other. A Task-board Bundle public
object appears in <code>manifest</code>, and every opaque byte object it names
appears in <code>blob</code>. <code>objects.get</code> MUST schema-validate each
non-blob response and reject an ID whose schema maps to another requested
namespace. Local excluded objects MUST NOT affect any root or count.

For each Section 11.3 Namespace, peers build the same deterministic sparse
radix trie over the 64 lowercase hexadecimal characters after
<code>sha256:</code>. Radix width is exactly one hexadecimal nibble. The root
prefix is the empty string. For a node at prefix P:

1. collect the unique IDs whose hex payload begins with P and set
   <code>count</code> to that set size;
2. when count is zero, only the empty root exists; it has no children or IDs;
3. when count is one, the node is a leaf at that prefix, has no children, and
   places the one complete <code>sha256:</code> ID in <code>ids</code>;
4. when count is at least two, <code>ids</code> is empty and the node has one
   child for each non-empty next-nibble group; a single child is retained when
   the IDs share that nibble; and
5. count greater than one at a 64-nibble prefix is an integrity failure because
   duplicate IDs were required to have been removed.

Children are sorted by ASCII label <code>0</code>–<code>9</code>, then
<code>a</code>–<code>f</code>. IDs are sorted bytewise. A child's
<code>count</code> and <code>hash</code> MUST equal its recursively constructed
node. The logical node object contains exactly:

~~~text
{"children":[{"count":uint53,"hash":digest,"label":hex-nibble},...],"count":uint53,"domain":"urn:ax:merkle-node:1","ids":[digest,...],"namespace":Namespace,"prefix":lowercase-hex}
~~~

The byte sequence hashed is the UTF-8 RFC 8785 JCS encoding of that logical
object exactly; <code>domain</code> provides domain separation. The node hash is
<code>sha256:</code> plus SHA-256 of those bytes. It is not computed from the
wire response envelope. <code>inventory.roots.root_id</code> and
<code>inventory.children.node_hash</code> are this value. A request for a valid
but non-materialized non-root prefix returns <code>not_found</code> rather than
inventing an empty child.

These Mesh RPC 2.0.0 fixtures are normative. The middle column is the complete
canonical root-node byte string before hashing:

| Fixture ID set in namespace <code>record</code> | Canonical root-node bytes | Expected root hash |
| --- | --- | --- |
| Empty | <code>{"children":[],"count":0,"domain":"urn:ax:merkle-node:1","ids":[],"namespace":"record","prefix":""}</code> | <code>sha256:6ed4e56353243641ade20bd0f9e9ae426dcc2d02c962c0a2e7208baae2eef1e8</code> |
| Singleton <code>sha256:000…000</code> | <code>{"children":[],"count":1,"domain":"urn:ax:merkle-node:1","ids":["sha256:0000000000000000000000000000000000000000000000000000000000000000"],"namespace":"record","prefix":""}</code> | <code>sha256:ab4c73cb6d0612884e1a3fec5f4e93d3a7e47f4f96899681216524d3abfaab07</code> |
| Branch <code>sha256:000…000</code>, <code>sha256:fff…fff</code> | <code>{"children":[{"count":1,"hash":"sha256:f047338baa8ba0e4050630c4bae2b18ae1e79366ed5d5b4b140952eebf74e6fc","label":"0"},{"count":1,"hash":"sha256:feb44d42c24a06a3ae665f317840b771cbd6d575dd0b8110f0c083a7fc0c504d","label":"f"}],"count":2,"domain":"urn:ax:merkle-node:1","ids":[],"namespace":"record","prefix":""}</code> | <code>sha256:34bdaac6a61aa6d54cfd1315fa6325489e34b83206b891e765e02850a5f14c26</code> |

The exact <code>inventory.children</code> success bodies for those root
requests are:

~~~json
{
  "namespace": "record",
  "prefix": "",
  "count": 0,
  "node_hash": "sha256:6ed4e56353243641ade20bd0f9e9ae426dcc2d02c962c0a2e7208baae2eef1e8",
  "children": [],
  "ids": []
}
~~~

~~~json
{
  "namespace": "record",
  "prefix": "",
  "count": 1,
  "node_hash": "sha256:ab4c73cb6d0612884e1a3fec5f4e93d3a7e47f4f96899681216524d3abfaab07",
  "children": [],
  "ids": [
    "sha256:0000000000000000000000000000000000000000000000000000000000000000"
  ]
}
~~~

~~~json
{
  "namespace": "record",
  "prefix": "",
  "count": 2,
  "node_hash": "sha256:34bdaac6a61aa6d54cfd1315fa6325489e34b83206b891e765e02850a5f14c26",
  "children": [
    {
      "label": "0",
      "count": 1,
      "hash": "sha256:f047338baa8ba0e4050630c4bae2b18ae1e79366ed5d5b4b140952eebf74e6fc"
    },
    {
      "label": "f",
      "count": 1,
      "hash": "sha256:feb44d42c24a06a3ae665f317840b771cbd6d575dd0b8110f0c083a7fc0c504d"
    }
  ],
  "ids": []
}
~~~

For the branch fixture, the child canonical bytes are the same logical shape
with prefix <code>0</code> or <code>f</code>, count one, no children, and the
corresponding full ID; their expected hashes are the values carried above.
Peers compare roots, recursively request differing children, and exchange
missing immutable objects.

<code>MIXED-NS-1</code> is the normative mixed-schema inventory fixture. The
synthetic IDs stand for schema-valid objects/bytes in the row shown; their
contents are not used to compute the inventory trie beyond their validated
identities. For compact exact notation, <code>Z(n)</code> is
<code>sha256:</code> followed by 63 ASCII <code>0</code> characters and the
single lowercase hexadecimal digit n; <code>T(n)</code> is the same construction
with 63 ASCII <code>2</code> characters. Thus every value has exactly 64 digest
nibbles.

| Namespace | Schema/byte assignments in bytewise ID order | Expected count | Expected root |
| --- | --- | ---: | --- |
| <code>record</code> | Session <code>Z(1)</code>; Lease <code>Z(2)</code>; Checkpoint <code>Z(3)</code>; Workspace Group <code>Z(4)</code>; Provider Identity <code>Z(5)</code> | 5 | <code>sha256:44c71ab5fdb7403c57a8a929d9fc90b2db3e8829b2615901c0841216d6750580</code> |
| <code>event</code> | Session Event <code>sha256:1111111111111111111111111111111111111111111111111111111111111111</code> | 1 | <code>sha256:533934b217b3d2f3999a2ec8cbb5ccfc0a7aff29c4eee0f7d35a0adca8cef15e</code> |
| <code>manifest</code> | Transfer Manifest <code>T(1)</code>; Blob Descriptor <code>T(2)</code>; Materialization Plan <code>T(3)</code>; Task-board Bundle <code>T(4)</code> | 4 | <code>sha256:cb60d01f92e1dae564a49f2ae782b9cf479a9e3849d1c84a8c907b68dec85202</code> |
| <code>tombstone</code> | Tombstone <code>sha256:3333333333333333333333333333333333333333333333333333333333333333</code> | 1 | <code>sha256:b890fa63b85a48c6e6a5e42cece3fb50e545062da103bb1f5bcfaa80d922f0d9</code> |
| <code>tombstone_ack</code> | Tombstone Acknowledgement <code>sha256:4444444444444444444444444444444444444444444444444444444444444444</code> | 1 | <code>sha256:4f5c58b2cee87816f09520570056ebe64c408dc484ff192aaf8583a308eda8e5</code> |
| <code>blob</code> | Raw blob <code>sha256:5555555555555555555555555555555555555555555555555555555555555555</code> | 1 | <code>sha256:eaff5e30efa41b95ad419948886433af94ab3c95de2a574a1c1cfcf6d45a7cd2</code> |

The expected roots use the exact Section 11.4 node encoding and namespace
domain.

In <code>MIXED-NS-EXCHANGE</code>, peer B lacks Checkpoint <code>Z(3)</code>,
Blob Descriptor <code>T(2)</code>, and the raw blob of 64 ASCII <code>5</code>
nibbles. Only <code>record</code>, <code>manifest</code>, and
<code>blob</code> roots differ. Recursive inventory plus
<code>objects.get</code> retrieves the Checkpoint and Descriptor; manifest-
authorized chunk transfer retrieves the raw blob. Closure validation then
produces all six roots above. Classifying the Descriptor as a record,
enumerating its chunks independently, or including a local marker is the
negative fixture <code>MIXED-NS-N1</code> and MUST fail the expected roots and
schema-to-namespace validation.

Union rules are:

1. an unknown digest is added only after schema and digest validation;
2. an existing identical digest is idempotent;
3. same digest with different bytes is quarantined and aborts sync;
4. tombstones and acknowledgements are unioned like records, not executed
   during object exchange;
5. lease heads are derived after union using Section 5.3;
6. losing-lease events are preserved in divergent branches; and
7. referenced blob transfer and destination materialization MUST start only
   after record union succeeds.

No last-writer-wins rule exists. Timestamps MUST NOT select a winner.

### 11.5 Resumable staging and validation

<code>transfer.begin</code> returns a UUIDv7 transfer ID and the bitmap of
objects/chunks already verified in a retained staging area. The sender transmits
only missing pieces. A retry with the same manifest and transfer ID MUST be
idempotent.

Validation MUST perform, in order:

1. frame and schema validation;
2. every object/chunk digest and size;
3. complete blob reassembly digest;
4. manifest path and type safety;
5. exclusion-policy confirmation;
6. referenced-object closure;
7. provider or task-board bundle validation;
8. workspace case-collision, symlink, and platform checks;
9. destination conflict detection; and
10. free-space and atomic-commit capability checks.

Failed staging MUST be retained for the configured retention period when safe,
with no destination mutation. <code>ax sync --resume TRANSFER_ID</code> resumes
it. Expired staging MAY be removed because it is not authoritative state.

### 11.6 Atomic commit

Before any filesystem mutation, the materializer MUST resolve every Section
10.5 authority and operation target, prove path disjointness, and revalidate
the operation's expected predecessor. A path outside its named authority or a
larger mutation than its <code>atomicity_boundary</code> is
<code>unsafe_path</code>, even if the process account could write it.

For a new or replaceable directory on one filesystem, the materializer MUST
construct a sibling staging directory, fsync durable contents and parent
directories where the platform supports it, and commit by atomic rename. When
an exchange primitive exists, replacement SHOULD use it.

For a merge into a provider's existing native store, the provider plan MUST
name the exact <code>provider_store</code> authority, targets, boundaries, and
expected prior digests. Each file MUST be
installed through a same-directory temporary name and atomic rename. Unrelated
native sessions MUST remain untouched.

A <code>two_phase_multi_root</code> plan first creates and fsyncs a rollback
copy for every target across all authorities, then performs only the listed
per-target atomic renames. The Materialization Journal is the coordinator. A
crash may expose a prefix of committed authorities, but recovery MUST either
validate and finish that exact plan or restore all predecessors; it MUST never
call the prefix a successful materialization or publish a marker early.

On Windows, open handles can prevent rename. The implementation MUST stop known
processes, retry boundedly, and fail with retained staging if atomic replacement
cannot be proven. It MUST NOT fall back to in-place partial overwrite.

### 11.7 Conflict handling

Workspace replication is enabled by default. Before materialization, the
destination is classified:

- <code>absent</code>;
- <code>empty</code>;
- <code>managed_unchanged</code>, matching its last checkpoint;
- <code>managed_divergent</code>; or
- <code>unmanaged_nonempty</code>.

This ordered five-value registry is the canonical
<code>DestinationClass</code> used by domain logic, RPC, CLI Result, journal
recovery, and Observation Events. The former spellings
<code>matching_managed</code>, <code>divergent_managed</code>, and
<code>unmanaged</code> are invalid in version 1.0.0; <code>empty</code> is never
collapsed into <code>absent</code>.

Only the first three MAY be committed automatically.
<code>managed_divergent</code> and <code>unmanaged_nonempty</code> MUST fail
closed with a structured comparison. The operator MAY then:

- inspect <code>ax diff</code>;
- materialize to a new copy;
- create a separate Git worktree;
- or explicitly replace a managed replica using
  <code>--replace-managed-replica --expect-checkpoint CHECKPOINT_ID</code>.

An unmanaged nonempty path MUST never be replaced. Before explicit managed
replacement, <code>ax</code> MUST checkpoint and preserve the destination's
divergent state. Classification MUST use the Section 10.6 current marker and a
fresh content capture; SQLite or a directory-name convention is insufficient.
The current owner then emits
<code>replica.replace_confirmed</code>: its expected checkpoint is the exact
checkpoint stored by the current marker, its expected marker ID is that exact
current marker, and its replacement checkpoint is the selected source
checkpoint. It next issues the matching <code>managed_replica</code> Tombstone
with the confirmation event as its causal basis and emits
<code>tombstone.issued</code>. The replacement Materialization Plan uses that
Tombstone ID and marker predecessor; without this event/Tombstone chain it MUST
fail before mutation.
Silent overwrite, timestamp-based overwrite, and broad path deletion are
forbidden.

## 12. Workspace replication

### 12.1 Workspace snapshot

Every checkpoint references a workspace-group Transfer Manifest. The snapshot
MUST be <code>kind = workspace_group</code> and carry the exact Section 10.4
<code>WorkspaceSnapshot</code>; every referenced member tree is in its transitive
child closure. That wire representation contains the exact state needed to
resume:

- each required repository or managed directory;
- sanitized remote URLs;
- HEAD object ID and symbolic branch, or detached state;
- reachable local commits needed for HEAD and submodules;
- staged index state;
- unstaged tracked content;
- untracked non-ignored content;
- configured agent project files even when ignored, subject to exclusions;
- recursive submodule identity, commit, and working state;
- repository-relative cwd; and
- the workspace-group sharing/worktree policy.

Ignored build outputs are excluded by default. An ignored file is included only
when named by a project/provider include rule and classified as non-secret.

### 12.2 Git workspace schema

The Git wire schema is the exact <code>kind = git</code>
<code>WorkspaceSnapshotMember</code> and its closed nested types in Section
10.4. There is no second prose-only Git descriptor. In particular,
<code>head</code> distinguishes branch, detached, and unborn states;
<code>object_pack</code> and its inventory carry offline object closure; the raw
<code>index</code> blob plus logical <code>GitIndexEntry</code> array preserve
stages and flags; <code>working_tree_manifest_id</code> carries actual tracked,
unstaged, untracked, and explicitly included ignored bytes; and submodule,
feature, cwd, and agent-config fields are all required members of that same
Transfer Manifest object.

Remote URLs MUST be sanitized. User info containing a password/token, credential
helpers with embedded secrets, and machine-local paths MUST be removed.
Repository config MUST be reconstructed from an allowlist: remotes, branch
tracking, object format, safe submodule URLs, and required worktree extensions.
Hooks, credential configuration, local include files, and arbitrary commands
MUST NOT be copied.

The <code>WS-GIT-ROUNDTRIP-1</code> and
<code>WS-TREE-ROUNDTRIP-1</code> fixtures in Section 10.4 are normative inputs
to <code>AC-WORK-001</code>/<code>AC-WORK-002</code>. An implementation MUST
parse those exact descriptors before invoking Git or writing a destination;
it MUST reject their listed negative mutations without relying on a live
repository to fill missing schema facts.

### 12.3 Git capture and materialization

Capture MUST quiesce agent input and filesystem-mutating provider work. It MUST
read Git state consistently and fail if HEAD, index, or included file digests
change during capture.

Materialization MUST:

1. create or validate a managed repository/worktree;
2. configure sanitized remotes;
3. import each repository's object pack into that repository's object database
   only and verify its required OIDs there; a superproject gitlink is validated
   against the child descriptor/pack, never by co-mingling child objects into
   the parent database;
4. establish the exact branch or detached HEAD without contacting a remote;
5. construct a temporary index from the descriptor and atomically install it;
6. materialize actual working-tree bytes, modes, and symlinks;
7. recurse through submodules using their logical mappings; and
8. compare resulting HEAD, index, status, cwd, and content digests with the
   descriptor.

An implementation MAY use the Git executable, a Go library, or both, but the
observable result is fixed by this section. Unsupported Git extensions, case
collisions, inaccessible filters, or object-format mismatches MUST fail closed.
Network fetch MAY be offered as an explicit repair, but materialization MUST NOT
silently depend on it.

Staged and unstaged states are distinct: the reconstructed index represents the
staged version, while the working-tree manifest represents actual working
bytes. A clean-looking working tree with a wrong index is a failed
materialization.
For a submodule, the superproject HEAD-tree pointer, stage-0 index
<code>gitlink_oid</code>, and checked-out <code>head.oid</code> MUST reproduce the
exact clean/staged/unstaged combination in Section 10.4.

### 12.4 Non-Git managed trees

A non-Git member is a complete managed tree manifest containing included
directories, files, symlinks, hardlinks, modes, and content digests. Capture
MUST verify the tree did not change between enumeration and digest completion,
or retry from the start.

The destination MUST be absent, empty, or a matching managed replica. A
divergent tree follows Section 11.7. There is no directory timestamp merge.

### 12.5 Agent project configuration

Provider/project instruction files required to resume MUST be included when
they are inside the managed workspace and not secret-bearing. Examples include
repository-scoped agent instructions, provider settings explicitly approved for
the project, and task-board files for a local board.

Global user configuration, plugins installed outside the workspace, API keys,
MCP OAuth tokens, keychains, and login state are machine-local. The destination
<code>doctor</code> check MUST report missing prerequisites rather than copying
them.

### 12.6 Workspace groups and worktrees

A group using <code>shared_checkout</code> is one atomic conflict and takeover
unit. All active sessions sharing it MUST quiesce, or graceful takeover MUST
fail with <code>workspace_group_busy</code>.

Before either strategy, the coordinator computes the exact Section 11.3
WorkspaceGroupExpectation from immutable Session Records, authoritative
session Tombstones, winning leases, lifecycle state, and local managed-replica
markers. It MUST NOT read a mutable <code>session_ids</code> list from a group
record. Every phase revalidates the same expectation.

With <code>workspace_mode = whole_group</code>, the coordinator creates one
group operation and a distinct idempotent handoff operation for every
member of
<code>MaterializationCohort.ownership_transfer_session_ids</code>. It quiesces
and stops exactly those cohort owners,
stages one workspace-group snapshot, prepares every successor lease, and only
then advances any lease. Destination resume is withheld until every cohort
lease has converged to that destination; a partial post-fence failure leaves
the affected destination sessions stopped and parks the old shared checkout
rather than resuming a subset against it.

The operator MAY instead select <code>separate_worktrees</code>. The materializer then
creates one managed Git worktree per active logical session from the shared
object store, applies that session's index/working state, and records independent
destination paths. It MUST not point two active owners at one mutable worktree.
Managed-tree members become separate managed copies. Only the selected
session's lease moves; every non-migrating owner retains its source checkout.

<code>WG-TAKEOVER-WHOLE-POS</code> starts with two active sessions sharing one
marker, uses one group operation/two session operations, stops both before the
first lease advance, installs one group snapshot, advances both leases, then
resumes both at the destination. <code>WG-TAKEOVER-WORKTREE-POS</code> moves one
session to a new marker/worktree and leaves the other lease and checkout
unchanged. <code>WG-TAKEOVER-JOIN-N1</code> adds a Session Record after prepare;
<code>WG-TAKEOVER-LEAVE-N1</code> adds an authoritative session Tombstone after
prepare. Both MUST fail with <code>workspace_group_changed</code> before any
lease advance; after an advance they enter the explicit partial group recovery
above and never silently shrink the cohort.

## 13. End-to-end lifecycle flows

Every mutating flow has a UUIDv7 <code>operation_id</code>. A retry with the
same operation ID and inputs MUST be idempotent. A retry with different inputs
MUST fail with <code>idempotency_mismatch</code>.

### 13.1 Direct-session launch

Preconditions:

- configuration and local host identity are valid;
- the session name is unused across the reachable mesh;
- the provider plugin is trusted and <code>probe</code> succeeds;
- requested profile mapping is available;
- destination workspace is validated or captured as a new managed workspace;
- the terminal backend is available; and
- no task-board fields are supplied.

Transitions:

1. Allocate session, caller-stable bootstrap-operation,
   first-checkpoint-operation, and initial lease IDs. If the workspace has a
   valid current managed-replica marker, reuse its unique Workspace Group
   Record after exact topology validation; otherwise allocate new workspace-
   group/workspace IDs and one new group record. Epoch is 1 and the local host
   is the holder.
2. Persist any new Workspace Group Record, then the Session Record referencing
   that group, the initial Lease Record, and <code>session.created</code> carrying
   both operation IDs before creating a process. Joining
   an existing group publishes no group update; derived membership changes by
   union of the new Session Record.
3. Create the durable terminal entry <code>ax pane SESSION_ID</code> with the
   bootstrap operation ID.
4. Call provider <code>launch</code> and validate its argv/env-name plan.
5. Start the provider through the terminal backend with the epoch-1 fencing
   token and persisted profile. Persist <code>provider.launched</code> with
   <code>execution_profile</code> equal to the Session Record and
   <code>profile_source_event_id = null</code>.
6. Call <code>identify-session</code>; persist the Provider Identity Record and
   <code>provider.identified</code> event.
7. When the first safe boundary is observed, create the workspace-group root
   manifest. If <code>portable_store</code> is enabled, call provider
   <code>native-store-plan phase=capture</code> and <code>capture</code> with the
   first-checkpoint operation ID into an
   isolated Object Sink; otherwise create a zero-entry provider manifest that
   references the exact Provider Identity Record. Validate both, then publish
   the direct-path checkpoint with a non-null provider manifest.
8. Publish immutable objects for replica sync and report <code>running</code>
   or <code>idle</code>.

The first-checkpoint operation ID keys the capture/export and checkpoint-
publication transaction even when a backend-only provider emits a zero-entry
manifest. An identical retry reuses the same immutable objects and event;
changing either operation ID after <code>session.created</code> is
<code>idempotency_mismatch</code>.

Until step 7 publishes the first Checkpoint, this is the closed
<em>bootstrap window</em>. The epoch-1 lease is authoritative with
<code>checkpoint_id = null</code>; the derived session state is
<code>creating</code> while a retry is eligible and <code>failed</code> after an
ambiguous/live-process error or explicit abort. No implementation may invent a
checkpoint ID or call that state <code>stopped</code>.

Failure handling is phase-exact:

| Fixture/boundary | Durable facts | Recovery |
| --- | --- | --- |
| <code>BOOT-DIRECT-BEFORE-TERMINAL</code> | Session/lease exist; no terminal, process, identity, or checkpoint | <code>ax resume</code> may retry terminal creation under the same IDs after probe; force stop emits bootstrap abort |
| <code>BOOT-DIRECT-AFTER-TERMINAL</code> | Wrapper exists; no provider process or checkpoint | Resume reuses that wrapper and retries launch once; force stop removes only the inert wrapper after closure proof |
| <code>BOOT-DIRECT-AFTER-PROCESS</code> | Provider may be live; no identified identity/checkpoint | Resume MUST first reconcile exact PID/PTY and bootstrap operation; if liveness/identity is ambiguous, remain failed and require stop/reconciliation rather than start a second process |
| <code>BOOT-DIRECT-AFTER-IDENTITY</code> | Identity/event exist; no checkpoint | Resume validates the same identity and continues capture; it MUST NOT call provider new-session launch |
| <code>BOOT-DIRECT-BEFORE-CHECKPOINT</code> | Captured objects may exist but no Checkpoint Record is authoritative | Validate/reuse immutable objects and publish the first checkpoint, or abort; objects are never relabeled as a checkpoint |

A bootstrap retry is allowed only at epoch 1, with a null lease checkpoint,
no authoritative <code>session.bootstrap_aborted</code>, and either proven no
provider process or one exact reconciled process/identity from this launch.
The retry reuses every already persisted operation/terminal/provider identity
and is idempotent; it never creates a second raw provider process. A graceful
stop may first reach a safe boundary and publish the initial checkpoint, then
execute the ordinary checkpointed stop. A force stop may close the process and
emit <code>session.bootstrap_aborted</code> followed by
<code>session.stopped</code> with null checkpoint,
<code>resumable=false</code>, and <code>closure_kind=bootstrap_abort</code>; the
resulting lifecycle state is <code>failed</code>, not <code>stopped</code>.
Closure with an unknown/live process is unsuccessful and emits neither event.

<code>BOOT-ABORT-CROSS-CONTRACT</code> is the exact successful force-closure
projection for a failure after process creation and before identity:

| Surface | Exact authoritative values |
| --- | --- |
| <code>session.bootstrap_aborted</code> payload | <code>{operation_id:BOOTSTRAP_ID,failure_phase:after_process,provider_identity_record_id:null,manager_session_ref:null,process_closed:true,store_closed:true,resume_allowed:false}</code> |
| Following <code>session.stopped</code> payload | <code>{graceful:false,checkpoint_id:null,resumable:false,closure_kind:bootstrap_abort,process_closed:true,store_closed:true}</code> |
| RPC <code>session.stop</code> success | <code>{operation_id:STOP_ID,already_applied:false,closure:{process_closed:true,store_closed:true,exit_code:EXIT_OR_NULL,remaining_process_handles:[],final_store_generation:null},final_checkpoint_id:null,resumable:false,bootstrap_aborted:true,resulting_state:failed}</code> |
| CLI <code>stop</code> body | Exact failed <code>SessionSummary</code> with both newest-checkpoint members null, plus <code>{graceful:false,checkpoint_id:null,resumable:false,bootstrap_aborted:true,process_closed:true,store_closed:true}</code> |

The event IDs and sequences are ordinary Section 5.2 identities. The RPC and
CLI operation ID is STOP_ID; the abort event retains BOOTSTRAP_ID so audit can
join the abandoned launch. <code>BOOT-ABORT-N1</code> changes any one null to a
digest, any closure boolean to false, resulting state to stopped, or resumable
to true; the attempted success MUST be rejected. After identity, exactly the
direct provider-identity or task-board manager-reference member becomes
non-null as Section 5.2 requires.

The command MUST NOT delete the workspace, native provider bytes, or immutable
records during recovery. The initial lease remains authoritative until an
explicit later ownership operation.

### 13.2 Task-board session launch

Preconditions are the direct launch preconditions except that the official
task-board bridge and the requested task-board capability MUST be available.
The logical board identity and, when applicable, exact
<code>board-goal-v2</code> reference/revision MUST be known. The Section 14.1
board ID/URL, launch mode, goal pair, and binding rules are the only public
resolution contract; provider ID or current directory MUST NOT silently choose
them.

Transitions:

1. Allocate distinct caller-stable bootstrap and first-checkpoint operation
   IDs. Create and durably persist the
   Workspace Group Record or reuse a marker-validated existing one exactly as
   Section 13.1, then create and durably persist the
   <code>kind = task_board</code> Session Record with creation-time
   <code>manager_session_ref = null</code>, the epoch-1 lease, and
   <code>session.created</code> carrying both IDs before asking task-board to
   create a process.
2. Invoke the Section 9.2 public bridge <code>launch</code> command with the
   bootstrap operation ID, the exact persisted lease/profile/provider/mode/goal/launch
   plan, logical workspace mapping, and no provider-private mutation.
3. Task-board returns a public manager session reference, exact provider
   version, ax binding, and capability result. Validate every repeated input,
   then persist
   <code>task_board.launched</code> with the Session Record profile and
   <code>profile_source_event_id = null</code>; this event, not an edit to the Session
   Record, establishes the current manager reference.
4. At a manager-proven safe boundary, invoke official
   <code>session export --mode snapshot</code> with the persisted first-checkpoint
   operation ID from <code>session.created</code>. Require the exact Section 9.2
   BridgeSafeBoundary with <code>safe = true</code>; input is released only
   after the proof and bundle are durable and before the bridge returns.
5. Validate the Task-board Bundle as opaque bytes plus public manifest.
6. For a local board, capture <code>.task-board</code> in the workspace
   manifest. For a remote board, verify the destination-independent board ID.
7. Map the bridge proof to Checkpoint Safe Boundary Evidence with
   <code>evidence = task_board_bridge</code>, publish the checkpoint, and report
   running/idle state. No private inspection may fill a missing proof member.

If the launch response is lost, repeat bridge <code>launch</code> with the same
bootstrap operation ID and identical body; task-board MUST return the recorded manager
reference without starting another process. A different body is
<code>idempotency_mismatch</code>. If launch succeeds but event persistence
fails, retry the event write from that recorded public result before accepting
new ax commands; private manager state is never queried.

If task-board creation succeeds but export fails, the local host remains owner,
the session is usable locally, and <code>ax</code> MUST report
<code>checkpoint_unavailable</code>. Cross-host takeover and fork remain
disabled until an export succeeds. <code>ax</code> MUST NOT repair the failure
by reading private manager state.

If the export response is lost, repeat the exact export operation ID and body.
Only the recorded bundle and safe-boundary proof may be used; a status response
that merely says <code>idle</code> is not a replacement checkpoint proof.

The task-board launch remains in the same bootstrap window until step 7. The
direct bootstrap rules apply with bridge status and caller-stable launch/export
IDs replacing PID/native-store reconciliation:

| Fixture/boundary | Required recovery |
| --- | --- |
| <code>BOOT-TB-BEFORE-LAUNCH</code> | Resume retries the same launch operation/body; no manager may exist under a new operation ID |
| <code>BOOT-TB-AFTER-LAUNCH</code> | Reconcile the public manager reference and exact Ax Binding, then retry export; do not inspect private state |
| <code>BOOT-TB-AFTER-EXPORT</code> | Reconcile the same export operation, validate bundle/proof, and publish the first checkpoint |
| <code>BOOT-TB-ABORT</code> | Bridge force-stop closes or proves absent the exact manager; emit bootstrap abort with null checkpoint and non-resumable failed state |

An ambiguous manager binding or status prevents both a second launch and a
successful abort. A later <code>ax resume</code> may bootstrap-retry only under
the exact epoch-1/null-checkpoint/no-abort predicate in Section 13.1.

### 13.3 Sync

Preconditions:

- source and destination are allowlisted and complete the RPC handshake;
- relevant contract major versions are compatible; and
- any owner-authored checkpoint carries the current winning lease.

Sync normally transfers the newest already validated checkpoint and does not
pause a running provider. If the owner elects to create a fresh checkpoint, it
MUST first establish the Section 7.6 safe boundary; a task-board session uses
bridge <code>export --mode snapshot</code> so input is released before sync
continues. A replica MUST never ask a provider or manager to create a new
checkpoint.

Transitions:

1. Exchange lease heads and inventory Merkle roots.
2. Union missing immutable records/events/tombstones and derive the winning
   lease.
3. Identify referenced manifests/blobs absent from either peer.
4. Begin or resume staged chunk transfer.
5. Validate and atomically commit immutable objects.
6. Optionally call <code>materialize.prepare</code> with
   <code>intent = passive_replica</code>, the selected checkpoint sessions in
   <code>materialization_session_ids</code>, and an empty ownership-transfer
   set. Choose workspace/composite when workspace bytes participate and
   provider/task-board only when they do not. A stopped replica is valid. The
   destination may commit/finalize only as dormant and MUST NOT run or resume a
   provider.
7. Record a <code>sync.completed</code> observation with counts/digests, never
   payload contents.

Syncing a replica MUST NOT run or resume the provider. A conflict MAY leave
immutable objects synchronized while workspace materialization remains
blocked; the result is partial and MUST use exit 15. A transport failure leaves
verified staging resumable.

### 13.4 Local attach

<code>ax attach NAME --local</code> requires the local host to be the winning
owner and the wrapper to be attachable. Before connecting input, it MUST refresh
the lease from reachable peers or state that it is operating on the latest
known lease within the configured refresh interval.

If a higher or winning same-epoch lease is observed, the wrapper MUST block
input, park or terminate its stale provider according to policy, preserve
diagnostics, and return <code>stale_owner</code>. Attach never changes
ownership.

### 13.5 Remote attach

Preconditions:

- a remote allowlisted host is the winning owner;
- SSH authentication succeeds; and
- the remote wrapper is attachable.

The local process executes the argv-equivalent of:

~~~shell
ssh -t HOST ax attach NAME --local
~~~

The remote command resolves NAME again and verifies the lease before accepting
input. The initiating host remains a replica. No Lease Record, workspace
materialization, provider snapshot, or task-board adoption is changed.

If SSH disconnects, the provider and durable terminal continue on the owner.
The operator MAY run remote attach again. If the owner cannot be reached, the
command reports <code>owner_unreachable</code> and suggests graceful takeover
only when contact returns, explicit force takeover, fork from the newest local
checkpoint, or cancel.

### 13.6 Graceful takeover

Command form is <code>ax takeover NAME --to HOST</code>; <code>--to</code>
defaults to the local host in interactive use.

Preconditions:

- source is reachable and proves it holds the winning lease;
- destination is allowlisted, is not the source, and has compatible contracts;
- destination provider/platform capabilities required by the session are
  available;
- workspace-group members can all be quiesced or separated into worktrees;
- one exact WorkspaceGroupExpectation and Section 12.6 workspace mode have
  been selected;
- destination conflicts are absent or already resolved;
- task-board bridge is available for a task-board session; and
- no other takeover operation is active for the session.

Transitions:

1. Destination allocates one group operation ID and one session operation ID
   for each migration-cohort member. It calls <code>handoff.prepare</code> for
   each, naming the identical WorkspaceGroupExpectation, source lease,
   destination host, expected source checkpoint, and MaterializationCohort whose
   two arrays both equal the selected migration cohort. A single-member cohort
   still carries the exact expectation and one-element arrays.
2. Source blocks new input and changes <code>running|idle</code> to
   <code>quiescing</code>.
3. Through <code>handoff.quiesce</code>, source calls provider or task-board
   quiesce and waits for a complete safe boundary. A task-board source uses
   bridge <code>export --mode handoff</code>, requires
   <code>BridgeSafeBoundary.safe = true</code>, maps it exactly to RPC and
   checkpoint evidence, and retains its source-control token. Timeout or an
   incomplete bridge proof fails closed.
4. Source captures a fresh checkpoint under the current lease. A direct source
   uses the Section 7.5 Object Sink path for a portable provider snapshot or a
   validated zero-entry identity manifest for a backend-only provider; a
   task-board source uses only the opaque bundle. Both use the exact Section
   10.4 workspace-group root.
5. Source performs the final bulk record/blob/workspace/board sync to
   destination.
6. Destination stages, validates, and conflict-checks every referenced object.
   It does not resume.
7. Destination calls <code>handoff.stop</code>. Source requests graceful
   provider/task-board stop, verifies process exit and durable-store closure,
   and records <code>session.stopped</code>. A task-board source consumes the
   bridge source-control token with bridge <code>stop</code>.
8. If normal exit appended provider/manager closure records, source captures a
   closure-only delta, creates a superseding validated checkpoint, and syncs
   that delta. Any unexpected workspace/background mutation fails the graceful
   flow while the source remains the stopped owner.
9. Destination calls tagged <code>materialize.prepare</code> with
   <code>intent = ownership_transfer</code>, the exact non-empty selected cohort
   in both cohort arrays, and kind workspace/provider/task-board/composite from
   the checkpoint sources. It then performs atomic materialization through RPC
   <code>materialize.commit</code>, which leaves a durable rollbackable prepared
   transaction; a direct portable-store path invokes provider
   <code>materialize</code> inside it. For task-board, destination also performs
   the journaled Section 10.6 import/open sequence inside commit, never before
   prepare. No prepared path accepts input.
10. After every migration-cohort member is stopped/prepared and group
   expectation still matches, destination creates each member's epoch
   <code>source_epoch + 1</code>, predecessor source
   lease, reason <code>graceful_takeover</code>, and checkpoint from step 4.
   When step 8 created a superseding checkpoint, that checkpoint replaces the
   step-4 checkpoint in this lease.
   Destination persists each lease, then calls <code>handoff.commit</code> so source and
   destination union and persist that Lease Record. Destination MUST verify it
   is still the winning lease after union; if a concurrent higher/winning lease
   exists, it MUST NOT adopt or resume.
11. For a direct session, destination validates native discovery and resumes
    through <code>ax pane SESSION_ID</code> with the checkpoint-derived
    effective profile and new fencing token, using plugin <code>resume</code>.
    For task-board, destination performs no out-of-band adopt or resume.
12. After exact direct process status proves the owner resumed, destination
    invokes <code>materialize.finalize</code> with
    <code>direct_owner_resumed</code>, the effective profile, and its source
    event. For task-board, it invokes finalize with
    <code>task_board_owner_resumed</code>; finalize consumes the journaled open
    token, adopts the exact binding, resumes with that profile, and proves
    bridge status. Finalize commits any provider transaction and removes
    rollback bytes. A lost response is recovered with
    <code>materialize.status</code>.
13. Source becomes a replica, its wrapper parks, and destination publishes
    <code>lease.transferred</code> and <code>session.resumed</code> for every
    moved member. The resumed event repeats the exact effective profile/source
    used by finalize. Whole-group mode reports all affected session IDs; separate-
    worktrees mode reports only the selected session.

Failure and recovery are phase-specific:

| Failure boundary | Authority | Required recovery |
| --- | --- | --- |
| Before source stop | Source lease remains owner and process MAY be unquiesced; destination staging is inert | Abort handoff, resume source input, or retry same operation |
| After source stop, before destination lease | Source remains logical owner but is stopped; destination is a replica | Retry materialization, resume source, or restart takeover from the same checkpoint |
| After destination lease is persisted | Destination is owner; source MUST NOT resume | Retry destination adopt/resume; a failed pre-resume prepared transaction may roll back destination bytes while authority stays at destination; if activation remains impossible, gracefully transfer back from stopped state or perform explicit force recovery |
| After provider resume/finalize but before response | Destination lease plus provider and materialization status decide success, not the lost client response | Retry operation ID; inspect provider/bridge and <code>materialize.status</code>; do not create another epoch or guess rollback |

No failure before step 10 MAY advance ownership. No failure after step 10 MAY
allow the old source to resume.
Before step 10, abort recovery MUST use <code>handoff.abort</code> so the source
records whether it unquiesced or remained stopped. After step 10,
<code>handoff.abort</code> MUST refuse because ownership recovery requires a new
lease transition.

### 13.7 Force takeover

Force takeover is an explicit recovery operation:

~~~shell
ax takeover NAME --to HOST --force --expect-owner HOST_ID --expect-epoch EPOCH
~~~

Interactive use MUST display that the old process can still exist, split-brain
history can result, and both histories will be preserved. Non-interactive use
MUST include destination, both expected values, and <code>--yes</code>.

Preconditions:

- destination is allowlisted and not known to hold a losing lease;
- the operator supplies/accepts the observed owner and epoch;
- the newest available checkpoint is integrity-valid; and
- destination materialization is either conflict-free or explicitly directed
  to a new copy/worktree;
- one exact WorkspaceGroupExpectation and Section 12.6 workspace mode are
  selected; whole-group mode has a recovery checkpoint for every migration
  member;
- the complete Session Record, provider identity, and persisted profile are
  available; and
- no local process is using the proposed destination native-store/workspace
  paths.

A direct session additionally requires an accepted <code>native_resume</code>
tuple and one of two exact recovery bases: an accepted
<code>portable_store</code> plan, or a provider probe proving that the
destination's machine-local authenticated backend already resolves the exact
Provider Identity Record without copied store bytes. Required destination
credentials remain machine-local. The terminal backend and profile mapping
MUST pass before lease advance.

A task-board session additionally requires bridge protocol 1.0.0 with
status/import/open/adopt/resume, an integrity-valid opaque bundle from the
selected checkpoint, and destination-local board/provider authentication. A
local board requires its staged <code>.task-board</code> tree and a successful
standalone <code>task-board validate</code>; a remote board requires access to
the exact logical board identity. <code>ax</code> MUST NOT substitute a whole-
board archive or inspect private manager state.

Common pre-lease preparation and fencing are:

1. Allocate one group operation and one takeover <code>operation_id</code> per
   migration member; attempt best-effort lease refresh and sync. Lack of source
   contact is not fatal. Every member uses the same WorkspaceGroupExpectation
   and MaterializationCohort with both arrays equal to the selected recovery
   cohort.
2. Preserve local destination divergence as an independent checkpoint or
   select a new copy/worktree. Select one immutable source checkpoint and pin
   all referenced object IDs.
3. Stage and validate workspace state without mutating the destination. For a
   direct session, also stage the accepted provider plan or prove exact backend
   identity resolution. For task-board, validate the opaque bundle and bridge
   capability/authentication only; bridge import/open is forbidden until
   <code>materialize.prepare</code> has durably created the transaction journal
   and fresh staging authority. No pre-lease staging accepts input.
4. Re-run membership, conflict, disk, terminal, provider/bridge,
   authentication, and profile
   checks. Any failure through this step aborts with the observed lease still
   authoritative. Staging and dormant state remain inert and may be retried or
   garbage-collected by their token-expiry rules.
5. Display/require the split-brain confirmation. Persist a machine-local
   confirmation receipt bound to operation ID, expected owner/epoch,
   checkpoint, destination, and all three accepted risks.
6. In whole-group mode, require all member confirmations and validated inert
   object staging before selecting each <code>max_observed_epoch + 1</code>.
   Provider and task-board materialization journals do not yet exist. Create a
   new random lease ID with reason <code>force_takeover</code> and that member's
   selected checkpoint, and durably persist it. In separate-worktrees mode this
   applies only to the selected session. Ownership MUST NOT advance before
   steps 1–5 pass for the full selected cohort.
7. Recompute the winner after every reachable peer response. If this lease has
   already lost, do not materialize, adopt, or resume. If it wins, emit
   <code>takeover.force_confirmed</code> followed by
   <code>lease.forced</code> under the new lease; the former must exactly match
   the receipt and accepted-risk tuple in Section 5.2.

The direct path then MUST:

1. invoke tagged RPC <code>materialize.prepare</code> with
   <code>intent = ownership_transfer</code>, the exact selected non-empty cohort,
   and provider/composite kind as workspace participation requires, then invoke
   <code>materialize.commit</code> to enter a rollbackable prepared
   workspace transaction and, only when <code>portable_store</code> is
   available, invoke plugin <code>materialize</code> inside it with the new
   fencing token;
2. validate native discovery of the exact Provider Identity Record, or validate
   exact authenticated-backend resolution for a backend-only identity;
3. fail with <code>unsupported_backend_identity</code> or
   <code>native_store_conflict</code> rather than create or relabel a blank
   provider session; and
4. call plugin <code>resume</code>, launch the returned plan through
   <code>ax pane SESSION_ID</code>, revalidate the lease before input, and
   prove the process is the exact native session; and
5. invoke RPC <code>materialize.finalize</code> with
   <code>activation = direct_owner_resumed</code>, the checkpoint-derived
   effective profile/source, recover a lost response through
   status, and only then publish <code>session.resumed</code>.

The task-board path then MUST:

1. invoke tagged RPC <code>materialize.prepare</code> with
   <code>intent = ownership_transfer</code>, the exact selected non-empty cohort,
   and task-board/composite kind as workspace participation requires, then enter
   a rollbackable prepared transaction. Commit performs the exact journaled
   bundle installation, bridge import, and dormant open; for a local board, run
   standalone <code>task-board validate</code> again against prepared bytes;
2. call <code>materialize.finalize</code> with
   <code>activation = task_board_owner_resumed</code>, the exact new binding,
   and checkpoint-derived effective profile/source. The coordinator consumes
   its journaled open token, adopts, verifies status, resumes, verifies status,
   and commits transaction cleanup;
3. publish <code>task_board.adopted</code> and
   <code>session.resumed</code> from the recovered finalize result, exactly
   once and with the same effective profile/source; and
4. never access the manager record, provider snapshot, or goal binding except
   as opaque bridge/bundle data.

On later union, all peers apply the deterministic lease rule. The prior owner
becomes stale, while losing-lease events and checkpoints remain in divergent-
history branches for reconciliation.

Failure and recovery are path- and phase-specific:

| Boundary | Authority and required recovery |
| --- | --- |
| Any direct capability, identity, store-plan, or staging failure before step 6 | No new lease exists. Abort safely, retain resumable staging when useful, and leave the observed owner unchanged. |
| Any task-board authentication, bundle, or board-validation failure before step 6 | No new lease exists and no bridge import/open has occurred. Discard inert staging or retry from the immutable bundle. No blank manager/provider session may be opened. |
| New force lease loses before activation | The deterministic winner owns. Roll back every prepared host/provider transaction, leave task-board state dormant, and park this destination. |
| Direct materialization/native-discovery failure after step 6 | Destination remains the stopped or failed owner. Use RPC rollback, which consumes the provider rollback token internally, retain staging/history, and retry the same operation or perform a newer explicit takeover. Never roll ownership back. |
| Task-board commit/import/open fails after step 6 | Destination remains the stopped owner. Recover the journal with status or roll back pre-adopt bytes; a new prepare may allocate fresh bridge sub-operation IDs only after the prior transaction is terminal. |
| Task-board open token expires after step 6 but before adopt | Destination remains the stopped owner. Roll back the terminal pre-adopt transaction, then prepare/import/open the same immutable bundle in a new materialization; never reuse the staging root or mutate the old journal. |
| Task-board adopt returns no response | Recover <code>materialize.status</code>, which reconciles bridge status. Exact binding continues; no binding retries the same adopt ID while its token is valid; another binding is <code>lease_conflict</code>. Never inspect private state or guess. |
| Task-board adopt succeeds but resume fails | Destination is the adopted, stopped/failed owner. Retry finalize/bridge resume with the same persisted IDs; do not roll back bytes, unadopt, restore the old owner, or replace it with a blank provider session. |
| Provider/bridge or materialization finalization response is lost | Lease, terminal/bridge status, provider transaction status, and RPC <code>materialize.status</code> decide the result. Retry by operation ID and do not create another epoch or guess rollback. |

The following sequence fixtures are normative. They start with source A at
epoch 4, destination B as replica, and checkpoint C4 unless a row says the
pre-lease gate fails:

| Fixture | Required phase trace | Required terminal authority/state |
| --- | --- | --- |
| <code>FT-DIRECT-POS</code> | stage workspace/store or backend proof → validate identity/profile → confirm → persist B epoch 5 → prepare → commit/prepared → discover exact native identity → resume → finalize/committed | B epoch 5 running; A stale after convergence; force-confirmed and lease-forced events precede resumed |
| <code>FT-DIRECT-PRE-NEG</code> | direct capability or backend identity check fails before confirmation/fencing | A epoch 4 unchanged; B has inert staging only; no force audit event or epoch-5 lease |
| <code>FT-DIRECT-POST-NEG</code> | persist B epoch 5 → prepared materialization/native discovery fails → provider then host rollback | B epoch 5 stopped/failed; A stale after convergence; no resumed event and no blank native session |
| <code>FT-TB-POS</code> | validate bundle/auth → confirm → persist B epoch 5 → prepare journal/fresh root → commit/import/open dormant → finalize/adopt/resume | B epoch 5 running and adopted; A stale; adoption event precedes resumed |
| <code>FT-TB-AUTH-NEG</code> | destination board/provider authentication fails before import/open | A epoch 4 unchanged; no manager activation, force event, or epoch-5 lease |
| <code>FT-TB-TOKEN-NEG</code> | persist B epoch 5 → commit/import/open dormant → token expires before adopt | B epoch 5 stopped; roll back pre-adopt transaction, then prepare/re-import/re-open same bundle; authority never rolls back |
| <code>FT-TB-ADOPT-UNKNOWN</code> | adopt response is lost → status returns exact binding, null, or different binding | Exact continues to resume; null retries dormant adopt; different fails lease conflict; B remains owner after epoch 5 |
| <code>FT-TB-RESUME-NEG</code> | adopt exact binding → bridge resume fails | B epoch 5 adopted and stopped/failed; retry resume only; no unadopt, A resume, or blank substitution |

If two force takeovers choose the same epoch, bytewise greater lease ID wins.
The loser MUST stop accepting input when it learns the winner. If destination
cannot resume after acquiring the lease, it remains the stopped/failed owner;
recovery is retry, graceful transfer from stopped state, or a newer explicit
force takeover. Ownership MUST NOT roll back implicitly.

### 13.8 Fork

<code>ax fork NAME --from CHECKPOINT --as NEW_NAME [--to HOST]</code> defaults
to the newest validated checkpoint; destination defaults to local only in
interactive use. Non-interactive use MUST supply <code>--to</code>.

Preconditions:

- checkpoint and all referenced objects are available and valid;
- NEW_NAME is unused;
- destination workspace conflict policy is satisfied;
- provider <code>fork</code> can produce a new native identity or a sanitized
  new-session plan; and
- task-board supports bundle open in <code>fork</code> mode when applicable.

Transitions:

1. Allocate a caller-stable fork operation ID, a new logical session ID, a new
   workspace-group ID, a fresh workspace ID for every source topology member,
   and an epoch-1 lease owned by the destination. No source ID is reused.
2. Derive and validate the exact Section 10.5 ForkWorkspaceProjection. Persist
   the complete new Workspace Group Record and every re-identified destination
   Transfer Manifest before publishing any object that refers to them. Source
   topology/manifests remain byte-identical.
3. Derive the effective execution profile and nullable profile-source event
   from the selected source checkpoint. Create the new Session Record with that
   profile, the new group/member IDs, and required core
   <code>fork_provenance</code>; persist it and its epoch-1 lease. A failure
   before this point leaves only unreferenced immutable projection objects and
   no logical fork.
4. For a direct session, invoke the side-effect-free provider <code>fork</code>
   planning operation with the fork operation ID. For
   <code>supported_import</code>, call <code>native-store-plan</code> in
   <code>mode=fork</code> before prepare and validate its provider component;
   <code>native_fork</code> has no provider-store component. Task-board uses the
   source bundle and does not call the direct-provider fork operation.
5. Invoke tagged <code>materialize.prepare</code> with
   <code>intent=fork</code>, the fresh destination session as the sole
   materialization member, an empty ownership-transfer set, the source and
   derived workspace manifests, and the exact projection. A direct native fork
   uses <code>kind=workspace</code> and the destination group as the Plan
   subject; a supported provider import or task-board clone uses
   <code>kind=composite</code> and the destination session as subject. Invoke
   <code>materialize.commit</code> to install the new copy/worktree and any
   provider/task-board branch in rollbackable prepared state.
6. For a direct provider, execute only the already validated fork Spawn Plan
   through <code>ax pane NEW_SESSION_ID</code> with the new lease/profile. A
   native fork allocates its new handle at that start; a supported import uses
   the prepared provider store. Call <code>identify-session</code>, require a
   new identity unequal to the source and equal to any planned native ID,
   persist its Provider Identity Record, and validate native discovery. Then
   finalize with <code>direct_owner_resumed</code>, the derived profile, and
   null new-session profile source.
7. For task-board, commit performs journaled bundle import/open in
   <code>fork</code> mode and requires a new manager/provider identity and
   independent goal-binding state. Finalize with
   <code>task_board_owner_resumed</code> adopts/resumes under the new epoch-1
   binding and derived profile with null new-session profile source. No raw bridge operation occurs outside the
   materialization coordinator.
8. After successful finalize, record <code>fork.created</code> with the source
   provenance, new Session Record ID, effective profile,
   <code>profile_source_event_id = null</code>, the source checkpoint's nullable
   profile event in <code>source_profile_event_id</code>, and mode; then record
   <code>session.resumed</code> with the new-record profile and null source. A lost
   response is reconciled by materialization and provider/bridge status before
   either event is emitted exactly once.

The exact Fork Provenance fixture for operation
<code>0198f4c8-28f0-7900-897a-1234567890ab</code> is:

~~~json
{
  "source_session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "source_checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "source_workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "operation_id": "0198f4c8-28f0-7900-897a-1234567890ab",
  "provider_fork_mode": "native",
  "extensions": {}
}
~~~

For <code>FORK-PROJECTION-POS</code>, the exact projection—and therefore the
complete inputs for deriving the newly persisted Workspace Group Record—is:

~~~json
{
  "projection_version": "workspace_fork_v1",
  "source_session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "source_workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
  "source_workspace_group_record_id": "sha256:3b366ca989681c63323c5de6db28198796aa913947ad3cd9456fc6dcee62b743",
  "source_workspace_manifest_id": "sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e",
  "destination_session_id": "0198f4c8-39a0-7a11-8a2b-2234567890ab",
  "destination_workspace_group_id": "0198f4c8-4ab0-7b22-8b3c-2234567890ab",
  "destination_workspace_group_record_id": "sha256:8f9fceda7f56a1e5c28c73192a915741c3b5fb6229e199b9b071b266136f7cf4",
  "destination_display_name": "payments-api-experiment",
  "destination_created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "destination_created_at": "2026-08-19T04:29:58.000Z",
  "destination_extensions": {},
  "member_mappings": [
    {"source_workspace_id":"0198f4c8-6c30-7d44-8d5e-1234567890ab","destination_workspace_id":"0198f4c8-5bc0-7c33-8c4d-2234567890ab","group_relative_path":"payments-api"},
    {"source_workspace_id":"0198f4c8-7d40-7e55-8e6f-2234567890ab","destination_workspace_id":"0198f4c8-6cd0-7d44-8d5e-2234567890ab","group_relative_path":"design-notes"}
  ],
  "manifest_mappings": [
    {"kind":"workspace_tree","source_manifest_id":"sha256:7cff7402aa5a31ba0cd7ff9bf49a9dc166b961c9f2b647d1c1084d3e70ce5db8","destination_manifest_id":"sha256:82864b91f66b77e032b5c9aeb86e20091bdf88f6d461e2a26e0d2f4107cfa306","source_subject_id":"0198f4c8-8e50-7f66-8f70-3234567890ab","destination_subject_id":"0198f4c8-7de0-7e55-8e6f-4234567890ab"},
    {"kind":"workspace_tree","source_manifest_id":"sha256:88d93f20f978b92e75d35e67ebd5a41b90ff1afe106363b05c0f7b08614eb4cf","destination_manifest_id":"sha256:549245f73bff80001d7f2310b06c446124100028e5301083189460b8829a476c","source_subject_id":"0198f4c8-6c30-7d44-8d5e-1234567890ab","destination_subject_id":"0198f4c8-5bc0-7c33-8c4d-2234567890ab"},
    {"kind":"workspace_tree","source_manifest_id":"sha256:8dc15e881e026e7cf59482395baaa8c47341e6bad6d87f44312a9d0b360aacd5","destination_manifest_id":"sha256:dd2b8f604b2934127616623b7c70240a6c3acc8e6cdfe6ebdfbf137160abeaaf","source_subject_id":"0198f4c8-7d40-7e55-8e6f-2234567890ab","destination_subject_id":"0198f4c8-6cd0-7d44-8d5e-2234567890ab"},
    {"kind":"workspace_group","source_manifest_id":"sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e","destination_manifest_id":"sha256:d44fa66c43658f7d4d5613f319c60fea70fbe933dea970f92884e0bb61106ff5","source_subject_id":"0198f4c8-5b20-7c33-8c4d-1234567890ab","destination_subject_id":"0198f4c8-4ab0-7b22-8b3c-2234567890ab"}
  ]
}
~~~

The following complete <code>FORK-PLAN-DIRECT-POS</code> object is the
workspace-only transaction for a provider-native fork. Its provider has no
portable-store mutation; the new native identity is created only by the
post-prepare Spawn Plan. The destination root is absent and configured as the
logical root <code>relux-forks</code>:

~~~jsonc
{
  "schema": "urn:ax:schema:materialization-plan",
  "schema_version": "1.0.0",
  "plan_id": "sha256:d4365a3e3c8736704febcabd008e458c6c661c329df444c2b79439b2b6d41dbb",
  "kind": "workspace",
  "intent": "fork",
  "subject_id": "0198f4c8-4ab0-7b22-8b3c-2234567890ab",
  "source_checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
  "source_manifest_ids": ["sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e"],
  "derived_manifest_ids": [
    "sha256:549245f73bff80001d7f2310b06c446124100028e5301083189460b8829a476c",
    "sha256:82864b91f66b77e032b5c9aeb86e20091bdf88f6d461e2a26e0d2f4107cfa306",
    "sha256:d44fa66c43658f7d4d5613f319c60fea70fbe933dea970f92884e0bb61106ff5",
    "sha256:dd2b8f604b2934127616623b7c70240a6c3acc8e6cdfe6ebdfbf137160abeaaf"
  ],
  "fork_projection": {
    "projection_version": "workspace_fork_v1",
    "source_session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
    "source_workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
    "source_workspace_group_record_id": "sha256:3b366ca989681c63323c5de6db28198796aa913947ad3cd9456fc6dcee62b743",
    "source_workspace_manifest_id": "sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e",
    "destination_session_id": "0198f4c8-39a0-7a11-8a2b-2234567890ab",
    "destination_workspace_group_id": "0198f4c8-4ab0-7b22-8b3c-2234567890ab",
    "destination_workspace_group_record_id": "sha256:8f9fceda7f56a1e5c28c73192a915741c3b5fb6229e199b9b071b266136f7cf4",
    "destination_display_name": "payments-api-experiment",
    "destination_created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
    "destination_created_at": "2026-08-19T04:29:58.000Z",
    "destination_extensions": {},
    "member_mappings": [
      {"source_workspace_id":"0198f4c8-6c30-7d44-8d5e-1234567890ab","destination_workspace_id":"0198f4c8-5bc0-7c33-8c4d-2234567890ab","group_relative_path":"payments-api"},
      {"source_workspace_id":"0198f4c8-7d40-7e55-8e6f-2234567890ab","destination_workspace_id":"0198f4c8-6cd0-7d44-8d5e-2234567890ab","group_relative_path":"design-notes"}
    ],
    "manifest_mappings": [
      {"kind":"workspace_tree","source_manifest_id":"sha256:7cff7402aa5a31ba0cd7ff9bf49a9dc166b961c9f2b647d1c1084d3e70ce5db8","destination_manifest_id":"sha256:82864b91f66b77e032b5c9aeb86e20091bdf88f6d461e2a26e0d2f4107cfa306","source_subject_id":"0198f4c8-8e50-7f66-8f70-3234567890ab","destination_subject_id":"0198f4c8-7de0-7e55-8e6f-4234567890ab"},
      {"kind":"workspace_tree","source_manifest_id":"sha256:88d93f20f978b92e75d35e67ebd5a41b90ff1afe106363b05c0f7b08614eb4cf","destination_manifest_id":"sha256:549245f73bff80001d7f2310b06c446124100028e5301083189460b8829a476c","source_subject_id":"0198f4c8-6c30-7d44-8d5e-1234567890ab","destination_subject_id":"0198f4c8-5bc0-7c33-8c4d-2234567890ab"},
      {"kind":"workspace_tree","source_manifest_id":"sha256:8dc15e881e026e7cf59482395baaa8c47341e6bad6d87f44312a9d0b360aacd5","destination_manifest_id":"sha256:dd2b8f604b2934127616623b7c70240a6c3acc8e6cdfe6ebdfbf137160abeaaf","source_subject_id":"0198f4c8-7d40-7e55-8e6f-2234567890ab","destination_subject_id":"0198f4c8-6cd0-7d44-8d5e-2234567890ab"},
      {"kind":"workspace_group","source_manifest_id":"sha256:a98ca90522b4de30e4aaaf9bf50529d09e15a817ffa67f94552fb313d1a1ad2e","destination_manifest_id":"sha256:d44fa66c43658f7d4d5613f319c60fea70fbe933dea970f92884e0bb61106ff5","source_subject_id":"0198f4c8-5b20-7c33-8c4d-1234567890ab","destination_subject_id":"0198f4c8-4ab0-7b22-8b3c-2234567890ab"}
    ]
  },
  "prepared_for_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "source_lease_epoch": 4,
  "source_lease_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "authorities": [
    {"authority_id":"workspace_fork","kind":"workspace","platform":"linux","root_path":"/srv/relux-forks","logical_root":"relux-forks","workspace_group_id":"0198f4c8-4ab0-7b22-8b3c-2234567890ab","write_policy":"managed_copy"}
  ],
  "expected_prior_checkpoint_id": null,
  "operations": [
    {"sequence":1,"action":"install_workspace_group","authority_id":"workspace_fork","target_relative_path":"payments-api-experiment","input_id":"sha256:d44fa66c43658f7d4d5613f319c60fea70fbe933dea970f92884e0bb61106ff5","expected_prior_digest":null,"atomicity_boundary":"target_directory"}
  ],
  "exclusions": ["credential","live_pid","machine_auth","socket","transient_lock"],
  "validations": ["manifest_closure","workspace_state"],
  "commit_strategy": "atomic_directory_rename",
  "rollback_required": true,
  "created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "created_at": "2026-08-19T04:29:59.000Z",
  "extensions": {}
}
~~~

The source manifest objects in Section 10.4 are the language-neutral input
bytes. Applying <code>workspace_fork_v1</code> MUST reproduce all four displayed
destination IDs: the submodule working tree, Git working tree, managed tree,
and group root in that order. Implementations MUST compare the fully derived
JCS bytes, not accept the mapping as an unchecked assertion.

The transaction variants are exact:

| Fixture | Prepare/commit input | Activation and terminal journal |
| --- | --- | --- |
| <code>FORK-TXN-DIRECT-NATIVE</code> | The displayed workspace plan, fresh session cohort, empty transfer set | Commit prepares the new workspace; the validated Spawn Plan creates one new native identity; finalize <code>direct_owner_resumed</code> commits the marker and leaves both provider/task-board transaction states <code>none</code> |
| <code>FORK-TXN-DIRECT-IMPORT</code> | Composite fork plan formed from the same projection plus the exact provider manifest/authority/operation returned for <code>mode=fork</code> | Commit leaves workspace and provider transaction prepared; discovery must find a new identity; finalize commits both only after process proof |
| <code>FORK-TXN-TASK-BOARD</code> | Composite fork plan formed from the same projection plus the source Task-board Bundle and one fresh task-board staging authority | Commit records import/open with <code>activation_mode=fork</code> and bridge <code>open mode=fork</code>; finalize adopts/resumes the new manager under the new lease, then commits marker and journal |

“Formed from” is the Section 10.5 composite tagged-union operation: it copies
the displayed source/derived/projection facts and workspace
authority/operation, unions exactly one permitted provider or task-board
authority/operation set, sorts authorities/operations/validations, renumbers
operations consecutively, sets the Plan kind/subject to composite/destination
session, selects <code>two_phase_multi_root</code>, and recomputes its ID. It is
not an out-of-band second transaction. In all three rows, a failure before
activation rolls the one prepared materialization back; a failure after
process start or adopt is recovered by status/finalize or an explicit fenced
stop and never by restoring bytes behind a live owner.

The fork Session Record MUST carry those values byte-for-byte for this fixture;
the <code>fork.created</code> event repeats source/checkpoint/record digest and
mode so a validator can join provenance without interpreting extensions.

Normative fork Session Record using that provenance:

~~~json
{
  "schema": "urn:ax:schema:session-record",
  "schema_version": "1.0.0",
  "record_id": "sha256:83c7152b9415c20c90e9009e1fe2e01f9cd3a45ca385b5bc2d678e979756427f",
  "subject_id": "0198f4c8-39a0-7a11-8a2b-2234567890ab",
  "session_id": "0198f4c8-39a0-7a11-8a2b-2234567890ab",
  "name": "payments-api-experiment",
  "kind": "direct",
  "created_at": "2026-08-19T04:30:00.000Z",
  "created_by_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "provider_id": "codex",
  "workspace_group_id": "0198f4c8-4ab0-7b22-8b3c-2234567890ab",
  "execution_profile": "yolo",
  "launch_plan": {
    "argv": ["codex"],
    "cwd_workspace_id": "0198f4c8-5bc0-7c33-8c4d-2234567890ab",
    "cwd_relative": ".",
    "env_names": ["OPENAI_API_KEY"],
    "env_literals": {},
    "contains_secrets": false,
    "extensions": {}
  },
  "task_board": null,
  "fork_provenance": {
    "source_session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
    "source_checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
    "source_workspace_group_id": "0198f4c8-5b20-7c33-8c4d-1234567890ab",
    "operation_id": "0198f4c8-28f0-7900-897a-1234567890ab",
    "provider_fork_mode": "native",
    "extensions": {}
  },
  "extensions": {}
}
~~~

The source lease, provider identity, history, and process are not changed.
Muse forks with non-empty or active <code>cron.db</code> are unsupported because
scheduled work could duplicate. Antigravity fork requires the authenticated
backend's native fork surface; copying local cache/transcripts is not a fork.
When a provider cannot fork faithfully, the command MUST report
<code>provider_fork_unsupported</code>; it MUST NOT relabel a blank chat as a
fork.

Fork failure and recovery are exact:

| Fixture/boundary | Required result |
| --- | --- |
| <code>FORK-BEFORE-TOPOLOGY</code> | Validation/allocation failure writes no destination topology, Session Record, lease, provider, or manager |
| <code>FORK-AFTER-TOPOLOGY</code> | Derived topology/manifests exist but Session Record does not; they remain harmless unreferenced immutable objects eligible for ordinary GC |
| <code>FORK-AFTER-SESSION</code> | New Session Record and epoch-1 lease exist, but no materialization; state is <code>creating</code> and the same operation may resume at prepare |
| <code>FORK-MATERIALIZE-NEG</code> | Prepare/commit fails before activation; rollback restores destination, new fork remains failed/creating owner, source is untouched |
| <code>FORK-DIRECT-IDENTITY-NEG</code> | Provider fork cannot prove a new identity; roll back pre-activation transaction and report <code>provider_fork_unsupported</code>; never use the source or a blank identity |
| <code>FORK-TB-OPEN-NEG</code> | Import/open fails; journal/status/expiry recovery applies and no manager is adopted |
| <code>FORK-AFTER-ACTIVATION</code> | Provider/manager is running but finalize response is lost; reconcile status and finalize with the same IDs; byte rollback or a second process is forbidden |
| <code>FORK-EVENT-LOST</code> | Finalize committed but event publication failed; retry the same event identities and do not recreate topology, lease, provider, or manager |

No fork failure changes the source lease, event chain, provider identity,
manager binding, workspace marker, or checkpoint. A fork with an authoritative
<code>session.bootstrap_aborted</code> is non-resumable and remains failed.

### 13.9 Stop

<code>ax stop NAME</code> is graceful by default and executes on the current
owner, locally or through authenticated <code>session.stop</code> RPC.

Preconditions are a winning owner lease and an available quiesce/stop path.
Transitions:

1. block input and enter <code>quiescing</code>;
2. wait for a complete safe boundary;
3. create and sync a validated checkpoint;
4. request normal provider/task-board stop;
5. require process exit and closed durable handles;
6. if normal exit appended provider/manager closure records, capture and sync a
   closure-only delta and superseding validated checkpoint; an unexpected
   workspace/background mutation fails closed while ownership remains local;
7. record and sync <code>session.stopped</code> with the newest checkpoint; and
8. retain the same lease, native store, workspace, terminal metadata, and
   checkpoints.

For a task-board session, steps 1–3 use bridge
<code>export --mode handoff</code>, step 4 consumes its source-control token
with bridge <code>stop</code>, and any replacement closure bundle returned in
step 6 remains opaque. For a direct session, the equivalent actions use the
provider plugin and terminal backend.

A graceful timeout leaves ownership unchanged and reports
<code>quiesce_timeout</code> or <code>stop_timeout</code>. The process MAY be
unquiesced if safe. <code>ax stop NAME --force</code> requires explicit
confirmation, preserves best-effort diagnostics/checkpoint state, terminates
the local process, records unclean stop, and does not imply a safe transferable
checkpoint.

The ordinary successful path returns a non-null final checkpoint,
<code>resumable=true</code>, <code>bootstrap_aborted=false</code>, and state
<code>stopped</code>. If the epoch-1 lease has no checkpoint, graceful stop MUST
either establish the first validated checkpoint and take that ordinary path or
fail without publishing a stop event. Confirmed force closure in that bootstrap
window returns a null checkpoint, <code>resumable=false</code>,
<code>bootstrap_aborted=true</code>, and state <code>failed</code>, after
publishing the exact two events in Section 13.1. A force stop of a session that
already has a checkpoint keeps that checkpoint ID, is resumable only from that
older checkpoint, sets <code>bootstrap_aborted=false</code>, and returns
<code>stopped</code> only after process/store closure is proved. An unknown
process or open store handle returns failure and leaves the command retryable;
it is never represented as a successful closure.

Stop is not delete. Deletion requires a separate future/administrative surface
that emits a Session Tombstone; v0.2.0 MUST NOT make stop delete state.

### 13.10 Resume

<code>ax resume NAME</code> is allowed only on the winning owner host. A replica
receives <code>not_owner</code> and explicit attach/takeover/fork choices.

The owner first refreshes lease knowledge and verifies its fencing token. If
the epoch-1 winning lease has a null checkpoint, resume is not an ordinary
resume: it executes only the Section 13.1/13.2 bootstrap retry predicate and
phase continuation. An authoritative bootstrap-abort event returns
<code>checkpoint_unavailable</code> and cannot be resumed. No later epoch may
have a null checkpoint.

For a validated checkpoint, derive the exact effective profile/source from its
event-head closure, probe the mapping/capabilities, and choose exactly one path:

1. <strong>No materialization.</strong> If the current managed marker and native
   provider/bridge status already equal the checkpoint and winning lease, do
   not create a transaction. Direct sessions validate native discovery, start
   <code>ax pane SESSION_ID</code>, invoke plugin resume with the effective
   profile, prove the process, and emit <code>session.resumed</code>. A
   task-board session validates the existing manager binding and calls the
   public bridge resume with a caller-stable ID/profile, proves status, and
   emits the event. A missing binding does not qualify for this path.
2. <strong>Direct materialization.</strong> Call tagged
   <code>materialize.prepare</code> with <code>intent=owner_resume</code>, the
   owner as the sole materialization member, empty ownership-transfer set, and
   workspace/provider/composite kind. Call commit and require durable
   <code>prepared</code>. Validate native discovery or exact backend identity,
   start the wrapper, invoke plugin resume, and prove the exact session. Then
   finalize with <code>direct_owner_resumed</code> and the effective
   profile/source; only a committed result permits <code>session.resumed</code>.
3. <strong>Task-board materialization.</strong> Prepare with task-board or
   composite kind and the same cohort rules. Commit installs the opaque bundle,
   imports, and opens dormant through the journal. Finalize with
   <code>task_board_owner_resumed</code>, the winning binding, and effective
   profile/source; finalize adopts/resumes and proves public bridge status.
   Only its committed result permits adoption/resume events.

Every materializing path is therefore
prepare → commit/prepared → identity or dormant validation → activation →
finalize/committed. A response lost at any arrow is recovered with
<code>materialize.status</code> plus plugin/bridge status under the same IDs.
Before direct process start or task-board adopt, validation failure, operator
abort, or lease loss invokes rollback. After a direct process is proven running
or task-board adopt succeeds, ordinary byte rollback is forbidden: the same
owner must finish status/finalize, stop the activation, or perform a new fenced
ownership operation. Failure leaves the session stopped/failed on that same
owner and preserves the journal.

Normative resume fixtures are:

| Fixture | Kind/path | Required terminal result |
| --- | --- | --- |
| <code>RESUME-NO-MAT-DIRECT</code> | Current workspace/native identity; no transaction | Same lease/profile, exact provider resumed, one resumed event |
| <code>RESUME-WORKSPACE</code> | Workspace-only prepare/commit, direct native state already current | Marker committed after direct activation; provider transaction remains none |
| <code>RESUME-PROVIDER</code> | Provider-only prepared transaction | Null marker/path; provider transaction commits only after exact resume |
| <code>RESUME-COMPOSITE-DIRECT</code> | Workspace plus portable provider | Both roots prepared; exact provider running before finalize cleans backups |
| <code>RESUME-TASK-BOARD</code> | Task-board-only bundle | Journal opened → adopted → resumed; null marker/path |
| <code>RESUME-COMPOSITE-TB</code> | Workspace plus bundle | Workspace remains rollbackable until bridge resume proof; then marker/finalize |
| <code>RESUME-PRE-ACTIVATION-NEG</code> | Any prepared path fails validation | Roll back and remain stopped owner |
| <code>RESUME-POST-ACTIVATION-NEG</code> | Activation succeeds, response/finalize fails | Status-recover/finalize or explicitly stop; never roll back behind live activation |

It MUST not create a new native session under the old logical identity.
Antigravity backend <code>not found</code> is
<code>unsupported_backend_identity</code>, not a successful blank resume.

### 13.11 Reboot restore

On wrapper/service restore:

1. rebuild or validate the local derived index;
2. inspect every previously running/idle local session;
3. refresh lease heads when peers are reachable;
4. mark losing local processes stale;
5. for winning local owners, validate the newest checkpoint and persisted
   profile;
6. recreate tmux wrapper panes or native Windows ConPTY wrappers; and
7. auto-resume only sessions whose configuration explicitly enables
   <code>restore.auto_resume</code> and whose provider safe-stop/restore gate
   passed.

Otherwise the wrapper parks and requires <code>ax resume</code>. On macOS,
Linux, and WSL2, tmux-resurrect/continuum MAY recreate panes but the wrapper
still performs these checks. Native Windows creates a new ConPTY and provider
process; it does not resurrect process memory.

### 13.12 Failure and recovery matrix

| Failure | Required behavior | Recovery |
| --- | --- | --- |
| SSH disconnect during record/chunk transfer | Keep verified staging and immutable committed objects; no partial materialization | Retry <code>ax sync --resume TRANSFER_ID</code> |
| Invalid digest/schema | Quarantine object, stop affected sync, identify peer/object without payload logging | Repair source or remove peer authorization; fetch a known-good object |
| Workspace divergence | No destination write | Diff, copy, worktree, or explicit managed-replica replacement |
| Provider quiesce cannot prove full idle | Graceful stop/takeover fails; owner unchanged | Wait/retry or explicit force action |
| Provider exits but store handles remain open | No post-stop/superseding checkpoint or takeover lease | Wait boundedly, diagnose, or force with unclean marker |
| Destination disk full | Retain existing destination; staging can remain partial | Free space and resume |
| Atomic rename blocked | Roll back or retain staging; never in-place overwrite | Close handles and retry |
| Plugin crash/invalid stdout | Record provider-host error; do not infer capability or success | Run doctor, repair/upgrade plugin, retry |
| Epoch-1 launch fails before first checkpoint | Never report stopped/resumable or invent a checkpoint | Reconcile and retry the same bootstrap identity, establish the first checkpoint, or prove closure and record non-resumable bootstrap abort |
| Task-board bridge missing/incompatible | Do not inspect private state; task-board portability disabled | Install compatible task-board contract |
| Task-board import/open/adopt fails before new lease | Old owner remains authoritative in graceful flow | Roll back dormant import and retry |
| Task-board adopt fails after new lease | Destination remains stopped owner | Retry adopt/resume or newer explicit transfer |
| Owner-resume response is lost | Preserve prepared journal and do not start a second process/manager | Reconcile materialization plus provider/bridge status, then finalize, roll back pre-activation, or explicitly stop post-activation |
| Antigravity backend cannot resolve UUID | No fake resume or blank replacement | Authenticate correct realm, use provider-native fork if possible, or report unsupported |
| Muse cron/background state cannot be fenced | Portable takeover/fork unavailable | Stop locally or wait for a supported adapter/version |
| Concurrent force takeovers | Deterministic lease winner; preserve losing history | Stop losing process and reconcile divergent branch |
| Old owner reconnects after force | Reject its lower/losing fencing token from authoritative sync/resume | Park/stop stale process; inspect divergent events |
| SQLite index corrupt | Do not sync database | Move corrupt index to local diagnostics and rebuild from immutable truth |
| Operator interrupt | Preserve transaction journal and report whether authority changed | Retry same operation ID; inspect status before another takeover |

## 14. CLI and operator experience

### 14.1 Command surface

The v0.2.0 command surface is:

~~~text
ax NAME [--action attach|takeover|fork|cancel] [--to HOST] [--as NEW_NAME] [--workspace-mode whole-group|separate-worktrees]
ax start NAME --provider ID [--profile standard|yolo] [--workspace PATH]
ax start NAME --task-board --provider ID --task ELEMENT_ID --board-id BOARD_ID [--board-url HTTPS_URL] --launch-mode primary-owner|tracked-prompt [--goal GOAL_ID --goal-revision REVISION] [--binding prompt|none] [--profile PROFILE] [--workspace PATH]
ax list [--all-peers]
ax status NAME
ax attach NAME [--local]
ax takeover NAME [--to HOST] [--workspace-mode whole-group|separate-worktrees] [--force --expect-owner ID --expect-epoch N] [--yes]
ax fork NAME [--from CHECKPOINT] --as NEW_NAME [--to HOST]
ax stop NAME [--force] [--yes]
ax resume NAME
ax sync [NAME|--all] [--peer HOST] [--resume TRANSFER_ID]
ax diff NAME [--peer HOST]
ax materialize NAME [--checkpoint CHECKPOINT] [--peer HOST] [--as-copy PATH | --as-worktree PATH | --replace-managed-replica --expect-checkpoint CHECKPOINT] [--yes]
ax doctor [--provider ID] [--peer HOST]
ax logs [--operation OPERATION_ID] [--session NAME] [--since TIME] [--peer HOST] [--cursor CURSOR] [--limit N]
ax peer list
ax peer probe HOST
ax session set-profile NAME standard|yolo
ax pane SESSION_ID
ax rpc serve --stdio
~~~

For the umbrella form, <code>--to</code> is permitted only with
<code>takeover</code> or <code>fork</code>, and <code>--as</code> is required and
permitted only with <code>fork</code>. <code>--workspace-mode</code> is permitted
only with takeover and follows the cohort rule below. In non-interactive mode, takeover and
fork MUST include <code>--to</code>; <code>local</code> is the explicit local-host
token. Interactive takeover/fork MAY default <code>--to</code> to local only
after displaying the resolved destination. <code>attach</code> always targets
the resolved owner and accepts neither action-specific flag.

Internal commands <code>pane</code> and <code>rpc serve</code> MAY be hidden
from short help but MUST have documented <code>--help</code>.

A task-board start has no implicit board, launch mode, goal, or binding lookup.
<code>--board-id</code> uses the Section 5.1 logical-ID grammar. Omitting
<code>--board-url</code> selects a local board; supplying it selects a remote
board and it MUST be an absolute userinfo/query/fragment-free HTTPS URL.
<code>--launch-mode primary-owner</code> maps to
<code>primary_owner</code>, requires <code>--goal</code> and a positive
<code>--goal-revision</code>, forbids <code>--binding</code>, and deterministically
sets <code>native_goal_binding = bound</code>. It additionally requires
<code>task_board_primary</code> and <code>native_goal_binding</code> enabled for
the provider/platform row. <code>--launch-mode tracked-prompt</code> maps to
<code>tracked_prompt</code>, requires explicit
<code>--binding prompt|none</code>, and requires <code>--goal</code> and
<code>--goal-revision</code> either together or both absent. It requires
<code>prompt_spawn</code>. No provider-ID heuristic may choose these values.
The normalized values populate the Session Record and bridge launch body
byte-for-byte.

When a takeover's migration cohort has more than one session, interactive use
MUST choose and display <code>whole-group</code> or
<code>separate-worktrees</code>; non-interactive use MUST supply
<code>--workspace-mode</code>. The CLI spellings map to Section 12.6
<code>whole_group</code> and <code>separate_worktrees</code>. The flag is
forbidden when the cohort has one member; that singleton has the canonical
internal and CLI-result value <code>whole_group</code>. This value does not
claim that another session moved—it records that the complete one-member
migration cohort was selected.

<code>ax logs</code> reads only the local host when <code>--peer</code> is
absent. A remote read requires an explicit allowlisted peer; it never silently
fans out. <code>--limit</code> is an integer 1–65,536, default 1,000.
<code>--cursor</code> is an opaque 1–512 character token returned by the same
host and is mutually exclusive with <code>--operation</code>,
<code>--session</code>, and <code>--since</code>; it carries the original filter
and ordering position. A remote cursor MUST be reused with the same
<code>--peer</code>; a local cursor forbids <code>--peer</code>. Cursor scope or
host mismatch is <code>invalid_arguments</code>. Events are returned in the
Section 18.1 total order, and <code>next_cursor = null</code> means exhaustion.
Every successful logs body carries the stable <code>emitting_host_id</code> of
the host whose durable stream was read, including a local invocation; it is
never null and is not the Observation Event's nullable
<code>peer_host_id</code> field. Every returned Observation Event MUST have
<code>host_id</code> equal to that emitter.

For a remote read, the local CLI resolves the explicit peer through the
allowlist and invokes the equivalent remote local-only command over SSH, for
example <code>ssh HOST ax logs --session NAME --limit N --json</code> or
<code>ssh HOST ax logs --cursor CURSOR --limit N --json</code>. The transport
MUST encode every argument separately using Section 6.3 platform-safe SSH
rules, MUST omit <code>--peer</code> from the remote invocation, and MUST
validate one CLI Result 1.0.0 whose <code>emitting_host_id</code> is the resolved
remote host. The remote local-only invocation obtains that ID from its own
configured stable host identity; it does not know or infer the initiating host.
After validation, the initiator relays the exact logical result without
changing any field. A remote cursor is opaque to the initiating host; it is
returned unchanged to that same peer. This read path uses authenticated SSH,
does not add a Mesh RPC operation, and does not grant access to another peer.
Host-ID mismatch is <code>host_identity_mismatch</code>; invalid/multiple JSON,
the wrong command tag, or a result containing an event whose
<code>host_id</code> differs from <code>emitting_host_id</code> is
<code>integrity_failure</code> and no event is returned.

<code>ax materialize</code> without a conflict flag targets the configured
managed path with policy <code>fail</code>. The three conflict choices are
mutually exclusive:

- <code>--as-copy PATH</code> requires an absent or empty path and creates a new
  managed replica path for the same logical session/workspace group; it does
  not fork or change ownership;
- <code>--as-worktree PATH</code> has the same identity/ownership behavior and
  requires at least one Git member. PATH is the new workspace-group root: each
  Git member becomes a managed worktree at its group-relative path and every
  managed-tree member becomes a managed copy at its group-relative path; and
- <code>--replace-managed-replica</code> targets only the configured path,
  requires <code>--expect-checkpoint</code> equal to its managed marker, refuses
  <code>unmanaged_nonempty</code>, checkpoints the divergent destination, and
  obtains the current owner's <code>replica.replace_confirmed</code> event and
  matching managed-replica Tombstone before mutation. Non-interactive
  replacement also requires <code>--yes</code>.

<code>--peer</code> executes the same transaction on that allowlisted peer. A
copy/worktree path is destination-native and MUST be transmitted as one safely
encoded argument, never a shell fragment. A replica materialization remains
dormant even after success.

### 14.2 Common flags and output

All user commands MUST support:

- <code>--config PATH</code>;
- <code>--data-dir PATH</code>;
- <code>--state-dir PATH</code>;
- <code>--cache-dir PATH</code>;
- <code>--runtime-dir PATH</code>;
- <code>--json</code> for one CLI Result 1.0.0 success object or Structured
  Error 1.0.0 failure object;
- <code>--no-color</code>;
- <code>--non-interactive</code>, which forbids prompts;
- <code>--timeout DURATION</code>; and
- <code>--verbose</code> without exposing payloads/secrets.

Commands with a documented confirmation additionally accept
<code>--yes</code>; commands without such a confirmation MUST reject it.

In text mode, data goes to stdout and prompts/diagnostics to stderr. In JSON
mode, stdout MUST contain exactly one JSON document; logs remain on stderr.
Progress MAY use stderr only when it is a TTY.

Destructive or split-brain-risk operations MUST prompt in interactive mode and
require <code>--yes</code> plus every documented expectation flag in
non-interactive mode. <code>--yes</code> alone MUST NOT bypass an expected
owner/epoch/checkpoint check.

JSON success output uses the independently versioned closed schema
<code>urn:ax:schema:cli-result</code> version <code>1.0.0</code>. It contains
exactly <code>schema</code>, <code>schema_version</code>,
<code>command</code>, <code>ok = true</code>, <code>operation_id</code>
(UUIDv7 or null), <code>session_id</code> (UUIDv7 or null), the tagged
<code>body</code>, and <code>extensions</code>. Failure output is one Structured
Error object from Section 15.1, not a CLI Result with <code>ok = false</code>.
The process exit status MUST equal that error's <code>exit_code</code>.

The following embedded CLI types are closed:

| Type | Exact members and constraints |
| --- | --- |
| <code>CapabilitySummary</code> | <code>status:available&#124;conditional&#124;unsupported&#124;unknown</code>, <code>enabled:boolean</code>, <code>detail:string[0..2048]</code> |
| <code>SessionSummary</code> | <code>session_id:UUIDv7</code>, <code>name:string[1..64]</code>, <code>kind:direct&#124;task_board</code>, <code>provider_id:provider-id</code>, <code>owner_host_id:UUIDv7</code>, <code>owner_host_name:string[1..64]</code>, <code>lease_epoch:uint53&gt;0</code>, <code>lease_id:UUIDv4</code>, <code>local_role:owner&#124;replica</code>, <code>state:SessionState</code>, <code>newest_checkpoint_id:digest&#124;null</code>, <code>newest_checkpoint_created_at:timestamp&#124;null</code>, <code>workspace_status:absent&#124;current&#124;staged&#124;conflict&#124;unsupported</code>, <code>capabilities:map(capability-name,CapabilitySummary)[0..7]</code>, <code>warnings:sorted unique string[0..1024]</code> |
| <code>PathDiff</code> | <code>path:path</code>, <code>classification:added&#124;removed&#124;modified&#124;type_changed&#124;mode_changed&#124;conflict</code>, <code>source_digest:digest&#124;null</code>, <code>destination_digest:digest&#124;null</code> |
| <code>PeerSummary</code> | <code>host_id:UUIDv7</code>, <code>name:string[1..64]</code>, <code>platform:macos&#124;linux&#124;wsl2&#124;windows</code>, <code>reachable:boolean</code>, <code>last_successful_sync_at:timestamp&#124;null</code>, <code>degraded_codes:sorted unique string[0..1024]</code> |
| <code>CLIFinding</code> | <code>severity:info&#124;warning&#124;error</code>, <code>code:string[1..128]</code>, <code>message:string[1..4096]</code>, <code>remediation:string[1..4096]&#124;null</code>, <code>source:core&#124;terminal&#124;provider&#124;mesh&#124;workspace&#124;task_board</code> |
| <code>MaterializationSummary</code> | <code>session_id:UUIDv7</code>, <code>checkpoint_id:digest</code>, <code>materialization_id:UUIDv7</code>, <code>mode:default&#124;copy&#124;worktree&#124;replace_managed_replica</code>, <code>destination_path:absolute-path</code>, <code>destination_classification:DestinationClass</code>, <code>preserved_checkpoint_id:digest&#124;null</code>, <code>committed:boolean</code>, <code>ownership_changed:boolean</code> |

The <code>command</code> tag selects exactly one body. Digest arrays and object
arrays keyed by an ID are sorted bytewise by that ID:

| Command tag | Exact body |
| --- | --- |
| <code>cancel</code> | <code>{name:string[1..64],cancelled:boolean}</code> with true required |
| <code>start</code> | <code>{session:SessionSummary,execution_profile:standard&#124;yolo,terminal_backend:tmux&#124;conpty}</code> |
| <code>list</code> | <code>{sessions:SessionSummary[0..65536],partial:boolean,unreachable_peer_ids:sorted unique UUIDv7[0..1024]}</code> |
| <code>status</code> | <code>{session:SessionSummary,process_present:boolean,active_operation_id:UUIDv7&#124;null,last_successful_sync:map(UUIDv7,timestamp)[0..1024]}</code> |
| <code>attach</code> | <code>{session:SessionSummary,mode:local&#124;remote,attached_owner_host_id:UUIDv7,detached:boolean,provider_exit_code:int32&#124;null}</code> |
| <code>takeover</code> | <code>{mode:graceful&#124;force,workspace_mode:whole_group&#124;separate_worktrees,destination_host_id:UUIDv7,source_host_id:UUIDv7,affected_session_ids:sorted unique UUIDv7[1..1024],lease_epoch:uint53&gt;0,lease_id:UUIDv4,checkpoint_id:digest,state:running&#124;idle&#124;stopped&#124;failed,materialized:boolean,adopted:boolean,resumed:boolean,warnings:sorted unique string[0..1024]}</code> |
| <code>fork</code> | <code>{source_session_id:UUIDv7,source_checkpoint_id:digest,session:SessionSummary,workspace_group_id:UUIDv7,provider_fork_mode:native&#124;supported_import&#124;task_board_clone}</code> |
| <code>stop</code> | <code>{session:SessionSummary,graceful:boolean,checkpoint_id:digest&#124;null,resumable:boolean,bootstrap_aborted:boolean,process_closed:boolean,store_closed:boolean}</code> |
| <code>resume</code> | <code>{session:SessionSummary,checkpoint_id:digest,terminal_backend:tmux&#124;conpty,native_session_id:string[1..512]}</code> |
| <code>sync</code> | <code>{peer_ids:sorted unique UUIDv7[1..1024],record_count:uint53,blob_count:uint53,byte_count:uint53,checkpoint_ids:sorted unique digest[0..4096],materialized:boolean,partial:boolean,transfer_id:UUIDv7&#124;null}</code> |
| <code>diff</code> | <code>{session_id:UUIDv7,peer_host_id:UUIDv7&#124;null,classification:identical&#124;different&#124;conflict,entries:PathDiff[0..65536]}</code> |
| <code>materialize</code> | <code>MaterializationSummary</code> |
| <code>doctor</code> | <code>{healthy:boolean,findings:CLIFinding[0..4096]}</code> |
| <code>logs</code> | <code>{emitting_host_id:UUIDv7,events:Observation Event[0..65536],next_cursor:string[1..512]&#124;null}</code> |
| <code>peer.list</code> | <code>{peers:PeerSummary[0..1024]}</code> |
| <code>peer.probe</code> | <code>{peer:PeerSummary,contracts:map(contract-name,sorted unique semver[1..16]),round_trip_ms:uint53}</code> |
| <code>session.set_profile</code> | <code>{session_id:UUIDv7,previous_profile:standard&#124;yolo,new_profile:standard&#124;yolo,event_id:digest}</code> |
| <code>pane</code> | <code>{session_id:UUIDv7,result:attached&#124;parked&#124;resumed&#124;stopped,winning_owner_host_id:UUIDv7,lease_epoch:uint53&gt;0}</code> |

The umbrella <code>ax NAME</code> reports the selected action's command tag; it
does not invent a separate resolve shape. A canceled chooser uses
<code>cancel</code>. <code>operation_id</code> is non-null for start, takeover,
fork, stop, resume, sync, materialize, and profile mutation, and null for pure reads. A
session-scoped command requires non-null <code>session_id</code> equal to every
nested Session Summary; <code>list</code>, <code>doctor</code>, and peer commands
use null. The internal streaming command <code>ax rpc serve --stdio</code> is an
RPC protocol endpoint, not a CLI Result producer, and MUST reject
<code>--json</code>.

The CLI stop tuple is mapped losslessly from RPC <code>session.stop</code>.
<code>checkpoint_id = null</code> is valid only with
<code>graceful=false</code>, <code>resumable=false</code>,
<code>bootstrap_aborted=true</code>, and nested session state
<code>failed</code>. A non-null checkpoint with nested state
<code>stopped</code> requires <code>resumable=true</code> and
<code>bootstrap_aborted=false</code>. Process and store closure must be true in
every success object; otherwise the command returns Structured Error instead.

A successful <code>MaterializationSummary</code> requires
<code>committed = true</code> and <code>ownership_changed = false</code>.
Replacement requires a non-null preserved checkpoint; every other mode
requires null. Its destination classification is the pre-transaction canonical
Section 11.7 value—copy/worktree normally report <code>absent</code> or
<code>empty</code>, replacement reports <code>managed_divergent</code>, and no
success may report <code>unmanaged_nonempty</code>.

Normative CLI success:

~~~json
{
  "schema": "urn:ax:schema:cli-result",
  "schema_version": "1.0.0",
  "command": "takeover",
  "ok": true,
  "operation_id": "0198f4c8-17e0-78ff-8879-1234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "body": {
    "mode": "force",
    "workspace_mode": "whole_group",
    "destination_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
    "source_host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
    "affected_session_ids": [
      "0198f4c8-3e70-7a11-8a2b-1234567890ab"
    ],
    "lease_epoch": 5,
    "lease_id": "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff",
    "checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
    "state": "running",
    "materialized": true,
    "adopted": false,
    "resumed": true,
    "warnings": ["previous_owner_may_still_be_running"]
  },
  "extensions": {}
}
~~~

For a task-board takeover, <code>adopted</code> MUST be true before
<code>resumed</code> can be true; for a direct takeover it MUST be false. The
Section 15.1 Structured Error example is the normative CLI failure shape.

### 14.3 Normative examples

Direct launch and later local resume:

~~~shell
ax start payments-api --provider codex --profile yolo --workspace .
ax stop payments-api
ax resume payments-api
~~~

Task-board prompt-mode launch:

~~~shell
ax start qwen-investigation --task-board --provider qwen \
  --task TASK-260819-example \
  --board-id agent-session-manager-spec \
  --launch-mode tracked-prompt --binding prompt \
  --profile standard --workspace .
~~~

Task-board goal-bound primary launch:

~~~shell
ax start codex-primary --task-board --provider codex \
  --task TASK-260819-example \
  --board-id agent-session-manager-spec \
  --launch-mode primary-owner \
  --goal PRIMARY-GOAL-260819-example --goal-revision 3 \
  --profile yolo --workspace .
~~~

Remote owner resolution without a prompt:

~~~shell
ax payments-api --non-interactive --action attach
ax payments-api --non-interactive --action takeover --to local
ax payments-api --non-interactive --action fork --as payments-api-experiment --to local
~~~

Force recovery:

~~~shell
ax takeover payments-api --to local --force \
  --expect-owner 0198f4c8-4a10-7b22-8b3c-1234567890ab \
  --expect-epoch 4 \
  --yes
~~~

Conflict-safe copy:

~~~shell
ax sync payments-api
ax diff payments-api
ax materialize payments-api --as-copy /srv/relux/replicas/payments
ax materialize payments-api --as-worktree /srv/relux/worktrees/payments
ax materialize payments-api --replace-managed-replica \
  --expect-checkpoint sha256:2222222222222222222222222222222222222222222222222222222222222222 \
  --yes
~~~

These commands materialize the same logical session; none is a fork and none
changes the lease. The following CLI fixtures are normative:

| Fixture | Invocation mutation | Result |
| --- | --- | --- |
| <code>CLI-MAT-N1</code> | Supply both <code>--as-copy</code> and <code>--as-worktree</code> | Exit 2, <code>invalid_arguments</code> |
| <code>CLI-MAT-N2</code> | Replacement without <code>--expect-checkpoint</code> | Exit 2, <code>invalid_arguments</code> |
| <code>CLI-MAT-N3</code> | Non-interactive replacement without <code>--yes</code> | Exit 16, <code>confirmation_required</code> |
| <code>CLI-MAT-N4</code> | Replacement targets <code>unmanaged_nonempty</code> | Exit 5, <code>workspace_conflict</code> |
| <code>CLI-MAT-N5</code> | Copy/worktree target is nonempty | Exit 5, <code>workspace_conflict</code> |
| <code>CLI-MAT-N6</code> | Worktree requested for a workspace group with no Git member | Exit 6, <code>capability_unavailable</code> |

Task-board launch and log grammar fixtures are:

| Fixture | Invocation property | Required result |
| --- | --- | --- |
| <code>CLI-TB-PRIMARY-POS</code> | Goal-bound primary example above | Board Goal is non-null, binding is <code>bound</code>, and bridge launch uses identical values |
| <code>CLI-TB-PROMPT-POS</code> | Qwen tracked-prompt example above | Goal is null, binding is <code>prompt</code>, and no primary capability is inferred |
| <code>CLI-TB-N1</code> | Task-board start omits board ID or launch mode | Exit 2, <code>invalid_arguments</code> |
| <code>CLI-TB-N2</code> | Primary omits either goal field or supplies <code>--binding</code> | Exit 2, <code>invalid_arguments</code> |
| <code>CLI-TB-N3</code> | Tracked prompt omits binding or supplies only one goal field | Exit 2, <code>invalid_arguments</code> |
| <code>CLI-LOG-LOCAL-POS</code> | <code>ax logs --session payments-api --limit 100</code> | Local events; result <code>emitting_host_id</code> equals the local stable host ID on every page |
| <code>CLI-LOG-REMOTE-POS</code> | <code>ax logs --peer workstation --session payments-api --limit 100</code>, then <code>ax logs --peer workstation --cursor NEXT</code> | SSH invokes the peer's local-only command; both raw results carry the allowlisted workstation host ID and stable pagination |
| <code>CLI-LOG-N1</code> | Cursor plus a filter, local cursor plus peer, or remote cursor with another peer | Exit 2, <code>invalid_arguments</code> |
| <code>CLI-LOG-N2</code> | SSH result emitter differs from the allowlisted peer | Exit 7, <code>host_identity_mismatch</code>; discard the result |
| <code>CLI-LOG-N3</code> | SSH result is forged/malformed, has another command tag, or contains an event from another emitting host | Exit 9, <code>integrity_failure</code>; return no partial events |

Normative copy result:

~~~json
{
  "schema": "urn:ax:schema:cli-result",
  "schema_version": "1.0.0",
  "command": "materialize",
  "ok": true,
  "operation_id": "0198f4c8-19e0-78ff-8879-2234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "body": {
    "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
    "checkpoint_id": "sha256:e051996f51f13ace4f5cdebe1e30fd26fd5fe104cfd6e6a7f9f1206ba3819656",
    "materialization_id": "0198f4c8-c290-73aa-9374-1234567890ab",
    "mode": "copy",
    "destination_path": "/srv/relux/replicas/payments",
    "destination_classification": "absent",
    "preserved_checkpoint_id": null,
    "committed": true,
    "ownership_changed": false
  },
  "extensions": {}
}
~~~

### 14.4 List and status fields

Text and JSON list/status MUST expose:

- session ID and name;
- direct/task-board kind and provider;
- winning owner host/name, lease epoch, and abbreviated lease ID;
- local role <code>owner</code> or <code>replica</code>;
- derived state;
- newest validated checkpoint and age;
- workspace materialization status/conflict;
- provider/platform capability statuses;
- last successful sync per peer; and
- warnings such as stale process, conditional capability, missing
  authentication, or divergent history.

No command MAY display or log credential values, raw transcript text, or opaque
bundle contents by default.

## 15. Errors and exit semantics

### 15.1 Structured Error

All machine-readable errors use <code>urn:ax:schema:error</code> version
<code>1.0.0</code>:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Structured Error schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>code</code> | string[1..128] | Stable lower-snake-case registry value |
| <code>message</code> | string[1..4096] | Human text; automation does not branch on it |
| <code>exit_code</code> | int32 | Exact Section 15.2 code assigned to <code>code</code> |
| <code>retryable</code> | boolean | True only when the identical request may safely be retried without new authority or confirmation |
| <code>operation_id</code> | UUIDv7, optional | Present whenever an operation was allocated |
| <code>session_id</code> | UUIDv7, optional | Present whenever the failure is session-scoped |
| <code>details</code> | diagnostic data map | Required, redacted open map constrained below |

~~~json
{
  "schema": "urn:ax:schema:error",
  "schema_version": "1.0.0",
  "code": "workspace_conflict",
  "message": "destination differs from its last materialized checkpoint",
  "exit_code": 5,
  "retryable": false,
  "operation_id": "0198f4c8-b180-7299-9273-1234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "details": {
    "expected_checkpoint": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    "remediations": ["diff", "copy", "worktree", "replace_managed_replica"]
  }
}
~~~

<code>schema</code>, <code>schema_version</code>, <code>code</code>,
<code>message</code>, <code>exit_code</code>, <code>retryable</code>, and
<code>details</code> are required. Operation and session IDs are optional and
MUST be present when known. Messages are for humans; automation MUST branch on
<code>code</code> and <code>exit_code</code>. Details MUST be redacted and
schema-valid.

The top-level object is closed. <code>message</code> is 1–4,096 UTF-8
characters. <code>details</code> is an explicitly open diagnostic data map, not
an implicit schema extension: it has 0–64 keys matching
<code>[a-z][a-z0-9_]{0,63}</code>, JSON values of maximum nesting depth 4, and
maximum canonical size 16 KiB. Readers MAY ignore unknown detail keys and MUST
never infer success, authority, or a remediation action from them. No detail
may contain a credential, raw transcript, environment secret, or opaque bundle
content.

Structured Error is independently versioned as a reusable schema, but that
does not imply independent negotiation inside every envelope. Provider
protocol <code>2.x</code>, task-board bridge <code>1.x</code>, and Mesh RPC
<code>2.x</code> each embed exactly Structured Error <code>1.0.0</code>. A
supported-major failure MUST use that exact object; the containing protocol
version is sufficient to select it. RPC hello MUST NOT advertise or negotiate
an <code>error</code> contract key. A future containing-protocol version may
bind another error version only by stating the new binding explicitly.

Bootstrap and incompatible-major behavior is exact:

| Surface | Supported-major failure before normal success | Unsupported major or unparseable first frame/output |
| --- | --- | --- |
| Provider JSON-over-stdio | A syntactically valid v2 request whose operation/body fails receives the Section 7.2 v2 failure envelope with Error 1.0.0 | The plugin MUST NOT masquerade a different-major object as v2. The host accepts no child error object, terminates/waits for exit as applicable, and emits its own local Error 1.0.0: <code>incompatible_protocol</code> for a recognizable major mismatch, otherwise <code>provider_protocol_error</code> |
| Task-board bridge facade | A syntactically valid v1 invocation failure receives the Section 9.2 v1 failure envelope with Error 1.0.0 | The facade output is not accepted as a bridge result. <code>ax</code> emits its own local Error 1.0.0: <code>incompatible_protocol</code> for a recognizable major mismatch, otherwise <code>task_board_bridge_unavailable</code> |
| Mesh RPC | Before hello success, a syntactically valid v2 non-hello request or invalid v2 hello receives one v2 failure envelope with Error 1.0.0 and the server then closes | An unsupported protocol major, invalid JSON, oversize line, missing protocol/version/request ID, or response that cannot be framed causes close without an RPC error frame. The initiator emits its own local Error 1.0.0: <code>incompatible_protocol</code> for a recognizable major mismatch, otherwise <code>transport_failure</code> |

A local error above is an <code>ax</code> CLI/observation result, not a forged
response attributed to the child or peer; it omits unknown operation/session
IDs and records redacted diagnostics only. Receivers MUST NOT parse a different
major's payload far enough to trust its error code, retryable bit, details, or
authority fields.

The normative binding fixtures are
<code>ERR-PROVIDER-COMPAT</code>, <code>ERR-BRIDGE-COMPAT</code>, and
<code>ERR-RPC-COMPAT</code>, which use the documented provider/RPC v2 and bridge
v1 failure envelopes; <code>ERR-PROVIDER-MAJOR</code>,
<code>ERR-BRIDGE-MAJOR</code>, and <code>ERR-RPC-MAJOR</code>, which change only
the containing protocol major to 3 for provider/RPC or 2 for the bridge and require the local
<code>incompatible_protocol</code> result; and
<code>ERR-PROVIDER-FIRST</code>, <code>ERR-BRIDGE-FIRST</code>, and
<code>ERR-RPC-FIRST</code>. Provider and RPC fixtures submit valid v2 envelopes
with an invalid first operation/body and require the bound v2 error; the bridge
fixture uses its valid v1 invocation and bound v1 error. The RPC fixture submits
<code>health.get</code> before hello, requires one bound v2 error, and then EOF.
<code>ERR-FIRST-UNFRAMED</code> supplies invalid JSON to
each stdio parser (or invalid JSON output from the bridge) and requires no
remote/child error to be trusted.

### 15.2 Exit codes

| Exit | Meaning |
| ---: | --- |
| 0 | Requested operation succeeded |
| 2 | Usage, invalid flag, or interactive choice required |
| 3 | Configuration or local precondition invalid |
| 4 | Session, checkpoint, peer, provider, or task-board identity not found |
| 5 | Workspace/native-store conflict; no silent overwrite |
| 6 | Capability unsupported, unknown, conditional, or incompatible |
| 7 | Authentication/authorization/allowlist failure |
| 8 | SSH/RPC transport failure; staging can be resumable |
| 9 | Integrity, schema, hash, or unsafe-path failure |
| 10 | Ownership/lease/fencing failure |
| 11 | Busy, quiesce timeout, or graceful stop timeout |
| 12 | Staging/materialization/rollback failure |
| 13 | Provider plugin/process failure |
| 14 | Task-board bridge/bundle/validation failure |
| 15 | Partial success: immutable sync succeeded but a requested materialization or peer did not |
| 16 | Explicit policy refusal, including missing destructive confirmation |
| 17 | Contract/schema migration required |
| 130 | Interrupted by operator signal before a clean response; inspect authority before retry |

### 15.3 Stable error codes

Protocol 1.0.0 fixes these code-to-exit mappings:

| Exit | Stable error codes |
| ---: | --- |
| 2 | <code>interactive_choice_required</code>, <code>invalid_arguments</code> |
| 3 | <code>invalid_config</code>, <code>idempotency_mismatch</code>, <code>local_precondition_failed</code> |
| 4 | <code>name_ambiguous</code>, <code>not_found</code> |
| 5 | <code>workspace_conflict</code>, <code>native_store_conflict</code> |
| 6 | <code>capability_unavailable</code>, <code>profile_mapping_unavailable</code>, <code>incompatible_protocol</code>, <code>incompatible_schema</code>, <code>provider_fork_unsupported</code>, <code>unsupported_backend_identity</code> |
| 7 | <code>authentication_failed</code>, <code>peer_not_allowlisted</code>, <code>host_identity_mismatch</code> |
| 8 | <code>owner_unreachable</code>, <code>transport_failure</code> |
| 9 | <code>unsafe_path</code>, <code>integrity_failure</code> |
| 10 | <code>not_owner</code>, <code>stale_owner</code>, <code>lease_conflict</code>, <code>invalid_state_transition</code> |
| 11 | <code>quiesce_timeout</code>, <code>stop_timeout</code>, <code>workspace_group_busy</code>, <code>workspace_group_changed</code> |
| 12 | <code>staging_incomplete</code>, <code>atomic_commit_unavailable</code>, <code>materialization_failed</code>, <code>rollback_failed</code> |
| 13 | <code>provider_timeout</code>, <code>provider_protocol_error</code>, <code>provider_process_failed</code> |
| 14 | <code>task_board_bridge_unavailable</code>, <code>task_board_bundle_invalid</code>, <code>task_board_validate_failed</code>, <code>checkpoint_unavailable</code> |
| 15 | <code>partial_sync</code> |
| 16 | <code>confirmation_required</code>, <code>policy_refused</code>, <code>secret_policy_violation</code> |
| 17 | <code>migration_required</code> |
| 130 | <code>interrupted</code> |

New error codes MAY be added in a compatible minor contract version, but an
unknown code retains the envelope's exit class and MUST NOT be interpreted as
success.

## 16. Security and threat boundary

### 16.1 Trusted mesh model

The security boundary is a trusted project mesh. Each authorized host and its
local operator can read synchronized project/session payloads. <code>ax</code>
does not protect payload confidentiality from an authorized peer, a trusted
provider plugin, or a compromised local user account.

Peers MUST be explicitly allowlisted by stable host ID and SSH endpoint.
Tailscale discovery MAY propose hosts but MUST NOT authorize them. SSH protects
authentication, integrity, and confidentiality in transport. v0.2.0 provides no
default payload encryption at rest and MUST NOT claim otherwise.

Machine-local credentials are a prerequisite at the destination. A successful
snapshot transfer MUST NOT imply that provider or remote-board authentication
will succeed.

### 16.2 Mandatory exclusions

No manifest or bundle generated by <code>ax</code> MAY intentionally include:

| Class | Examples |
| --- | --- |
| Provider credentials | API keys, OAuth tokens, <code>auth.json</code>, account cookies, subscription tokens |
| SSH/private identity | SSH private keys, agent sockets, known-host mutation state |
| Environment secrets | Secret environment values, dotenv secrets unless explicitly managed as project content outside <code>ax</code> |
| Machine authentication | Apple Keychain, Secret Service, Windows Credential Manager, task-board login tokens |
| Live process identity | PIDs used for control, process handles, terminal IDs used as authority |
| IPC/runtime | Unix sockets, named pipes, tmux server sockets, session-message tokens |
| Transient locking | Lock files, live SQLite WAL/SHM/journals, updater locks, provider PID locks |
| Mutable derived indexes | <code>ax</code> SQLite and provider caches not required by a documented import/resume contract |

Opaque durable provider history MAY contain historical paths or historical PID
facts inside byte-preserved transcripts. Those facts MAY be transferred as
sensitive history when required for native resume, but MUST remain inert and
MUST NOT be treated as current process, ownership, or routing authority. This
does not permit copying a live PID/lock control artifact.

Transcripts and tool outputs can themselves contain secrets entered by an
operator or printed by tools. v0.2.0 does not claim reliable content-level
secret scrubbing. Operators MUST therefore treat all payloads as sensitive and
authorize only trusted project peers. An implementation SHOULD offer a
best-effort scanner and warning, but scanner success MUST NOT be described as a
confidentiality guarantee.

### 16.3 Path and filesystem safety

Receivers MUST treat manifests, filenames, symlinks, hardlinks, modes, provider
plans, and archive members as untrusted input even from an allowlisted peer.
They MUST prevent:

- path traversal, absolute paths, drive/UNC injection, alternate streams, and
  repeatedly encoded separators;
- symlink/reparse escape during both validation and commit;
- case-fold collisions on case-insensitive destinations;
- replacement of unmanaged paths;
- device/FIFO/socket creation;
- broad deletion from tombstones; and
- time-of-check/time-of-use swaps by validating through directory handles or
  equivalent safe filesystem primitives.

Archive extraction MUST occur inside a newly created staging root. Validation
MUST be repeated after extraction and before commit.

### 16.4 Command and plugin safety

All process invocations MUST use argv arrays and native process APIs. Shell
command construction from names, paths, provider output, or peer data is
forbidden. Remote SSH commands MUST use a fixed <code>ax</code> entry point and
platform-safe encoding.

Provider plugins are privileged code. Explicit trust by path/digest is required
unless compiled in. Plugin stdout is protocol input and MUST be validated.
Plugin stderr, provider logs, and doctor output MUST be redacted before
persistence.

### 16.5 Force-takeover risk

Epoch fencing protects converged <code>ax</code> state; it cannot stop an
unreachable old process from changing its local workspace or external systems.
Force takeover MUST therefore:

- require explicit owner/epoch expectations;
- warn about split brain and external side effects;
- avoid overwriting either workspace history;
- preserve losing-lease events and both workspace checkpoints; and
- fence stale history from authoritative sync/resume after convergence.

### 16.6 Out of scope

v0.2.0 does not provide Byzantine consensus, hostile-peer isolation,
multi-tenant access control, end-to-end snapshot encryption, secret
distribution, provider-account migration, revocation of actions already sent
to external services, or sandboxing stronger than the provider/OS configuration
selected by the operator.

## 17. Compatibility and migration

### 17.1 Semantic-version rules

Each contract in Section 1.5 versions independently:

- a major increment MAY break syntax or semantics and MUST require explicit
  negotiation/migration;
- a minor increment MAY add optional operations, enum values, or namespaced
  extension fields but MUST preserve all prior semantics;
- a patch increment MAY clarify constraints or fix a validator defect without
  adding a field or changing behavior.

Within any negotiated major version, new object data MUST live under a namespaced
<code>extensions</code> entry unless the consumer negotiated a newer minor
schema. Unknown top-level fields remain an error. Protocol peers choose the
highest mutually supported minor within a common major; they MUST NOT select a
major by coercion.

Independent release versions do not override an explicit embedding rule.
Provider protocol and Mesh RPC major 2 and task-board bridge major 1 each bind
Structured Error 1.0.0 as Section 15.1 specifies; those envelopes do not
negotiate the error schema separately. Compatibility is evaluated first for the
containing protocol and then against its fixed embedded-error validator.

The v0.2.0 correction is an explicit major-version boundary. Provider protocol
1.0.0, Mesh RPC 1.0.0, and Materialization recovery state 1.0.0 remain the
immutable v0.1.0 contracts and MUST NOT be interpreted using the corrected
2.0.0 request or journal shapes. There is no in-place migration of a live
machine-local 1.0.0 materialization transaction: upgrade MUST first reach a
safe terminal state or roll it back with the v0.1.0 implementation, then create
a new 2.0.0 transaction. A 2.0.0 peer or plugin rejects major 1 rather than
coercing its missing IDs or freezing an evolving status read.

### 17.2 Reader/writer behavior

A writer emits exactly the negotiated version. A reader:

1. rejects an unsupported major;
2. accepts the same/lower supported minor;
3. preserves unknown namespaced extensions byte-for-byte when forwarding an
   immutable object;
4. rejects an unknown ownership/security enum that would affect behavior; and
5. MAY retain an unknown event as inert history but MUST NOT derive state from
   it.

An <code>enabled = true</code> capability is valid only for the exact negotiated
contract and provider tuple. Version range mismatch changes it to conditional
or unsupported.

### 17.3 Immutable data migration

Immutable objects MUST never be edited in place. A migration creates a new
schema-versioned object that references the prior object in
<code>extensions["works.relux.ax.migrated-from"]</code>. That extension value is
a closed object containing exactly <code>schema_id:string</code>,
<code>schema_version:semver</code>, and <code>object_id:digest</code>. The writer
validates the new object and atomically advances a local reference. Old objects
remain available for rollback until retention policy allows collection.

Configuration migration MUST create a backup, write a new file atomically, and
require <code>ax migrate config</code> for a major change. The CLI MUST NOT
silently rewrite a major-version config at startup.

The derived SQLite index MAY be rebuilt at any time. It is never a migration
source of truth.

### 17.4 Upgrade and downgrade

Before upgrading, <code>ax</code> SHOULD checkpoint locally owned sessions.
After upgrade it MUST run schema/plugin/task-board compatibility checks before
auto-resume.

A downgraded binary that cannot understand current records MUST enter
read-only diagnostic mode for those sessions. It MUST NOT resume, transfer
ownership, materialize, or write lower-version replacements.

Provider upgrades invalidate prior tuple-specific acceptance until the adapter's
declared version range and compatibility fixture cover the new version. Muse
and Antigravity unknowns in Section 8 remain explicit version gates.

## 18. Observability and operations

### 18.1 Observation Event

Machine-readable logs use <code>urn:ax:schema:observation</code> version
<code>1.0.0</code>:

~~~json
{
  "schema": "urn:ax:schema:observation",
  "schema_version": "1.0.0",
  "stream_id": "0198f4c8-29f0-7900-897a-2234567890ab",
  "sequence": 184,
  "timestamp": "2026-08-19T04:30:00.000Z",
  "level": "info",
  "event": "takeover.phase",
  "operation_id": "0198f4c8-b180-7299-9273-1234567890ab",
  "session_id": "0198f4c8-3e70-7a11-8a2b-1234567890ab",
  "host_id": "0198f4c8-4a10-7b22-8b3c-1234567890ab",
  "peer_host_id": "0198f4c8-7d40-7e55-8e6f-1234567890ab",
  "phase": "destination_validated",
  "result": "success",
  "duration_ms": 1240,
  "counts": {
    "records": 12,
    "events": 0,
    "manifests": 0,
    "blobs": 4,
    "chunks": 0,
    "bytes": 8192,
    "retries": 0
  },
  "object_ids": [],
  "error_code": null,
  "extensions": {}
}
~~~

The Observation Event is not identity-addressed, but its JSON Lines object is
closed and contains exactly:

| Field | Type | Constraint |
| --- | --- | --- |
| <code>schema</code> | string | Exact Observation schema identifier |
| <code>schema_version</code> | semver | Exact <code>1.0.0</code> |
| <code>stream_id</code> | UUIDv7 | Stable per host installation; changing it starts a new explicitly separate stream |
| <code>sequence</code> | uint53 | Starts at 1 and increases by exactly one before each durable append |
| <code>timestamp</code> | timestamp | Observation time; not authority |
| <code>level</code> | enum | <code>debug</code>, <code>info</code>, <code>warn</code>, or <code>error</code> |
| <code>event</code> | observation-name | <code>[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){1,7}</code>, 3–128 characters |
| <code>operation_id</code> | UUIDv7 or null | Required null when no operation exists |
| <code>session_id</code> | UUIDv7 or null | Required null for non-session events |
| <code>host_id</code> | UUIDv7 | Emitting host |
| <code>peer_host_id</code> | UUIDv7 or null | Required null when no peer participates |
| <code>phase</code> | string[1..128] or null | Stable lower-snake-case phase or null |
| <code>result</code> | enum | <code>started</code>, <code>success</code>, <code>partial</code>, <code>failure</code>, or <code>cancelled</code> |
| <code>duration_ms</code> | uint53 or null | Null for a point/start event; otherwise elapsed milliseconds |
| <code>counts</code> | ObservationCounts or null | Closed aggregate below |
| <code>object_ids</code> | sorted unique digest[0..4096] | Redacted object identities only |
| <code>error_code</code> | string[1..128] or null | Stable Section 15 code when result is partial/failure |
| <code>extensions</code> | object | Reverse-DNS extension keys only; no payload content |

<code>ObservationCounts</code> contains exactly
<code>records:uint53</code>, <code>events:uint53</code>,
<code>manifests:uint53</code>, <code>blobs:uint53</code>,
<code>chunks:uint53</code>, <code>bytes:uint53</code>, and
<code>retries:uint53</code>. Counters not used by an applicable aggregate are
zero; a point event with no aggregate uses null instead of a partial counts
object. <code>partial</code> and <code>failure</code> require non-null error code;
all other results require null. <code>duration_ms</code> is non-null for the
terminal observation of a measured operation and null for its
<code>started</code> observation.

The durable log order is <code>sequence</code> within the one active
<code>stream_id</code>; timestamps never break ties. The stream ID is stored in
owner-only state and survives log rotation. If that state is deliberately
reset, the old stream remains read-only and a new stream begins at one;
<code>ax logs</code> returns streams in bytewise UUIDv7 order, then sequence. A cursor
contains or authenticates the host ID, stream ID, next sequence, original
filter, and limit without exposing secrets. It MUST be rejected after scope or
host mismatch rather than silently restarting pagination.

Normative negative fixtures are: missing or repeated sequence; missing nullable
<code>peer_host_id</code>; result <code>ok</code>; partial result with null error;
a counts object omitting <code>chunks</code>; negative bytes; an object ID array
with duplicates; and an unknown top-level <code>provider</code> field. Each MUST
be rejected. Provider detail belongs under a negotiated reverse-DNS extension,
not an undeclared member.

Logs MUST NOT contain prompt/transcript/tool-output content, opaque bundle
bytes, environment values, authorization headers, key material, full remote
URLs with user info, or raw plugin stderr without redaction. Session names MAY
be omitted in favor of IDs in durable logs.

JSON Lines observations MUST be written below <code>&lt;state&gt;/logs</code>
with owner-only permissions or an equivalent Windows user-only DACL. The user
service MAY also mirror redacted events to launchd/systemd/Windows service
logging. <code>ax logs</code> reads the local durable stream; remote logs require
an explicit peer flag and the authenticated, allowlisted SSH remote-CLI path in
Section 14.1. Mesh RPC 2.0.0 deliberately has no log-read operation. The remote
process returns its own non-null emitting host identity and the initiator does
not rewrite it. Log retrieval MUST NOT become a public listener.

### 18.2 Required events

At minimum, emit:

- <code>service.started</code>, <code>service.stopped</code>, and
  <code>service.health</code>;
- <code>rpc.connected</code>, <code>rpc.rejected</code>, and
  <code>rpc.disconnected</code>;
- <code>sync.inventory</code>, <code>sync.transfer</code>,
  <code>sync.validated</code>, and <code>sync.partial</code>;
- <code>materialization.conflict</code>,
  <code>materialization.prepared</code>,
  <code>materialization.committed</code>, and
  <code>materialization.rolled_back</code>;
- <code>lease.observed</code>, <code>lease.changed</code>,
  <code>lease.stale_process</code>, and
  <code>lease.concurrent_force</code>;
- <code>provider.probed</code>, <code>provider.quiesced</code>,
  <code>provider.captured</code>, <code>provider.stopped</code>, and
  <code>provider.failed</code>;
- <code>task_board.launched</code>, <code>task_board.exported</code>, <code>task_board.imported</code>,
  <code>task_board.opened</code>, and <code>task_board.adopted</code>; and
- one <code>takeover.phase</code> or <code>fork.phase</code> event for every
  numbered transition in Section 13.

### 18.3 Metrics and health

The service SHOULD expose local text/JSON metrics through
<code>ax status --json</code> or a machine-local endpoint, never a public
listener. Metric names are:

<code>ax_sessions</code>, <code>ax_stale_processes</code>,
<code>ax_divergent_histories</code>, <code>ax_peer_reachable</code>,
<code>ax_sync_seconds</code>, <code>ax_sync_bytes</code>,
<code>ax_transfer_retries</code>, <code>ax_materialization_conflicts</code>,
<code>ax_provider_probe_success</code>, and
<code>ax_checkpoint_age_seconds</code>.

Labels MUST be bounded: host ID, provider ID, platform, operation kind, result,
and error code. Session ID/name MUST NOT be a metrics label.

<code>ax doctor</code> MUST report:

- local path/config/index health;
- terminal backend and service status;
- peer allowlist/SSH/RPC compatibility;
- provider executable version, trust digest, profile mapping, and every
  capability status/evidence/detail;
- required machine-local authentication presence without revealing values;
- newest checkpoint/materialization health;
- task-board bridge version/capabilities; and
- stale processes, retained staging, divergence, and tombstone backlog.

Doctor exit is non-zero when a requested provider/session operation is
unavailable. Unknown facts MUST appear as unknown, not as green checks.

### 18.4 Audit retention

Lease changes, force confirmations, explicit managed replacements, task-board
launch/adoption, profile changes, and tombstone issuance/resolution MUST use the exact
Section 5.2 Session Event types and payloads. In particular, a force receipt is
represented by <code>takeover.force_confirmed</code>, replacement by
<code>replica.replace_confirmed</code>, initial launch by
<code>task_board.launched</code>, adoption by <code>task_board.adopted</code>,
and deletion lifecycle by
<code>tombstone.issued</code>/<code>tombstone.resolved</code>. The event and
every referenced immutable object MUST be retained as long as the corresponding
Session Record.

A workspace- or managed-replica-scoped Tombstone is audited on its
<code>authorizing_session_id</code> chain; its event payload repeats the
workspace subject and target reference. Other sessions sharing the workspace
group discover the Tombstone by union and MUST apply the Section 10.7 conflict
rules, but MUST NOT synthesize a second issuance event. Peer receipt is the
separately versioned Tombstone Acknowledgement, not a Session Event and not
owner authority. It follows the Tombstone retention/GC rule.

Routine debug logs MAY rotate locally. Session Events, Tombstones, and
Acknowledgements are immutable authority/evidence; log files and Observation
Events are not.

## 19. <code>ax</code> implementation conformance and product release

### 19.1 Implementation phases

These are ordered phases for an implementation that intends to claim
<code>ax</code> product conformance version 0.2.0. They are not prerequisites
for publishing this specification and are not permission to ship a required
core target half-implemented:

1. <strong>Contract fixtures</strong>: implement parsers/validators, canonical
   identities, compatibility negotiation, error schema, and golden examples.
2. <strong>Local lifecycle</strong>: implement state/lease engine, derived
   index, direct plugin host, tmux wrapper, stop/resume, and daemonless use.
3. <strong>Mesh and workspace</strong>: implement SSH RPC, Merkle union,
   resumable chunks, staging, Git/non-Git materialization, tombstones, and
   conflicts.
4. <strong>Provider and task-board adapters</strong>: enable only
   tuple-specific accepted capabilities; implement the opaque bridge.
5. <strong>Native Windows</strong>: implement ConPTY/process supervisor,
   PowerShell-safe SSH, Windows materialization/atomicity, and user service.
6. <strong>Product release hardening</strong>: run every required acceptance
   lane, validate product-facing docs/examples, test migration/downgrade, and
   retain the implementation's conformance evidence.

Each phase MUST leave prior accepted fixtures green. Experimental provider cells
remain disabled and visible in doctor.

### 19.2 Platform lanes

The automated suite MUST provide these lanes:

| Lane | Environment | Required coverage |
| --- | --- | --- |
| <code>PF-MAC-ARM64</code> | Current supported macOS on arm64 | Core CLI, launchd, tmux, SSH loopback, Git/non-Git, local provider probes |
| <code>PF-MAC-AMD64</code> | Supported macOS on amd64 or reproducible hosted runner | Core CLI and providers that publish amd64 support |
| <code>PF-LINUX-AMD64</code> | Ubuntu 20.04+ baseline | Core CLI, systemd user, tmux, OpenSSH, filesystems, providers |
| <code>PF-LINUX-ARM64</code> | arm64 Linux | Core/storage/RPC and providers that publish arm64 support |
| <code>PF-WSL2-AMD64</code> | WSL2 with systemd and Windows-mounted plus Linux-home filesystems | Linux backend, tmux restore, path/locking/signal/auth differences |
| <code>PF-WIN11-AMD64</code> | Windows 11 24H2 PowerShell | Native ConPTY, Scheduled Task/service, OpenSSH, NTFS conflict/atomicity |
| <code>PF-WIN11-ARM64</code> | Windows 11 arm64 where provider artifact exists | Core CLI plus only documented provider artifacts |

At least PF-MAC-ARM64, PF-LINUX-AMD64, PF-WSL2-AMD64, and PF-WIN11-AMD64 are
product-release-blocking core lanes. A missing hosted runner does not permit
claiming a cell; the project MUST use a self-hosted lane or leave it
conditional.

### 19.3 Provider acceptance suites

Suite codes:

- <strong>D</strong>: probe, launch, identify, native stop/resume, persisted
  profile, native command interoperability;
- <strong>P</strong>: closed-store or backend-aware cross-host materialization,
  changed destination path, isolated Object Sink capture, per-blob resumable
  transfer, exclusions, prepare/status/commit/rollback recovery, validation,
  incompatible-version negative case;
- <strong>M</strong>: PTY/ConPTY input quiescence, idle proof, interruption,
  graceful exit, process/database flush;
- <strong>T1</strong>: task-board goal-bound primary launch/export/import/open/adopt;
  and
- <strong>TP</strong>: task-board tracked prompt launch/export/import/open/adopt,
  including a null-goal bundle.

| Provider | macOS | Linux | WSL2 | Native Windows |
| --- | --- | --- | --- | --- |
| Codex | D, P, M, T1 | D, P, M, T1 | D, P, M, T1 | D, P, M, T1 only after native-store/ConPTY pass |
| Claude | D, P, M, T1 | D, P, M, T1 | D, P, M, T1 | D/P/M/T1 conditional pending native PowerShell/ConPTY pass |
| Gemini | D, P, M, TP | D, P, M, TP | D/P/M/TP conditional | D, P, M, TP on Windows 11 24H2+ |
| Muse | D on probed macOS tuple; P expected disabled; M conditional; TP | D/M/TP conditional; P disabled | D/M/TP conditional; P disabled | D/M unknown and disabled; P disabled; TP only if task-board runtime supports it |
| Antigravity | D backend-positive and backend-negative; P expected disabled; M | Same plus DBus/keyring | D/M conditional; P disabled | D/M conditional; P disabled |
| Pi | D, P, M | D/P/M conditional by exact version | D/P/M conditional | D/P/M conditional |
| Qwen | TP only | TP only | TP only where runtime probe passes | TP only where runtime probe passes |
| Future plugin | Negative unknown/disabled test | Same | Same | Same |

For every C or ? cell, the suite MUST assert <code>enabled = false</code>,
operation refusal with exit 6, and an actionable doctor detail. For every U
cell, it MUST assert deterministic refusal and no provider/native-store
mutation. A capability MAY change to A only after its named suite passes on the
exact tuple and the evidence record is published.

Muse promotion additionally requires subagent/tool-output/encrypted-reasoning
fidelity, benign cron fencing, clean exit, date-shard/path change, fork without
duplicated scheduled work, and incompatible-version failure. Antigravity
promotion requires same-realm success, different/no-account failure, deleted
backend UUID failure without blank replacement, cache merge preserving
unrelated entries, <code>Stop.fullyIdle</code> false/true cases, and closed
SQLite handles.

### 19.4 End-to-end acceptance cases

| ID | Required automated assertion |
| --- | --- |
| <code>AC-OWN-001</code> | One winning owner and zero/many replicas are derived from all union orders. |
| <code>AC-OWN-002</code> | Lower and losing same-epoch events cannot affect authoritative state and remain preserved. |
| <code>AC-LAUNCH-001</code> | Direct launch creates record/lease/wrapper/provider identity/checkpoint and native resume works outside <code>ax</code>. |
| <code>AC-LAUNCH-002</code> | Task-board public launch starts from a null creation-record manager ref, persists <code>task_board.launched</code>, survives a lost response with the same caller operation ID, exports an opaque bundle, and never reads private manager bytes. |
| <code>AC-PATH-001</code> | Flags, the exact five-variable environment registry, configuration loading, platform defaults, and every process component resolve identical roots; empty and unknown <code>AX_*</code> values follow Section 3.2. |
| <code>AC-TB-BOUNDARY-001</code> | Safe and unsafe bridge proofs map field-for-field into Checkpoint and RPC evidence; provider version/generation mismatch, background work, and a lost export response cannot publish a checkpoint or duplicate a bundle. |
| <code>AC-SYNC-001</code> | Set-union converges independent of peer/order/retry; live SQLite is absent from manifests. |
| <code>AC-SYNC-002</code> | 4 MiB chunk interruption resumes only missing chunks and validates the whole blob. |
| <code>AC-NS-001</code> | Every identity-bearing schema and raw blob maps to exactly one Section 11.4 namespace; excluded local objects change no root, and both independent implementations reproduce all <code>MIXED-NS-1</code> roots. |
| <code>AC-MAT-001</code> | Source-only provider capture writes only a fresh Object Sink; two blobs with chunk zero remain distinct; cross-host authority-scoped prepare/status/commit/rollback and every listed crash point preserve or restore exact bytes. |
| <code>AC-MAT-002</code> | Tagged workspace/provider/task-board/composite prepare/result fixtures preserve kind, intent, passive-versus-transfer cohorts, stopped-session behavior, and managed-replica nullability through status/finalize/rollback. |
| <code>AC-MAT-003</code> | Full Materialization Plan objects for all four kinds accept only their registered source/authority/action/validation/strategy combinations; provider and task-board one-root transactions have a legal strategy and every full negative object fails before staging. |
| <code>AC-MAT-004</code> | A lost <code>materialize.prepare</code> response is retried with the same caller-created operation/materialization IDs and canonical body, returns the byte-identical receipt after receiver restart, and creates exactly one journal and one set of derived authorities/IDs; a changed body fails with <code>idempotency_mismatch</code>, while later status reads may evolve through durable phases under fresh request IDs. |
| <code>AC-PTX-001</code> | Fresh provider processes prepare/status/commit/rollback through the same host-created object/transaction authorities; same-filesystem and path-disjointness checks pass or fail before mutation, and all five rollback reasons round-trip exactly. |
| <code>AC-PTX-002</code> | <code>(operation, operation_id)</code> is the sole provider mutation idempotency key; a lost-response mutation retry that changes materialization ID, transaction ID, plan, authority, activation, or rollback reason returns <code>idempotency_mismatch</code> and creates no second transaction root; <code>materialize-status</code> carries no operation ID and may evolve from prepared to committed or rolled back. |
| <code>AC-MARKER-001</code> | Absent, matching, content/path-mismatching, replacement, and crash-reconstructed Managed Replica Markers produce the exact classifications, marker identity, atomic current/history writes, and fail-closed recovery in Section 10.6. |
| <code>AC-ATTACH-001</code> | Remote attach uses SSH, changes no lease/manifest, and reconnects after client loss. |
| <code>AC-TAKE-001</code> | Graceful takeover follows every phase, stops source before lease advance, persists profile, and leaves source a replica. |
| <code>AC-TAKE-002</code> | Failure before/after source stop and before/after lease advance has exactly the authority/recovery in Section 13.6. |
| <code>AC-FORCE-001</code> | Unreachable old owner is fenced after convergence; warnings/expectations are required; both histories survive. |
| <code>AC-FORCE-002</code> | Concurrent same-epoch force records select the same winner on every peer. |
| <code>AC-FORCE-DIRECT-001</code> | Direct force takeover stages before fencing, advances one lease, atomically materializes, proves the exact native/backend identity, and resumes without creating a blank session. |
| <code>AC-FORCE-DIRECT-002</code> | Direct capability/identity failure before fencing leaves authority unchanged; post-fence materialization/resume failure rolls back destination bytes but leaves the destination stopped owner. |
| <code>AC-FORCE-TB-001</code> | Task-board force takeover validates inert inputs, advances one lease, then prepares a journal/fresh staging root, commits import/open dormant, finalizes the exact adopt/resume binding, and never reads private manager state. |
| <code>AC-FORCE-TB-002</code> | Missing auth/bundle/bridge, expired tokens, lost adopt response, and post-adopt resume failure follow Section 13.7 without blank substitution or ownership rollback. |
| <code>AC-FORK-001</code> | Fork deterministically projects the old group/member/manifests to new identities, persists new topology/session/epoch-1 lease, runs direct or task-board materialization through prepare/commit/activation/finalize, and leaves every source object/authority unchanged. |
| <code>AC-FORK-002</code> | Failures before/after topology, session persistence, materialization, provider identity, bridge open/adopt, process activation, finalize, and event publication follow the Section 13.8 recovery matrix without blank identity or duplicate activation. |
| <code>AC-STOP-001</code> | Graceful stop creates checkpoint, closes provider, retains lease/state, and resumes with persisted profile. |
| <code>AC-BOOT-001</code> | Every epoch-1 pre-checkpoint direct/task-board launch failure is either idempotently retried under the same process/manager identity, promoted through a first checkpoint, or force-closed as a null-checkpoint non-resumable failed bootstrap; RPC/Event/CLI shapes agree. |
| <code>AC-RESUME-001</code> | No-materialization, workspace-only, provider-only, task-board-only, and both composite owner-resume paths execute their exact prepare/commit/activation/finalize or rollback/status recovery and emit one profile-consistent resumed event. |
| <code>AC-RESTORE-001</code> | tmux restore invokes wrapper and parks remote/stale owners; it does not migrate a session. |
| <code>AC-RESTORE-002</code> | Native Windows recreates ConPTY after reboot and resumes only after lease/checkpoint validation. |
| <code>AC-WORK-001</code> | The exact Section 10.4 Git root/child fixtures round-trip branch/detached HEAD, object pack, raw/logical index, staged versus working bytes, untracked files, modes, submodules, features, cwd, and project config without network access. |
| <code>AC-WORK-002</code> | The exact managed-tree variant round-trips and rejects Git-only members; concurrent capture mutation retries/fails. |
| <code>AC-WORK-003</code> | Divergent managed and unmanaged destinations fail closed; diff/copy/worktree/explicit managed replacement behave as specified. |
| <code>AC-WORK-004</code> | Shared checkout migrates as a group or separates into worktrees; one member cannot move alone while busy. |
| <code>AC-WORK-005</code> | Parent and every initialized submodule pack validate in isolated object databases; clean, staged-pointer, unstaged-pointer, and combined pointer triples round-trip without copying child objects into the parent pack. |
| <code>AC-GROUP-001</code> | Concurrent Session Record joins and authoritative session-Tombstone leaves derive one order-independent live membership set; conflicting topology records park the group. |
| <code>AC-GROUP-002</code> | Whole-group and separate-worktree fixtures revalidate the exact WorkspaceGroupExpectation at every phase and never silently shrink or partially activate a changed cohort. |
| <code>AC-TOMB-001</code> | All four Tombstone scopes and Acknowledgements validate; exact-path delete/modify/recreate golden cases converge or fail closed independent of union order; traversal/wildcard/root attempts fail; retention/ack/live-reference gates GC. |
| <code>AC-SEC-001</code> | Credential/key/socket/PID/lock/auth fixtures are excluded across direct and task-board paths. |
| <code>AC-SEC-002</code> | SSH/allowlist host-ID mismatch fails and discovery cannot authorize. |
| <code>AC-SEC-003</code> | Archive traversal, symlink escape, case collision, special file, and command injection fixtures fail. |
| <code>AC-TB-001</code> | Caller-ID launch/export/import/open is idempotent, open is dormant, only winning-owner adopt can resume, graceful/force stop are invocable, local board runs standalone <code>task-board validate</code>, and prompt bundles accept the conditional null goal. |
| <code>AC-TB-002</code> | Remote board transfers identity only and requires destination-local credentials. |
| <code>AC-TB-003</code> | Primary and prompt bundle projection preserves complete Board/Goal/Launch objects, non-secret literals, and extensions; the exact <code>sha256/HH/REST</code> archive member set rejects missing, extra, mis-sharded, and digest-mismatched bytes. |
| <code>AC-TB-004</code> | Durable task-board journal/status state recovers import/open/adopt/resume lost responses, crashes, expiry, and binding mismatch across graceful, force, passive, resume, and fork paths; bridge mutation never precedes journal creation. |
| <code>AC-PROFILE-001</code> | Direct and task-board start → profile change → checkpoint → takeover/resume/fork use one effective profile/source across bundle, plugin/bridge activation, and events; Pi's equal provider mapping does not erase the ax profile change. |
| <code>AC-PATH-002</code> | Every object, record, manifest, bundle blob, quarantine item, provider sink/source, and marker history maps a digest through the same two-hex-shard/62-hex-leaf algorithm on POSIX and native Windows. |
| <code>AC-VERS-001</code> | Contracts version independently; explicit containing-protocol Error bindings are honored; major mismatch/downgrade fail read-only and minor extensions preserve semantics. |
| <code>AC-ERR-001</code> | Every failure class returns the stable exit/error mapping and JSON stdout remains one document. |
| <code>AC-ERR-002</code> | Provider, bridge, and RPC compatible, incompatible-major, and pre-handshake/first-frame fixtures either use the statically bound Error 1.0.0 envelope or close and produce only the specified local error. |
| <code>AC-WIRE-001</code> | Every Section 1.5 contract and every embedded tagged variant in Appendix D accepts its positive fixture and rejects missing, null-invalid, enum-invalid, unsafe-number, oversized, forbidden-variant, and unknown members. |
| <code>AC-NUM-001</code> | Python, JavaScript, Go, and CBOR implementations agree on every Section 1.6 safe/decimal boundary vector; numeric 2^53 and wider values are rejected without rounding. |
| <code>AC-MERKLE-001</code> | Empty, singleton, branch, shared-prefix, and randomized ID sets produce the Section 11.4 roots in two independent implementations and every children response rehashes exactly. |
| <code>AC-CLI-001</code> | Every Section 14.3 non-interactive example parses; missing takeover destination, missing fork name/destination, action-inapplicable flags, and invalid materialize conflict flag combinations fail with their specified exits. |
| <code>AC-CLI-002</code> | Copy and worktree materialize the same session without lease change; managed replacement requires expected checkpoint, confirmation event, preserved divergence, and refuses unmanaged content. |
| <code>AC-CLI-003</code> | Goal-bound primary and tracked-prompt task-board launches require and normalize the exact board/mode/goal/binding inputs; local and explicit-peer log reads paginate with host-bound cursors and stable ordering. |
| <code>AC-CLI-004</code> | Local and SSH-remote log pages carry the actual non-null emitting host ID; cursor pages preserve it, and mismatched or forged remote results return no events. |
| <code>AC-OBS-001</code> | Required events/metrics exist and a secret/transcript canary never appears in logs. |
| <code>AC-DOC-001</code> | All internal section references, local links, JSON/TOML examples, tables, and traceability rows validate. |
| <code>AC-REF-001</code> | A schema-aware reference walker resolves every normative simple/dotted field expression and enum token against the containing closed registry (including MaterializationCohort fields), rejects aliases absent from that schema, and separately validates every extension key against Section 1.6. |
| <code>AC-DIAG-001</code> | Structurizr and PlantUML sources render; committed SVGs are visually inspected and match Sections 3 and 13. |

### 19.5 <code>ax</code> implementation release acceptance rule

An implementation MAY claim <code>ax</code> product conformance 0.2.0 only when:

1. all product-release-blocking core platform lanes pass;
2. every A provider cell passes its suites;
3. every C/?/U cell passes its negative-advertisement tests;
4. all Section 19.4 cases pass;
5. no credential/excluded-state fixture enters an artifact;
6. its product documentation and generated examples validate from a clean
   implementation checkout.

Unknown provider facts do not block an implementation release when, and only
when, their cells remain disabled and truthful.

These runtime lanes and provider suites are an implementation-conformance gate,
not the <code>agent-session-manager-spec</code> publication gate. Section 20 MAY
publish the normative contract before any <code>ax</code> product binary exists;
it MUST NOT claim that the unimplemented runtime cases passed.

## 20. Specification publication and governance

### 20.1 Repository and release

The specification repository MUST be public at
<code>relux-works/agent-session-manager-spec</code>, use <code>main</code> as
the default branch, and carry the MIT License. The first specification release
is <code>v0.2.0</code>.

The release commit and annotated tag MUST both be signed using Ivan Oparin's
SSH signing key <code>~/.ssh/ivanopcode</code>. The commit author is:

~~~text
Ivan Oparin <oparin@me.com>
~~~

No AI <code>Co-Authored-By</code> trailer or other AI attribution trailer MUST
appear in any commit message, including the release commit. The release commit
MUST contain only the human author above and MUST be SSH-signed with
<code>~/.ssh/ivanopcode</code>. Automation MUST NOT stage, commit, tag, or push;
automation MUST stop before any <code>git add</code>/<code>git commit</code>/
<code>git tag</code>/<code>git push</code> operation and hand the exact reviewed
commands to the user for explicit human execution. The model MAY be acknowledged
only in prose documentation outside commit metadata, clearly marked as
non-commit attribution and only when explicitly requested; it MUST NOT appear as
a commit co-author.

### 20.2 Publication gate

This section governs the <code>agent-session-manager-spec</code> repository's
specification release <code>v0.2.0</code>, not an <code>ax</code> executable
release. The publication task MUST:

1. verify a clean checkout contains SPEC, public operator/contributor guides,
   diagram sources and rendered SVGs, VERSION, CHANGELOG, release notes, and MIT
   License;
2. run the repository's accepted validation entry point as a standalone
   process and retain its real exit code;
3. explicitly verify that the publication validator does not require an
   <code>ax</code> binary, provider runtime, platform lane, or any Section 19
   product-conformance result;
4. verify <code>VERSION</code>, document metadata, changelog, release notes, and
   tag all say <code>v0.2.0</code>;
5. prepare the exact signed-commit command with author
   <code>Ivan Oparin &lt;oparin@me.com&gt;</code> and no AI trailer, and hand it
   to the user for explicit review; automation MUST NOT stage or commit before
   human approval;
6. prepare the exact signed annotated <code>v0.2.0</code> tag command and hand it
   to the user for explicit review; automation MUST NOT create the tag before
   human approval;
7. after the human creates the commit and tag, verify both signatures locally
   with <code>git log --show-signature -1</code> and
   <code>git tag --verify v0.2.0</code>;
8. hand the exact <code>git push</code> commands for <code>main</code> and the
   <code>v0.2.0</code> tag to the user; automation MUST NOT push before explicit
   human approval and only after accepted validation/review;
9. verify the public repository, default branch, license, commit signature, tag
   signature, and release URL; and
10. attach publication evidence to the board.

No automation MAY publish, stage, commit, tag, or push before validation
acceptance and explicit human review of every stage/commit/tag/push command.
Automation MUST stop before those operations and hand the exact reviewed
commands to the user. SemVer applies to specification releases; independent
schema/protocol versions remain as listed in Section 1.5.

Publication acceptance case <code>SPEC-PUB-001</code> MUST run in a fixture
checkout containing no <code>ax</code> executable and pass all specification
structure, contract-fixture, link, diagram, metadata, and signature-preflight
checks available before signing. Any validator that tries to execute product
acceptance cases from Section 19 fails this publication case.

## Appendix A. Normative traceability

### A.1 Settled-decision traceability

| Settled input section | Normative specification sections |
| --- | --- |
| Product and operator model | Sections 1, 2, 5, 13, 14 |
| Terminal persistence | Sections 3.1–3.2, 4, 13.4–13.11, 19.2–19.4 |
| Providers and native stores | Sections 7, 8, 13.1, 13.6–13.10, Appendix C |
| Task-board integration | Sections 2.2, 9, 13.2, 13.6–13.10, 19.3–19.4 |
| Mesh and replication | Sections 1.6, 3.2–3.3, 6, 10–12, 13.3, 16, 19 |
| Attach, takeover, failure, and fork | Sections 5.3–5.7, 13, 14, 15, 16.5, 19.4 |
| Implementation stack and delivery | Sections 1.3–1.6, 3–7, 10–12, 17–20 |
| Publication metadata | Section 20 |

### A.2 Story acceptance traceability

| <code>STORY-260819-iscto1</code> criterion | Normative source and delivery route |
| --- | --- |
| SPEC.md is normative and detailed | This document, especially Sections 1–20 |
| README provides the operator interface | The repository README provides the entry point and contract map; Section 14 is the normative CLI/UX source, and downstream <code>TASK-260819-1i3olz</code> owns expanded public README/CONTRIBUTING rendering |
| C4 and PlantUML sources render successfully | Section 3.1 fixes C4 scope and Section 13 fixes sequence/state semantics; downstream <code>TASK-260819-37heok</code> owns sources/SVG/render evidence |
| macOS, Linux, WSL2, and native Windows PowerShell are explicit | Sections 3.2, 4, 8.4, 11.6, 13.11, and 19.2–19.3 |
| All settled decisions are traceable | Appendix A.1 |
| Independent reviewer accepts the artifact | Required board reviewer route after this task's <code>to-review</code> handoff |

The Epic criterion for a signed public <code>v0.2.0</code> specification release
maps only to Section 20 and remains owned by the downstream validation and
publication tasks. Section 19 governs a future product implementation and is
not a prerequisite for that publication.

### A.3 Task acceptance traceability

| Task criterion | Normative sections |
| --- | --- |
| Exactly one owner, epoch fencing, replicas | Sections 2.2, 5.3, 11.4, 13.6–13.7, AC-OWN cases |
| Complete graceful/force/attach/fork/stop/resume preconditions, transitions, failures, recovery | Section 13, especially distinct direct/task-board force paths in 13.7, and Section 15 |
| Direct native-store and opaque task-board paths are distinct | Sections 2.1–2.2, 7–9, 13.1–13.2 |
| Union immutable replication; never live SQLite; conflicts fail closed | Sections 3.3, 10–12 |
| Manifests, staging, validation, atomicity, tombstones, workspace groups, Git/non-Git | Sections 10–12 and 19.4 |
| Honest platform/provider matrices including Windows/WSL2, Pi, Qwen | Sections 7.7 and 8 |
| Trusted mesh, allowlist, SSH, no encryption claim, machine-local credentials, exclusions | Sections 6, 11.1, and 16 |
| Independently versioned plugin/RPC/record/bundle/config/CLI result with explicit embedded-error bindings | Sections 1.5–1.6, 5, 7, 9–11, 14.2, 15.1, and 17 |
| CLI, exit codes, observability, implementation rollout/acceptance, specification publication | Sections 14, 15, 18, 19, and the independent Section 20 gate |
| No unresolved implementation question except provider version gates | Appendix B |

### A.4 Second-review closure traceability

| Reviewer finding | Normative closure |
| --- | --- |
| Closed registry and embedded shapes | Sections 5.4–5.6, 7.5, 10.4, 18.1, and the exhaustive positive/negative fixture rules in Appendix D |
| Exact Git and managed-tree state | Section 10.4 tagged manifests, recursive submodule state, language-neutral pack/index/blob corpus, and Section 12 round-trip rules |
| Canonical state and destination enums | SessionState in Section 5.7, explicit task-board mapping in Section 9.2, DestinationClass in Sections 11.3 and 11.7, and their RPC/CLI reuse |
| Executable task-board creation and persistence | Public launch/idempotency/force-stop bridge in Section 9.2, nullable prompt bundle in Section 9.3, and launch/takeover flows in Section 13 |
| Provider capture, transfer, and rollback | Object Sink plus capture and prepare/status/commit/rollback in Section 7.5, per-blob journal state in Section 10.6, and composite recovery in Sections 11.3 and 13 |
| JCS integer interoperability | Safe JSON number domain, decimal-string escape hatch, and cross-language boundary vectors in Section 1.6 plus AC-NUM cases in Section 19.4 |
| Public conflict-resolution UX | Exact copy/worktree/managed-replacement grammar, confirmation policy, CLI Result, and accepted/rejected fixtures in Sections 14.1–14.3 |

### A.5 Third-review closure traceability

| Reviewer finding | Normative closure |
| --- | --- |
| Contradictory environment overrides | One five-entry flag/environment registry, value-kind and empty/unknown rules in Section 3.2; identical precedence in Sections 6.1 and 14.2; <code>AC-PATH-001</code> and Appendix D fixtures |
| Missing task-board safe-boundary facts | Closed <code>BridgeSafeBoundary</code>, provider-version result, safe/unsafe/lost-response fixtures, and total bridge-to-Checkpoint-to-RPC mapping in Sections 9.2, 11.3, 13.2, and 13.6 |
| Provider capture/materialization roots were unnamed | Disjoint capture/materialize request variants and source authorities in Section 7.5; destination <code>RootAuthority</code>, per-operation target/predecessor/boundary, and cross-host fixtures in Sections 10.5 and 11.6 |
| Managed-replica marker had no contract | Closed machine-local marker variant, JCS identity, exact paths, atomic write, classification, migration, replacement, and crash fixtures in Sections 3.2, 10.6, 11.3, and 11.7 |
| Anti-entropy namespace membership was partial | Total schema/byte-to-namespace table, local exclusions, mixed-schema roots, and exchange fixture in Section 11.4 |
| Workspace Group membership had no evolution rule | Immutable topology with membership derived from immutable Session Records and authoritative session Tombstones; exact expectation, concurrent join/leave, and group/worktree takeover rules in Sections 5.6, 11.3, 12.6, and 13.1–13.7 |
| Public task-board launch and log inputs were incomplete | Exact board/mode/goal/binding launch grammar and local/remote cursor-bound log grammar, results, and positive/negative fixtures in Sections 14.1–14.3 |
| Normative references violated closed grammars | Valid <code>works.relux.ax.migrated-from</code> extension in Section 17.3, corrected <code>GitSubmodule</code> field paths in Section 10.4, and the static <code>AC-REF-001</code>/Appendix D checks |

### A.6 Fourth-review closure traceability

| Reviewer finding | Normative closure |
| --- | --- |
| Task-board bundle projection and blob paths were ambiguous | Section 9.3 defines whole-object Session/bridge projection, preservation of non-secret literals/extensions, exact binding-state derivation, canonical <code>bundle.json</code>, and the unique <code>sha256/HH/REST</code> regular-file member set; <code>AC-TB-003</code> and Appendix D cover round trips and path negatives |
| Materialization could not represent passive/stopped or non-workspace work | Section 11.3 defines MaterializationKind/Intent/Cohort/Sources and tagged request/result nullability; Sections 13.3, 13.6–13.7, and 13.10 select passive replica, owner resume, or ownership transfer explicitly; <code>AC-MAT-002</code> covers all six lanes |
| Provider transactions could not survive fresh plugin processes safely | Sections 3.2 and 7.5 define host-created object-source/transaction authorities, exact durable layout, path disjointness, same-filesystem atomicity, restart lookup/retention, and all-operation authority passing; Section 10.6 journals the authority and Section 11.3 maps every rollback reason; <code>AC-PTX-001</code> covers cross-process recovery |
| Structured Error lacked protocol negotiation/bootstrap rules | Provider/RPC major 2 and bridge major 1 statically bind Error 1.0.0 in Sections 7.2, 9.2, 11.2, and 15.1; Section 17 distinguishes independent release from explicit embedding; compatible, major-mismatch, and first-frame fixtures map to <code>AC-ERR-002</code> |
| Remote log transport and host identity contradicted | Sections 14.1–14.3 and 18.1 use one allowlisted SSH remote-CLI transport, require non-null <code>emitting_host_id</code> locally and remotely, preserve cursor host scope, reject forged/mismatched results, and explicitly add no Mesh RPC operation; <code>AC-CLI-004</code> covers the sequence |

### A.7 Fifth-review closure traceability

| Reviewer finding | Normative closure |
| --- | --- |
| Materialization Plan kinds/strategies were not closed | Section 10.5 defines intent, source/derived IDs, fork projection, the exhaustive kind/source/authority/action/validation/strategy matrix, full positive plans for all four kinds, full negative objects, and legal validation-only/single-root strategies; <code>AC-MAT-003</code> covers execution |
| Task-board materialization lacked durable subtransaction recovery | Section 10.6 defines the exact journaled bridge IDs, tokens, references, state/null rules, order, cleanup, and crash/expiry cases; Section 11.3 exposes token-free status and Sections 13.3/13.6–13.8/13.10 use the same coordinator; <code>AC-TB-004</code> covers all paths |
| Provider idempotency had two keys | Section 7.5 makes <code>(operation, operation_id)</code> the sole mutation key and all IDs/authorities immutable mutation-retry input, while status is an evolving read without an operation ID; the <code>PTX-IDEMPOTENCY-ID-*</code> fixtures and <code>AC-PTX-002</code> reject a second root without freezing status |
| Owner resume omitted commit/finalize/rollback | Section 13.10 defines no-materialization, direct, and task-board paths through prepare, commit/prepared, activation, finalize or phase-safe rollback/status recovery; <code>AC-RESUME-001</code> covers every source-kind lane |
| Fork could not produce a new workspace identity | Sections 10.5 and 13.8 define the complete old→new topology/manifest projection, new records/lease, transactional direct/task-board activation, provenance/profile authority, and phase failure matrix; <code>AC-FORK-001..002</code> cover derivation and recovery |
| Epoch-1 failed launch had no stop/resume representation | Sections 5.2, 5.7, 11.3, 13.1–13.2, 13.9–13.10, and 14.2 define bootstrap retry/abort, nullable checkpoint, non-resumable failed state, and exact RPC/Event/CLI agreement; <code>AC-BOOT-001</code> covers every boundary |
| Git submodule pack rule contradicted repository boundaries | Sections 10.4 and 12.3 make parent/child packs independent, define the head-tree/index/checked-out triple, and require clean/staged/unstaged/combined cases in isolated object databases; <code>AC-WORK-005</code> covers it |
| Effective profile authority conflicted with events/bundles | Sections 2.4, 5.2, 5.4, 9.3, 11.3, and 13 repeat one checkpoint-derived effective profile/source through launch, bundle, takeover, resume, and fork, including Pi's equal mapping; <code>AC-PROFILE-001</code> covers both persistence paths |
| Digest path and cohort reference grammars were unresolved | Section 3.2 defines one Windows-safe <code>digest_path_v1</code> with golden vectors reused by provider/bundle/marker stores; Section 12.6 names <code>MaterializationCohort.ownership_transfer_session_ids</code> exactly; <code>AC-PATH-002</code> and schema-aware <code>AC-REF-001</code> cover both |

## Appendix B. Explicit provider version gates

The following are the only intentionally unsettled facts in this contract. They
are external provider/version/platform evidence gates with fail-closed runtime
behavior, not architecture choices:

- Muse 0.2.1 store, cron, resume, import, quiesce, and stop behavior;
- Muse native Windows install/store/support behavior despite published
  artifacts;
- Muse full-idle signaling and safe portability of non-empty
  <code>cron.db</code>;
- Antigravity authoritative SQLite root/schema/checkpoint/import and offline
  restore behavior;
- Antigravity backend/account/custom-endpoint realm portability, exact Windows
  home-root expansion, and WSL2 behavior;
- exact minimum OS versions where providers do not publish them;
- Codex, Claude, Gemini, and Pi closed-store portability on each platform until
  P suites pass;
- provider/platform PTY and ConPTY behavior until M suites pass;
- Pi task-board prompt/primary/goal-binding support;
- Antigravity task-board support; and
- every future-plugin capability before accepted probe/test evidence.

All such cells have <code>enabled = false</code>. No implementation design is
left to inference: the promotion rule is Section 19.3.

## Appendix C. Evidence and primary references

Provider behavior is version-sensitive. These references support the stated
surface while the matrices retain the stricter tuple-specific gates:

1. Settled decisions attached to <code>TASK-260819-1h306n</code>.
2. Accepted <code>TASK-260819-1ecd6x</code>
   [Muse and Antigravity evidence report](.research/260819_muse-antigravity-native-store-contracts.md),
   including its primary-source ledger and accepted limitations.
3. [Official Codex CLI command reference](https://developers.openai.com/codex/cli/reference/)
   for resume/fork and unrestricted flags.
4. [Official Codex WSL guidance](https://learn.chatgpt.com/docs/windows/wsl)
   and [native Windows sandbox guidance](https://learn.chatgpt.com/docs/windows/windows-sandbox).
5. [Anthropic Claude Code setup](https://docs.anthropic.com/en/docs/claude-code/getting-started)
   plus the locally probed Claude Code 2.1.229 help surface.
6. [Gemini CLI session management](https://geminicli.com/docs/cli/session-management/)
   and [installation requirements](https://geminicli.com/docs/get-started/installation/),
   plus locally probed Gemini CLI 0.54.4 help.
7. [Pi usage/session documentation](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/usage.md)
   and [Pi settings/session-directory documentation](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/settings.md),
   plus locally probed Pi 0.73.1 help.

Local help probes are evidence only for the exact installed versions and macOS
host. They do not establish another platform cell.

## Appendix D. Normative contract fixture catalog

### D.1 Fixture execution rules

This appendix is part of the normative contract. A fixture marked positive
MUST parse under its named 1.0.0 contract, satisfy every conditional invariant,
and, when identity-addressed, reproduce its embedded digest after omitting only
the schema-defined self-ID. A negative mutation is applied alone to a fresh
positive fixture. It MUST fail before state derivation or destination mutation;
an implementation MUST NOT repair, round, ignore, or default the changed fact.

For every closed object—including every nested object in the second table—the
suite also generates these four mechanical negative fixtures:

1. <code>CLOSED-MISSING</code>: remove each required member in turn;
2. <code>CLOSED-NULL</code>: replace each non-null member with null in turn;
3. <code>CLOSED-UNKNOWN</code>: add <code>"unexpected":true</code> at that exact
   object depth; and
4. <code>CLOSED-BOUNDARY</code>: test the declared minimum, maximum, one below,
   and one above for every string, array, map, and numeric bound.

The positive is accepted only at valid bounds. Every invalid derivative is
rejected with the applicable stable Section 15 code. Reverse-DNS extension and
explicit data-map members are excluded from <code>CLOSED-UNKNOWN</code> only for
their declared data keys; their containing object remains closed. These rules
turn the examples and exact tables into language-neutral fixture definitions,
not suggestions for a generator to invent defaults.
Fences labeled <code>jsonc</code> in Section 10.5 contain strict comment-free
JSON and are part of this fixture set; the gate MUST parse them with the same
JSON/JCS implementation and MUST NOT skip their identities because of the
display-language label.

### D.2 Registry-contract fixtures

| Section 1.5 contract | Positive fixture anchor | Additional required negative mutation |
| --- | --- | --- |
| Configuration | Section 6.2 TOML and Section 3.2 path registry | Add root <code>unknown_root</code>; add secret value; set unsafe SSH host-key bypass; exercise all five flags/environment values plus empty and unknown <code>AX_*</code> cases |
| Provider protocol | Section 7.2 envelopes and every Section 7.5 row | Mismatch request ID; success with both body/error; operation/body tag mismatch; compatible/major/invalid-first-output Error binding fixtures |
| Provider manifest | Section 7.3 with all fifteen operations | Remove <code>capture</code> or one transaction operation; duplicate provider ID discovery remains fatal |
| Provider probe | Section 7.4 | Set <code>enabled=true</code> on conditional/unknown/unsupported; omit one requested capability |
| Mesh RPC | Section 11.2 envelopes and every Section 11.3 row | Send non-hello first; mismatch nonce; advertise an <code>error</code> contract; use legacy state/destination enum; exercise compatible/major/unframed failure behavior |
| Session Record | Section 5.1 direct and task-board examples plus Section 13.8 fork | Direct with task-board object; task-board creation with non-null manager ref; fork without provenance |
| Session Event | Section 5.2 envelope instantiated for every payload row, including profile-bearing launch/resume/fork and bootstrap abort/stop | Payload/tag mismatch; lease sequence zero/gap; profile/source mismatch; bootstrap null/resumable/state mismatch; unknown member in one payload |
| Lease Record | Section 5.3 | Epoch 4 with null predecessor; epoch jump; checkpoint from another session |
| Checkpoint Record | Section 5.4 and <code>CP-N1..N4</code> | Both persistence IDs null/non-null; unsafe boundary published as validated |
| Workspace Group | Section 5.6 Git record and managed-tree fragment | <code>WG-N1..N4</code>; duplicate/case-colliding group path; conflicting same-group topology record |
| Provider Identity | Section 5.5 and nested resume identity | Unknown identity kind; non-string opaque value; backend realm required but null |
| Blob Descriptor | Section 10.2 | Chunk gap/overlap, wrong whole size, more than 32,768 chunks |
| Transfer Manifest | Every Section 10.4 root/tree/provider and entry fragment | <code>TM-*</code> mutations, tag-field leakage, missing transitive child closure |
| Transfer Chunk Descriptor | Section 10.3 | Offset/index disagreement, non-final short chunk, raw digest mismatch |
| Tombstone | Section 10.7 full workspace entry and three target fragments | Target/scope mismatch, wildcard/root path, losing-lease issuance |
| Tombstone Acknowledgement | Section 10.7 acknowledgement | Conflict disposition with null checkpoint; non-conflict disposition with non-null checkpoint |
| Materialization Plan | Section 10.5 full workspace/provider/task-board/composite plans, full direct-native fork plan, ForkWorkspaceProjection, and task-board authority | All full <code>PLAN-*-N1</code> objects; kind/source/authority/action/validation/strategy mismatch; fork projection/map/derived-ID mismatch; operation sequence gap; plan for another host; replace without exact prior checkpoint |
| Materialization recovery state | Section 10.6 journal, Provider/Task-board Journal Transactions, and Managed Replica Marker variants | Flat chunk indexes; prepared provider transaction without token or full authority; task-board state/token/reference/null mismatch; changed retry IDs; <code>MARKER-*</code> identity/path/predecessor/crash mismatches; cross-variant member leakage |
| Task-board bridge | Section 9.2 launch pair, safe-boundary pair, and every operation row | Internal/new retry operation ID; unsafe proof marked safe; changed lost-response retry; graceful stop without token; force stop with token; compatible/major/invalid-first-output Error binding fixtures |
| Task-board bundle | Section 9.3 primary, prompt, and profile-changed projections plus exact archive member set | <code>TB-BUNDLE-*</code> goal/binding/projection/profile mutations; full-digest leaf, wrong shard, missing/extra/directory member, noncanonical JSON, or blob mismatch |
| Structured Error | Section 15.1 | Unknown top-level member; nesting depth 5; secret canary in details; all nine containing-protocol binding fixtures plus unframed input |
| Observation Event | Section 18.1 and its listed negative fixtures | Partial/failure without error; incomplete counts; unsafe integer |
| CLI Result | Section 14.2 takeover and Section 14.3 materialize/log examples | Command/body tag mismatch; wrong null top-level IDs; false success invariant; null/wrong log emitter or mixed event hosts |

### D.3 Embedded tagged-union coverage

The following fixture families are exhaustive. For a table-driven family,
<code>POS-&lt;tag&gt;</code> means: copy the nearest valid containing envelope,
select that exact table row, populate every member with its minimum valid value
or the documented normative value, and recompute any containing self-ID.
<code>NEG-&lt;tag&gt;-LEAK</code> adds one member that belongs only to the next row
(wrapping to the first); it MUST be rejected as a forbidden member.

| Embedded family | Required positive tags | Required family-specific negatives |
| --- | --- | --- |
| Session Record kind | <code>direct</code>, <code>task_board</code> | Wrong task-board nullability; creation manager ref non-null |
| Task-board launch mode | <code>primary_owner</code>, <code>tracked_prompt</code> | Goal/binding conditional mismatch |
| Fork provenance mode | <code>native</code>, <code>supported_import</code>, <code>task_board_clone</code> | Source/checkpoint/operation mismatch |
| Session Event payload | Every event type in Section 5.2, including task-board launch/adoption and tombstone audit | Payload/tag mismatch and unknown payload member |
| Provider operation body | All fifteen rows in Section 7.5 | Request/success tag mismatch; capture sink escape; transaction ID reuse with changed plan |
| Native-store-plan request/result | <code>capture</code>, <code>materialize</code> | Destination member on capture; source workspace member on materialize; result tag mismatch |
| Provider source authority role | <code>durable_store</code>, <code>durable_index</code>, <code>derived_cache</code> | Undeclared authority, excluded root, source escape, or destination access in a capture plan |
| Provider transaction state | <code>unknown</code>, <code>prepared</code>, <code>committed</code>, <code>rolled_back</code> | Token/discovery null-rule mismatch |
| Provider host authority | <code>provider_object_source</code>, <code>provider_transaction</code> | Bare path in place of authority; peer-selected root; ID/path/layout mismatch; overlap; wrong provider; cross-filesystem provider authority; fresh process receives a changed authority |
| Task-board bridge operation | <code>launch</code>, <code>status</code>, <code>export</code>, <code>import</code>, <code>open</code>, <code>adopt</code>, <code>stop</code>, <code>resume</code> | Caller-ID mismatch; token/mode mismatch; replay with changed arguments |
| Task-board open mode | <code>dormant_replica</code>, <code>fork</code> | New-session and new-identity booleans inverted |
| Transfer Manifest kind | <code>workspace_group</code>, <code>workspace_tree</code>, <code>provider</code>, <code>task_board</code>, <code>composite</code> | Tagged metadata null-rule mismatch |
| Materialization RootAuthority | <code>workspace</code>, <code>provider_store</code>, <code>task_board_staging</code> | Cross-tag field leakage, root overlap, wrong host/platform, or unauthorized atomicity boundary |
| RPC materialization kind | <code>workspace</code>, <code>provider</code>, <code>task_board</code>, <code>composite</code> | Source/workspace-request mismatch; wrong plan kind; managed-replica/destination nullability mismatch at any phase |
| RPC materialization intent | <code>passive_replica</code>, <code>owner_resume</code>, <code>ownership_transfer</code>, <code>fork</code> | Empty/non-empty transfer-set mismatch; passive activation; owner-resume lease advance; missing/extra fork projection; intent changes after prepare |
| Materialization Plan kind | <code>workspace</code>, <code>provider</code>, <code>task_board</code>, <code>composite</code> | Every full Section 10.5 negative kind/source/authority/action/validation/strategy object plus <code>NEG-&lt;tag&gt;-LEAK</code> |
| Task-board journal state | <code>not_started</code>, <code>imported</code>, <code>opened</code>, <code>adopted</code>, <code>resumed</code>, <code>dormant_finalized</code>, <code>rolled_back</code>, <code>failed</code> | Token/reference/expiry/binding/cleanup null-rule mismatch; unstable operation ID; token exposed by RPC |
| Materialization recovery document | <code>journal</code>, <code>managed_replica_marker</code> | Cross-tag field leakage, stale plan/checkpoint, invalid marker self-ID, or non-atomic current pointer |
| Manifest entry | <code>directory</code>, <code>file</code>, <code>symlink</code>, <code>hardlink</code> | Every <code>TM-ENTRY-*</code> plus <code>NEG-&lt;tag&gt;-LEAK</code> |
| Workspace snapshot member | <code>git</code>, <code>managed_tree</code> | Git field on managed tree; missing member child |
| Git HEAD | <code>branch</code>, <code>detached</code>, <code>unborn</code> | OID/ref conditional mismatch |
| Git submodule | initialized branch, initialized detached, uninitialized | Nullable state mismatch; recursive manifest absent |
| Tombstone target | <code>session</code>, <code>workspace_entry</code>, <code>provider_snapshot</code>, <code>managed_replica</code> | Scope/subject/target mismatch; broad path |
| RPC operation body | Every operation row in Section 11.3, including materialize status/finalize | Request/success tag mismatch; mutation omits initiator or expectation |
| Materialization phase | <code>unknown</code>, <code>staging</code>, <code>validating</code>, <code>prepared</code>, <code>committing</code>, <code>rolling_back</code>, <code>committed</code>, <code>rolled_back</code>, <code>failed</code> | Known-field and error-code null-rule mismatch |
| SessionState | All eleven Section 5.7 values | <code>created</code>, <code>starting</code>, <code>quiesced</code> rejected in RPC/CLI session state |
| DestinationClass | All five Section 11.7 values | Legacy aliases rejected; empty not collapsed |
| CLI Result body | Every command-tag row in Section 14.2 | Command/body tag mismatch; operation/session null-rule mismatch |
| Observation result | <code>started</code>, <code>success</code>, <code>partial</code>, <code>failure</code>, <code>cancelled</code> | Error/duration conditional mismatch |

### D.4 Cross-contract sequence fixtures

The wire-shape fixtures are necessary but not sufficient. The acceptance suite
MUST also run, without substituting mocks for the relevant state boundary:

- <code>TB-LAUNCH-LOST-1</code>: lose the first public launch response, retry
  the identical caller operation ID, observe one manager process/reference, and
  persist one authoritative <code>task_board.launched</code> event;
- <code>TB-BOUNDARY-SAFE-1</code> and <code>TB-BOUNDARY-UNSAFE</code>: map every
  bridge member into Checkpoint/RPC evidence, reject background activity or a
  provider-version/generation mismatch, and publish no checkpoint from an
  unsafe proof;
- <code>TB-EXPORT-LOST-RESPONSE</code>: lose a safe export result, repeat the
  same operation/body, obtain byte-identical bundle/proof/token facts, and
  reject a changed retry without duplicating or unblocking the export;
- <code>TB-PROMPT-NULL-GOAL-1</code>: launch/export/import/open/adopt/resume the
  Qwen-style tracked-prompt record and null-goal bundle;
- <code>TB-BUNDLE-PROJECTION-PRIMARY-POS</code> and
  <code>TB-BUNDLE-PROMPT-POS</code>: round-trip non-empty allowed
  Board/Goal/Launch extensions and non-secret launch literals without dropping
  or normalizing a member; run every <code>TB-ARCHIVE-PATH-*</code> case against
  the exact regular-file set;
- <code>PATH-REGISTRY-1</code>: for each of the five Section 3.2 rows, prove
  flag-over-environment-over-default precedence and file/directory kind; prove
  an empty value is unset and an unknown <code>AX_*</code> value has no effect;
- <code>PROVIDER-CAPTURE-TRANSFER-1</code>: produce
  <code>PROVIDER-CAPTURE-POS</code> in an isolated sink, independently verify
  and transfer its descriptor/blob closure, and prove no excluded or live-store
  file was written;
- <code>PROVIDER-FIRST-CAPTURE-1</code> and
  <code>PROVIDER-CROSS-HOST-1</code>: run capture with no destination members,
  then execute <code>PROVIDER-PLAN-MATERIALIZE-POS</code> using disjoint
  workspace/provider roots; every executor mutates only its authorized targets
  and rollback restores all predecessor digests;
- every <code>PTX-*</code> and <code>MJ-CRASH-*</code> provider/materialization
  recovery fixture;
- all four kind-tag positive plans, the full direct-native fork plan, and four
  full negative Section 10.5 plan objects,
  including the provider/task-board one-root strategy cases and the complete
  <code>FORK-PROJECTION-POS</code> bottom-up digest derivation;
- every <code>MAT-*</code> tagged kind/intent fixture, including stopped passive
  sync, stopped-owner resume, provider-only, task-board-only, workspace-only,
  and composite ownership transfer from prepare through terminal status;
- <code>PTX-CROSS-PROCESS-COMMIT</code> and
  <code>PTX-CROSS-PROCESS-ROLLBACK</code>: use a fresh plugin process for every
  phase with the same exact authorities, then exercise all five rollback
  reasons and the cross-filesystem/changed-authority negatives;
- every <code>PTX-IDEMPOTENCY-ID-*</code> case after a lost response, proving a
  changed materialization ID, transaction ID, or authority cannot allocate or
  mutate a second transaction root;
- every <code>TB-TXN-*</code> journal/status case through import, open, adopt,
  resume, dormant finalization, token expiry, crash, and lost response in
  passive sync, graceful/force takeover, owner resume, and fork;
- every <code>BOOT-DIRECT-*</code> and <code>BOOT-TB-*</code> launch boundary,
  mapping the resulting RPC stop body, Session Events, CLI Result, derived
  state, and later resume eligibility without inventing a checkpoint;
- every <code>RESUME-*</code> and <code>FORK-*</code> lifecycle case, executing
  actual modeled prepare/commit/activation/finalize or rollback/status
  transitions rather than searching for prose literals;
- every Section 2.4 <code>PROFILE-*</code> sequence, including bundle projection
  and Pi's two distinct ax profiles with one equal provider mapping;
- every <code>MARKER-*</code> fixture: recompute the marker and path-fingerprint
  hashes, classify absent/matching/divergent states, prove replacement links its
  predecessor, and recover or reject each crash point without trusting SQLite;
- <code>MIXED-NS-1</code>, <code>MIXED-NS-EXCHANGE</code>, and
  <code>MIXED-NS-N1</code>: reproduce all six roots in two implementations,
  transfer only the three missing objects/bytes, and prove excluded local
  marker/journal/chunk state changes no root;
- every <code>WG-JOIN-*</code>, <code>WG-LEAVE-*</code>, and
  <code>WG-TAKEOVER-*</code> fixture: union membership in both orders and test
  whole-group/worktree revalidation before and after the first lease advance;
- <code>WS-GIT-ROUNDTRIP-1</code>, every <code>WS-SUBMODULE-*</code> pointer case,
  and <code>WS-TREE-ROUNDTRIP-1</code>, validating the parent and every child
  pack in separate empty object databases before exact post-materialization
  comparison; and
- every <code>CLI-MAT-N*</code> grammar/policy fixture plus positive same-session
  copy, worktree, and managed replacement; and
- every <code>CLI-TB-*</code> and <code>CLI-LOG-*</code> fixture, including
  primary/tracked-prompt normalization, local/remote cursor host binding,
  emitting-host equality, SSH host mismatch, and forged-result rejection; and
- every <code>ERR-*</code> binding fixture in Section 15.1, proving that provider,
  bridge, and RPC supported-major failures use Error 1.0.0 while unsupported or
  unframed input is never trusted as a remote/child error.

The document-fixture gate MUST also derive the Section 3.2 and 6.1 environment
names independently and require equal sets; match every normative extension
key against the Section 1.6 reverse-DNS grammar; reject any legacy underscore-
separated migration-extension spelling; execute every Section 3.2
<code>digest_path_v1</code> golden/negative vector on POSIX and native-Windows
path libraries; and resolve every normative simple or dotted field expression
with a schema-aware parser against the exact containing field table. A literal
substring search is not a reference check: the parser must bind the expression
to its named closed type, follow each component, validate enum members, and
reject aliases or singular/plural variants absent from that type. In
particular, the Git checks MUST resolve
<code>GitSubmodule.working_tree_manifest_id</code>,
<code>GitSubmodule.gitlink_oid</code>, and
<code>GitSubmodule.head.oid</code>, and MUST reject any unregistered flat or
renamed member when it purports to belong to <code>GitSubmodule</code>. It MUST
also resolve
<code>MaterializationCohort.ownership_transfer_session_ids</code> and reject
<code>migration_session_id</code> or any other unregistered cohort spelling.

Specification publication validation MUST parse and cross-reference this
catalog but MUST NOT execute provider binaries or claim these future product
conformance cases passed. Section 19 owns product execution; Section 20 remains
the independent document-publication gate.

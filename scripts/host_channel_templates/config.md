### 6.6 Configuration 4.0.0 host-channel migration

Configuration 4.0.0 retains Configuration 3.0.0 except for the following exact
changes. All other closed members, path precedence and five environment
variables remain unchanged. No secret or TLS-verification override is added.

| Key | Required value / constraint |
| --- | --- |
| <code>schema_version</code> | Exact <code>4.0.0</code> |
| <code>mesh.transport</code> | Required, exact <code>ssh_tls13</code>; no default or alternative |
| <code>mesh.host_channel</code> | Required, exact closed table below |

The <code>mesh.host_channel</code> table contains exactly:

| Key | Required value / constraint |
| --- | --- |
| <code>version</code> | Exact <code>1.0.0</code> |
| <code>credential_id</code> | SHA-256 digest of the local leaf certificate DER |

No per-peer override exists: every peer in a Config-4 mesh requires Host
Channel 1 and RPC 5. The credential is loaded from the machine-local Section
11.10.2 store; neither a certificate nor private-key bytes belong in TOML.
The existing endpoint/SSH authentication and host-ID allowlist remain necessary
but are insufficient without enrolled TLS identity. Unknown/missing/partial
configuration, credential or trust state is a refusal, never legacy selection.

Migration is an explicit local operator action, never first-connect behavior.
First upgrade both binaries while keeping the old configuration bytes intact;
create local credentials and exchange public enrollment material out of band;
validate all intended peers' UUIDs and fingerprints; then preview a Config-4
replacement with the retained Config-3 fields, selected credential and complete
peer set. Apply only after explicit operator confirmation, an owner-only backup,
and validation of that exact preview against the current configuration/trust
generation. Older Config-1/2 inputs first use the existing explicit migrations.
A missing peer enrollment blocks activation; an operator may explicitly remove
a peer from the preview, but the implementation cannot silently drop it.

Replacement is atomic and crash durable. On restart select only the last fully
committed configuration plus valid local trust state; partial writes park with
<code>invalid_config</code>. Config-4 readers MUST NOT rewrite historical files,
and old readers MUST refuse Config-4 mutation. A Config-4 installation refuses
the unflagged legacy server invocation before reading stdin. A Config-1/2/3
installation refuses the flagged host-channel invocation. No byte sniffing,
extension field, argv host UUID, environment value, or failed handshake can
select a fallback. Legacy RPC 2/3/4 dual-stack obligations apply only to explicitly
legacy installations; they never require a Config-4 endpoint to accept legacy.
An operator rollback requires stopping every host channel, explicit replacement
of configuration from the preserved backup, and acknowledgement that the legacy
installation has no Host Channel assurance; it is not a connection retry.

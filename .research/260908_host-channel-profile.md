# Host Channel profile: source evidence and decision bounds

Date: 2026-09-08. Task: TASK-260908-3j2ipi. This report supports SPEC Sections
6.6 and 11.10; SPEC remains the sole normative authority.

The approved direction is standard TLS 1.3 mutual authentication inside the
existing SSH byte stream, dedicated machine-local host keys and out-of-band
public-credential enrollment. No runtime implementation is present in this
repository. No real AX handshake, private-key storage, race or platform result
is claimed by this work.

| Primary source | Observed building block | AX design implication / limit |
| --- | --- | --- |
| [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446), Sections 4.3.2, 4.4, 4.6, 8 | TLS certificate authentication, CertificateVerify/Finished, resumption and early-data mechanisms; CertificateRequest authority-list bound | Require full mutual authentication and disable resumption/0-RTT. Client-local handshake return alone is not evidence that the server accepted its final flight; await authenticated hello success before ordinary RPC. Bound trust-root hints rather than truncating them. |
| [RFC 5280](https://www.rfc-editor.org/rfc/rfc5280), Sections 4.1, 4.2, 6 | Standard certificate fields, path validation, constraints and key usages | AX chooses a one-root/one-leaf P-256 profile, exact public credential pinning and local revocation. These are AX policy choices, not claims of an RFC-defined AX profile. |
| [Go crypto/tls](https://pkg.go.dev/crypto/tls), Config and ConnectionState | Required verified client certificates, TLS version bounds, ALPN, standard verification plus VerifyConnection, ticket controls | Keep standard verification enabled; supplement with enrolled leaf/root/SPKI/UUID checks. Explicit pool, role and name inputs are required. |
| [Go crypto/x509](https://pkg.go.dev/crypto/x509), Certificate and VerifyOptions | X.509 creation and verification, roots and EKUs | Use maintained cryptography and normal validation. A verified CA or SAN alone is not AX enrollment. |
| [OpenSSH sshd](https://man.openbsd.org/sshd.8) | Server-side authorized-key restrictions and forced commands | Restricted SSH accounts may harden a deployment; a client-selected wrapper is not equivalent protection against account compromise. |
| [Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh) | Tailscale controls its SSH server/authentication and policy | Apply the same inner TLS profile, without assuming OpenSSH authorized_keys or a per-platform native Tailscale server implementation. |

The leaf identifies the configured UUID through one DNS SAN used only for
verification; it does not cause a DNS query. Every credential generation uses
fresh root and leaf keys, with the root private key destroyed after issuance.
Explicit DER/SPKI fingerprints prevent enrollment of a different certificate
merely because the same CA signed it. Certificate renewal is fresh-key rotation,
not silent issuance under old trust.

Revocation is per-verifier authority. It serializes with effect boundaries,
invalidates the authorization generation and closes live/idle streams within a
bounded interval. It cannot revoke an offline verifier's stale store remotely,
undo effects already committed, or protect a locally compromised account.

## Logbook

- Reconciled the existing registry before choosing versions: Config 3/RPC 4 are
  occupied by v0.5.0 TerminalBackend contracts. Prepared Config 4/RPC 5 and new
  Host Channel 1/Host Trust Store 1, with historical definitions retained.
- Corrected draft error wording against the closed registry: use
  host_identity_mismatch / peer_not_allowlisted (exit 7), incompatible_protocol
  (exit 6) and transport_failure (exit 8); no permission_denied code was added.
- Existing historical section hashes initially included appended new sections.
  Changed only the end markers; retained the same hashes and old section bytes.
- Synthetic contract vectors validate publication consistency only. Actual
  certificate parsing/chain verification and concurrent runtime behavior remain
  unknown until AC-HOST-001 is exercised by a product implementation.
- No logbook CLI or connector is exposed in this run; this persisted logbook is
  linked from the task outcome and attached through task-board resource CRUD.

- CR1 rework reproduced both independent token-preserving attacks and the
  surviving 65/65 suite in disposable copies. The cause was separate normative
  phrase checks and hard-coded admission facts. SPEC now owns the executable
  predicate policy; the public gate interprets it and checks its rendered table.
  Review-bound explanation templates protect prose agreement as an explicitly
  separate integrity measure, not natural-language semantic proof.
- Cross-context fixture vectors exercise request/resume/retry/queue/recovery
  and both carriers. Scope mutants change the policy and regenerate its table;
  only wrong vector decisions count as behavioral kills. The initial new
  lower-byte-bound mutant survived (no zero-byte vector); added both-side
  boundary vectors for every numeric source predicate before rerunning.
- CONTRIBUTING active workflow and checklist now use signed-delivery authority
  and separate parent-owned release publication. Preparation creates no tag.

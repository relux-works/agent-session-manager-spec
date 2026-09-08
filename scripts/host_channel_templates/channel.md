### 11.10 Host Channel 1.0.0 and Mesh RPC 5.0.0

This is the standard cross-platform strong-identity profile, independent of
SSH implementation. It is a new explicit transport, not an extension to a
legacy hello. Both endpoints MUST use a maintained TLS implementation; AX MUST
NOT implement a custom challenge-signature or record-encryption protocol.

#### 11.10.1 Launch, TLS and dispatch

The Config-4 initiator starts exactly the equivalent of:

~~~shell
ssh -T HOST ax rpc serve --stdio --host-channel 1.0.0
~~~

SSH remains authenticated and server-verified. OpenSSH over a Tailscale network
and native Tailscale SSH both carry the same ordered binary stdin/stdout stream;
no PTY, shell banner on stdout, text conversion, alternate command, or shared
TCP listener is permitted. Stderr is bounded sanitized diagnostics only.
Native Tailscale SSH has its own authentication/server and policy; OpenSSH
<code>authorized_keys</code>/forced-command behavior MUST NOT be assumed for it.
Neither an SSH username, source address, tailnet node, launcher argument nor
a hello value establishes AX host identity. Availability of a particular SSH
server on a platform requires product testing; protocol parity is not a claim
that native Tailscale SSH servers exist on every AX target.

The initiator is TLS client and remote process TLS server. The first stdout/
stdin bytes are TLS records, with no plaintext preface or version negotiation.
Both sides require TLS 1.3 exclusively, ALPN exactly <code>ax-host/1</code>,
full certificate authentication on every connection, and the Section 11.10.2
certificate checks. Session tickets, PSKs, session resumption, 0-RTT, TLS 1.2,
post-handshake client authentication, plaintext fallback and downgrade retries
are forbidden. A missing ALPN or resumed connection is rejected. There is no
RPC frame, error envelope, health read, version probe, or application dispatch
before mutual authentication; failed TLS closes the SSH stream.

In Go, configure <code>MinVersion=MaxVersion=tls.VersionTLS13</code>,
<code>InsecureSkipVerify=false</code>,
<code>ClientAuth=tls.RequireAndVerifyClientCert</code> on the server,
<code>SessionTicketsDisabled=true</code>, a nil client session cache, and
<code>NextProtos=["ax-host/1"]</code>. Use only the explicitly enrolled roots
in <code>RootCAs</code>/<code>ClientCAs</code>, never the system pool. Exclude
revoked/expired entries from these pools. The total encoded CA distinguished-
name list MUST fit the TLS 65,535-byte CertificateRequest authority-list bound;
refuse activation if it cannot, never truncate the trust set silently. The client
sets <code>ServerName</code> to the expected UUID-derived DNS SAN below, not the
SSH endpoint. Additional <code>VerifyConnection</code> checks MUST supplement
successful standard chain/name/time/EKU verification, not replace or disable it.
They check the exact enrolled leaf, root, key, UUID, role and current trust state.
TLS exporters, key logs and secret traffic material MUST NOT be persisted.

The TLS handshake has a fixed 10-second wall-clock deadline and at most 1 MiB
of incoming handshake bytes per side, including certificate records, before
completion; an adapter around SSH pipes MUST enforce cancellation and these
limits even when a peer sends no bytes. The subsequent hello has a separate
10-second deadline and the existing 8 MiB line / 5 MiB object limits; remaining
requests use the configured RPC timeout. Limits count bytes, not characters.
No application bytes may be interpreted as RPC until the TLS handshake returns
success locally. TLS permits a client to finish its handshake before the server
has accepted its final flight; consequently the client may send only encrypted
hello at that point. The server MUST finish verifying the client's Certificate,
CertificateVerify and Finished before parsing hello, and sends hello success
only after current authorization and identity equality pass. The initiator
MUST receive and validate that success before any other RPC operation.

RPC 5 has the exact RPC-4 operations, envelope/body shapes, eight namespaces,
limits and 25-key hello map from Section 11.9, with only the containing
<code>protocol_version</code> and <code>contracts.rpc</code> changed to
<code>5.0.0</code> and <code>["5.0.0"]</code>. No authentication, trust,
configuration, error or transport key is added to hello. Structured Error
remains statically bound to 1.3.0. Every received hello host ID MUST equal the
uniquely verified enrolled host UUID; on the client that UUID MUST also equal
the selected configured destination. Local outgoing hello MUST use the local
credential's UUID equal to Config-4 host ID. Nonces retain their correlation
semantics and are not identity proof. A TLS-authenticated peer is still refused
when it is not allowlisted or its hello identity differs.

After TLS, a valid RPC-5 non-hello request before hello success or an invalid
RPC-5 hello receives at most one encrypted Error 1.3.0 failure and closes;
identity refusal uses <code>host_identity_mismatch</code>, missing allowlist
permission uses <code>peer_not_allowlisted</code> (both exit 7); a contract
mismatch <code>incompatible_protocol</code>. Unframeable input and other RPC
majors close without a frame. Before TLS completes, only a standard TLS alert
may be sent, never JSON. The initiating CLI uses existing local <code>authentication_failed</code>
(exit 7) for a known peer certificate/handshake authentication failure and
<code>transport_failure</code> (exit 8) for transport I/O, timeout or unclassified
EOF. Local config/credential-store loading failure is <code>invalid_config</code>
(exit 3) before launch. Use <code>incompatible_protocol</code> (exit 6) only when
incompatibility is actually known, not inferred from EOF. No new Error enum or
exit code is introduced.

#### 11.10.2 Certificate issuance and enrolled trust

Host Credential Profile 1 is part of Host Channel 1, with no online CA service.
For each credential generation the host generates two distinct CSPRNG ECDSA
P-256 key pairs locally: a self-signed root CA and a leaf signed by that CA.
Root and leaf use X.509 v3, ECDSA-with-SHA256 signatures and distinct positive
random 128-bit serial numbers. The root is used only to sign this one leaf;
its private key MUST be destroyed after successful issuance. Rotation generates
both fresh keys and certificates. Reissuing a leaf under an enrolled CA does
not enroll it. TLS sends only the leaf; the exact root is already local trust.

| Certificate member | Root | Leaf |
| --- | --- | --- |
| Subject / issuer | CN <code>AX Host Root HOST_UUID</code>, self-issued | CN <code>AX Host HOST_UUID</code>, issuer equals root subject |
| Basic Constraints (critical) | CA=true, pathLen=0 | CA=false, no pathLen |
| Key Usage (critical) | keyCertSign only | digitalSignature only |
| Extended Key Usage (noncritical) | Absent | Exactly clientAuth and serverAuth |
| Subject Alternative Name (noncritical) | Absent | Exactly one DNS name <code>HOST_UUID.host.ax.invalid</code>; no other SAN type |
| Validity | notBefore=issuance time minus 300s; notAfter=notBefore plus 366 days | Same notBefore; notAfter=notBefore plus 90 days |
| Subject Key Identifier (noncritical) | SHA-1 of subjectPublicKey BIT STRING contents | Same construction for leaf key |
| Authority Key Identifier (noncritical) | Root SKI | Root SKI |

HOST_UUID is the configured lowercase canonical UUIDv7, without braces. No
wildcard, CN-only name, alternative UUID, extra subject attribute, extension,
intermediate, AIA fetch, CRL URL or OCSP dependency is allowed in this profile.
The DNS SAN is a verification name, never a DNS lookup or network endpoint.
Root self-signature, leaf signature, exact fields above, valid P-256 public
points, root/leaf lifetime and current validity of both certificates MUST be
checked at enrollment and handshake. Certificate validity uses the actual
local UTC time inclusively within notBefore/notAfter; no extra acceptance skew
or expiry grace is allowed. Unavailable/untrusted local time refuses admission;
clock correction cannot extend a previously scheduled stream expiry. No FIPS
certification or hardware non-exportability is claimed by choosing P-256.

Host Trust Store 1.0.0 is owner-only JSON at
<code>STATE_DIR/host-channel/trust.json</code>. It is machine-local authority,
not an immutable mesh object, and has exactly these fields:

| Field | Type / constraint |
| --- | --- |
| <code>schema</code> | Exact <code>urn:ax:schema:host-trust-store</code> |
| <code>schema_version</code> | Exact <code>1.0.0</code> |
| <code>generation</code> | uint53 greater than zero; increments by one per committed trust/config authorization change; exhaustion refuses mutation |
| <code>entries</code> | CredentialEntry[0..4096], sorted by credential_id, no duplicates |

Each CredentialEntry contains exactly <code>host_id:UUIDv7</code>,
<code>credential_id:digest</code> (SHA-256 of leaf DER),
<code>spki_id:digest</code> (SHA-256 of leaf SubjectPublicKeyInfo DER),
<code>root_id:digest</code> (SHA-256 of root DER),
<code>leaf_der:base64url</code>, <code>root_der:base64url</code> (each unpadded,
canonical and decoding to 1..16384 bytes),
<code>state:active|retiring|revoked</code>, <code>enrolled_at:timestamp</code>,
and <code>retire_at:timestamp|null</code>. The last field is non-null exactly
for retiring entries and later than enrolled_at. Revoked entries retain their
public bytes permanently as reuse tombstones. An unreadable, malformed,
partially read, duplicate-key, unknown-field or missing store is never an empty
store. Initial creation of an empty generation-1 store is explicit local setup.

Enrollment is local operator authorization of the tuple (host UUID, leaf DER
fingerprint, SPKI fingerprint, root DER fingerprint), verified over an
independent authenticated out-of-band channel. Imported public bytes MUST
reproduce those fingerprints and the profile before the transaction commits.
SSH discovery, a first hello, a remote claim, and a certificate being self-signed
are not approval. Remote RPC cannot mutate the trust store. Both directions
need enrollment; one side enrolling another does not imply reciprocity.

Across all entries, including revoked ones, a leaf, leaf public key or root
MUST NOT map to more than one host UUID. Multiple entries for the same leaf or
SPKI are invalid, including attempted renewal with the same key. Duplicate
root IDs are also invalid, even for the same UUID. At most two
non-revoked credentials may belong to a host, solely during rotation. A root
trusted for one host never grants its other issued certificates admission.
After ordinary TLS verification, an exact leaf/root/SPKI match against one
currently admitted entry yields the verified UUID. Zero or multiple matches
refuse. SAN alone and CA membership alone are insufficient. Both EKUs are
required by the profile; chain verification additionally validates serverAuth
at the client and clientAuth at the server.

Local leaf PEM and PKCS#8 private-key PEM are stored under
<code>STATE_DIR/host-channel/credentials/HEX_CREDENTIAL_ID/</code> as
<code>certificate.pem</code> and <code>private-key.pem</code>; HEX_CREDENTIAL_ID
is the 64 lowercase hex characters after <code>sha256:</code>. The root public
PEM is <code>root.pem</code>. No other file may select identity. Validate the
private/public match, profile and configured host ID before use. Directories
are 0700 and files 0600 on Unix; Windows requires equivalent owner-only ACLs.
Reject symlinks/reparse escapes or group/world write access. Do not forward SSH
agents or reuse SSH/provider keys. Credential/trust files, backups, private
keys and authorization caches MUST NOT enter replication, snapshots, cloning,
Session Directory, logs or exported diagnostic bundles. Operators exchange only
explicitly selected public enrollment material outside replication.

#### 11.10.3 Rotation, revocation and authorization generations

Rotation keeps host UUID and creates a new credential. Explicitly enroll the
new tuple on each participating peer before selecting it in Config-4. The
local atomic trust transition admits the new entry as active and marks the old
entry retiring with a fixed retire_at no more than 24 hours after that
transition and no later than old leaf expiry. There is no overlap extension;
no second rotation starts until the retiring entry is revoked. Failed or
incomplete enrollment leaves the new route unavailable, never auto-trusted.
At retire_at old admission ends and old streams close even if the new route
is unavailable. A peer offline during rotation must explicitly catch up; no
mesh-wide atomic enrollment or central CA availability is assumed.

Trust changes and Config-4 peer/credential changes share a machine-local
cross-process authorization lock and crash-durable generation transaction.
Readers MUST obtain one coherent committed snapshot (config plus trust), never
mix an old allowlist with new credentials. Every opened stream binds the local
credential ID, verified remote credential ID/UUID and snapshot generation.
A trust/config commit invalidates all streams of the prior generation; every
process, including daemonless RPC children, MUST close them within one second
of the commit using cancellation plus a bounded watchdog, even when idle.
Missing/failed generation reads close the stream. Filesystem notifications
alone are insufficient. At certificate expiry or retire_at the same rule
applies, with no new dispatch at or after the deadline. Process crashes close
the underlying stream; a dead process is not an authorization subscriber.

Every application dispatch checks current generation, credential validity,
allowlist membership and authenticated hello. Its check and dispatch admission
MUST hold the same authorization lock, so revocation cannot commit between them.
A read admitted before revocation may be interrupted by stream cancellation;
no new read is admitted afterward from the stale generation. Each mutation, including resumed
transfer, retry, queued work and recovery, additionally rechecks these facts
under the authorization lock immediately before each externally visible
side-effect boundary. The generation check and that boundary serialize with
revocation/config commit. Work prepared under an old generation cannot gain
new authority by refreshing a cached number: discard its authorization and
replan/revalidate through a fresh mutually authenticated connection. Existing
lease, operation and idempotency checks still apply. An effect already committed
before revocation is not undone; pending work must stop at the next boundary
and use the existing recovery journal. Long provider calls must not hold the
authorization lock across unbounded work; revocation cannot report success
while an effect boundary still holds prior authorization.

Revocation is an explicit local atomic transition to revoked, increments the
generation, forbids all future admissions of that key and closes old streams.
Removing an allowlisted host also increments generation and invalidates streams.
Success means the durable decision committed; the documented one-second close
bound does not permit any later dispatch or mutation from the stale generation.
A crash after commit but before acknowledgements cannot restore authority.
Failed commits report failure; they cannot be reported as absence or success.
Revocation is local: the operator must distribute it explicitly to every peer;
a disconnected peer with stale trust cannot be claimed globally revoked.
Loss/copy/compromise of a key requires revocation and new out-of-band enrollment,
not same-key recovery. Host UUID reuse after total trust-state loss requires
operator reconciliation of every peer, never automatic enrollment.

#### 11.10.4 Assurance and executable fixture bounds

TLS proves possession of an enrolled private key and protects records. It does
not prove unique physical hardware, current ownership of a Session, or an
uncompromised operator/account. A copied key authenticates until each verifier
revokes it. An attacker able to read/replace local AX state, credentials or
binaries is outside this assurance. Arbitrary shell access to that account
cannot be made safe by a wrapper. A restricted server-enforced SSH account is
an alternative deployment hardening measure, not equivalent host evidence and
not a substitute for this profile. Remote attach/log CLI paths remain their
existing SSH contracts; they do not acquire RPC-5 host-channel assurance.

The following closed gate registry defines source-level fixture families.
Each family MUST have positive and negative vectors. These are contract model
checks, not an executed TLS deployment, private-key custody proof or product
conformance result. Real certificate-chain, handshake, race/timeout and platform
acceptance remains required by <code>AC-HOST-001</code>.

| Gate | Predicate required for admission |
| --- | --- |
| HC-TLS | Both peers verify full TLS 1.3 and exact ALPN; no resumption or early data |
| HC-CERT | Standard chain, profile, time and role verification succeed in both directions |
| HC-MAP | Exact enrolled leaf/root/key maps uniquely to the configured UUID |
| HC-HELLO | Both hello IDs equal verified UUIDs and nonce/contract/limit validation succeeds |
| HC-DISPATCH | No application dispatch before mutual TLS and hello success |
| HC-MIGRATE | Config 4 selects the explicit Host Channel 1 launch and RPC 5 only |
| HC-LIFECYCLE | Explicit enrollment and bounded fresh-key rotation; revoked keys never reenter |
| HC-GENERATION | Dispatch and every mutation boundary use the current committed authorization generation |
| HC-EXCLUDE | Credential and trust material remains local, outside replication |
| HC-PARITY | The same TLS requirements apply over OpenSSH and native Tailscale SSH |

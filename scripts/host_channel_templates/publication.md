## Signing, release, and attribution

### Publication gate

The full gate is normative in [SPEC.md §20.2](SPEC.md#202-publication-gate). In order:

1. Verify a clean checkout contains `SPEC.md`, `README.md`, `CONTRIBUTING.md`, diagram sources and rendered SVGs, `VERSION`, `CHANGELOG`, release notes, and `LICENSE` (MIT).
2. Run the accepted validation entry point as a standalone process and retain its real exit code.
3. Explicitly verify that the validator does not require an `ax` binary, provider runtime, platform lane, or any [§19](SPEC.md#19-ax-implementation-conformance-and-product-release) result.
4. Verify `VERSION`, current document metadata, changelog and release notes identify prepared `v0.6.0`; verify every existing release tag is unchanged. There is no preparation tag.
5. Run the semantic crash/restart gate and focused expected-red mutations; weakening the three outcomes, boundary registry, evidence, owner uniqueness, or native-identity preservation must produce an actionable diagnostic.
6. Create signed commits for the reviewed scope and publish a feature branch/PR under explicit delivery authorization.
7. Obtain a real review verdict and required green checks on the exact signed head; never impersonate independent approval or bypass protection.
8. Verify signatures and PR/remote head equality, then land accepted signed commits without rewriting them or forcing main. If main advances, repeat signed rebase, review and checks.
9. Keep release tags unchanged during preparation; the parent owns later release publication after all constituent Stories and gates are accepted and landed.
10. For signed PR delivery verify the public repository, default branch, license, commit signature and exact PR/remote head. The parent verifies the tag signature and release URL only during the later authorized release publication.
11. Attach publication evidence to the board.

Explicit delivery authorization permits automation to stage the reviewed scope, create signed commits, and push a feature branch/PR after validation. Required independent review and checks must accept the exact signed head before landing; advancing main requires a signed rebase and fresh review/checks. Preparation MUST NOT create a release tag. The parent owns separate release publication only after all constituent Stories and publication gates are accepted and landed. See [§20.2](SPEC.md#202-publication-gate), `SPEC-PUB-001`, and `SPEC-PUB-CRASH-001`.

### Signing

- **Author**: `Ivan Oparin <oparin@me.com>` — this is the commit author for the release commit. No AI `Co-Authored-By` trailer is included.
- **Signing key**: `~/.ssh/ivanopcode` (SSH signing key). Delivery commits must be signed with this key. If the parent later publishes an annotated release tag `v0.6.0`, that tag must also be signed with this key. The repository's Git config must set `gpg.format ssh`, `user.signingkey ~/.ssh/ivanopcode`, `commit.gpgsign true`, and `tag.gpgsign true`.
- **Delivery authority**: explicit user authorization permits signed branch/PR delivery after review and checks. Release tags are separate parent-owned publication; preparation creates no tag.
- Verify committed signatures locally; verify a release tag only when the parent has actually published one:

```shell
git log --show-signature -1
# Parent only, after actual release publication (not preparation):
git tag --verify v0.6.0
```

### AI attribution policy

No commit message — including the release commit — may contain an AI `Co-Authored-By` trailer or other AI attribution trailer. The model is not a commit co-author. If an acknowledgement is explicitly requested, it MAY appear only in prose documentation outside commit metadata, clearly marked as non-commit attribution; it MUST NOT appear as a commit trailer. See [SPEC.md §20.1](SPEC.md#201-repository-and-release).

## Checklist for a spec PR

- [ ] Change is authorized by a settled decision or an explicit recorded refinement.
- [ ] `SPEC.md` is the only normative edit; `README.md`/`CONTRIBUTING.md` only summarize and link.
- [ ] Traceability rows in [Appendix A](SPEC.md#appendix-a-normative-traceability) updated.
- [ ] Contract registry and fixture catalog updated if a contract or variant changed.
- [ ] Crash/restart gate semantics and focused expected-red mutations pass when Section 13 multi-step recovery changes.
- [ ] No unsupported capability claimed; no default-encryption claim added; WSL2 and native Windows remain distinct.
- [ ] Diagram sources re-rendered, SVGs committed, and visual inspection done.
- [ ] `./run_validation.sh` exits `0` as a standalone process.
- [ ] `task-board validate` exits `0`.
- [ ] Commit carries correct author `Ivan Oparin <oparin@me.com>`, is SSH-signed with `~/.ssh/ivanopcode`, contains no AI `Co-Authored-By` trailer, and was created under explicit signed-delivery authorization after validation. Required review and checks accept the exact signed head before landing; no release tag is created during preparation.

For host-channel edits run `python3 scripts/test_host_channel.py` in addition to
the public validation and retained expected-red suite. Fixtures are synthetic
contract evidence; real TLS and platform acceptance remains `AC-HOST-001`.

Host admission predicates are read from SPEC.md §11.10.5. Its rendered table
and the operational explanation templates must agree; refreshing the document
digest cannot waive these checks. The ledger separately reports individually
witnessed field obligations, family coverage and runtime/prose blind spots.

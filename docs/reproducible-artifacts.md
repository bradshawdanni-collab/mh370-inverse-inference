# Reproducible Build Artifacts (DX.2.1 Policy)

This repository defines a canonical software environment for reproducible source bundles and related release artifacts. The goal is strict, byte-for-byte reproducibility within the declared canonical environment, while treating cross-platform rebuilds as later diagnostic evidence rather than an immediate merge gate.

## Architecture

```text
Pinned repository state
    -> normalized archive construction
    -> timestamp and ownership normalization
    -> timestamp-free compression
    -> SHA256SUMS generation
    -> manifest verification
    -> uploaded canonical artifact
```

## Canonical environment

The initial canonical build environment is the Linux runner defined in `.github/workflows/dx2-compliance.yml`.

The workflow:

- checks out one repository commit;
- sets `SOURCE_DATE_EPOCH` from that commit timestamp;
- sorts archive entries by name;
- removes variable access-time and change-time metadata;
- normalizes owner and group identifiers to `0/0`;
- suppresses gzip timestamps with `gzip -n`;
- generates `SHA256SUMS`;
- verifies the manifest before uploading the artifact.

A canonical artifact is compliant only when its byte stream matches its generated manifest inside this declared environment.

## Dependency isolation

Future compiled or packaged release workflows must use immutable dependency inputs.

Required controls are:

- content-hashed lockfiles where supported;
- frozen or synchronized installation modes;
- no floating dependency versions in release paths;
- no opportunistic build-time network fetches;
- local vendoring or content-addressed caches when offline execution is required.

The current DX.2.1 source-bundle workflow does not install dependencies because it archives repository source directly.

## Metadata normalization

Canonical archives must use equivalent controls to:

```bash
tar --sort=name \
    --format=posix \
    --pax-option=delete=atime,delete=ctime \
    --mtime="@${SOURCE_DATE_EPOCH}" \
    --owner=0 --group=0 --numeric-owner \
    -cf research-bundle.tar src
gzip -n research-bundle.tar
```

Any replacement implementation must preserve the same observable normalization contract.

## Manifest policy

Every canonical artifact must be listed in a `SHA256SUMS` manifest generated from the final byte stream.

The workflow must verify the manifest before artifact upload or release promotion.

## Signature policy

Detached signature enforcement is deferred until the repository has all of the following:

- a dedicated release signing key;
- protected GitHub secrets or a hardware-backed signing service;
- documented key rotation procedures;
- documented revocation and recovery procedures;
- named responsibility for release approval.

Until that governance exists, the absence of `SHA256SUMS.sig` is not a CI failure.

## Cross-environment rebuilds

A later DX.2 slice may rebuild the same artifact on macOS or another independent environment.

Cross-environment equality will initially be advisory because host toolchain and compression implementations may differ. A mismatch should trigger investigation, but it should not block a canonical artifact that passes its hard in-environment manifest gate.

## Validation checklist

- [ ] The canonical artifact matches `SHA256SUMS`.
- [ ] Archive entries are sorted deterministically.
- [ ] Owner and group metadata are normalized to `0/0`.
- [ ] Variable access-time and change-time metadata are absent.
- [ ] Compression uses timestamp suppression.
- [ ] No undeclared network fetch occurs during artifact construction.
- [ ] Any future signing gate is backed by documented key governance.
- [ ] Any cross-environment variance is recorded as advisory diagnostic evidence.

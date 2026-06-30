# Contributing

## Development setup

Create an isolated environment and install the project with development tools:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Standard local checks

Run the full quality sequence before pushing:

```bash
ruff check .
black --check .
mypy src
pytest
```

## RGAP data-change checks

Changes under `data/satcom/` are governed by the Reference Governance and Admission Protocol rules implemented in this repository.

Before pushing a branch that adds, changes, moves, or removes SATCOM data:

1. Update at least one approved registry:

   ```text
   data/source-register.csv
   data/satcom/source_register.yaml
   data/satcom/published/source_register.yaml
   ```

2. Record the artifact identifier, canonical source, retrieval time, licence or terms, SHA-256 checksum, transformation history, uncertainty notes, version, and admission state.

3. Keep unverified or incomplete records below `ADMITTED`, such as `PROPOSED` or `RETRIEVED`.

4. Run the deep registry check:

   ```bash
   pytest tests/test_registry_integrity.py
   ```

5. Run the complete local sequence:

   ```bash
   ruff check .
   black --check .
   mypy src
   pytest tests/test_registry_integrity.py
   pytest
   ```

## Computing a SHA-256 checksum

Linux or macOS:

```bash
sha256sum path/to/file
```

On macOS systems without `sha256sum`:

```bash
shasum -a 256 path/to/file
```

Python, cross-platform:

```bash
python -c "from hashlib import sha256; from pathlib import Path; p=Path('path/to/file'); print(sha256(p.read_bytes()).hexdigest())"
```

The checksum must be generated from the exact checked-in payload. The SHA-256 value for an empty file and placeholder strings are rejected for admitted records.

## Admission rule

An artifact may be marked `ADMITTED` only when all mandatory fields are present and verified. The repository test rejects admitted records with missing, blank, malformed, or placeholder provenance values.

The GitHub Actions workflow `.github/workflows/rgap-audit.yml` enforces two layers:

- a coarse check requiring SATCOM data changes to be accompanied by a register change;
- a deep Python integrity check for admitted records.

These checks enforce evidence housekeeping. They do not establish scientific correctness or authorize a crash-location claim.

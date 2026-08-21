# Contributing to Sub-Enum

Thank you for your interest in contributing to **Sub-Enum**! We welcome bug reports, improvements, documentation updates, and new passive discovery sources.

---

## Project Philosophy & Scope Boundaries

Sub-Enum is designed to be a **fast, evidence-rich subdomain enumeration and asset inventory tool for bug bounty hunters and penetration testers**.

To maintain high code quality and focus, we enforce strict project boundaries:

### What Sub-Enum DOES:
- Subdomain discovery (passive and active DNS/permutation).
- Target scope normalization and strict suffix enforcement.
- Discovery method and provider provenance preservation.
- Active DNS validation (A, AAAA, CNAME) and wildcard filtering.
- Lightweight HTTP probing and technology/header enrichment.
- Historical scan tracking and change detection (`diff`, `history`).

### What Sub-Enum DOES NOT do (Out of Scope):
- General vulnerability scanning (e.g., Nuclei, template runners).
- Web crawling, spidering, or directory brute-forcing (e.g., Katana, ffuf).
- Port scanning and network probing (e.g., Naabu, Nmap).
- Vulnerability exploitation or takeover automation.

*Rule of thumb: If a proposed feature does not directly improve subdomain enumeration, validation, or asset triage, it should remain a downstream tool in the researcher's workflow.*

---

## Local Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/tobiasGuta/sub-enum.git
cd sub-enum
```

### 2. Create a virtual environment and install dev dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
```

### 3. Run the test suite
```bash
pytest -v
```

### 4. Format & Lint
```bash
ruff check src tests
```

---

## Guidelines for Adding New Passive Sources

If you are adding or proposing a new passive discovery source:
1. **Prefer Native HTTP/JSON Adapters**: Do not add heavy binary dependencies if a lightweight, reliable REST/JSON API exists.
2. **Strict Scope Validation**: Every candidate hostname must pass through `normalize_candidate(hostname, domain)`.
3. **Preserve Provenance**: Tag records with `source = "<provider-name>"` and `method = "passive"`. Never fabricate confidence or data types.
4. **Isolate Failures**: Network timeouts, HTTP 429/5xx errors, or malformed responses from a passive source must be recorded cleanly in `ToolRun` and must **never** crash the overall scan.
5. **Add Automated Tests**: Write mock-based unit tests for successful parsing, empty responses (`[]`), scope filtering, duplicate deduplication, and error conditions in `tests/`.

---

## Submitting a Pull Request

1. Fork the repository and create a descriptive branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Write clean, type-annotated Python code following the existing project structure.
3. Ensure all tests pass:
   ```bash
   pytest
   ```
4. Commit your changes with clear messages.
5. Open a Pull Request on GitHub with a description of the problem solved and test validation details.


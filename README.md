# Sub-Enum

Sub-Enum is a focused subdomain-enumeration tool for bug bounty hunters and penetration testers. Its job is to turn a root domain into a **clean, in-scope, evidence-rich subdomain inventory** without becoming a general vulnerability scanner.

## What v0.2 changes

Sub-Enum now treats discovery quality and evidence as first-class data:

- **Strict scope enforcement** on every candidate returned by external tools.
- **Subfinder as the primary passive engine**, with contributing provider provenance preserved from JSONL output.
- **Findomain as a secondary passive source** when installed.
- **Assetfinder demoted to opt-in** (`--assetfinder`) so overlap can be measured instead of assumed useful.
- **Chaos is expected through Subfinder's provider system**, not launched as a duplicate default command.
- **dnsx JSONL validation** with wildcard-aware A resolution plus AAAA/CNAME enrichment.
- **AlterX replaces altdns** for target-aware, enriched permutations.
- **PureDNS + massdns are optional deep-mode tools** for large DNS validation/bruteforce workflows.
- **httpx JSONL enrichment** rather than regex-parsing terminal output.
- **Canonical `assets.jsonl`**, while keeping simple TXT files for shell pipelines.
- **SQLite scan history**, `diff`, `history`, and per-source contribution reporting.
- **Pinned tested external-tool refs** instead of `go install ...@latest`.
- **Python 3.11+** and a flat modern package layout.

Sub-Enum intentionally does **not** bundle web crawling, content discovery, template vulnerability scanning, SQL injection tooling, or exploit automation. Those are downstream tasks.

## Pipeline

```text
root domain
   |
   v
scope normalization
   |
   v
passive discovery
   |- Subfinder (+ provider provenance)
   |- Findomain (optional secondary source)
   `- Assetfinder (opt-in compatibility source)
   |
   v
DNS validation
   |- dnsx (standard)
   `- PureDNS/massdns (optional deep backend)
   |
   +--> wildcard filtering / DNS evidence
   |
   v
AlterX target-aware permutations
   |
   v
DNS validation of generated candidates
   |
   v
httpx structured HTTP enrichment
   |
   v
assets.jsonl + TXT exports + SQLite history
```

## Profiles

### Passive

Only passive enumeration and provenance collection.

```bash
sub-enum scan -d example.com --profile passive
```

### Standard

The default bug-bounty workflow: passive discovery, DNS validation, bounded target-aware AlterX permutations, re-validation, and HTTP enrichment.

```bash
sub-enum scan -d example.com
```

### Deep

Adds support for a PureDNS/massdns resolver backend and optional large wordlist brute forcing. Deep mode requires an explicit resolver list before PureDNS is used automatically.

```bash
sub-enum scan -d example.com \
  --profile deep \
  --resolvers resolvers.txt \
  --wordlist subdomains.txt
```

PureDNS is deliberately optional because high-volume DNS enumeration needs a curated resolver list and different operational care than a normal scan.

## Installation

Python 3.11+ is required.

For development or a local clone, `pipx` is recommended for CLI isolation:

```bash
git clone https://github.com/tobiasGuta/sub-enum.git
cd sub-enum
pipx install .
```

The core workflow expects `subfinder`, `dnsx`, and `httpx`. Standard permutations additionally use `alterx`. Run:

```bash
sub-enum doctor
```

If Go 1.25+ is already installed, Sub-Enum can install the managed Go dependencies at the tested refs:

```bash
sub-enum doctor --install
```

Findomain remains a separately installed optional source. PureDNS deep mode also requires `massdns`.

## Subfinder API providers

Sub-Enum does not duplicate the entire passive-provider credential system. Configure API-backed sources in Subfinder's provider config (for example Chaos, GitHub, SecurityTrails, Censys, and other supported providers), then Sub-Enum preserves the contributing source names in `assets.jsonl`.

Use:

```bash
subfinder -ls
```

to inspect the providers supported by your installed Subfinder build.

## Outputs

Each target gets its own directory:

```text
example.com/
├── assets.jsonl
├── all_subdomains.txt
├── resolved_subdomains.txt
├── live_subdomains.txt
├── dangling_cname_candidates.txt
├── wildcard_roots.txt
├── source_stats.json
└── run_manifest.json
```

### `assets.jsonl`

This is the canonical Sub-Enum dataset. Each hostname can retain:

- root domain
- passive/provider sources
- discovery methods (`passive`, `permutation`, `bruteforce`)
- A / AAAA / CNAME evidence
- wildcard state
- dangling-CNAME candidate state
- HTTP URL/status/title/technology/IP/CDN evidence
- confidence classification
- first/last observation timestamps

Generated permutations are **not** treated as validated merely because AlterX produced them. DNS evidence is kept separate.

### Confidence labels

Sub-Enum uses explainable labels instead of a fake numeric risk score:

- `confirmed` — DNS validated and observed by multiple discovery sources.
- `resolved` — DNS validated.
- `passive_only` — passively observed but not currently DNS validated.
- `generated` — permutation/bruteforce candidate without validation.
- `wildcard_suspect` — associated with wildcard evidence.
- `dangling_cname_candidate` — CNAME evidence exists without A/AAAA evidence; this is a triage lead, **not a vulnerability claim**.

## History and change detection

Completed scans are stored in `~/.sub-enum/history.db` unless `--no-history` is used.

```bash
sub-enum history example.com
sub-enum diff example.com
sub-enum sources example.com
```

This makes recurring bug-bounty recon useful: new hosts, disappeared hosts, DNS changes, and HTTP changes can be surfaced without manually diffing text files.

## Useful controls

```bash
# Multiple root domains
sub-enum scan -L targets.txt --workers 4

# Passive provider breadth
sub-enum scan -d example.com --all-sources

# Disable target-aware mutations
sub-enum scan -d example.com --no-permutations

# Skip HTTP enrichment
sub-enum scan -d example.com --no-http

# Tune DNS/HTTP pressure
sub-enum scan -d example.com --dns-rate 200 --http-threads 30

# Opt into Assetfinder for comparison/coverage testing
sub-enum scan -d example.com --assetfinder
```

The v0.1 invocation remains accepted:

```bash
sub-enum -d example.com
```

and is internally treated as a standard scan.

## Docker

The image builds pinned tested versions of Subfinder, dnsx, httpx, AlterX and PureDNS, plus a pinned massdns commit and Findomain release.

```bash
docker build -t sub-enum:0.2.0 .
docker run --rm -v "$(pwd)/scans:/scans" sub-enum:0.2.0 \
  scan -d example.com --output-root /scans
```

For API-backed Subfinder sources, mount your provider configuration read-only into the container.

## Scope and responsible use

Sub-Enum rejects external-tool output that does not equal the requested root domain or end in `.<root-domain>`. This prevents unrelated results from silently entering a bug-bounty target inventory.

Use Sub-Enum only on assets you are authorized to test, and always follow the program's scope and automation rules.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
ruff check src tests
```

The orchestration layer intentionally remains Python for v0.2. The expensive enumeration, DNS, mutation and HTTP work is already performed by optimized Go/Rust tools; a Go rewrite should only be considered after the CLI/data model stabilizes and a single-binary/cross-platform requirement justifies the migration.

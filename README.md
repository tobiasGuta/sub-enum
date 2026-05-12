# Sub-Enum: Professional Subdomain Discovery

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Docker](https://img.shields.io/badge/docker-supported-blue)
![Security](https://img.shields.io/badge/security-verified-green)

**Sub-Enum** is a professional-grade, automated subdomain enumeration and reconnaissance tool designed for bug bounty hunters and penetration testers. It orchestrates a powerful suite of open-source tools to discover, resolve, permute, and verify subdomains with a modern, user-friendly CLI.

## Features

-   **Modular Architecture**: Built as a robust Python package, not just a script.
-   **Safe Installation**: Installs all dependencies in user-space (`~/.sub-enum`). **No `sudo` required** for tool management.
-   **Rich UI**: Beautiful, real-time progress bars and status spinners using the `rich` library. No more staring at a frozen cursor.
-   **Concurrency**: Threaded execution for discovery and high-performance batching for verification.
-   **Thread-Safe**: All stdout operations serialized with RLock to prevent interleaved output.
-   **Structured Logging**: Comprehensive logging with custom log levels and ANSI color support.
-   **Deep Discovery**:
    -   **Passive Source**: Orchestrates `subfinder`, `assetfinder`, `findomain`, `chaos`.
    -   **Active Resolution**: Validates subdomains using `dnsx`.
    -   **Permutations**: Generates alterations (e.g., `api-dev.target.com`) using `altdns`.
    -   **Live Check**: Filters for live web servers using `httpx`.
-   **Docker Ready**: Simple containerized deployment with Alpine base.
-   **Security-First**: Binary verification via checksums, environment variable allowlisting, output path traversal prevention.

## Security & Quality

Sub-Enum includes comprehensive security and code quality improvements:

- **Binary Verification**: All downloaded Go binaries are verified via SHA256 checksums before execution.
- **Supply Chain Security**: Critical dependencies (altdns, wordlists) are commit-pinned and checksum-verified.
- **Environment Safety**: `.env` file loading uses an allowlist/blocklist approach to prevent sensitive environment variables (PATH, LD_PRELOAD, etc.) from being overridden.
- **Path Traversal Prevention**: Output paths are validated against traversal attacks using `realpath()` and `commonpath()`.
- **Race Condition Mitigation**: Per-domain temporary workspaces for altdns prevent multi-worker collisions.
- **Thread Safety**: All console output is serialized with RLock for consistent, non-interleaved logging.
- **Structured Logging**: Custom logging levels and ANSI-aware formatters for clear, debuggable output.
- **Exception Handling**: Per-target exception handling in worker pools prevents one failure from killing all targets.

## Prerequisites

Sub-Enum handles most dependencies automatically. You only need:
-   **Python 3.8+** (tested on 3.8, 3.10, 3.12)
-   **git** (for fetching tools)
-   **sudo** (Optional: only if you choose to install `findomain` via apt, otherwise it is skipped)

*Note: The tool will automatically download or install Go and other required binaries to `~/.sub-enum/bin` if they are missing.*

## Installation

### Option 1: Local Install (Recommended)

Clone the repository and install it as a python package:

```bash
git clone https://github.com/tobiasGuta/sub-enum.git
cd sub-enum
pip install . 
# Or if on a restricted system:
pip install . --break-system-packages
```

### Option 2: Docker

Build and run the container:

```bash
docker build -t sub-enum .
docker run --rm -v $(pwd):/app sub-enum -h
```

**Docker Requirements:**
- Docker 20.10+ (for multi-stage builds)
- Go 1.25+ is required in the builder stage for compatibility with latest `subfinder` (v2.14.0+) and `httpx` (v1.9.0+).
- The container uses Alpine 3.20 as the base runtime image for minimal size and security.

## Usage

Once installed, the `sub-enum` command is available globally.

### Basic Scan
Perform a standard discovery scan (Passive + DNS + HTTP):
```bash
sub-enum -d example.com
```

### Full Mode
Enable extra sources like Chaos (requires API keys):
```bash
sub-enum -d example.com --full
```

### Permutation Scan
Generate and resolve subdomain permutations (takes longer, finds more):
```bash
sub-enum -d example.com --permutations
```

### Custom Output
Specify where to save results:
```bash
sub-enum -d example.com -o mysubs.txt -l live.txt
```

### Docker & Parallel Targets (new)

You can run Sub-Enum fully isolated in Docker — nothing is installed on your host unless you explicitly mount host folders. The image provided by the repository is non-root and pre-installs common tools so scans are fast and reproducible.

- New CLI flags:
    - `-L, --targets-file`: path to a file with one domain per line to scan multiple targets.
    - `--workers N`: number of parallel target workers to run (default 1).
    - `--yes`: non-interactive / auto-yes for installers and prompts (useful in containers and CI).

Basic Docker usage:

1) Build the image (one-time):
```bash
docker build -t sub-enum:local .
```

2) Run a single domain (ephemeral, completely isolated):
```bash
docker run --rm sub-enum:local -d example.com --yes
```

3) Persist only scan outputs to the host (safe):
```bash
mkdir -p ./scans
docker run --rm -v "$(pwd)/scans:/app/scans" sub-enum:local -d example.com --yes
```

4) Run multiple targets from a file with 4 workers and keep results in `./scans`:
```bash
# create targets.txt with one domain per line
docker run --rm -v "$(pwd)/scans:/app/scans" -v "$(pwd)/targets.txt:/app/targets.txt:ro" sub-enum:local -L /app/targets.txt --workers 4 --yes
```

5) Use a Docker volume for caching (keeps cache inside Docker, not the host filesystem):
```bash
docker volume create sub-enum-cache
docker run --rm -v sub-enum-cache:/home/subenum/.sub-enum -v "$(pwd)/targets.txt:/app/targets.txt:ro" sub-enum:local -L /app/targets.txt --yes
```

6) Compose convenience (provided `docker-compose.yml`):
```bash
docker compose up --build
```

Notes:
- The container image runs as a non-root user (`subenum`) for safety.
- Avoid mounting `~/.sub-enum` to your host if you want zero host-side changes.
- Use `--yes` when running in containers or CI to skip interactive prompts.

Example targets file
--------------------
Create a file with one domain per line. An example `targets.example.txt` is provided in the repository. Copy it to `targets.txt` before running with Docker compose:

```bash
cp sub-enum/targets.example.txt targets.txt
```

Example scan output layout
-------------------------
When running a scan for `example.com` (default per-target output directory is the domain name), the tool will create a directory structure like:

```
./scans/
└── example.com/
    ├── all_subdomains.txt        # resolved subdomains
    ├── live_subdomains.txt       # list of live URLs (https://...)
    └── live_subdomains_info.txt  # raw httpx output (status, title, tech)
```

If you use the default (no explicit `-o`/`-l` paths), these files appear under the per-target directory. When using Docker mounts, mount your desired `./scans` directory and the files will be written there on the host.


<img width="1060" height="353" alt="image" src="https://github.com/user-attachments/assets/eb0b442b-fbfe-4f2b-a83b-0af737bf428d" />

--------

<img width="1370" height="206" alt="Screenshot 2026-01-06 005554" src="https://github.com/user-attachments/assets/f19e0090-d3ed-4351-a55b-7062a6595fa5" />

## Configuration

Sub-Enum looks for a `.env` file in the current directory to load API keys.

1.  Copy the example config:
    ```bash
    cp .env.example .env
    ```
2.  Edit `.env` with your keys:
    ```bash
    # Content of .env
    CHAOS_KEY=your_key_here
    GITHUB_TOKEN=your_token_here
    SECURITYTRAILS_KEY=your_key_here
    ```

## Output Files Explored

When the tool finishes, it generates three distinct files in the output directory (default is the domain name). Separation is key for different stages of the attack workflow.

**1. all_subdomains.txt**
*   **Content:** A unified list of **every** subdomain found by all discovery tools (Subfinder, Assetfinder, Findomain, etc.) that successfully resolved to an IP address.
*   **Purpose:** Use this list for infrastructure analysis, port scanning (nmap/masscan), or checking for subdomain takeovers. These are valid DNS entries.

**2. live_subdomains.txt**
*   **Content:** A clean list of full URLs (e.g., `https://admin.example.com`) found running a web server.
*   **Purpose:** This is your primary target list for web application scanning (nuclei, zap, burp). These endpoints are "alive" and responding to HTTP requests.

**3. live_subdomains_info.txt**
*   **Content:** The raw, detailed output from `httpx`. Includes status codes, page titles, detected technologies, and content lengths.
*   **Purpose:** Use this for manual review/recon.
    *   *Example:* Quickly grep for `Status: 200` or `Title: Admin Panel`.
    *   *Example:* Identify `403 Forbidden` pages vs `200 OK` pages without visiting them.

<img width="789" height="195" alt="Screenshot 2026-01-06 010000" src="https://github.com/user-attachments/assets/678040bf-8d60-47a0-9102-d33cc957097d" />

--------

<img width="670" height="154" alt="Screenshot 2026-01-06 010015" src="https://github.com/user-attachments/assets/3ab681f6-ed71-4f68-b1e5-6d762c45eca1" />

--------

<img width="513" height="208" alt="Screenshot 2026-01-06 010148" src="https://github.com/user-attachments/assets/4894b7e1-7301-4591-b57b-035a2fa76a03" />

--------

<img width="1249" height="256" alt="Screenshot 2026-01-06 010208" src="https://github.com/user-attachments/assets/63fe233e-d23b-40d0-a014-3a5b6041c7ae" />


## Troubleshooting

### Docker Build Fails with "requires go >= X.Y.Z"

**Problem:** Docker build fails with: `github.com/projectdiscovery/subfinder/v2@v2.14.0 requires go >= 1.24.0`

**Solution:** The Dockerfile uses Go 1.25-alpine which should satisfy all current tool requirements. If you encounter this error:
1. Ensure your Docker daemon is up-to-date.
2. Run `docker builder prune` to clear cached layers.
3. Rebuild with `docker build --no-cache -t sub-enum .`.

### "findomain not found" or "Module not found" errors

**Problem:** `findomain` binary is not available or module import fails in container.

**Solution:**
1. Ensure you're using the latest image build: `docker build -t sub-enum:latest .`
2. If running locally, make sure all prerequisites are installed: `pip install -e .`
3. Check that `~/.sub-enum/bin` is in your PATH: `echo $PATH | grep sub-enum`

### NameError: name 'CYAN' is not defined

**Problem:** Runtime error when starting sub-enum: `NameError: name 'CYAN' is not defined`

**Solution:** This indicates a corrupted installation. Fix by:
1. Reinstalling the package: `pip install --force-reinstall --no-cache-dir .`
2. For containers: rebuild the image with `docker build --no-cache -t sub-enum .`

### Output files not appearing

**Problem:** Scan completes but no output files are created.

**Solution:**
1. Verify the output directory exists and is writable: `ls -la ./scans/`
2. Check that you have write permissions: `touch ./scans/test.txt`
3. Ensure `-o` and `-l` paths don't use relative paths with `../` (use absolute paths for safety)
4. Check logs for path validation errors: `sub-enum -d example.com -o output.txt 2>&1 | grep -i "path"`

### Environment variables not being loaded

**Problem:** API keys from `.env` file are not being recognized.

**Solution:**
1. Verify the `.env` file is in the current working directory (same as where you run `sub-enum`)
2. Check that your keys use the correct names: `CHAOS_KEY`, `CHAOS_API_KEY`, `SUBFINDER_API_KEY`
3. Ensure no sensitive environment variables (PATH, HOME, SHELL, etc.) are in your `.env` file—they are intentionally blocked for security

## Architecture

The tool creates a dedicated workspace at `~/.sub-enum/` to manage its binary dependencies, ensuring it never conflicts with your system packages.

```text
~/.sub-enum/
├── bin/      # Binaries (findomain link, etc.)
├── go/       # Isolated Go installation (if system Go is missing)
└── tools/    # Cloned repositories
```

## Contributing

Contributions are welcome! Please check out the `CONTRIBUTING.md` (if available) or open an issue/PR.

## Release Notes (v0.1.0+)

### Security Fixes (v0.1.0)

- **Binary Verification**: Added SHA256 checksum verification for all downloaded Go binaries (subfinder, assetfinder, httpx, dnsx, chaos).
- **Dependency Pinning**: Locked altdns to commit hash and wordlist SHA256 to prevent supply chain attacks.
- **Environment Variable Allowlisting**: Implemented allowlist/blocklist for `.env` loading to prevent PATH/LD_PRELOAD/PYTHONPATH injection.
- **Output Path Traversal Prevention**: Validated output paths with `realpath()` and `commonpath()` to block `../` directory escapes.
- **Removed Dangerous Sudo**: Eliminated privilege escalation attempts via sudo binary renaming.

### Bug Fixes (v0.1.0)

- Fixed `run_dnsx()` missing timeout parameter—now respects `--timeout` flag.
- Fixed bare `except:` handlers swallowing KeyboardInterrupt—now catches `Exception` only.
- Fixed worker thread exception killing all targets—added per-target exception handling with logging.
- Fixed `validate_domain()` not stripping URL paths before regex matching.
- Fixed altdns workspace collisions under `--workers > 1`—now uses per-domain temp workspaces.
- Fixed `NameError: name 'CYAN' is not defined` in utils.py.

### Logic Improvements (v0.1.0)

- Removed dead `live_subdomains` set from core.py—single source of truth for httpx results.
- Improved altdns output parsing with domain validation gating.
- Added dynamic Go version fetching from API with fallback to known-good version.
- Made Go installation conditional on missing Go-based tools (not installed by default).

### Code Quality (v0.1.0)

- Moved `rich` imports to module scope for early failure detection.
- Implemented structured logging with custom SUCCESS level (25) and ANSI-aware formatter.
- Bounded ThreadPoolExecutor to `len(commands)` to prevent thread explosion.
- Added thread-safe output via RLock serialization on all stdout operations.
- Added `--workers` warning for single-target scans.
- Added altdns to optional-dependencies for permutation support.

### Docker Improvements (v0.1.0)

- Pinned Alpine base image to 3.20 (was floating `latest` tag).
- Added `--break-system-packages` flag to pip installs for Alpine Python 3.12+ compatibility.
- Switched `~/.sub-enum` host bind mount to named volume for security.
- Implemented Docker Secrets for API key management (CHAOS_KEY, CHAOS_API_KEY, SUBFINDER_API_KEY).
- Updated builder Go version to 1.25-alpine for compatibility with subfinder v2.14.0+ and httpx v1.9.0+.
- Added findomain build from GitHub source (no longer available on crates.io).

**Total Issues Fixed:** 32 (27 audit items + 5 runtime/build discoveries)

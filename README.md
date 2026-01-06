# Sub-Enum: Professional Subdomain Discovery

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Docker](https://img.shields.io/badge/docker-supported-blue)

**Sub-Enum** is a professional-grade, automated subdomain enumeration and reconnaissance tool designed for bug bounty hunters and penetration testers. It orchestrates a powerful suite of open-source tools to discover, resolve, permute, and verify subdomains with a modern, user-friendly CLI.

## Features

-   **Modular Architecture**: Built as a robust Python package, not just a script.
-   **Safe Installation**: Installs all dependencies in user-space (`~/.sub-enum`). **No `sudo` required** for tool management.
-   **Rich UI**: Beautiful, real-time progress bars and status spinners using the `rich` library. No more staring at a frozen cursor.
-   **Concurrency**: Threaded execution for discovery and high-performance batching for verification.
-   **Deep Discovery**:
    -   **Passive Source**: Orchestrates `subfinder`, `assetfinder`, `findomain`, `chaos`.
    -   **Active Resolution**: Validates subdomains using `dnsx`.
    -   **Permutations**: Generates alterations (e.g., `api-dev.target.com`) using `altdns`.
    -   **Live Check**: Filters for live web servers using `httpx`.
-   **Docker Ready**: Simple containerized deployment.

## Prerequisites

Sub-Enum handles most dependencies automatically. You only need:
-   **Python 3.8+**
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

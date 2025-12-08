# Subdomain Finder Tool (Community Edition)

This is a comprehensive, unified subdomain enumeration tool designed for bug bounty hunters and penetration testers. It orchestrates multiple tools to discover, resolve, permute, and verify subdomains.

https://github.com/user-attachments/assets/3593ca35-f6d4-4625-8022-2f2475e22265

# Features

- **Unified Architecture**: One script (`sub_enum.py`) to rule them all.
- **Parallel Execution**: Runs discovery tools concurrently.
- **DNS Resolution**: Verifies subdomains using `dnsx` to ensure they are resolvable.
- **Permutation Scanning**: Generates and resolves permutations (e.g., `api-dev.target.com`) using `altdns`.
- **Live Verification**: Checks for live web servers using `httpx`.
- **Docker Support**: Run anywhere without dependency hell.
- **Config Management**: Load API keys safely from a `.env` file.

# Prerequisites

The script attempts to install missing tools, but for the best experience, you should have:
- Python 3
- Go
- Rust (for Findomain)

**Tools Used:**
- subfinder
- assetfinder
- findomain
- dnsx
- httpx
- sublist3r (Full Mode)
- chaos (Full Mode)
- altdns (Permutations)

# Installation

### Local Installation
```bash
git clone https://github.com/tobiasGuta/sub-enum.git
cd sub-enum
chmod +x sub_enum.py
```

### Docker Installation
```bash
docker build -t sub-enum .
```

# Usage

### 1. Basic Scan
Fast discovery using passive sources + DNS resolution + HTTP check.
```bash
./sub_enum.py -d example.com
```

### 2. Full Scan
Includes `sublist3r` and `chaos` (requires API key).
```bash
./sub_enum.py -d example.com --full
```

### 3. Permutation Scan
Generates alterations (e.g., `dev.example.com` -> `dev-staging.example.com`) and resolves them.
```bash
./sub_enum.py -d example.com --permutations
```

### 4. Docker Usage
```bash
# Mount current directory to /app to save results locally
docker run -v $(pwd):/app sub-enum -d example.com
```

# Configuration

Copy the example config and add your API keys:
```bash
cp .env.example .env
nano .env
```

Supported keys:
- `CHAOS_KEY`
- `GITHUB_TOKEN` (for Subfinder)
- `SECURITYTRAILS_KEY` (for Subfinder)

# Output

- **all_subdomains.txt**: All resolved subdomains.
- **live_subdomains.txt**: Subdomains with running HTTP servers.

# Support
If my tool helped you land a bug bounty, consider buying me a coffee ☕️!

---

<div align="center">
  <a href="https://www.buymeacoffee.com/tobiasguta">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="200" />
  </a>
</div>

---

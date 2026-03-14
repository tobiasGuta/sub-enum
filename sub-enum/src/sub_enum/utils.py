import os
import shutil
import re
import subprocess
from typing import List

from .config import BLUE, RED, YELLOW, GREEN, RESET

# Global flag set by the CLI to control interactive prompts/auto-yes behavior
_AUTO_YES = False


def set_auto_yes(value: bool) -> None:
    """Set whether interactive prompts should default to yes.

    Call this from the CLI (core) when `--yes` / non-interactive mode is requested.
    """
    global _AUTO_YES
    _AUTO_YES = bool(value)


def get_auto_yes() -> bool:
    return _AUTO_YES

def load_env(filepath=".env"):
    """Load environment variables from a .env file."""
    if not os.path.exists(filepath):
        return
    print(f"{BLUE}[*] Loading configuration from {filepath}...{RESET}")
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

def check_tool_availability(tool):
    """Check if a tool is available in the system PATH."""
    return shutil.which(tool)

def ensure_path_context():
    """Ensure Go and Rust bin directories are in PATH for the current process."""
    home = os.path.expanduser("~")
    go_bin = os.path.join(home, "go", "bin")
    cargo_bin = os.path.join(home, ".cargo", "bin")
    local_bin = os.path.join(home, ".local", "bin")
    tool_bin = os.path.join(home, ".sub-enum", "bin")
    current_path = os.environ.get("PATH", "")
    path_elems: List[str] = current_path.split(":") if current_path else []
    paths_to_add: List[str] = []

    def _add_if_missing(p: str) -> None:
        if p and p not in path_elems:
            paths_to_add.append(p)

    _add_if_missing(tool_bin)
    _add_if_missing(go_bin)
    _add_if_missing(cargo_bin)
    _add_if_missing(local_bin)

    if paths_to_add:
        # Prepend paths so local tools take precedence
        os.environ["PATH"] = f"{':'.join(paths_to_add)}:{current_path}"

def validate_domain(domain):
    """Validate and clean the domain input."""
    if not domain:
        return None
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.rstrip('/')
    
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not re.match(pattern, domain):
        return None
    return domain

def remove_conflicting_httpx():
    """Rename system httpx to avoid conflicts with ProjectDiscovery httpx."""
    httpx_path = shutil.which("httpx")
    if not httpx_path:
        return
    if "go/bin" in httpx_path:
        return

    # If auto-yes mode is enabled, do not attempt privileged renames. Just warn.
    if get_auto_yes():
        print(f"{YELLOW}[!] Found conflicting httpx at {httpx_path}. Auto-yes enabled; skipping rename.{RESET}")
        return

    print(f"{YELLOW}[!] Found conflicting httpx at {httpx_path}.{RESET}")
    choice = input(f"{BLUE}[?] Do you want to rename it to 'httpx_legacy' to avoid conflicts? (yes/no): {RESET}").strip().lower()
    if choice == "yes":
        try:
            new_path = f"{httpx_path}_legacy"
            # Do not perform sudo automatically; the user will be prompted by subprocess if required
            subprocess.run(["sudo", "mv", httpx_path, new_path], check=True)
            print(f"{GREEN}[✓] Renamed {httpx_path} to {new_path}.{RESET}")
        except Exception as e:
            print(f"{RED}[✗] Failed to rename httpx: {e}{RESET}")

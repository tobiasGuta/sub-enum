import os
import shutil
import re
import subprocess
from .config import BLUE, RED, YELLOW, GREEN, RESET

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
    paths_to_add = []
    
    if tool_bin not in current_path:
        paths_to_add.append(tool_bin)
    if go_bin not in current_path:
        paths_to_add.append(go_bin)
    if cargo_bin not in current_path:
        paths_to_add.append(cargo_bin)
    if local_bin not in current_path:
        paths_to_add.append(local_bin)
        
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

    print(f"{YELLOW}[!] Found conflicting httpx at {httpx_path}.{RESET}")
    # In a professional tool, we might warn instead of interactively prompting/moving files without flag
    # But keeping behavior for now
    choice = input(f"{BLUE}[?] Do you want to rename it to 'httpx_legacy' to avoid conflicts? (yes/no): {RESET}").strip().lower()
    if choice == "yes":
        try:
            new_path = f"{httpx_path}_legacy"
            subprocess.run(["sudo", "mv", httpx_path, new_path], check=True)
            print(f"{GREEN}[✓] Renamed {httpx_path} to {new_path}.{RESET}")
        except Exception as e:
            print(f"{RED}[✗] Failed to rename httpx: {e}{RESET}")

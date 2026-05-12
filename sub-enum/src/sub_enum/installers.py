import os
import subprocess
import shutil
import platform
import stat
import sys
import json
import urllib.request
import hashlib
from typing import Optional, Tuple

from .config import BLUE, RED, YELLOW, GREEN, RESET
from .utils import check_tool_availability, get_auto_yes, get_logger


logger = get_logger(__name__)

# Define base directories for user-space installation
HOME = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME, ".sub-enum")
BIN_DIR = os.path.join(BASE_DIR, "bin")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")

# Third-party dependency pinning for supply chain security
# These commit hashes should be periodically updated to newer stable versions
# To update: check https://github.com/infosec-au/altdns/commits and verify the commit
ALTDNS_GIT_COMMIT = "d67e19d39ef3bef73acbfc9987c9c2fa8b0a9a9d"  # altdns stable commit
ALTDNS_WORDLIST_SHA256 = "aa89a100db9609de33d67668c0b6a998cd0f4d7f5dd94e32d26fd7804162ff26"  # words.txt SHA256
# To compute the wordlist SHA256: wget -O- https://raw.githubusercontent.com/infosec-au/altdns/master/words.txt | sha256sum



def init_workspace() -> None:
    """Create the user-space workspace directories.

    This is intentionally not executed at import time to avoid side effects during
    unit tests or when the module is imported by other tooling.
    """
    for directory in [BASE_DIR, BIN_DIR, TOOLS_DIR]:
        os.makedirs(directory, exist_ok=True)

def get_latest_go_version() -> Tuple[str, Optional[str]]:
    """Fetch the latest stable Go version and checksum from the official Go releases API.
    
    Returns a tuple of (filename, sha256_checksum).
    Falls back to a known stable version with None checksum if the API call fails.
    """
    # Detect current platform
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map Python platform names to Go platform names
    platform_map = {
        ("linux", "x86_64"): "linux-amd64",
        ("linux", "aarch64"): "linux-arm64",
        ("darwin", "x86_64"): "darwin-amd64",
        ("darwin", "arm64"): "darwin-arm64",
        ("windows", "amd64"): "windows-amd64",
        ("windows", "x86_64"): "windows-amd64",
    }
    
    go_platform = platform_map.get((system, machine))
    if not go_platform:
        # Fallback for unknown platforms
        if system == "linux":
            go_platform = "linux-amd64"
        elif system == "darwin":
            go_platform = "darwin-amd64"
        elif system == "windows":
            go_platform = "windows-amd64"
        else:
            go_platform = "linux-amd64"  # Default fallback
    
    try:
        # Query the official Go releases API
        url = "https://go.dev/dl/?mode=json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            # Find the latest stable release
            for release in data:
                if not release.get("unstable", False):  # Only stable releases
                    # Find a file matching our platform
                    for file_info in release.get("files", []):
                        if go_platform in file_info.get("filename", ""):
                            filename = file_info.get("filename")
                            sha256 = file_info.get("sha256")
                            logger.info(f"[!] Latest stable Go version: {filename}")
                            return (filename, sha256)
            
            # If no suitable release found, fall back
            raise Exception("No suitable Go release found")
            
    except Exception as e:
        # Fallback to a known stable version (without checksum verification)
        logger.warning(f"[!] Could not fetch latest Go version ({e}). Using fallback version.")
        fallback_version = f"go1.23.4.{go_platform}.tar.gz"
        logger.warning(f"[!] Fallback Go version: {fallback_version}")
        return (fallback_version, None)

def verify_sha256(file_path: str, expected_sha256: str) -> bool:
    """Verify that a file's SHA256 matches the expected value."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        computed_sha256 = sha256_hash.hexdigest()
        if computed_sha256 == expected_sha256:
            logger.success("[✓] SHA256 checksum verified.")
            return True
        else:
            logger.error("[✗] SHA256 checksum mismatch!")
            logger.error(f"    Expected: {expected_sha256}")
            logger.error(f"    Got:      {computed_sha256}")
            return False
    except Exception as e:
        logger.error(f"[✗] Error verifying checksum: {e}")
        return False


def install_go():
    """Install Go to the user's home directory to avoid sudo."""
    # We'll use a local go folder
    go_install_dir = os.path.join(BASE_DIR, "go")
    
    # Get the latest stable Go version and its checksum
    default_version, expected_sha256 = get_latest_go_version()
    default_url = f"https://go.dev/dl/{default_version}"

    logger.warning(f"[!] Go is missing. The default version to install is: {default_version}")
    if get_auto_yes():
        user_choice = "yes"
    else:
        logger.info(f"[?] Do you want to install this version locally to {go_install_dir}? (yes/no):")
        user_choice = input().strip().lower()

    if user_choice != "yes":
        logger.error("[✗] Skipping Go installation.")
        return

    logger.warning(f"[!] Installing Go version: {default_version}")

    try:
        # Download
        subprocess.run(["wget", default_url, "-O", "go_tar.gz"], check=True)
        logger.success("[✓] Go downloaded.")

        # Verify checksum if available
        if expected_sha256:
            logger.warning("[!] Verifying checksum...")
            if not verify_sha256("go_tar.gz", expected_sha256):
                logger.error("[✗] Checksum verification failed. Aborting installation to prevent running malicious code.")
                if os.path.exists("go_tar.gz"):
                    os.remove("go_tar.gz")
                return
        else:
            logger.warning("[!] WARNING: Could not verify checksum (API unavailable). Proceeding without verification.")

        # Extract to local dir
        if os.path.exists(go_install_dir):
             shutil.rmtree(go_install_dir)
        
        # Make parent dir if needed (it is BASE_DIR)
        subprocess.run(["tar", "-C", BASE_DIR, "-xzf", "go_tar.gz"], check=True)
        logger.success(f"[✓] Go extracted to {go_install_dir}.")

        if os.path.exists("go_tar.gz"):
            os.remove("go_tar.gz")

        # Set up environment variables for this session
        go_bin = os.path.join(go_install_dir, "bin")
        os.environ["PATH"] = f"{go_bin}:{os.environ['PATH']}"
        os.environ["GOROOT"] = go_install_dir
        
        logger.success("[✓] Go installed locally.")
        logger.warning("Add this to your shell config to make it permanent:")
        logger.info(f'export PATH=$PATH:{go_bin}')
        logger.info(f'export GOROOT={go_install_dir}')
        
    except Exception as e:
        logger.error(f"[✗] Failed to install Go: {e}")

def install_tool_go(tool_name, package_path):
    """Generic function to install Go tools."""
    logger.warning(f"[!] {tool_name} is missing.")
    
    # Check if we have go (system or local)
    if not shutil.which("go"):
        # Check if we just installed it locally
        local_go = os.path.join(BASE_DIR, "go", "bin", "go")
        if os.path.exists(local_go):
             # Update env if not already picked up
             os.environ["PATH"] = f"{os.path.dirname(local_go)}:{os.environ['PATH']}"
        else:
            logger.error("[✗] Go is not installed. Please install Go first.")
            return
    if get_auto_yes():
        user_choice = "yes"
    else:
        logger.info(f"[?] Do you want to install {tool_name} using Go? (yes/no):")
        user_choice = input().strip().lower()
    if user_choice == "yes":
        try:
            logger.success(f"[✓] Installing {tool_name}...")
            # This installs to $GOBIN or $HOME/go/bin usually, which is fine as it is user space.
            subprocess.run(["go", "install", f"{package_path}@latest"], check=True)
            logger.success(f"[✓] {tool_name} installed successfully!")
        except subprocess.CalledProcessError as e:
            logger.error(f"[✗] Error installing {tool_name}: {e}")
    else:
        logger.error(f"[✗] Skipping {tool_name} installation.")

def install_findomain():
    """Install Findomain using apt (requires sudo)."""
    logger.warning("[!] Findomain is missing.")
    if get_auto_yes():
        user_choice = "yes"
    else:
        logger.info("[?] Do you want to install Findomain using apt? (yes/no):")
        user_choice = input().strip().lower()

    if user_choice == "yes":
        logger.success("[✓] Findomain installation requires sudo; this package will not run sudo automatically.")
        logger.warning("Please run: sudo apt update && sudo apt install -y findomain")
    else:
        logger.error("[✗] Skipping Findomain installation.")

def install_altdns():
    logger.warning("[!] altdns is missing.")
    if get_auto_yes():
        user_choice = "yes"
    else:
        logger.info("[?] Do you want to install altdns using pip? (yes/no):")
        user_choice = input().strip().lower()
    if user_choice == "yes":
        try:
            logger.success("[✓] Installing altdns...")
            # Pin to specific commit hash for supply chain security
            altdns_url = f"git+https://github.com/infosec-au/altdns.git@{ALTDNS_GIT_COMMIT}"
            subprocess.run([sys.executable, "-m", "pip", "install", altdns_url], check=True)
            logger.success("[✓] altdns installed successfully!")
        except subprocess.CalledProcessError as e:
            logger.error(f"[✗] Error installing altdns: {e}")
    else:
        logger.error("[✗] Skipping altdns installation.")

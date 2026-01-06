import os
import subprocess
import shutil
import platform
import stat
from .config import BLUE, RED, YELLOW, GREEN, RESET
from .utils import check_tool_availability

# Define base directories for user-space installation
HOME = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME, ".sub-enum")
BIN_DIR = os.path.join(BASE_DIR, "bin")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")

# Ensure directories exist
for directory in [BASE_DIR, BIN_DIR, TOOLS_DIR]:
    os.makedirs(directory, exist_ok=True)

def install_go():
    """Install Go to the user's home directory to avoid sudo."""
    # We'll use a local go folder
    go_install_dir = os.path.join(BASE_DIR, "go")
    
    default_version = "go1.25.5.linux-amd64.tar.gz"
    default_url = f"https://go.dev/dl/{default_version}"

    print(f"\n{YELLOW}[!] Go is missing. The default version to install is: {default_version}{RESET}")
    user_choice = input(f"{BLUE}[?] Do you want to install this version locally to {go_install_dir}? (yes/no): {RESET}").strip().lower()

    if user_choice != "yes":
        print(f"{RED}[✗] Skipping Go installation.{RESET}")
        return

    print(f"{YELLOW}[!] Installing Go version: {default_version}{RESET}")

    try:
        # Download
        subprocess.run(["wget", default_url, "-O", "go_tar.gz"], check=True)
        print(f"{GREEN}[✓] Go downloaded.{RESET}")

        # Extract to local dir
        if os.path.exists(go_install_dir):
             shutil.rmtree(go_install_dir)
        
        # Make parent dir if needed (it is BASE_DIR)
        subprocess.run(["tar", "-C", BASE_DIR, "-xzf", "go_tar.gz"], check=True)
        print(f"{GREEN}[✓] Go extracted to {go_install_dir}.{RESET}")

        if os.path.exists("go_tar.gz"):
            os.remove("go_tar.gz")

        # Set up environment variables for this session
        go_bin = os.path.join(go_install_dir, "bin")
        os.environ["PATH"] = f"{go_bin}:{os.environ['PATH']}"
        os.environ["GOROOT"] = go_install_dir
        
        print(f"{GREEN}[✓] Go installed locally.{RESET}")
        print(f"{YELLOW}Add this to your shell config to make it permanent:{RESET}")
        print(f'export PATH=$PATH:{go_bin}')
        print(f'export GOROOT={go_install_dir}')
        
    except Exception as e:
        print(f"{RED}[✗] Failed to install Go: {e}{RESET}")

def install_tool_go(tool_name, package_path):
    """Generic function to install Go tools."""
    print(f"\n{YELLOW}[!] {tool_name} is missing.{RESET}")
    
    # Check if we have go (system or local)
    if not shutil.which("go"):
        # Check if we just installed it locally
        local_go = os.path.join(BASE_DIR, "go", "bin", "go")
        if os.path.exists(local_go):
             # Update env if not already picked up
             os.environ["PATH"] = f"{os.path.dirname(local_go)}:{os.environ['PATH']}"
        else:
            print(f"{RED}[✗] Go is not installed. Please install Go first.{RESET}")
            return

    user_choice = input(f"{BLUE}[?] Do you want to install {tool_name} using Go? (yes/no): {RESET}").strip().lower()
    if user_choice == "yes":
        try:
            print(f"{GREEN}[✓] Installing {tool_name}...{RESET}")
            # This installs to $GOBIN or $HOME/go/bin usually, which is fine as it is user space.
            subprocess.run(["go", "install", f"{package_path}@latest"], check=True)
            print(f"{GREEN}[✓] {tool_name} installed successfully!{RESET}")
        except subprocess.CalledProcessError as e:
            print(f"{RED}[✗] Error installing {tool_name}: {e}{RESET}")
    else:
        print(f"{RED}[✗] Skipping {tool_name} installation.{RESET}")

def install_findomain():
    """Install Findomain using apt (requires sudo)."""
    print(f"\n{YELLOW}[!] Findomain is missing.{RESET}")
    user_choice = input(f"{BLUE}[?] Do you want to install Findomain using apt? (yes/no): {RESET}").strip().lower()

    if user_choice == "yes":
        try:
            print(f"{GREEN}[✓] Installing Findomain via apt...{RESET}")
            subprocess.run(["sudo", "apt", "update"], check=False) # Update is good practice but might fail if no internet/locked
            subprocess.run(["sudo", "apt", "install", "-y", "findomain"], check=True)
            print(f"{GREEN}[✓] Findomain installed successfully!{RESET}")

        except subprocess.CalledProcessError as e:
            print(f"{RED}[✗] Error installing Findomain: {e}{RESET}")
            print(f"{YELLOW}Try manually running: sudo apt install findomain{RESET}")
    else:
        print(f"{RED}[✗] Skipping Findomain installation.{RESET}")

def install_altdns():
    print(f"\n{YELLOW}[!] altdns is missing.{RESET}")
    user_choice = input(f"{BLUE}[?] Do you want to install altdns using pip? (yes/no): {RESET}").strip().lower()
    if user_choice == "yes":
        try:
            print(f"{GREEN}[✓] Installing altdns...{RESET}")
            # Ensure --user is passed if not in venv, but pip sometimes handles it.
            # safe approach:
            subprocess.run(["pip3", "install", "git+https://github.com/infosec-au/altdns.git", "--break-system-packages"], check=True)
            print(f"{GREEN}[✓] altdns installed successfully!{RESET}")
        except subprocess.CalledProcessError as e:
            print(f"{RED}[✗] Error installing altdns: {e}{RESET}")
    else:
        print(f"{RED}[✗] Skipping altdns installation.{RESET}")

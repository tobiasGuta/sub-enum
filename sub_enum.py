#!/usr/bin/env python3

import subprocess
import os
import argparse
import shutil
import tempfile
import re
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import time
import sys

ART = '''
\033[96m
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢶⣦⣤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠈⠹⡆⢀⣤⣤⡀⢠⣤⢠⣤⣿⡤⣴⡆⠀⣴⠀⠀⠀⢠⣄⠀⢠⡄⠀⠀⠀⣤⣄⣿⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠰⠆⠀⣷⢸⣧⣀⡀⢸⢹⡆⠀⢸⡇⠠⣧⢤⣿⠀⠀⠀⢸⡟⣦⣸⡇⡞⡙⢣⡀⢠⡇⠀⢿⠋⠛⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⣠⠟⢸⣇⣀⡀⣿⠉⢻⡀⢸⡇⠀⣿⠀⣿⠀⠀⠀⣸⡇⠘⢿⡏⢇⣁⡼⠃⣼⠃⠀⣼⡓⠒⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⡿⠒⠋⠁⠀⠈⠉⠉⠁⠉⠀⠀⠀⠀⠉⠀⠉⠀⠉⠀⠀⠀⠉⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠛⠓⠲⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣠⣴⣶⣾⣿⣿⣾⣷⣦⣤⣿⣶⣶⣤⣄⣀⢤⡀⠀⠀⠀⠀⢰⣴⣶⣷⣴⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣄⣀⣀⣀⣤⣤⣶⣶⣶⣦⣤⠤
⠠⠔⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠀⠀⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⢀⣀⣤⣾⣿⣿⣿⣿⣿⣿⣿⠟⠛⠛⠂⠀⠀
⠀⠀⠀⠘⠋⠉⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣤⡀⢻⣿⣿⣿⣿⡏⠀⠀⠀⢀⣤⣾⣿⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠘⠀⡿⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⣿⣿⣿⣿⣤⣴⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠛⠟⠋⣿⣿⡿⠋⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⠋⠙⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡿⠀⠸⠋⣿⣿⣿⠛⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠻⣿⣿⣿⠋⠛⠇⠀⠀⢹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠃⠀⠀⢀⣿⣿⠁⠀⠈⢻⣿⣿⣿⣿⣿⡿⠋⠈⣿⣿⡏⠃⠀⠘⣿⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡏⠀⠀⠀⠈⣿⣿⣿⣿⣿⠀⠀⠀⠸⣿⣇⠀⠀⠀⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀⠀⣼⣿⣿⣿⣿⣿⡄⠀⠀⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠁⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⠆⠀⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣇⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⢠⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣦⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⠋⠉⠉⠛⠉⠋⠻⣿⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⣤⣾⣿⣿⣿⣿⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿⣿⣿⡇⠙⠀⠀⠀⢸⠋⣿⣿⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⢿⣷⡢⡀⠀⠀⢀⣰⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⠀⠁⠁⠀⠀⠀⠀⠉⢠⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡄⠀⠀⠀⠀⠀⠀⠀⣾⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣇⠀⠀⠀⠀⠀⠀⢸⣿⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⡿⠀⠀⠀⠀⠀⠀⠘⢿⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠃⠀⠀⠀⠀⠀⠀⠀⠈⠻⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀3.2⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
\033[0m
'''

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

REQUIRED_TOOLS_BASIC = ["go", "subfinder", "assetfinder", "findomain", "httpx", "dnsx"]
REQUIRED_TOOLS_FULL = ["sublist3r", "chaos"]
REQUIRED_TOOLS_PERM = ["altdns"]

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
    # Update PATH to include common Go and Rust bin directories for the current process
    home = os.path.expanduser("~")
    go_bin = os.path.join(home, "go", "bin")
    cargo_bin = os.path.join(home, ".cargo", "bin")
    
    current_path = os.environ.get("PATH", "")
    
    # Prepend paths so local tools take precedence over system tools (fixes httpx conflict)
    if go_bin not in current_path:
        os.environ["PATH"] = f"{go_bin}:{current_path}"
        current_path = os.environ["PATH"] # Update for next check
        
    if cargo_bin not in current_path:
        os.environ["PATH"] = f"{cargo_bin}:{current_path}"
        
    return shutil.which(tool)

def validate_domain(domain):
    """Validate and clean the domain input."""
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.rstrip('/')
    
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not re.match(pattern, domain):
        return None
    return domain

def install_go():
    default_version = "go1.23.6.linux-amd64.tar.gz"
    default_url = f"https://go.dev/dl/{default_version}"

    print(f"\n{YELLOW}[!] Go is missing. The default version to install is: {default_version}{RESET}")
    user_choice = input(f"{BLUE}[?] Do you want to install this version? (yes/no): {RESET}").strip().lower()

    if user_choice != "yes":
        custom_url = input(f"{BLUE}[?] Enter the download URL for a newer Go version: {RESET}").strip()
        if custom_url:
            default_url = custom_url
            default_version = custom_url.split("/")[-1]
        else:
            print(f"{RED}[✗] No valid URL provided. Skipping Go installation.{RESET}")
            return

    print(f"{YELLOW}[!] Installing Go version: {default_version}{RESET}")

    try:
        subprocess.run(["wget", default_url], check=True)
        print(f"{GREEN}[✓] Go downloaded.{RESET}")

        subprocess.run(["sudo", "tar", "-C", "/usr/local", "-xzf", default_version], check=True)
        print(f"{GREEN}[✓] Go extracted to /usr/local.{RESET}")

        os.remove(default_version)
        print(f"{GREEN}[✓] Installation file removed.{RESET}")

        print(f"\n{YELLOW}[!] IMPORTANT: To complete the installation, add Go to your PATH.{RESET}")
        print("    Run the following commands (or add them to your shell config like ~/.zshrc or ~/.bashrc):")
        print('    export PATH=$PATH:/usr/local/go/bin')
        print('    export PATH=$PATH:$HOME/go/bin')
        
    except Exception as e:
        print(f"{RED}[✗] Failed to install Go: {e}{RESET}")

def install_tool_go(tool_name, package_path):
    """Generic function to install Go tools."""
    print(f"\n{YELLOW}[!] {tool_name} is missing.{RESET}")
    
    if not check_tool_availability("go"):
        print(f"{RED}[✗] Go is not installed. Please install Go first.{RESET}")
        return

    user_choice = input(f"{BLUE}[?] Do you want to install {tool_name} using Go? (yes/no): {RESET}").strip().lower()
    if user_choice == "yes":
        try:
            print(f"{GREEN}[✓] Installing {tool_name}...{RESET}")
            subprocess.run(["go", "install", f"{package_path}@latest"], check=True)
            print(f"{GREEN}[✓] {tool_name} installed successfully!{RESET}")
        except subprocess.CalledProcessError as e:
            print(f"{RED}[✗] Error installing {tool_name}: {e}{RESET}")
    else:
        print(f"{RED}[✗] Skipping {tool_name} installation.{RESET}")

def install_findomain():
    print(f"\n{YELLOW}[!] Findomain is missing.{RESET}")
    user_choice = input(f"{BLUE}[?] Do you want to install Findomain? (yes/no): {RESET}").strip().lower()

    if user_choice == "yes":
        try:
            print(f"{GREEN}[✓] Installing dependencies...{RESET}")
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "git", "curl", "build-essential"], check=True)

            if not check_tool_availability("rustc"):
                print(f"{YELLOW}Rust not found, installing Rust...{RESET}")
                subprocess.run("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh", shell=True, check=True)
                print(f"{YELLOW}[!] Rust installed. You may need to restart your shell or source ~/.cargo/env{RESET}")
            
            desktop_path = os.path.expanduser("~/Desktop")
            os.chdir(desktop_path)
            
            if not os.path.exists("findomain"):
                print(f"{GREEN}[✓] Cloning Findomain repository...{RESET}")
                subprocess.run(["git", "clone", "https://github.com/findomain/findomain.git"], check=True)

            os.chdir("findomain")
            print(f"{GREEN}[✓] Building Findomain...{RESET}")
            subprocess.run("cargo build --release", shell=True, check=True)

            print(f"{GREEN}[✓] Copying Findomain binary to /usr/bin...{RESET}")
            subprocess.run(["sudo", "cp", "target/release/findomain", "/usr/bin/"], check=True)
            print(f"{GREEN}[✓] Findomain installation completed successfully!{RESET}")

        except subprocess.CalledProcessError as e:
            print(f"{RED}[✗] Error installing Findomain: {e}{RESET}")
    else:
        print(f"{RED}[✗] Skipping Findomain installation.{RESET}")

def install_sublist3r():
    print(f"\n{YELLOW}[!] sublist3r is missing.{RESET}")
    user_choice = input(f"{BLUE}[?] Do you want to install using git? (yes/no): {RESET}").strip().lower()

    if user_choice == "yes":
        try:
            subprocess.run(["sudo", "apt", "install", "git", "-y"], check=True)
            
            os.chdir(os.path.expanduser("~/Desktop"))
            if not os.path.exists("Sublist3r"):
                subprocess.run(["git", "clone", "https://github.com/aboul3la/Sublist3r.git"], check=True)
            
            os.chdir("Sublist3r")
            print(f"{GREEN}[✓] Installing dependencies...{RESET}")
            subprocess.run(["sudo", "pip3", "install", "-r", "requirements.txt", "--break-system-packages"], check=True)

            if not os.path.isfile("./sublist3r.py"):
                subprocess.run(["sudo", "python3", "setup.py", "install"], check=True)

            subprocess.run(["sudo", "ln", "-sf", os.path.abspath("sublist3r.py"), "/usr/local/bin/sublist3r"], check=True)
            subprocess.run(["sudo", "chmod", "+x", "/usr/local/bin/sublist3r"], check=True)
            
            print(f"{GREEN}[✓] sublist3r installation completed successfully!{RESET}")
        except subprocess.CalledProcessError as e:
            print(f"{RED}[✗] Error installing sublist3r: {e}{RESET}")

def install_altdns():
    print(f"\n{YELLOW}[!] altdns is missing.{RESET}")
    user_choice = input(f"{BLUE}[?] Do you want to install altdns using pip? (yes/no): {RESET}").strip().lower()
    if user_choice == "yes":
        try:
            print(f"{GREEN}[✓] Installing altdns...{RESET}")
            # Install directly from GitHub to ensure we get the right version/tools
            subprocess.run(["pip3", "install", "git+https://github.com/infosec-au/altdns.git", "--break-system-packages"], check=True)
            print(f"{GREEN}[✓] altdns installed successfully!{RESET}")
        except subprocess.CalledProcessError as e:
            print(f"{RED}[✗] Error installing altdns: {e}{RESET}")
    else:
        print(f"{RED}[✗] Skipping altdns installation.{RESET}")

def run_tool(command, tool_name, timeout=None):
    try:
        print(f"{BLUE}[*] Running {tool_name}...{RESET}")
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return set(result.stdout.strip().splitlines())
        else:
            if result.stdout:
                 return set(result.stdout.strip().splitlines())
            print(f"{YELLOW}[!] {tool_name} warning/error: {result.stderr.strip()}{RESET}")
    except subprocess.TimeoutExpired:
        print(f"{RED}[✗] {tool_name} timed out after {timeout} seconds.{RESET}")
    except Exception as e:
        print(f"{RED}[✗] Exception running {tool_name}: {e}{RESET}")
    return set()

def run_dnsx(subdomains):
    """Resolve subdomains using dnsx."""
    if not subdomains:
        return set()
    
    print(f"{BLUE}[*] Resolving {len(subdomains)} subdomains with dnsx...{RESET}")
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write("\n".join(subdomains))
            temp_path = temp.name

        command_simple = ["dnsx", "-l", temp_path, "-silent"]
        result_simple = subprocess.run(command_simple, capture_output=True, text=True)
        
        resolved = set(result_simple.stdout.strip().splitlines())
        print(f"{GREEN}[✓] dnsx resolved {len(resolved)} valid subdomains.{RESET}")
        return resolved
        
    except Exception as e:
        print(f"{RED}[✗] Error running dnsx: {e}{RESET}")
        return set()
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

def run_altdns(domain, subdomains, timeout=None):
    """Generate permutations using altdns."""
    if not subdomains:
        return set()
    
    print(f"{BLUE}[*] Generating permutations for {len(subdomains)} subdomains...{RESET}")
    
    wordlist_path = "words.txt"
    if not os.path.exists(wordlist_path):
        print(f"{YELLOW}[!] words.txt not found. Downloading default wordlist...{RESET}")
        try:
            subprocess.run(["wget", "https://raw.githubusercontent.com/infosec-au/altdns/master/words.txt", "-O", wordlist_path], check=True)
        except:
            print(f"{RED}[✗] Failed to download wordlist. Skipping permutations.{RESET}")
            return set()

    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_subs:
            temp_subs.write("\n".join(subdomains))
            temp_subs_path = temp_subs.name
            
        output_perms = "altdns_output.txt"
        
        command = ["altdns", "-i", temp_subs_path, "-o", "data_output", "-w", wordlist_path, "-r", "-s", output_perms]
        
        print(f"{BLUE}[*] Running altdns (this may take a while)...{RESET}")
        
        try:
            subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
             print(f"{YELLOW}[!] altdns timed out after {timeout} seconds. Checking for partial results...{RESET}")

        perms = set()
        if os.path.exists(output_perms):
            with open(output_perms, "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) >= 1:
                        perms.add(parts[0])
            os.remove(output_perms)
            
        if os.path.exists("data_output"):
            os.remove("data_output")
            
        print(f"{GREEN}[✓] altdns found {len(perms)} new permutations.{RESET}")
        return perms

    except Exception as e:
        print(f"{RED}[✗] Error running altdns: {e}{RESET}")
        return set()
    finally:
        if 'temp_subs_path' in locals() and os.path.exists(temp_subs_path):
            os.remove(temp_subs_path)

def filter_httpx(subdomains, output_file, info_output_file, timeout=None):
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write("\n".join(subdomains))
            temp_path = temp.name

        print(f"{BLUE}[*] Running httpx on {len(subdomains)} subdomains...{RESET}")
        
        httpx_command = [
            "httpx", "-ip", "-cdn", "-title", "-status-code", "-tech-detect", "-silent", "-l", temp_path
        ]
        
        try:
            httpx_result = subprocess.run(httpx_command, capture_output=True, text=True, timeout=timeout)
            
            if httpx_result.returncode != 0:
                print(f"{RED}[✗] httpx failed with exit code {httpx_result.returncode}{RESET}")
                if httpx_result.stderr:
                    print(f"{YELLOW}Stderr: {httpx_result.stderr.strip()}{RESET}")
            
            if httpx_result.stdout:
                with open(info_output_file, "w") as f:
                    f.write(httpx_result.stdout)
                print(f"{GREEN}[✓] Saved httpx info to {info_output_file}{RESET}")

            live_subdomains = set(httpx_result.stdout.strip().splitlines())
            
            if not live_subdomains and httpx_result.returncode == 0:
                 print(f"{YELLOW}[!] httpx returned 0 results. This might be due to network issues or no live domains.{RESET}")

        except subprocess.TimeoutExpired:
            print(f"{RED}[✗] httpx timed out after {timeout} seconds.{RESET}")
            return set()
        
        urls = set()
        for line in live_subdomains:
            match = re.search(r'(https?://\S+)', line)
            if match:
                urls.add(match.group(1))

        with open(output_file, "w") as file:
            file.write("\n".join(sorted(urls)))

        return live_subdomains

    except Exception as e:
        print(f"{RED}[✗] Error in filtering live subdomains: {e}{RESET}")
        return set()
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

def remove_conflicting_httpx():
    """Rename system httpx to avoid conflicts with ProjectDiscovery httpx."""
    httpx_path = shutil.which("httpx")
    if not httpx_path:
        return

    if "go/bin" in httpx_path:
        return

    print(f"{YELLOW}[!] Found conflicting httpx at {httpx_path}.{RESET}")
    choice = input(f"{BLUE}[?] Do you want to rename it to 'httpx_legacy' to avoid conflicts? (yes/no): {RESET}").strip().lower()
    if choice == "yes":
        try:
            new_path = f"{httpx_path}_legacy"
            subprocess.run(["sudo", "mv", httpx_path, new_path], check=True)
            print(f"{GREEN}[✓] Renamed {httpx_path} to {new_path}.{RESET}")
        except Exception as e:
            print(f"{RED}[✗] Failed to rename httpx: {e}{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Automated Subdomain Discovery Tool (Community Edition)", 
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--domain", required=True, help="Target domain (e.g., example.com)")
    parser.add_argument("-o", "--output", default="all_subdomains.txt", help="Output file for all discovered subdomains")
    parser.add_argument("-l", "--live-output", default="live_subdomains.txt", help="Output file for live subdomains")
    parser.add_argument("--full", action="store_true", help="Use all available tools (including sublist3r, chaos)")
    parser.add_argument("--permutations", action="store_true", help="Run permutation scanning using altdns")
    parser.add_argument("--config", default=".env", help="Path to configuration file (default: .env)")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout for each tool in seconds (default: 600)")
    
    args = parser.parse_args()

    print(ART)
    
    load_env(args.config)

    domain = validate_domain(args.domain)
    if not domain:
        print(f"{RED}[✗] Invalid domain format: {args.domain}{RESET}")
        return

    output_dir = domain
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"{BLUE}[*] Created output directory: {output_dir}{RESET}")
        except OSError as e:
            print(f"{RED}[✗] Failed to create directory {output_dir}: {e}{RESET}")
            return

    if os.path.dirname(args.output):
        output_file = args.output
    else:
        output_file = os.path.join(output_dir, args.output)

    if os.path.dirname(args.live_output):
        live_output_file = args.live_output
    else:
        live_output_file = os.path.join(output_dir, args.live_output)
        
    info_output_file = os.path.join(output_dir, "live_subdomains_info.txt")

    tools_to_check = REQUIRED_TOOLS_BASIC.copy()
    if args.full:
        tools_to_check.extend(REQUIRED_TOOLS_FULL)
        print(f"{RED}[ WARNING] Full mode enabled. Ensure API keys are set for Chaos.{RESET}")
    
    if args.permutations:
        tools_to_check.extend(REQUIRED_TOOLS_PERM)

    missing_tools = []
    for tool in tools_to_check:
        if not check_tool_availability(tool):
            missing_tools.append(tool)

    if "httpx" not in missing_tools:
        try:
            # ProjectDiscovery httpx supports -version, python-httpx does not
            subprocess.run(["httpx", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print(f"{YELLOW}[!] Detected incorrect httpx version (likely python-httpx).{RESET}")
            remove_conflicting_httpx()
            missing_tools.append("httpx")
    
    if missing_tools:
        print(f"{YELLOW}[!] Missing tools: {', '.join(missing_tools)}{RESET}")
        
        if "go" in missing_tools:
            install_go()
            if not check_tool_availability("go"):
                print(f"{RED}[✗] Go is still missing. Cannot proceed with Go-based tools.{RESET}")
                return

        if "assetfinder" in missing_tools:
            install_tool_go("assetfinder", "github.com/tomnomnom/assetfinder")
        
        if "subfinder" in missing_tools:
            install_tool_go("subfinder", "github.com/projectdiscovery/subfinder/v2/cmd/subfinder")
            
        if "httpx" in missing_tools:
            install_tool_go("httpx", "github.com/projectdiscovery/httpx/cmd/httpx")
            
        if "dnsx" in missing_tools:
            install_tool_go("dnsx", "github.com/projectdiscovery/dnsx/cmd/dnsx")
            
        if "chaos" in missing_tools and args.full:
            install_tool_go("chaos", "github.com/projectdiscovery/chaos-client/cmd/chaos")

        if "findomain" in missing_tools:
            install_findomain()

        if "sublist3r" in missing_tools and args.full:
            install_sublist3r()
            
        if "altdns" in missing_tools and args.permutations:
            install_altdns()

    commands = {
        "Subfinder": ["subfinder", "-silent", "-d", domain],
        "Assetfinder": ["assetfinder", "--subs-only", domain],
        "Findomain": ["findomain", "-t", domain]
    }
    
    if args.full:
        commands["Sublist3r"] = ["sublist3r", "-d", domain, "-o", "/dev/stdout"]
        commands["Chaos"] = ["chaos", "-d", domain]

    print(f"{BLUE}[*] Discovering subdomains for {domain}...{RESET}")
    
    all_subdomains = set()
    with ThreadPoolExecutor() as executor:
        future_to_tool = {executor.submit(run_tool, cmd, name, args.timeout): name for name, cmd in commands.items()}
        for future in concurrent.futures.as_completed(future_to_tool):
            tool_name = future_to_tool[future]
            try:
                results = future.result()
                print(f"{GREEN}[+] {tool_name} found {len(results)} subdomains{RESET}")
                all_subdomains.update(results)
            except Exception as exc:
                print(f"{RED}[✗] {tool_name} generated an exception: {exc}{RESET}")

    print(f"{BLUE}[*] Verifying subdomains with dnsx...{RESET}")
    resolved_subdomains = run_dnsx(all_subdomains)
    
    if args.permutations:
        perm_subdomains = run_altdns(domain, resolved_subdomains, args.timeout)
        resolved_subdomains.update(perm_subdomains)

    with open(output_file, "w") as file:
        file.write("\n".join(sorted(resolved_subdomains)) + "\n")
    print(f"{GREEN}[✓] Saved {len(resolved_subdomains)} resolved subdomains to {output_file}{RESET}")

    print(f"{BLUE}[*] Checking for live subdomains...{RESET}")
    live_subdomains = filter_httpx(resolved_subdomains, live_output_file, info_output_file, args.timeout)
    print(f"{GREEN}[✓] Saved {len(live_subdomains)} live subdomains to {live_output_file}{RESET}")

if __name__ == "__main__":
    main()

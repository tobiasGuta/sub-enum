#!/usr/bin/env python3

import subprocess
import os
import argparse
from concurrent.futures import ThreadPoolExecutor
import re

# List of required tools
required_tools = ["go", "subfinder", "assetfinder", "sublist3r", "findomain", "httpx"]

art = '''
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
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀2.0⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
'''

print(art)

# Function to check if a tool is installed
def check_tool_availability(tool):
    result = subprocess.run(["which", tool], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None

# Function to install Go if missing
def install_go():
    default_version = "go1.23.6.linux-amd64.tar.gz"  # Check for the latest version before using this
    default_url = f"https://go.dev/dl/{default_version}"

    print(f"\n[!] Go is missing. The default version to install is: {default_version}")
    user_choice = input("[?] Do you want to install this version? (yes/no): ").strip().lower()

    if user_choice != "yes":
        custom_url = input("[?] Enter the download URL for a newer Go version: ").strip()
        if custom_url:
            default_url = custom_url
            default_version = custom_url.split("/")[-1]
        else:
            print("[✗] No valid URL provided. Skipping Go installation.")
            return

    print(f"[!] Installing Go version: {default_version}")

    try:
        # Download Go
        subprocess.run(["wget", default_url], check=True)
        print("[✓] Go downloaded.")

        # Extract Go
        subprocess.run(["sudo", "tar", "-C", "/usr/local", "-xzf", default_version], check=True)
        print("[✓] Go extracted to /usr/local.")

        # Remove tar file
        os.remove(default_version)
        print("[✓] Installation file removed.")

        # Add Go to PATH
        with open(os.path.expanduser("~/.zshrc"), "a") as file:
            file.write('\nexport PATH=$PATH:/usr/local/go/bin\n')
            file.write('\nexport PATH=$PATH:$HOME/go/bin\n')
        print("[✓] Go path added to ~/.zshrc.")

        # Apply changes
        print("[!] Restart your terminal or run `source ~/.zshrc` to apply the changes.")
        print("[✓] Go installation completed successfully!")

    except Exception as e:
        print(f"[✗] Failed to install Go: {e}")

def install_sublist3r():
    print(f"\n[!] sublist3r is missing.")
    user_choice = input("[?] Do you want to install using git? (yes/no): ").strip().lower()

    if user_choice == "yes":
        # Install git if not already installed
        try:
            subprocess.run(["sudo", "apt", "install", "git", "-y"], check=True)
            print("[✓] Git installed successfully.")

            # Change to the Desktop directory
            os.chdir(os.path.expanduser("~/Desktop"))
            print(f"[✓] Changed directory to {os.getcwd()}")

            # Clone the sublist3r repository
            subprocess.run(["git", "clone", "https://github.com/aboul3la/Sublist3r.git"], check=True)
            print("[✓] sublist3r cloned from GitHub.")

            # Change to the sublist3r directory
            os.chdir(os.path.expanduser("~/Desktop/Sublist3r"))
            print(f"[✓] Changed directory to {os.getcwd()}")

            # Install the required dependencies
            subprocess.run(["sudo", "pip3", "install", "-r", "requirements.txt", "--break-system-packages"], check=True)
            print("[✓] Dependencies installed successfully.")

            # Check if the sublist3r executable exists or needs to be built
            if not os.path.isfile("./sublist3r.py"):
                print("[!] sublist3r executable not found. Attempting to build it.")
                subprocess.run(["sudo", "python3", "setup.py", "install"], check=True)
                print("[✓] sublist3r built and installed successfully.")
            else:
                print("[✓] sublist3r executable found.")

            # Move the executable to /usr/local/bin and set permissions
            subprocess.run(["sudo", "mv", "subbrute", "/usr/local/bin/"], check=True)
            subprocess.run(["sudo", "mv", "./sublist3r.py", "/usr/local/bin/sublist3r"], check=True)
            subprocess.run(["sudo", "chmod", "+x", "/usr/local/bin/sublist3r"], check=True)

            print("[✓] sublist3r installation completed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"[✗] Error installing sublist3r: {e}")
    else:
        print("[✗] Skipping sublist3r installation.")
        return

def install_assetfinder():
    print(f"\n[!] assetfinder is missing.")
    
    # Check if Go is installed
    try:
        subprocess.run(["go", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[✓] Go is already installed.")
    except subprocess.CalledProcessError:
        print("[✗] Go is not installed.")
        user_choice = input("[?] Do you want to install Go? (yes/no): ").strip().lower()
        if user_choice == "yes":
            install_go()  # Assuming you have already defined the install_go function
        else:
            print("[✗] Skipping assetfinder installation as Go is required.")
            return

    # Install assetfinder using Go
    try:
        print("[!] Installing assetfinder using Go...")
        subprocess.run(["go", "install", "github.com/tomnomnom/assetfinder@latest"], check=True)
        print("[✓] assetfinder installation completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"[✗] Error installing assetfinder: {e}")  

def install_subfinder():
    print(f"\n[!] subfinder is missing.")
    user_choice = input("[?] Do you want to install using Go? (yes/no): ").strip().lower()

    if user_choice == "yes":
        try:
            # Install subfinder using Go
            print("[✓] Installing Subfinder...")
            subprocess.run(["go", "install", "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"], check=True)
            print("[✓] subfinder installed successfully!")

        except subprocess.CalledProcessError as e:
            print(f"[✗] Error installing subfinder: {e}")
    else:
        print("[✗] Skipping subfinder installation.")
        return

def install_findomain():
    print(f"\n[!] Findomain is missing.")
    user_choice = input("[?] Do you want to install Findomain? (yes/no): ").strip().lower()

    if user_choice == "yes":
        try:
            # Install dependencies
            print("[✓] Installing dependencies...")
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "git", "curl", "build-essential"], check=True)
            print("[✓] Dependencies installed.")

            # Install Rust (if not already installed)
            print("[✓] Checking for Rust installation...")
            rust_check = subprocess.run(["which", "rustc"], capture_output=True, text=True)

            if rust_check.returncode != 0:  # Rust is not installed
                print("Rust not found, installing Rust...")
                subprocess.run("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh", shell=True, check=True)

                # Ensure Cargo is in the PATH by adding it to ~/.zshrc
                with open(os.path.expanduser("~/.zshrc"), "a") as file:
                    file.write('\n# Adding Cargo to PATH\n')
                    file.write('. "$HOME/.cargo/env"\n')
                print("[✓] Rust installed successfully.")
                print("[✓] Cargo added to ~/.zshrc.")
                
                # Apply the changes immediately by sourcing the ~/.zshrc file
                subprocess.run("source ~/.zshrc", shell=True, check=True)
                
            else:
                print("[✓] Rust is already installed.")

            # Change to Desktop directory
            desktop_path = os.path.expanduser("~/Desktop")
            os.chdir(desktop_path)
            print(f"[✓] Changed directory to {os.getcwd()}")

            # Clone the Findomain repository
            print("[✓] Cloning Findomain repository...")
            subprocess.run(["git", "clone", "https://github.com/findomain/findomain.git"], check=True)

            # Navigate to the Findomain directory
            os.chdir("findomain")
            print(f"[✓] Changed directory to {os.getcwd()}")

            # Build Findomain - Update subprocess call to use shell=True
            print("[✓] Building Findomain...")
            subprocess.run("cargo build --release", shell=True, check=True)

            # Copy the binary to /usr/bin
            print("[✓] Copying Findomain binary to /usr/bin...")
            subprocess.run(["sudo", "cp", "target/release/findomain", "/usr/bin/"], check=True)
            print("[✓] Findomain installation completed successfully!")

        except subprocess.CalledProcessError as e:
            print(f"[✗] Error installing Findomain: {e}")
    else:
        print("[✗] Skipping Findomain installation.")
        return


def install_httpx():
    print(f"\n[!] httpx is missing.")
    user_choice = input("[?] Do you want to install httpx using Go? (yes/no): ").strip().lower()

    if user_choice == "yes":
        try:
            # Install httpx using Go
            print("[✓] Installing httpx...")
            subprocess.run(["go", "install", "github.com/projectdiscovery/httpx/cmd/httpx@latest"], check=True)
            print("[✓] httpx installed successfully!")

        except subprocess.CalledProcessError as e:
            print(f"[✗] Error installing httpx: {e}")
    else:
        print("[✗] Skipping httpx installation.")
        return

# Function to check which subdomains are live using dnsx and httpx
def filter_httpx(subdomains, output_file):
    try:
        # Write the subdomains to a temporary file
        with open("temp_subdomains.txt", "w") as file:
            file.write("\n".join(subdomains))

        # Run httpx to check live subdomains with status codes and technology detection
        httpx_command = [
            "httpx", "-ip", "-cdn", "-title", "-status-code", "-tech-detect", "-silent", "-l", "temp_subdomains.txt"
        ]
        httpx_result = subprocess.run(httpx_command, capture_output=True, text=True)
        
        if httpx_result.returncode != 0:
            print(f"[✗] httpx error: {httpx_result.stderr}")
            return set()

        live_subdomains = set(httpx_result.stdout.strip().splitlines())

        # Extract only URLs and write to the specified output file
        urls = set()
        for line in live_subdomains:
            match = re.match(r'^(https?://[^ ]+)', line)
            if match:
                urls.add(match.group(1))

        # Write the live URLs to the provided output file
        with open(output_file, "w") as file:
            file.write("\n".join(urls))

        return live_subdomains

    except Exception as e:
        print(f"[✗] Error in filtering live subdomains: {e}")
        return set()

    finally:
        # Clean up the temporary file
        os.remove("temp_subdomains.txt")

# Function to run subdomain discovery tools in parallel
def run_subdomain_discovery(domain):
    tools = {
        "Subfinder": ["subfinder", "-silent", "-d", domain],
        "Assetfinder": ["assetfinder", "--subs-only", domain],
        "Sublist3r": ["sublist3r", "-d", domain, "-o", "/dev/stdout"],
        "Findomain": ["findomain", "-t", domain]
    }

    all_subdomains = set()

    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda item: run_tool(item[1], item[0]), tools.items())

    for result in results:
        if result:
            all_subdomains.update(result)

    return all_subdomains

# Function to run a tool and return its output as a set
def run_tool(command, tool_name):
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return set(result.stdout.strip().splitlines())
        else:
            print(f"[✗] {tool_name} error: {result.stderr}")
    except Exception as e:
        print(f"[✗] Exception running {tool_name}: {e}")
    return set()

# Check each tool and print its status
missing_tools = []

for tool in required_tools:
    tool_path = check_tool_availability(tool)
    if tool_path:
        print(f"[✓] {tool} is installed at {tool_path}.")
        
        # Check if httpx is specifically in /usr/bin/httpx and remove it using sudo
        if tool == "httpx" and tool_path == "/usr/bin/httpx":
            print("[!] Removing httpx from /usr/bin/httpx with sudo...")
            try:
                subprocess.run(["sudo", "rm", "-f", "/usr/bin/httpx"], check=True)
                print("[✓] httpx has been removed.")
            except subprocess.CalledProcessError as e:
                print(f"[✗] Failed to remove httpx: {e}")
    else:
        print(f"[✗] {tool} is missing.")
        missing_tools.append(tool)

# If Go is missing, ask user before installing
if "go" in missing_tools:
    install_go()
    missing_tools.remove("go")  # Remove from missing tools list after installation

if "sublist3r" in missing_tools:
    install_sublist3r()
    missing_tools.remove("sublist3r") 

if "assetfinder" in missing_tools:
    install_assetfinder()
    missing_tools.remove("assetfinder")

if "subfinder" in missing_tools:
    install_subfinder()
    missing_tools.remove("subfinder")

if "findomain" in missing_tools:
    install_findomain()
    missing_tools.remove("findomain")

if "httpx" in missing_tools:
    install_httpx()
    missing_tools.remove("httpx")

# Main function with command-line argument handling
def main():
    # Set up argparse to handle command-line arguments
    parser = argparse.ArgumentParser(description="Automated Subdomain Discovery Tool", 
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--domain", required=True, help="Target domain (e.g., example.com)")
    parser.add_argument("-o", "--output", default="all_subdomains.txt", help="Output file for all discovered subdomains (default: all_subdomains.txt)")
    parser.add_argument("-l", "--live-output", default="live_subdomains.txt", help="Output file for live subdomains (default: live_subdomains.txt)")
    parser.add_argument("-u", "--output_file", required=True, help="Path to the output file to store live URLs.")

    # Parsing the arguments
    args = parser.parse_args()

    if missing_tools:
        print(f"\n[!] Missing tools: {', '.join(missing_tools)}")
    else:
        print("\n[✓] All required tools are installed.")

    print(f"[*] Discovering subdomains for {args.domain}...")
    subdomains = run_subdomain_discovery(args.domain)

    # Save all discovered subdomains
    with open(args.output, "w") as file:
        file.write("\n".join(sorted(subdomains)) + "\n")

    print(f"[✓] Saved {len(subdomains)} subdomains to {args.output}")

    print("[*] Checking for live subdomains...")
    # Use args.output_file instead of output_file
    live_subdomains = filter_httpx(subdomains, args.output_file)

    # Save live subdomains
    with open(args.live_output, "w") as file:
        file.write("\n".join(sorted(live_subdomains)) + "\n")

    print(f"[✓] Saved {len(live_subdomains)} live subdomains to {args.live_output}")

if __name__ == "__main__":
    main()

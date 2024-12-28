import subprocess
import requests
import re
import shutil
import os
import time
import itertools
import sys
from typing import Set
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants and Configurations
# Define file paths for temporary and output files
TEMP_SUBDOMAINS_FILE = "temp_subdomains.txt"
OUTPUT_FILE = "all_subdomains.txt"

# Characters for the spinner animation
SPINNER_CHARS = ["|", "/", "-", "\\"]

# ASCII art for visual flair in the console output
ART = """
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
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""


def show_spinner(message: str, task_callable):
    """
    Displays a spinner animation while waiting for a task to complete.

    Args:
        message (str): Message to display alongside the spinner.
        task_callable (callable): A callable function that evaluates to True when the task is complete.
    """
    sys.stdout.write(f"{message} ")
    sys.stdout.flush()
    spinner = itertools.cycle(SPINNER_CHARS)
    while not task_callable():
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write("\b")
    print("✅")


def check_tool_availability(tool_name: str) -> bool:
    """
    Checks if a required tool is available on the system.

    Args:
        tool_name (str): Name of the tool to check.

    Returns:
        bool: True if the tool is available, False otherwise.
    """
    if shutil.which(tool_name) is None:
        print(f"[✗] {tool_name} not found. Please install it to continue.")
        return False
    print(f"[✓] {tool_name} is available.")
    return True


def run_tool(command: list, tool_name: str) -> Set[str]:
    """
    Executes an external command-line tool and processes its output.

    Args:
        command (list): List containing the command and its arguments.
        tool_name (str): Name of the tool being executed.

    Returns:
        Set[str]: A set of extracted subdomains from the tool's output.
    """
    try:
        # Start tool in a subprocess
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Spinner animation until the process completes
        show_spinner(f"Running {tool_name}", lambda: process.poll() is not None)

        # Capture the output from the process
        stdout, _ = process.communicate()

        return filter_subdomains(stdout) if process.returncode == 0 else set()
    except Exception as e:
        print(f"[✗] Error running {tool_name}: {e}")
        return set()


def filter_subdomains(output: str) -> Set[str]:
    """
    Extracts valid subdomains from a given string using regular expressions.

    Args:
        output (str): The string output from a command or tool.

    Returns:
        Set[str]: A set of valid subdomains.
    """
    return set(re.findall(r"\b[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+\b", output))


def fetch_crtsh_subdomains(domain: str) -> Set[str]:
    """
    Fetches subdomains related to the given domain from crt.sh.

    Args:
        domain (str): The domain to query.

    Returns:
        Set[str]: A set of subdomains retrieved from crt.sh.
    """
    url = f"https://crt.sh/?q={domain}&output=json"
    retries = 3

    for attempt in range(1, retries + 1):
        try:
            print(
                f"Fetching crt.sh subdomains (Attempt {attempt}/{retries}): ",
                end="",
                flush=True,
            )

            response = None

            # Use the spinner to indicate the task progress
            def fetch_task():
                nonlocal response
                response = requests.get(url, timeout=10)
                return response.status_code == 200

            show_spinner("Fetching", fetch_task)

            if response and response.status_code == 200:
                print("✅")
                data = response.json()
                return {
                    entry["name_value"]
                    for entry in data
                    if domain in entry.get("name_value", "")
                }
            else:
                print("❌")
                print(
                    f"[✗] crt.sh request failed with status code {response.status_code if response else 'None'}"
                )
        except requests.exceptions.Timeout:
            print("❌ Timeout occurred.")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"❌ General error: {e}")
        time.sleep(2)

    print("[✗] All retry attempts failed.")
    return set()


def save_subdomains(subdomains: Set[str], output_file: str, domain: str):
    """
    Saves filtered subdomains to a specified output file.

    Args:
        subdomains (Set[str]): Set of subdomains to save.
        output_file (str): Path to the output file.
        domain (str): The domain being processed (used for filtering).
    """
    try:
        filtered_subdomains = [sub for sub in subdomains if domain in sub]
        with open(output_file, "w") as file:
            file.write("\n".join(sorted(filtered_subdomains)) + "\n")
        print(f"[✅] {len(filtered_subdomains)} subdomains saved to {output_file}.")
    except Exception as e:
        print(f"[✗] Error saving to file: {e}")


def filter_dnsx_httpx(subdomains: Set[str], domain: str) -> Set[str]:
    """
    Resolves subdomains using dnsx and filters live ones using httpx.

    Args:
        subdomains (Set[str]): Set of subdomains to process.
        domain (str): The domain being processed.

    Returns:
        Set[str]: A set of live subdomains.
    """
    live_subdomains = set()
    try:
        # Write subdomains to a temporary file
        with open(TEMP_SUBDOMAINS_FILE, "w") as file:
            file.write("\n".join(subdomains))

        # Run dnsx to resolve DNS entries
        dnsx_command = ["dnsx", "-silent", "-l", TEMP_SUBDOMAINS_FILE]
        dnsx_result = subprocess.run(dnsx_command, capture_output=True, text=True)

        resolved_domains = (
            dnsx_result.stdout.strip().splitlines()
            if dnsx_result.returncode == 0
            else []
        )

        # Helper function to process each domain with httpx
        def check_httpx(domain: str):
            if not domain.startswith(("http://", "https://")):
                domain = f"http://{domain}"

            httpx_command = ["httpx", domain, "--follow-redirects"]
            httpx_result = subprocess.run(httpx_command, capture_output=True, text=True)

            if httpx_result.returncode == 0:
                live_subdomains.add(domain)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(check_httpx, domain) for domain in resolved_domains
            ]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[✗] Error processing domain: {e}")

        return live_subdomains
    except Exception as e:
        print(f"[✗] Error during dnsx/httpx filtering: {e}")
        return set()
    finally:
        if os.path.exists(TEMP_SUBDOMAINS_FILE):
            os.remove(TEMP_SUBDOMAINS_FILE)


def main():
    """
    Main entry point for the script. Handles subdomain enumeration and live domain validation.
    """
    print(ART)
    domain = input(" 📓 DEATH NOTE: ").strip()

    if not domain:
        print("[!] No domain entered. Exiting.")
        return

    tools = {
        "sublist3r": ["sublist3r", "-d", domain],
        "subfinder": ["subfinder", "-d", domain],
        "assetfinder": ["assetfinder", "--subs-only", domain],
        "findomain": ["findomain", "--target", domain],
    }

    all_subdomains = set()

    # Run external tools
    for tool, cmd in tools.items():
        if check_tool_availability(cmd[0]):
            all_subdomains.update(run_tool(cmd, tool))

    # Fetch crt.sh subdomains
    all_subdomains.update(fetch_crtsh_subdomains(domain))

    # Filter live subdomains
    live_subdomains = filter_dnsx_httpx(all_subdomains, domain)

    if live_subdomains:
        save_subdomains(live_subdomains, OUTPUT_FILE, domain)
        display_output = input("Display Output? [Y/n]: ").strip().lower()
        if display_output in ("y", ""):
            with open(OUTPUT_FILE, "r") as file:
                print("\n[Output] Subdomains:")
                print(file.read())
    else:
        print("[!] No live subdomains found.")


if __name__ == "__main__":
    main()

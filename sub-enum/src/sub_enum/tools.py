import subprocess
import os
import tempfile
import re
from typing import Iterable, Set, Tuple, List

from .config import BLUE, RED, YELLOW, GREEN, RESET

def run_tool(command: Iterable[str], tool_name: str, timeout: int = None) -> Set[str]:
    """Run a subprocess command and return stdout lines as a set.

    Captures stderr for better diagnostics but returns stdout lines. Timeouts and
    errors are logged to stderr and produce an empty set.
    """
    try:
        result = subprocess.run(list(command), capture_output=True, text=True, timeout=timeout)
        output_lines = result.stdout.strip().splitlines() if result.stdout else []
        if result.returncode != 0 and result.stderr:
            # Log stderr to the console for visibility
            print(f"{YELLOW}[!] {tool_name} stderr: {result.stderr.strip()}{RESET}")
        return set(output_lines)
    except subprocess.TimeoutExpired:
        print(f"{RED}[✗] {tool_name} timed out after {timeout} seconds.{RESET}")
    except Exception as e:
        print(f"{RED}[✗] Exception running {tool_name}: {e}{RESET}")
    return set()

def run_dnsx(subdomains):
    """Resolve subdomains using dnsx."""
    if not subdomains:
        return set()
    
    # Silenced start message
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write("\n".join(subdomains))
            temp_path = temp.name

        command_simple = ["dnsx", "-l", temp_path, "-silent"]
        result_simple = subprocess.run(command_simple, capture_output=True, text=True)

        resolved_lines = result_simple.stdout.strip().splitlines() if result_simple.stdout else []
        resolved = set(resolved_lines)
        # Silenced completion message
        return resolved
        
    except Exception as e:
        print(f"{RED}[✗] Error running dnsx: {e}{RESET}")
        return set()
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def run_altdns(domain, subdomains, timeout=None):
    """Generate permutations using altdns."""
    if not subdomains:
        return set()
    
    # Silenced start message
    
    wordlist_path = "words.txt"
    if not os.path.exists(wordlist_path):
        # Allow this print as it indicates a download action, good for user to know why it's pausing
        print(f"{YELLOW}[!] words.txt not found. Downloading default wordlist...{RESET}")
        try:
            subprocess.run(["wget", "https://raw.githubusercontent.com/infosec-au/altdns/master/words.txt", "-O", wordlist_path], check=True)
        except:
            print(f"{RED}[✗] Failed to download wordlist. Skipping permutations.{RESET}")
            return set()

    temp_subs_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_subs:
            temp_subs.write("\n".join(subdomains))
            temp_subs_path = temp_subs.name
            
        output_perms = "altdns_output.txt"
        
        command = ["altdns", "-i", temp_subs_path, "-o", "data_output", "-w", wordlist_path, "-r", "-s", output_perms]
        
        try:
            subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"{YELLOW}[!] altdns timed out after {timeout} seconds. Checking for partial results...{RESET}")

        perms = set()
        if os.path.exists(output_perms):
            with open(output_perms, "r") as f:
                for line in f:
                    parts = line.split(":")
                    if parts:
                        perms.add(parts[0].strip())
            os.remove(output_perms)
            
        if os.path.exists("data_output"):
            os.remove("data_output")
            
        # Silenced completion message
        return perms

    except Exception as e:
        print(f"{RED}[✗] Error running altdns: {e}{RESET}")
        return set()
    finally:
        if temp_subs_path and os.path.exists(temp_subs_path):
            os.remove(temp_subs_path)

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from itertools import islice

def chunked_iterable(iterable, size):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk

def filter_httpx(subdomains, output_file, info_output_file, timeout=None):
    if not subdomains:
        return set()

    BATCH_SIZE = 100
    total_subs = len(subdomains)
    live_subdomains = set()
    
    # We'll collect all formatted output to write to info file at the end.
    all_raw_output: List[str] = []

    print(f"\n{BLUE}[*] Running httpx on {total_subs} subdomains (Batch size: {BATCH_SIZE})...{RESET}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}", justify="right"),
        TimeElapsedColumn(),
        transient=False
    ) as progress:
        task = progress.add_task("[cyan]Checking candidates...", total=total_subs)
        
        for batch in chunked_iterable(subdomains, BATCH_SIZE):
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
                    temp.write("\n".join(batch))
                    temp_path = temp.name

                # Add -threads for speed if needed, normally httpx handles it well. 
                # -threads 50 is default. Let's bump to 100 for batch processing.
                httpx_command = [
                    "httpx", "-ip", "-cdn", "-title", "-status-code", "-tech-detect", 
                    "-silent", "-l", temp_path, "-threads", "100"
                ]
                
                # Run subprocess for this batch
                result = subprocess.run(httpx_command, capture_output=True, text=True, timeout=timeout)
                
                if result.stdout:
                    lines = result.stdout.strip().splitlines()
                    # raw httpx output lines
                    all_raw_output.extend(lines)
                    live_subdomains.update(lines)

            except subprocess.TimeoutExpired:
                 # Just log specific failure but continue
                 print(f"{RED}[!] Batch timeout.{RESET}")
            except Exception as e:
                 print(f"{RED}[!] Batch error: {e}{RESET}")
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            
            # Update progress by batch length
            progress.advance(task, advance=len(batch))

    # After loop, process results
    if all_raw_output:
        with open(info_output_file, "w") as f:
            f.write("\n".join(all_raw_output))
            # Silenced info save message

    if not live_subdomains:
         print(f"{YELLOW}[!] httpx returned 0 results.{RESET}")
    
    urls: Set[str] = set()
    for line in all_raw_output:
        match = re.search(r'(https?://\S+)', line)
        if match:
            urls.add(match.group(1))

    with open(output_file, "w") as file:
        file.write("\n".join(sorted(urls)))

    # Return the set of parsed URLs (not raw httpx lines) for accurate counts and downstream use
    return urls


def parse_httpx_output(lines: Iterable[str]) -> Set[str]:
    """Parse raw httpx lines and extract URLs.

    This helper is useful for unit tests to validate parsing.
    """
    urls: Set[str] = set()
    for line in lines:
        match = re.search(r'(https?://\S+)', line)
        if match:
            urls.add(match.group(1))
    return urls

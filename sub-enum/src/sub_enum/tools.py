import subprocess
import os
import tempfile
import shutil
import re
import hashlib
from typing import Iterable, Set, Tuple, List

from .config import BLUE, RED, YELLOW, GREEN, RESET
from .installers import ALTDNS_WORDLIST_SHA256
from .utils import validate_domain, get_logger


logger = get_logger(__name__)

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
            logger.warning(f"[!] {tool_name} stderr: {result.stderr.strip()}")
        return set(output_lines)
    except subprocess.TimeoutExpired:
        logger.error(f"[✗] {tool_name} timed out after {timeout} seconds.")
    except Exception as e:
        logger.error(f"[✗] Exception running {tool_name}: {e}")
    return set()

def run_dnsx(subdomains, timeout=None):
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
        try:
            result_simple = subprocess.run(command_simple, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.error(f"[✗] dnsx timed out after {timeout} seconds.")
            return set()

        resolved_lines = result_simple.stdout.strip().splitlines() if result_simple.stdout else []
        resolved = set(resolved_lines)
        # Silenced completion message
        return resolved
        
    except Exception as e:
        logger.error(f"[✗] Error running dnsx: {e}")
        return set()
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def run_altdns(domain, subdomains, output_dir, timeout=None):
    """Generate permutations using altdns."""
    if not subdomains:
        return set()
    
    # Silenced start message

    temp_workspace = None
    try:
        temp_workspace = tempfile.mkdtemp(prefix="altdns_", dir=output_dir)

        wordlist_path = os.path.join(temp_workspace, "words.txt")
        # Allow this print as it indicates a download action, good for user to know why it's pausing
        logger.warning("[!] words.txt not found. Downloading default wordlist...")
        try:
            subprocess.run(["wget", "https://raw.githubusercontent.com/infosec-au/altdns/master/words.txt", "-O", wordlist_path], check=True)

            # Verify checksum for supply chain security
            logger.warning("[!] Verifying wordlist integrity...")
            sha256_hash = hashlib.sha256()
            try:
                with open(wordlist_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                computed_sha256 = sha256_hash.hexdigest()
                if computed_sha256 == ALTDNS_WORDLIST_SHA256:
                    logger.success("[✓] Wordlist integrity verified.")
                else:
                    logger.error("[✗] Wordlist SHA256 mismatch! Possible supply chain attack.")
                    logger.error(f"    Expected: {ALTDNS_WORDLIST_SHA256}")
                    logger.error(f"    Got:      {computed_sha256}")
                    logger.error("[✗] Aborting to prevent using potentially tampered wordlist.")
                    return set()
            except Exception as e:
                logger.error(f"[✗] Error verifying wordlist: {e}")
                return set()

        except Exception:
            logger.error("[✗] Failed to download wordlist. Skipping permutations.")
            return set()

        temp_subs_path = os.path.join(temp_workspace, "input.txt")
        with open(temp_subs_path, "w") as temp_subs:
            temp_subs.write("\n".join(subdomains))

        output_perms = os.path.join(temp_workspace, "altdns_output.txt")
        data_output_path = os.path.join(temp_workspace, "data_output")
        
        command = ["altdns", "-i", temp_subs_path, "-o", data_output_path, "-w", wordlist_path, "-r", "-s", output_perms]
        
        try:
            subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f"[!] altdns timed out after {timeout} seconds. Checking for partial results...")

        perms = set()
        if os.path.exists(output_perms):
            with open(output_perms, "r") as f:
                for line in f:
                    candidate = line.strip().split(":", 1)[0].strip()
                    if validate_domain(candidate):
                        perms.add(candidate)
            
        # Silenced completion message
        return perms

    except Exception as e:
        logger.error(f"[✗] Error running altdns: {e}")
        return set()
    finally:
        if temp_workspace and os.path.exists(temp_workspace):
            shutil.rmtree(temp_workspace)

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
    
    # We'll collect all formatted output to write to info file at the end.
    all_raw_output: List[str] = []

    logger.info(f"[*] Running httpx on {total_subs} subdomains (Batch size: {BATCH_SIZE})...")

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

            except subprocess.TimeoutExpired:
                 # Just log specific failure but continue
                  logger.warning("[!] Batch timeout.")
            except Exception as e:
                  logger.warning(f"[!] Batch error: {e}")
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

    urls: Set[str] = set()
    for line in all_raw_output:
        match = re.search(r'(https?://\S+)', line)
        if match:
            urls.add(match.group(1))

    if not urls:
            logger.warning("[!] httpx returned 0 results.")

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

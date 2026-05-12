import argparse
import os
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import subprocess
from typing import Optional, Set

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .config import (
    ART, REQUIRED_TOOLS_BASIC, REQUIRED_TOOLS_FULL, REQUIRED_TOOLS_PERM,
    RED, GREEN, YELLOW, BLUE, RESET
)
from .utils import (
    load_env, validate_domain, check_tool_availability,
    ensure_path_context, remove_conflicting_httpx, set_auto_yes,
    configure_logging, get_logger
)
from .installers import (
    install_go, install_tool_go, install_findomain,
    install_altdns, init_workspace
)
from .tools import run_tool, run_dnsx, run_altdns, filter_httpx


logger = get_logger(__name__)


def _resolve_safe_output_path(base_dir: str, requested_path: str, label: str) -> Optional[str]:
    """Resolve an output path and reject paths that escape the target directory."""
    if os.path.isabs(requested_path):
        candidate = os.path.realpath(requested_path)
    else:
        candidate = os.path.realpath(os.path.join(base_dir, requested_path))

    base_real = os.path.realpath(base_dir)
    try:
        if os.path.commonpath([candidate, base_real]) != base_real:
            logger.error(f"[✗] Refusing unsafe {label} path outside {base_dir}: {requested_path}")
            return None
    except ValueError:
        logger.error(f"[✗] Refusing unsafe {label} path: {requested_path}")
        return None

    return candidate

def main():
    parser = argparse.ArgumentParser(description="Automated Subdomain Discovery Tool (Community Edition)", 
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--domain", help="Target domain (e.g., example.com)")
    parser.add_argument("-L", "--targets-file", help="File with one target domain per line")
    parser.add_argument("-o", "--output", default="all_subdomains.txt", help="Output file for all discovered subdomains")
    parser.add_argument("-l", "--live-output", default="live_subdomains.txt", help="Output file for live subdomains")
    parser.add_argument("--full", action="store_true", help="Use all available tools (including chaos)")
    parser.add_argument("--permutations", action="store_true", help="Run permutation scanning using altdns")
    parser.add_argument("--config", default=".env", help="Path to configuration file (default: .env)")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout for each tool in seconds (default: 600)")
    parser.add_argument("--yes", action="store_true", help="Automatic yes to prompts (non-interactive)")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel worker targets to run (default: 1)")
    
    args = parser.parse_args()

    configure_logging()
    logger.info(ART, extra={"raw": True})
    
    load_env(args.config)
    set_auto_yes(args.yes)
    # create workspace dirs explicitly
    init_workspace()
    ensure_path_context()

    # Build list of targets from -d or -L
    targets = []
    if args.domain:
        targets.append(args.domain)
    if args.targets_file:
        if not os.path.exists(args.targets_file):
            logger.error(f"[✗] Targets file not found: {args.targets_file}")
            return
        with open(args.targets_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    targets.append(line)

    if not targets:
        logger.error("[✗] No target specified. Use -d or -L.")
        return

    # Validate and normalize targets
    clean_targets = []
    for t in targets:
        domain = validate_domain(t)
        if not domain:
            logger.warning(f"[!] Skipping invalid domain: {t}")
            continue
        clean_targets.append(domain)

    if not clean_targets:
        logger.error("[✗] No valid targets to process.")
        return

    # We'll run each target in its own workspace directory. The per-target run
    # will create the directories it needs.

    def run_for_target(domain: str) -> None:
        output_dir = domain
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                logger.info(f"[*] Created output directory: {output_dir}")
            except OSError as e:
                logger.error(f"[✗] Failed to create directory {output_dir}: {e}")
                return

        output_file = _resolve_safe_output_path(output_dir, args.output, "output")
        if not output_file:
            return

        live_output_file = _resolve_safe_output_path(output_dir, args.live_output, "live output")
        if not live_output_file:
            return

        info_output_file = os.path.join(output_dir, "live_subdomains_info.txt")

        # Check tool availability for this run
        tools_to_check = REQUIRED_TOOLS_BASIC.copy()
        if args.full:
            tools_to_check.extend(REQUIRED_TOOLS_FULL)
            logger.warning("[ WARNING] Full mode enabled. Ensure API keys are set for Chaos.")
        if args.permutations:
            tools_to_check.extend(REQUIRED_TOOLS_PERM)

        missing_tools = []
        for tool in tools_to_check:
            if not check_tool_availability(tool):
                missing_tools.append(tool)

        if "httpx" not in missing_tools:
            try:
                subprocess.run(["httpx", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                logger.warning("[!] Detected incorrect httpx version (likely python-httpx).")
                remove_conflicting_httpx()
                if not check_tool_availability("httpx"):
                    missing_tools.append("httpx")

        # Attempt installs only if needed; installers will respect auto-yes
        if missing_tools:
            logger.warning(f"[!] Missing tools: {', '.join(missing_tools)}")
            go_based_tools = {"assetfinder", "subfinder", "httpx", "dnsx", "chaos"}
            if any(tool in missing_tools for tool in go_based_tools) and not check_tool_availability("go"):
                install_go()
                ensure_path_context()
                if not check_tool_availability("go"):
                    logger.error("[✗] Go is still missing. Cannot proceed with Go-based tools.")
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
            if "altdns" in missing_tools and args.permutations:
                install_altdns()

        # Build discovery commands
        commands = {
            "Subfinder": ["subfinder", "-silent", "-d", domain],
            "Assetfinder": ["assetfinder", "--subs-only", domain],
            "Findomain": ["findomain", "-t", domain]
        }
        if args.full:
            commands["Chaos"] = ["chaos", "-d", domain]

        console = Console()
        logger.info(f"[*] Discovering subdomains for {domain}...")

        all_subdomains = set()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Running discovery tools...", total=len(commands))

            with ThreadPoolExecutor(max_workers=len(commands)) as executor:
                future_to_tool = {executor.submit(run_tool, cmd, name, args.timeout): name for name, cmd in commands.items()}

                for future in concurrent.futures.as_completed(future_to_tool):
                    tool_name = future_to_tool[future]
                    progress.advance(task)
                    try:
                        results = future.result()
                        logger.success(f"[+] {tool_name} found {len(results)} subdomains")
                        all_subdomains.update(results)
                    except Exception as exc:
                        logger.error(f"[✗] {tool_name} generated an exception: {exc}")

        logger.info("[*] Verifying subdomains with dnsx...")

        with console.status("[bold green]Running dnsx resolution...") as status:
            resolved_subdomains = run_dnsx(all_subdomains, args.timeout)

        if args.permutations:
            with console.status("[bold green]Running altdns permutations...") as status:
                perm_subdomains = run_altdns(domain, resolved_subdomains, output_dir, args.timeout)
                resolved_subdomains.update(perm_subdomains)

        with open(output_file, "w") as file:
            file.write("\n".join(sorted(resolved_subdomains)) + "\n")
        logger.success(f"[✓] Saved {len(resolved_subdomains)} resolved subdomains to {output_file}")

        live_urls = filter_httpx(resolved_subdomains, live_output_file, info_output_file, args.timeout)
        logger.success(f"[✓] Saved {len(live_urls)} live subdomains to {live_output_file}")

    # Run targets with workers
    workers = max(1, args.workers)
    if len(clean_targets) == 1 and workers > 1:
        logger.warning(f"[!] Single target supplied; ignoring --workers={workers} and running sequentially.")
    if len(clean_targets) == 1 or workers == 1:
        for t in clean_targets:
            run_for_target(t)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_target = {pool.submit(run_for_target, t): t for t in clean_targets}
            for future in concurrent.futures.as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    _ = future.result()
                except Exception as e:
                    logger.error(f"[✗] Error processing target {target}: {e}")
    # end of main

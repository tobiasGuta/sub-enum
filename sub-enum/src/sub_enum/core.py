import argparse
import os
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import subprocess

from .config import (
    ART, REQUIRED_TOOLS_BASIC, REQUIRED_TOOLS_FULL, REQUIRED_TOOLS_PERM,
    RED, GREEN, YELLOW, BLUE, RESET
)
from .utils import (
    load_env, validate_domain, check_tool_availability, 
    ensure_path_context, remove_conflicting_httpx
)
from .installers import (
    install_go, install_tool_go, install_findomain, 
    install_altdns
)
from .tools import run_tool, run_dnsx, run_altdns, filter_httpx

def main():
    parser = argparse.ArgumentParser(description="Automated Subdomain Discovery Tool (Community Edition)", 
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--domain", required=True, help="Target domain (e.g., example.com)")
    parser.add_argument("-o", "--output", default="all_subdomains.txt", help="Output file for all discovered subdomains")
    parser.add_argument("-l", "--live-output", default="live_subdomains.txt", help="Output file for live subdomains")
    parser.add_argument("--full", action="store_true", help="Use all available tools (including chaos)")
    parser.add_argument("--permutations", action="store_true", help="Run permutation scanning using altdns")
    parser.add_argument("--config", default=".env", help="Path to configuration file (default: .env)")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout for each tool in seconds (default: 600)")
    
    args = parser.parse_args()

    print(ART)
    
    load_env(args.config)
    ensure_path_context()

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
    # Re-verify availability after ensure_path_context
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
            if not check_tool_availability("httpx"):
                 missing_tools.append("httpx")
    
    if missing_tools:
        print(f"{YELLOW}[!] Missing tools: {', '.join(missing_tools)}{RESET}")
        
        if "go" in missing_tools:
            install_go()
            # Reload path context in case go was added
            ensure_path_context()
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

        if "altdns" in missing_tools and args.permutations:
            install_altdns()

    commands = {
        "Subfinder": ["subfinder", "-silent", "-d", domain],
        "Assetfinder": ["assetfinder", "--subs-only", domain],
        "Findomain": ["findomain", "-t", domain]
    }
    
    if args.full:
        commands["Chaos"] = ["chaos", "-d", domain]

    # Initialize Rich Console
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    
    console = Console()
    console.print(f"[bold blue][*] Discovering subdomains for {domain}...[/bold blue]")
    
    all_subdomains = set()
    
    # Use Rich Progress Bar for concurrent tools
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]Running discovery tools...", total=len(commands))
        
        with ThreadPoolExecutor() as executor:
            future_to_tool = {executor.submit(run_tool, cmd, name, args.timeout): name for name, cmd in commands.items()}
            
            for future in concurrent.futures.as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                progress.advance(task)
                try:
                    results = future.result()
                    console.print(f"[green][+] {tool_name} found {len(results)} subdomains[/green]")
                    all_subdomains.update(results)
                except Exception as exc:
                    console.print(f"[red][✗] {tool_name} generated an exception: {exc}[/red]")

    console.print(f"[bold blue][*] Verifying subdomains with dnsx...[/bold blue]")
    
    # Simple spinner for single-step tools
    with console.status("[bold green]Running dnsx resolution...") as status:
        resolved_subdomains = run_dnsx(all_subdomains)
    
    if args.permutations:
        with console.status("[bold green]Running altdns permutations...") as status:
            perm_subdomains = run_altdns(domain, resolved_subdomains, args.timeout)
            resolved_subdomains.update(perm_subdomains)

    with open(output_file, "w") as file:
        file.write("\n".join(sorted(resolved_subdomains)) + "\n")
    print(f"{GREEN}[✓] Saved {len(resolved_subdomains)} resolved subdomains to {output_file}{RESET}")

    # Removed print statement as filter_httpx now handles UI
    # print(f"{BLUE}[*] Checking for live subdomains...{RESET}")
    live_subdomains = filter_httpx(resolved_subdomains, live_output_file, info_output_file, args.timeout)
    print(f"{GREEN}[✓] Saved {len(live_subdomains)} live subdomains to {live_output_file}{RESET}")

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

from rich.console import Console
from rich.table import Table

from .config import ART, OPTIONAL_TOOLS, PINNED_GO_TOOLS, REQUIRED_STANDARD, VERSION
from .history import diff_recent, latest_source_stats, recent_scans, save_scan
from .installers import init_workspace, install_many
from .models import AssetRecord, source_statistics
from .tools import (
    ToolRun,
    run_alterx,
    run_assetfinder,
    run_dnsx,
    run_findomain,
    run_httpx,
    run_puredns_bruteforce,
    run_puredns_resolve,
    run_subfinder,
    tool_version,
)
from .utils import (
    check_tool_availability,
    configure_logging,
    ensure_path_context,
    get_logger,
    load_env,
    normalize_candidate,
    validate_domain,
    write_lines,
)

logger = get_logger(__name__)
console = Console()


def _asset(assets: Dict[str, AssetRecord], hostname: str, root_domain: str) -> AssetRecord:
    if hostname not in assets:
        assets[hostname] = AssetRecord(hostname=hostname, root_domain=root_domain)
    return assets[hostname]


def _merge_observations(
    assets: Dict[str, AssetRecord],
    observations: Dict[str, Set[str]],
    root_domain: str,
    method: str,
) -> None:
    for hostname, sources in observations.items():
        normalized = normalize_candidate(hostname, root_domain)
        if not normalized:
            continue
        asset = _asset(assets, normalized, root_domain)
        for source in sources:
            asset.observe(source, method)


def _record_run(run_log: List[ToolRun], run: ToolRun) -> None:
    run_log.append(run)
    if run.success:
        logger.success(f"[✓] {run.name}: {run.observations} observations in {run.duration_seconds:.2f}s")
    else:
        detail = run.error or run.stderr or "unknown error"
        logger.warning(f"[!] {run.name} failed: {detail}")


def _required_for_profile(profile: str, no_http: bool, no_permutations: bool) -> Set[str]:
    required = {"subfinder"}
    if profile != "passive":
        required.add("dnsx")
        if not no_http:
            required.add("httpx")
        if not no_permutations:
            required.add("alterx")
    return required


def _missing_tools(names: Iterable[str]) -> List[str]:
    return sorted(name for name in set(names) if not check_tool_availability(name))


def _write_artifacts(
    output_dir: Path,
    assets: Dict[str, AssetRecord],
    runs: Sequence[ToolRun],
    wildcard_roots: Set[str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(assets.values(), key=lambda item: item.hostname)

    with (output_dir / "assets.jsonl").open("w", encoding="utf-8") as handle:
        for asset in ordered:
            handle.write(json.dumps(asset.to_dict(), sort_keys=True) + "\n")

    discovered = [asset.hostname for asset in ordered]
    resolved = [asset.hostname for asset in ordered if asset.dns_validated]
    live_urls = sorted(
        {
            str(item.get("url"))
            for asset in ordered
            for item in asset.http
            if item.get("url")
        }
    )
    dangling = [asset.hostname for asset in ordered if asset.dangling_cname_candidate]

    write_lines(output_dir / "all_subdomains.txt", discovered)
    write_lines(output_dir / "resolved_subdomains.txt", resolved)
    write_lines(output_dir / "live_subdomains.txt", live_urls)
    write_lines(output_dir / "wildcard_roots.txt", wildcard_roots)
    write_lines(output_dir / "dangling_cname_candidates.txt", dangling)

    stats = source_statistics(ordered)
    (output_dir / "source_stats.json").write_text(
        json.dumps(stats, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    run_payload = [
        {
            "name": run.name,
            "success": run.success,
            "duration_seconds": round(run.duration_seconds, 3),
            "returncode": run.returncode,
            "error": run.error,
            "stderr": run.stderr[-2000:] if run.stderr else "",
            "observations": run.observations,
            "metadata": run.metadata,
            "command": run.command,
        }
        for run in runs
    ]
    (output_dir / "run_manifest.json").write_text(
        json.dumps(run_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _mark_dangling_candidates(assets: Dict[str, AssetRecord]) -> None:
    for asset in assets.values():
        cname = asset.dns.get("cname")
        if cname and not asset.dns.get("a") and not asset.dns.get("aaaa"):
            asset.dangling_cname_candidate = True


def _resolve_stage(
    domain: str,
    candidates: Set[str],
    assets: Dict[str, AssetRecord],
    args: argparse.Namespace,
    run_log: List[ToolRun],
    wildcard_roots: Set[str],
) -> Set[str]:
    if not candidates:
        return set()

    validated_candidates = set(candidates)
    use_puredns = (
        args.dns_backend == "puredns"
        or (
            args.dns_backend == "auto"
            and args.profile == "deep"
            and check_tool_availability("puredns")
            and check_tool_availability("massdns")
            and bool(args.resolvers)
        )
    )
    if use_puredns:
        if not check_tool_availability("puredns") or not check_tool_availability("massdns"):
            logger.warning("[!] PureDNS requested but puredns/massdns is unavailable; falling back to dnsx.")
        elif not args.resolvers:
            logger.warning("[!] PureDNS requested without --resolvers; falling back to dnsx for predictable results.")
        else:
            valid, wildcards, run = run_puredns_resolve(
                domain,
                candidates,
                timeout=args.timeout,
                resolvers=args.resolvers,
                trusted_resolvers=args.trusted_resolvers,
            )
            _record_run(run_log, run)
            if run.success:
                validated_candidates = valid
                wildcard_roots.update(wildcards)

    records, dns_runs = run_dnsx(
        domain,
        validated_candidates,
        timeout=args.timeout,
        rate_limit=args.dns_rate,
    )
    for run in dns_runs:
        _record_run(run_log, run)

    resolved: Set[str] = set()
    for hostname, evidence in records.items():
        asset = _asset(assets, hostname, domain)
        asset.merge_dns(evidence)
        if evidence.get("wildcard"):
            asset.wildcard = True
        if asset.dns_validated and not asset.wildcard:
            resolved.add(hostname)
    _mark_dangling_candidates(assets)
    return resolved


def scan_target(domain: str, args: argparse.Namespace) -> int:
    output_dir = Path(args.output_root).expanduser().resolve() / domain
    assets: Dict[str, AssetRecord] = {}
    run_log: List[ToolRun] = []
    wildcard_roots: Set[str] = set()

    logger.info(f"[*] Passive discovery for {domain}")
    passive_jobs = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        passive_jobs.append(executor.submit(run_subfinder, domain, args.timeout, args.all_sources))
        if not args.no_findomain and check_tool_availability("findomain"):
            passive_jobs.append(executor.submit(run_findomain, domain, args.timeout))
        if args.assetfinder and check_tool_availability("assetfinder"):
            passive_jobs.append(executor.submit(run_assetfinder, domain, args.timeout))

        for future in as_completed(passive_jobs):
            observations, run = future.result()
            _record_run(run_log, run)
            _merge_observations(assets, observations, domain, "passive")

    if not assets:
        logger.warning(f"[!] No in-scope passive observations were produced for {domain}.")

    if args.profile == "passive":
        _write_artifacts(output_dir, assets, run_log, wildcard_roots)
        if not args.no_history:
            save_scan(domain, args.profile, assets.values(), source_statistics(assets.values()))
        return 0

    initial_candidates = set(assets)
    resolved = _resolve_stage(domain, initial_candidates, assets, args, run_log, wildcard_roots)

    if not args.no_permutations and check_tool_availability("alterx") and assets:
        logger.info(f"[*] Generating target-aware permutations for {domain}")
        seed_hosts = sorted(resolved or set(assets))
        generated, run = run_alterx(
            domain,
            seed_hosts,
            timeout=args.timeout,
            limit=args.alterx_limit,
        )
        _record_run(run_log, run)
        new_candidates: Set[str] = set()
        for hostname in generated:
            if hostname in assets:
                continue
            asset = _asset(assets, hostname, domain)
            asset.observe("alterx:enrich", "permutation")
            new_candidates.add(hostname)
        resolved.update(_resolve_stage(domain, new_candidates, assets, args, run_log, wildcard_roots))

    if args.profile == "deep" and args.wordlist:
        if not (check_tool_availability("puredns") and check_tool_availability("massdns")):
            logger.warning("[!] --wordlist deep brute force requires both puredns and massdns; skipping brute force.")
        elif not args.resolvers:
            logger.warning("[!] --wordlist deep brute force requires --resolvers; skipping brute force.")
        else:
            logger.info(f"[*] Deep DNS bruteforce for {domain}")
            brute_hosts, wildcards, run = run_puredns_bruteforce(
                domain,
                args.wordlist,
                timeout=args.timeout,
                resolvers=args.resolvers,
                trusted_resolvers=args.trusted_resolvers,
            )
            _record_run(run_log, run)
            wildcard_roots.update(wildcards)
            new_brute: Set[str] = set()
            for hostname in brute_hosts:
                asset = _asset(assets, hostname, domain)
                asset.observe("puredns:bruteforce", "bruteforce")
                new_brute.add(hostname)
            resolved.update(_resolve_stage(domain, new_brute, assets, args, run_log, wildcard_roots))

    if not args.no_http and resolved:
        logger.info(f"[*] HTTP enrichment for {len(resolved)} DNS-validated hosts")
        http_results, run = run_httpx(
            domain,
            resolved,
            timeout=args.timeout,
            threads=args.http_threads,
        )
        _record_run(run_log, run)
        for hostname, observations in http_results.items():
            asset = _asset(assets, hostname, domain)
            for observation in observations:
                asset.add_http(observation)

    _write_artifacts(output_dir, assets, run_log, wildcard_roots)
    stats = source_statistics(assets.values())
    scan_id: Optional[int] = None
    if not args.no_history:
        scan_id = save_scan(domain, args.profile, assets.values(), stats)

    logger.success(f"[✓] {domain}: {len(assets)} discovered, {len(resolved)} DNS-validated")
    logger.success(f"[✓] Results: {output_dir}")
    if scan_id is not None:
        logger.info(f"[*] History scan id: {scan_id}")
    return 0


def _targets_from_args(args: argparse.Namespace) -> List[str]:
    raw: List[str] = []
    if args.domain:
        raw.append(args.domain)
    if args.targets_file:
        path = Path(args.targets_file)
        if not path.is_file():
            raise ValueError(f"targets file not found: {path}")
        raw.extend(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

    targets: List[str] = []
    for value in raw:
        domain = validate_domain(value)
        if not domain:
            logger.warning(f"[!] Skipping invalid target: {value}")
            continue
        if domain not in targets:
            targets.append(domain)
    return targets


def run_scan(args: argparse.Namespace) -> int:
    load_env(args.config)
    required = _required_for_profile(args.profile, args.no_http, args.no_permutations)
    missing = _missing_tools(required)
    if missing:
        logger.error(f"[✗] Missing required tools: {', '.join(missing)}")
        logger.error("    Run: sub-enum doctor --install")
        return 3

    targets = _targets_from_args(args)
    if not targets:
        logger.error("[✗] No valid target. Use -d DOMAIN or -L FILE.")
        return 2

    workers = max(1, args.workers)
    if workers == 1 or len(targets) == 1:
        results = [scan_target(domain, args) for domain in targets]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(scan_target, domain, args): domain for domain in targets}
            for future in as_completed(futures):
                domain = futures[future]
                try:
                    results.append(future.result())
                except Exception as exc:  # pragma: no cover - outer isolation boundary
                    logger.error(f"[✗] Unexpected target failure for {domain}: {exc}")
                    results.append(1)
    return 0 if all(code == 0 for code in results) else 1


def run_doctor(args: argparse.Namespace) -> int:
    if args.install:
        managed = ["subfinder", "dnsx", "httpx", "alterx", "puredns"]
        install_many(name for name in managed if not check_tool_availability(name))
        ensure_path_context()

    table = Table(title=f"Sub-Enum {VERSION} environment")
    table.add_column("Tool")
    table.add_column("Role")
    table.add_column("Status")
    table.add_column("Version / pin")

    roles = {
        "subfinder": "primary passive discovery",
        "dnsx": "DNS validation / wildcard filtering",
        "httpx": "HTTP enrichment",
        "findomain": "secondary passive discovery",
        "alterx": "target-aware permutations",
        "puredns": "optional deep DNS backend",
        "massdns": "PureDNS backend",
        "assetfinder": "optional compatibility source",
    }
    names = list(REQUIRED_STANDARD) + [name for name in OPTIONAL_TOOLS if name not in REQUIRED_STANDARD]
    for name in names:
        installed = check_tool_availability(name)
        status = "OK" if installed else ("optional" if name in OPTIONAL_TOOLS else "MISSING")
        version = tool_version(name) if installed else ""
        if name in PINNED_GO_TOOLS:
            pin = PINNED_GO_TOOLS[name][1]
            version = f"{version or 'installed'} (tested: {pin})" if installed else f"tested: {pin}"
        table.add_row(name, roles[name], status, version or "-")
    console.print(table)
    console.print(f"Python: {sys.version.split()[0]}")
    return 0


def run_diff(args: argparse.Namespace) -> int:
    domain = validate_domain(args.domain)
    if not domain:
        return 2
    result = diff_recent(domain)
    if not result:
        console.print(f"Need at least two saved scans for {domain}.")
        return 0
    console.print(f"[bold]Diff for {domain}[/bold]")
    console.print(f"Added: {len(result['added'])}  Removed: {len(result['removed'])}  Changed: {len(result['changed'])}")
    for hostname in result["added"]:
        console.print(f"[green]+ {hostname}[/green]")
    for hostname in result["removed"]:
        console.print(f"[red]- {hostname}[/red]")
    for item in result["changed"]:
        console.print(f"[yellow]~ {item['hostname']}[/yellow]")
    if args.json:
        console.print_json(data=result)
    return 0


def run_history(args: argparse.Namespace) -> int:
    domain = validate_domain(args.domain)
    if not domain:
        return 2
    rows = recent_scans(domain, limit=args.limit)
    table = Table(title=f"Scan history: {domain}")
    for column in ("ID", "Profile", "Created", "Assets"):
        table.add_column(column)
    for row in rows:
        table.add_row(str(row["id"]), str(row["profile"]), str(row["created_at"]), str(row["asset_count"]))
    console.print(table)
    return 0


def run_sources(args: argparse.Namespace) -> int:
    domain = validate_domain(args.domain)
    if not domain:
        return 2
    stats = latest_source_stats(domain)
    if not stats:
        console.print(f"No saved source statistics for {domain}. Run a scan first.")
        return 0
    table = Table(title=f"Latest source contribution: {domain}")
    table.add_column("Source")
    table.add_column("Observed assets", justify="right")
    for source, count in stats.items():
        table.add_row(source, str(count))
    console.print(table)
    return 0


def _add_scan_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-d", "--domain")
    parser.add_argument("-L", "--targets-file")
    parser.add_argument("--profile", choices=("passive", "standard", "deep"), default="standard")
    parser.add_argument("--output-root", default=".", help="Parent directory for per-domain outputs")
    parser.add_argument("--config", default=".env", help="Optional allowlisted credential env file")
    parser.add_argument("--timeout", type=int, default=600, help="Per-tool timeout in seconds")
    parser.add_argument("--workers", type=int, default=1, help="Parallel root-domain workers")
    parser.add_argument("--dns-rate", type=int, default=0, help="dnsx requests/second; 0 leaves tool default")
    parser.add_argument("--http-threads", type=int, default=50)
    parser.add_argument("--alterx-limit", type=int, default=5000, help="Maximum target-aware permutations")
    parser.add_argument("--dns-backend", choices=("auto", "dnsx", "puredns"), default="auto")
    parser.add_argument("--resolvers", help="Resolver list for PureDNS deep mode")
    parser.add_argument("--trusted-resolvers", help="Optional trusted resolver list for PureDNS")
    parser.add_argument("--wordlist", help="Deep profile PureDNS brute-force wordlist")
    parser.add_argument("--all-sources", action="store_true", help="Ask Subfinder to use all configured sources")
    parser.add_argument("--assetfinder", action="store_true", help="Opt in to legacy Assetfinder source")
    parser.add_argument("--no-findomain", action="store_true")
    parser.add_argument("--no-permutations", action="store_true")
    parser.add_argument("--no-http", action="store_true")
    parser.add_argument("--no-history", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sub-enum",
        description="Evidence-rich subdomain enumeration for bug bounty reconnaissance.",
    )
    parser.add_argument("--version", action="version", version=f"sub-enum {VERSION}")
    sub = parser.add_subparsers(dest="command")

    scan = sub.add_parser("scan", help="Discover and validate subdomains")
    _add_scan_arguments(scan)

    doctor = sub.add_parser("doctor", help="Inspect the recon toolchain")
    doctor.add_argument("--install", action="store_true", help="Install missing managed Go tools at tested refs")

    diff_parser = sub.add_parser("diff", help="Compare the two most recent scans")
    diff_parser.add_argument("domain")
    diff_parser.add_argument("--json", action="store_true")

    history_parser = sub.add_parser("history", help="List saved scans")
    history_parser.add_argument("domain")
    history_parser.add_argument("--limit", type=int, default=10)

    sources_parser = sub.add_parser("sources", help="Show latest per-source contribution")
    sources_parser.add_argument("domain")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_logging()
    init_workspace()
    ensure_path_context()
    logger.info(ART, extra={"raw": True})

    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0] not in {"scan", "doctor", "diff", "history", "sources", "-h", "--help", "--version"}:
        if any(token in raw_argv for token in ("-d", "--domain", "-L", "--targets-file")):
            raw_argv = ["scan", *raw_argv]
    elif raw_argv and raw_argv[0] in {"-d", "--domain", "-L", "--targets-file"}:
        raw_argv = ["scan", *raw_argv]

    parser = build_parser()
    args = parser.parse_args(raw_argv)

    if args.command == "scan":
        return run_scan(args)
    if args.command == "doctor":
        return run_doctor(args)
    if args.command == "diff":
        return run_diff(args)
    if args.command == "history":
        return run_history(args)
    if args.command == "sources":
        return run_sources(args)

    parser.print_help()
    return 0

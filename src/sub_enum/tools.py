from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .config import VERSION
from .utils import extract_apex_domain, get_logger, normalize_candidate, write_lines

logger = get_logger(__name__)


@dataclass
class ToolRun:
    name: str
    command: List[str]
    success: bool
    duration_seconds: float
    returncode: Optional[int] = None
    stderr: str = ""
    error: Optional[str] = None
    observations: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


def run_command(command: Sequence[str], name: str, timeout: Optional[int] = None) -> Tuple[ToolRun, str]:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        run = ToolRun(
            name=name,
            command=list(command),
            success=proc.returncode == 0,
            duration_seconds=time.monotonic() - started,
            returncode=proc.returncode,
            stderr=(proc.stderr or "").strip(),
        )
        if proc.returncode != 0:
            run.error = f"exit code {proc.returncode}"
        return run, proc.stdout or ""
    except subprocess.TimeoutExpired as exc:
        return (
            ToolRun(
                name=name,
                command=list(command),
                success=False,
                duration_seconds=time.monotonic() - started,
                error=f"timed out after {timeout} seconds",
                stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
            ),
            "",
        )
    except Exception as exc:  # pragma: no cover - defensive subprocess boundary
        return (
            ToolRun(
                name=name,
                command=list(command),
                success=False,
                duration_seconds=time.monotonic() - started,
                error=str(exc),
            ),
            "",
        )


def _parse_json_lines(raw: str) -> Iterable[Dict[str, Any]]:
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            yield value


def run_subfinder(domain: str, timeout: int, all_sources: bool = False) -> Tuple[Dict[str, Set[str]], ToolRun]:
    command = ["subfinder", "-d", domain, "-json", "-collect-sources", "-disable-update-check"]
    if all_sources:
        command.append("-all")
    run, stdout = run_command(command, "subfinder", timeout)
    observations: Dict[str, Set[str]] = {}

    for item in _parse_json_lines(stdout):
        host = item.get("host") or item.get("input") or item.get("domain")
        normalized = normalize_candidate(str(host or ""), domain)
        if not normalized:
            continue
        sources: Set[str] = set()
        raw_sources = item.get("sources")
        if isinstance(raw_sources, list):
            sources.update(str(source) for source in raw_sources if source)
        source = item.get("source")
        if source:
            sources.add(str(source))
        if not sources:
            sources.add("subfinder")
        observations.setdefault(normalized, set()).update(f"subfinder:{source}" for source in sources)

    # Compatibility fallback if a future/older subfinder emits plain lines despite JSON flags.
    if run.success and not observations:
        for line in stdout.splitlines():
            normalized = normalize_candidate(line, domain)
            if normalized:
                observations.setdefault(normalized, set()).add("subfinder")

    run.observations = len(observations)
    return observations, run


def run_findomain(domain: str, timeout: int) -> Tuple[Dict[str, Set[str]], ToolRun]:
    run, stdout = run_command(["findomain", "-t", domain], "findomain", timeout)
    observations: Dict[str, Set[str]] = {}
    for line in stdout.splitlines():
        normalized = normalize_candidate(line, domain)
        if normalized:
            observations.setdefault(normalized, set()).add("findomain")
    run.observations = len(observations)
    return observations, run


def run_assetfinder(domain: str, timeout: int) -> Tuple[Dict[str, Set[str]], ToolRun]:
    run, stdout = run_command(["assetfinder", "--subs-only", domain], "assetfinder", timeout)
    observations: Dict[str, Set[str]] = {}
    for line in stdout.splitlines():
        normalized = normalize_candidate(line, domain)
        if normalized:
            observations.setdefault(normalized, set()).add("assetfinder")
    run.observations = len(observations)
    return observations, run


_CIRCUIT_BREAKER_RATE_LIMITED: Set[str] = set()


def reset_circuit_breakers() -> None:
    _CIRCUIT_BREAKER_RATE_LIMITED.clear()


def run_crtname(
    domain: str,
    timeout: int = 15,
) -> Tuple[Dict[str, Set[str]], ToolRun, Dict[str, Dict[str, Any]]]:
    effective_timeout = max(1, min(timeout, 15)) if timeout else 15
    started = time.monotonic()

    if "crt.name" in _CIRCUIT_BREAKER_RATE_LIMITED:
        run = ToolRun(
            name="crt.name",
            command=["GET", "https://crt.name/v1/search"],
            success=False,
            duration_seconds=0.0,
            error="rate_limited",
            metadata={"reason": "rate_limited"},
        )
        return {}, run, {}

    apex = extract_apex_domain(domain) or domain
    params = urllib.parse.urlencode({"apex": apex, "format": "json", "dates": "1"})
    url = f"https://crt.name/v1/search?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"sub-enum/{VERSION} (+https://github.com/tobiasGuta/sub-enum)",
            "Accept": "application/json",
        },
    )

    observations: Dict[str, Set[str]] = {}
    provider_metadata: Dict[str, Dict[str, Any]] = {}
    max_bytes = 25 * 1024 * 1024  # 25MB response protection

    try:
        with urllib.request.urlopen(req, timeout=effective_timeout) as response:
            status_code = getattr(response, "status", 200)
            if status_code == 429:
                _CIRCUIT_BREAKER_RATE_LIMITED.add("crt.name")
                run = ToolRun(
                    name="crt.name",
                    command=["GET", url],
                    success=False,
                    duration_seconds=time.monotonic() - started,
                    returncode=429,
                    error="rate_limited",
                    metadata={"reason": "rate_limited"},
                )
                return {}, run, {}

            content = response.read(max_bytes + 1)
            if len(content) > max_bytes:
                run = ToolRun(
                    name="crt.name",
                    command=["GET", url],
                    success=False,
                    duration_seconds=time.monotonic() - started,
                    error="response_too_large",
                    metadata={"max_bytes": max_bytes},
                )
                return {}, run, {}

            raw_text = content.decode("utf-8", errors="replace")

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            run = ToolRun(
                name="crt.name",
                command=["GET", url],
                success=False,
                duration_seconds=time.monotonic() - started,
                error=f"malformed_json: {exc}",
            )
            return {}, run, {}

        if not isinstance(data, list):
            run = ToolRun(
                name="crt.name",
                command=["GET", url],
                success=False,
                duration_seconds=time.monotonic() - started,
                error=f"unexpected_response_format: expected list, got {type(data).__name__}",
            )
            return {}, run, {}

        for item in data:
            if not isinstance(item, dict):
                continue
            raw_sub = item.get("sub") or item.get("subdomain") or item.get("name")
            if not raw_sub:
                continue
            normalized = normalize_candidate(str(raw_sub), domain)
            if not normalized:
                continue
            observations.setdefault(normalized, set()).add("crt.name")

            raw_first_seen = item.get("first_seen")
            if isinstance(raw_first_seen, str) and raw_first_seen.strip():
                clean_date = raw_first_seen.strip()
                existing_meta = provider_metadata.setdefault(normalized, {})
                prev_date = existing_meta.get("first_seen")
                if prev_date:
                    existing_meta["first_seen"] = min(str(prev_date), clean_date)
                else:
                    existing_meta["first_seen"] = clean_date

        run = ToolRun(
            name="crt.name",
            command=["GET", url],
            success=True,
            duration_seconds=time.monotonic() - started,
            observations=len(observations),
            metadata={"apex": apex, "target_scope": domain},
        )
        return observations, run, provider_metadata

    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            _CIRCUIT_BREAKER_RATE_LIMITED.add("crt.name")
            error_reason = "rate_limited"
        else:
            error_reason = f"HTTP {exc.code}: {exc.reason}"
        run = ToolRun(
            name="crt.name",
            command=["GET", url],
            success=False,
            duration_seconds=time.monotonic() - started,
            returncode=exc.code,
            error=error_reason,
            metadata={"reason": error_reason},
        )
        return {}, run, {}
    except urllib.error.URLError as exc:
        run = ToolRun(
            name="crt.name",
            command=["GET", url],
            success=False,
            duration_seconds=time.monotonic() - started,
            error=f"network_error: {exc.reason}",
        )
        return {}, run, {}
    except (TimeoutError, socket.timeout):
        run = ToolRun(
            name="crt.name",
            command=["GET", url],
            success=False,
            duration_seconds=time.monotonic() - started,
            error=f"timed out after {effective_timeout} seconds",
        )
        return {}, run, {}
    except Exception as exc:
        run = ToolRun(
            name="crt.name",
            command=["GET", url],
            success=False,
            duration_seconds=time.monotonic() - started,
            error=str(exc),
        )
        return {}, run, {}


def _dns_values(item: Dict[str, Any], key: str) -> List[str]:
    value = item.get(key)
    if value is None:
        # Some ProjectDiscovery JSON serializers use upper-case DNS record names.
        value = item.get(key.upper())
    if value is None:
        return []
    if isinstance(value, list):
        return sorted({str(entry).rstrip(".") for entry in value if entry})
    if isinstance(value, str):
        return [value.rstrip(".")]
    return [str(value)]


def _merge_dns_json(raw: str, domain: str, records: Dict[str, Dict[str, Any]], query_key: str) -> None:
    for item in _parse_json_lines(raw):
        host = item.get("host") or item.get("input") or item.get("name")
        normalized = normalize_candidate(str(host or ""), domain)
        if not normalized:
            continue
        evidence = records.setdefault(normalized, {})
        values = _dns_values(item, query_key)
        if values:
            evidence[query_key] = values
        if item.get("cdn"):
            evidence["cdn"] = item.get("cdn")
        if item.get("asn"):
            evidence["asn"] = item.get("asn")
        if item.get("rcode") or item.get("status_code"):
            evidence["rcode"] = item.get("rcode") or item.get("status_code")
        if item.get("wildcard") is not None:
            evidence["wildcard"] = bool(item.get("wildcard"))


def _run_dns_query(
    input_file: str,
    domain: str,
    query_key: str,
    timeout: int,
    rate_limit: Optional[int],
    auto_wildcard: bool,
) -> Tuple[ToolRun, str]:
    command = ["dnsx", "-l", input_file, "-silent", "-json", "-omit-raw", "-disable-update-check"]
    if query_key != "a":
        command.append(f"-{query_key}")
    if rate_limit and rate_limit > 0:
        command.extend(["-rate-limit", str(rate_limit)])
    if auto_wildcard and query_key == "a":
        command.append("-auto-wildcard")
    run, stdout = run_command(command, f"dnsx:{query_key}", timeout)

    # dnsx <=1.2.x does not know -auto-wildcard. Fall back to the documented
    # wildcard-domain mode so users with older installations still fail safely.
    if auto_wildcard and query_key == "a" and not run.success and "auto-wildcard" in (run.stderr + (run.error or "")):
        fallback = [
            "dnsx", "-l", input_file, "-silent", "-json", "-omit-raw",
            "-disable-update-check", "-wildcard-domain", domain,
        ]
        if rate_limit and rate_limit > 0:
            fallback.extend(["-rate-limit", str(rate_limit)])
        run, stdout = run_command(fallback, "dnsx:a:wildcard", timeout)
        run.metadata["wildcard_mode"] = "wildcard-domain"
    elif auto_wildcard and query_key == "a":
        run.metadata["wildcard_mode"] = "auto-wildcard"
    return run, stdout


def run_dnsx(
    domain: str,
    hosts: Iterable[str],
    timeout: int,
    rate_limit: Optional[int] = None,
) -> Tuple[Dict[str, Dict[str, Any]], List[ToolRun]]:
    candidates = sorted(set(hosts))
    if not candidates:
        return {}, []

    records: Dict[str, Dict[str, Any]] = {}
    runs: List[ToolRun] = []
    temp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("\n".join(candidates) + "\n")
            temp_path = handle.name

        for key in ("a", "aaaa", "cname"):
            run, stdout = _run_dns_query(
                temp_path,
                domain,
                key,
                timeout,
                rate_limit,
                auto_wildcard=(key == "a"),
            )
            runs.append(run)
            if run.success:
                _merge_dns_json(stdout, domain, records, key)

        for hostname, evidence in records.items():
            evidence["validated"] = bool(evidence.get("a") or evidence.get("aaaa") or evidence.get("cname"))
        return records, runs
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def run_alterx(domain: str, hosts: Iterable[str], timeout: int, limit: int = 5000) -> Tuple[Set[str], ToolRun]:
    candidates = sorted(set(hosts))
    if not candidates:
        return set(), ToolRun("alterx", [], True, 0.0, observations=0)
    temp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("\n".join(candidates) + "\n")
            temp_path = handle.name
        command = ["alterx", "-l", temp_path, "-enrich", "-silent", "-disable-update-check"]
        if limit > 0:
            command.extend(["-limit", str(limit)])
        run, stdout = run_command(command, "alterx", timeout)
        generated = {
            normalized
            for line in stdout.splitlines()
            if (normalized := normalize_candidate(line, domain)) is not None
        }
        generated.difference_update(candidates)
        run.observations = len(generated)
        return generated, run
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def run_puredns_resolve(
    domain: str,
    hosts: Iterable[str],
    timeout: int,
    resolvers: Optional[str] = None,
    trusted_resolvers: Optional[str] = None,
) -> Tuple[Set[str], Set[str], ToolRun]:
    candidates = sorted(set(hosts))
    if not candidates:
        return set(), set(), ToolRun("puredns", [], True, 0.0, observations=0)

    with tempfile.TemporaryDirectory(prefix="subenum-puredns-") as tmp:
        base = Path(tmp)
        input_path = base / "input.txt"
        valid_path = base / "valid.txt"
        wildcard_path = base / "wildcards.txt"
        write_lines(input_path, candidates)
        command = [
            "puredns", "resolve", str(input_path),
            "--write", str(valid_path),
            "--write-wildcards", str(wildcard_path),
        ]
        if resolvers:
            command.extend(["--resolvers", resolvers])
        if trusted_resolvers:
            command.extend(["--resolvers-trusted", trusted_resolvers])
        run, _ = run_command(command, "puredns", timeout)
        valid = set(valid_path.read_text(encoding="utf-8").splitlines()) if valid_path.exists() else set()
        wildcards = set(wildcard_path.read_text(encoding="utf-8").splitlines()) if wildcard_path.exists() else set()
        valid = {host for host in (normalize_candidate(item, domain) for item in valid) if host}
        wildcards = {item.strip().lstrip("*.").rstrip(".") for item in wildcards if item.strip()}
        run.observations = len(valid)
        run.metadata["wildcard_roots"] = sorted(wildcards)
        return valid, wildcards, run


def run_puredns_bruteforce(
    domain: str,
    wordlist: str,
    timeout: int,
    resolvers: Optional[str] = None,
    trusted_resolvers: Optional[str] = None,
) -> Tuple[Set[str], Set[str], ToolRun]:
    with tempfile.TemporaryDirectory(prefix="subenum-brute-") as tmp:
        base = Path(tmp)
        valid_path = base / "valid.txt"
        wildcard_path = base / "wildcards.txt"
        command = [
            "puredns", "bruteforce", wordlist, domain,
            "--write", str(valid_path),
            "--write-wildcards", str(wildcard_path),
        ]
        if resolvers:
            command.extend(["--resolvers", resolvers])
        if trusted_resolvers:
            command.extend(["--resolvers-trusted", trusted_resolvers])
        run, _ = run_command(command, "puredns:bruteforce", timeout)
        valid = set(valid_path.read_text(encoding="utf-8").splitlines()) if valid_path.exists() else set()
        wildcards = set(wildcard_path.read_text(encoding="utf-8").splitlines()) if wildcard_path.exists() else set()
        valid = {host for host in (normalize_candidate(item, domain) for item in valid) if host}
        wildcards = {item.strip().lstrip("*.").rstrip(".") for item in wildcards if item.strip()}
        run.observations = len(valid)
        run.metadata["wildcard_roots"] = sorted(wildcards)
        return valid, wildcards, run


def run_httpx(
    domain: str,
    hosts: Iterable[str],
    timeout: int,
    threads: int = 50,
) -> Tuple[Dict[str, List[Dict[str, Any]]], ToolRun]:
    candidates = sorted(set(hosts))
    if not candidates:
        return {}, ToolRun("httpx", [], True, 0.0, observations=0)
    temp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("\n".join(candidates) + "\n")
            temp_path = handle.name
        command = [
            "httpx", "-l", temp_path, "-json", "-silent", "-disable-update-check",
            "-status-code", "-title", "-tech-detect", "-ip", "-cname", "-cdn",
            "-threads", str(max(1, threads)),
        ]
        run, stdout = run_command(command, "httpx", timeout)
        results: Dict[str, List[Dict[str, Any]]] = {}
        for item in _parse_json_lines(stdout):
            raw_host = item.get("host") or item.get("input") or item.get("url")
            normalized = normalize_candidate(str(raw_host or ""), domain)
            if not normalized and item.get("url"):
                match = re.match(r"https?://([^/:]+)", str(item["url"]))
                if match:
                    normalized = normalize_candidate(match.group(1), domain)
            if not normalized:
                continue
            evidence = {
                "url": item.get("url") or item.get("input"),
                "status_code": item.get("status_code"),
                "title": item.get("title"),
                "technologies": item.get("tech") or item.get("technologies") or [],
                "ip": item.get("host_ip") or item.get("ip"),
                "cname": item.get("cname"),
                "cdn": item.get("cdn_name") or item.get("cdn"),
                "webserver": item.get("webserver"),
            }
            results.setdefault(normalized, []).append({k: v for k, v in evidence.items() if v not in (None, "", [])})
        run.observations = sum(len(items) for items in results.values())
        return results, run
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def tool_version(tool: str, timeout: int = 10) -> Optional[str]:
    path = shutil.which(tool)
    if not path:
        return None
    flags = ["-version", "--version", "version"]
    for flag in flags:
        run, stdout = run_command([path, flag], f"{tool}:version", timeout)
        text = (stdout or run.stderr).strip()
        if run.success and text:
            return text.splitlines()[0][:200]
    return "installed"


def parse_httpx_output(lines: Iterable[str]) -> Set[str]:
    """Legacy helper retained for downstream users/tests of v0.1 output."""
    urls: Set[str] = set()
    for line in lines:
        match = re.search(r"(https?://\S+)", line)
        if match:
            urls.add(match.group(1))
    return urls

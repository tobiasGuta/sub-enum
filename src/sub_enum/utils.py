from __future__ import annotations

import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def _logger_success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


if not hasattr(logging.Logger, "success"):
    logging.Logger.success = _logger_success  # type: ignore[attr-defined]


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[96m",
        logging.INFO: "\033[94m",
        SUCCESS_LEVEL: "\033[92m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[91m",
        logging.CRITICAL: "\033[91m",
    }
    RESET = "\033[0m"

    def format(self, record):
        message = record.getMessage()
        if getattr(record, "raw", False) or not sys.stdout.isatty():
            return message
        return f"{self.COLORS.get(record.levelno, '')}{message}{self.RESET}"


def configure_logging(level=logging.INFO) -> None:
    root_logger = logging.getLogger("sub_enum")
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.propagate = False
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter())
    root_logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger("sub_enum" if name is None else f"sub_enum.{name}")


logger = get_logger(__name__)

ALLOWED_ENV_VARS = {
    "CHAOS_KEY",
    "CHAOS_API_KEY",
    "SUBFINDER_API_KEY",
    "GITHUB_TOKEN",
    "SECURITYTRAILS_KEY",
}

BLOCKED_ENV_VARS = {
    "PATH",
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "PYTHONPATH",
    "PYTHONHOME",
    "GOPATH",
    "GOBIN",
    "GOROOT",
    "HOME",
    "SHELL",
    "IFS",
}


def load_env(filepath: str = ".env") -> None:
    """Load only explicitly allowed credential variables from a simple .env file."""
    path = Path(filepath)
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in ALLOWED_ENV_VARS and key not in BLOCKED_ENV_VARS:
            os.environ[key] = value.strip()
        else:
            logger.warning(f"[!] Skipping unsafe or unknown env var: {key}")


def check_tool_availability(tool: str) -> Optional[str]:
    return shutil.which(tool)


def ensure_path_context() -> None:
    """Prepend Sub-Enum-managed and common user binary paths portably."""
    home = Path.home()
    candidates = [
        home / ".sub-enum" / "bin",
        home / ".sub-enum" / "go" / "bin",
        home / "go" / "bin",
        home / ".cargo" / "bin",
        home / ".local" / "bin",
    ]
    current = os.environ.get("PATH", "")
    existing = current.split(os.pathsep) if current else []
    prepend = [str(path) for path in candidates if str(path) not in existing]
    if prepend:
        os.environ["PATH"] = os.pathsep.join(prepend + existing)


def validate_domain(domain: str) -> Optional[str]:
    """Normalize a user supplied root domain into an ASCII FQDN."""
    if not domain:
        return None
    value = domain.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/", 1)[0].split(":", 1)[0].rstrip(".")
    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    if len(value) > 253:
        return None
    labels = value.split(".")
    if len(labels) < 2:
        return None
    label_re = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
    if any(not label_re.match(label) for label in labels):
        return None
    if not re.fullmatch(r"[a-z]{2,63}|xn--[a-z0-9-]{2,59}", labels[-1]):
        return None
    return value


COMMON_MULTIPART_SUFFIXES = {
    "ac.jp", "ac.uk", "co.il", "co.in", "co.jp", "co.kr", "co.nz", "co.uk", "co.za",
    "com.ar", "com.au", "com.br", "com.cn", "com.hk", "com.mx", "com.sg", "com.tr", "com.tw",
    "edu.au", "edu.cn", "edu.hk", "edu.mx", "edu.sg", "edu.tr", "edu.tw",
    "gov.ar", "gov.au", "gov.br", "gov.cn", "gov.hk", "gov.il", "gov.in", "gov.sg", "gov.tr", "gov.tw", "gov.uk", "gov.za",
    "govt.nz", "id.au", "idv.hk", "idv.tw", "ltd.uk", "me.uk", "ne.jp", "ne.kr", "net.au",
    "net.br", "net.cn", "net.hk", "net.in", "net.mx", "net.nz", "net.sg", "net.tr", "net.tw", "net.uk", "net.za",
    "or.jp", "or.kr", "org.ar", "org.au", "org.br", "org.cn", "org.hk", "org.il", "org.in", "org.mx", "org.nz", "org.sg", "org.tr", "org.tw", "org.uk", "org.za",
    "plc.uk",
}


def extract_apex_domain(domain: str) -> Optional[str]:
    """Extract the registrable eTLD+1 apex from a domain or subdomain."""
    normalized = validate_domain(domain)
    if not normalized:
        return None
    labels = normalized.split(".")
    if len(labels) <= 2:
        return normalized
    two_part = f"{labels[-2]}.{labels[-1]}"
    if two_part in COMMON_MULTIPART_SUFFIXES:
        return ".".join(labels[-3:]) if len(labels) >= 3 else normalized
    return ".".join(labels[-2:])


def normalize_candidate(candidate: str, root_domain: str) -> Optional[str]:
    """Normalize an external-tool result and enforce the requested root scope."""
    if not candidate:
        return None
    value = candidate.strip().lower().rstrip(".")
    value = re.sub(r"^https?://", "", value)
    value = value.split("/", 1)[0]
    if ":" in value and not value.startswith("["):
        value = value.split(":", 1)[0]
    normalized = validate_domain(value)
    if not normalized:
        return None
    if normalized == root_domain or normalized.endswith(f".{root_domain}"):
        return normalized
    return None


def safe_output_path(base_dir: Path, requested: str) -> Path:
    base = base_dir.resolve()
    candidate = Path(requested)
    if not candidate.is_absolute():
        candidate = base / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"output path escapes target directory: {requested}") from exc
    return candidate


def write_lines(path: Path, values: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    unique = sorted({value for value in values if value})
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(unique) + ("\n" if unique else ""), encoding="utf-8")
    tmp.replace(path)

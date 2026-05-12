import builtins
import logging
import os
import shutil
import re
import subprocess
import sys
from typing import List, Optional

from .config import BLUE, RED, YELLOW, GREEN, CYAN, RESET

# Global flag set by the CLI to control interactive prompts/auto-yes behavior
_AUTO_YES = False
SUCCESS_LEVEL = 25

logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def _logger_success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


if not hasattr(logging.Logger, "success"):
    logging.Logger.success = _logger_success


class ColorFormatter(logging.Formatter):
    """Apply ANSI colors based on the log level."""

    LEVEL_COLORS = {
        logging.DEBUG: CYAN,
        logging.INFO: BLUE,
        SUCCESS_LEVEL: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: RED,
    }

    def format(self, record):
        message = record.getMessage()
        if getattr(record, "raw", False):
            return message

        color = self.LEVEL_COLORS.get(record.levelno, RESET)
        return f"{color}{message}{RESET}"


def configure_logging(level=logging.INFO) -> None:
    """Configure structured console logging for the application."""
    root_logger = logging.getLogger("sub_enum")
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter())
    root_logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger under the application namespace."""
    return logging.getLogger("sub_enum" if name is None else f"sub_enum.{name}")


logger = get_logger(__name__)

# Only accept configuration keys that are expected to hold API credentials.
# System-sensitive variables are always rejected even if they appear in .env.
ALLOWED_ENV_VARS = {
    "CHAOS_KEY",
    "CHAOS_API_KEY",
    "SUBFINDER_API_KEY",
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
    "TERM",
}


def set_auto_yes(value: bool) -> None:
    """Set whether interactive prompts should default to yes.

    Call this from the CLI (core) when `--yes` / non-interactive mode is requested.
    """
    global _AUTO_YES
    _AUTO_YES = bool(value)


def get_auto_yes() -> bool:
    return _AUTO_YES

def _should_load_env_key(key: str) -> bool:
    """Return True only for safe, expected environment variables."""
    normalized_key = key.strip()
    if not normalized_key:
        return False
    if normalized_key in BLOCKED_ENV_VARS:
        return False
    return normalized_key in ALLOWED_ENV_VARS

def load_env(filepath=".env"):
    """Load environment variables from a .env file."""
    if not os.path.exists(filepath):
        return
    logger.info(f"[*] Loading configuration from {filepath}...")
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                normalized_key = key.strip()
                normalized_value = value.strip()
                if _should_load_env_key(normalized_key):
                    os.environ[normalized_key] = normalized_value
                else:
                    logger.warning(f"[!] Skipping unsafe or unknown env var: {normalized_key}")

def check_tool_availability(tool):
    """Check if a tool is available in the system PATH."""
    return shutil.which(tool)

def ensure_path_context():
    """Ensure Go and Rust bin directories are in PATH for the current process."""
    home = os.path.expanduser("~")
    go_bin = os.path.join(home, "go", "bin")
    cargo_bin = os.path.join(home, ".cargo", "bin")
    local_bin = os.path.join(home, ".local", "bin")
    tool_bin = os.path.join(home, ".sub-enum", "bin")
    current_path = os.environ.get("PATH", "")
    path_elems: List[str] = current_path.split(":") if current_path else []
    paths_to_add: List[str] = []

    def _add_if_missing(p: str) -> None:
        if p and p not in path_elems:
            paths_to_add.append(p)

    _add_if_missing(tool_bin)
    _add_if_missing(go_bin)
    _add_if_missing(cargo_bin)
    _add_if_missing(local_bin)

    if paths_to_add:
        # Prepend paths so local tools take precedence
        os.environ["PATH"] = f"{':'.join(paths_to_add)}:{current_path}"

def validate_domain(domain):
    """Validate and clean the domain input."""
    if not domain:
        return None
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.split('/')[0]
    domain = domain.rstrip('/')
    
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not re.match(pattern, domain):
        return None
    return domain

def remove_conflicting_httpx():
    """Warn about a conflicting httpx and prefer the Go binary via PATH."""
    httpx_path = shutil.which("httpx")
    if not httpx_path:
        return
    if os.path.normpath(os.path.join(os.path.expanduser("~"), "go", "bin")) in os.path.normpath(httpx_path):
        return

    logger.warning(f"[!] Found conflicting httpx at {httpx_path}.")
    logger.warning("[!] Leaving the binary untouched. Prepending the local Go bin directory to PATH will make the correct httpx take precedence.")
    ensure_path_context()

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Tuple

from .config import PINNED_GO_TOOLS
from .utils import ensure_path_context, get_logger

logger = get_logger(__name__)

HOME = Path.home()
BASE_DIR = HOME / ".sub-enum"
BIN_DIR = BASE_DIR / "bin"
GO_DIR = BASE_DIR / "go"


def init_workspace() -> None:
    BIN_DIR.mkdir(parents=True, exist_ok=True)


def install_pinned_go_tool(tool_name: str) -> bool:
    """Install a tested Go tool ref; never use @latest."""
    if tool_name not in PINNED_GO_TOOLS:
        raise ValueError(f"unsupported managed tool: {tool_name}")
    ensure_path_context()
    go = shutil.which("go")
    if not go:
        logger.error("[✗] Go is required to install managed Go tools. Install Go 1.25+ first.")
        return False

    package, ref = PINNED_GO_TOOLS[tool_name]
    env = os.environ.copy()
    env["GOBIN"] = str(BIN_DIR)
    command = [go, "install", f"{package}@{ref}"]
    logger.info(f"[*] Installing {tool_name} from pinned ref {ref}...")
    result = subprocess.run(command, env=env, text=True)
    if result.returncode != 0:
        logger.error(f"[✗] Failed to install {tool_name} ({ref}).")
        return False
    logger.success(f"[✓] Installed {tool_name} {ref} to {BIN_DIR}")
    return True


def install_many(tool_names: Iterable[str]) -> Tuple[int, int]:
    successes = 0
    failures = 0
    for name in tool_names:
        if install_pinned_go_tool(name):
            successes += 1
        else:
            failures += 1
    return successes, failures

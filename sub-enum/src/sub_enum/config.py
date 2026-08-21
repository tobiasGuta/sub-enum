from __future__ import annotations

VERSION = "0.2.0"

ART = (
    "\033[96m\n"
    + r"""
  _____       _       ______
 / ____|     | |     |  ____|
| (___  _   _| |__   | |__   _ __  _   _ _ __ ___
 \___ \| | | | '_ \  |  __| | '_ \| | | | '_ ` _ \
 ____) | |_| | |_) | | |____| | | | |_| | | | | | |
|_____/ \__,_|_.__/  |______|_| |_|\__,_|_| |_| |_|
"""
    + f"                                    v{VERSION}\n"
    + "\033[0m\n"
)

PINNED_GO_TOOLS = {
    "subfinder": ("github.com/projectdiscovery/subfinder/v2/cmd/subfinder", "v2.14.0"),
    "dnsx": ("github.com/projectdiscovery/dnsx/cmd/dnsx", "v1.3.0"),
    "httpx": ("github.com/projectdiscovery/httpx/cmd/httpx", "v1.10.0"),
    "alterx": ("github.com/projectdiscovery/alterx/cmd/alterx", "v0.1.0"),
    "puredns": ("github.com/d3mondev/puredns/v2", "v2.1.1"),
    "assetfinder": ("github.com/tomnomnom/assetfinder", "4e95d8701aae8cff1c27af2626eb22ba110ad583"),
}

REQUIRED_STANDARD = ("subfinder", "dnsx", "httpx")
OPTIONAL_TOOLS = ("findomain", "alterx", "puredns", "massdns", "assetfinder")

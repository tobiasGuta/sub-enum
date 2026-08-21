from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AssetRecord:
    """Canonical representation of one in-scope hostname.

    The record intentionally stores discovery provenance and validation evidence
    separately. A passive observation is useful even if the hostname no longer
    resolves, while DNS/HTTP evidence can raise confidence for active triage.
    """

    hostname: str
    root_domain: str
    sources: Set[str] = field(default_factory=set)
    methods: Set[str] = field(default_factory=set)
    dns: Dict[str, Any] = field(default_factory=dict)
    http: List[Dict[str, Any]] = field(default_factory=list)
    provider_observations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    wildcard: bool = False
    dangling_cname_candidate: bool = False
    first_seen: str = field(default_factory=utc_now)
    last_seen: str = field(default_factory=utc_now)

    def observe(self, source: str, method: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if source:
            self.sources.add(source)
        if method:
            self.methods.add(method)
        if metadata:
            existing = self.provider_observations.setdefault(source, {})
            for key, value in metadata.items():
                if value is None:
                    continue
                if key == "first_seen":
                    prev = existing.get("first_seen")
                    if prev:
                        # Earliest observation date wins
                        existing["first_seen"] = min(str(prev), str(value))
                    else:
                        existing["first_seen"] = str(value)
                else:
                    existing[key] = value
        self.last_seen = utc_now()

    def merge_dns(self, evidence: Dict[str, Any]) -> None:
        for key, value in evidence.items():
            if value in (None, "", [], {}):
                continue
            if isinstance(value, list):
                existing = self.dns.get(key, [])
                if not isinstance(existing, list):
                    existing = [existing]
                self.dns[key] = sorted({str(item) for item in existing + value if item})
            else:
                self.dns[key] = value
        self.last_seen = utc_now()

    def add_http(self, evidence: Dict[str, Any]) -> None:
        if not evidence:
            return
        url = evidence.get("url")
        if url and any(item.get("url") == url for item in self.http):
            return
        self.http.append(evidence)
        self.last_seen = utc_now()

    @property
    def dns_validated(self) -> bool:
        for key in ("a", "aaaa", "cname"):
            value = self.dns.get(key)
            if value:
                return True
        return bool(self.dns.get("validated"))

    @property
    def confidence(self) -> str:
        if self.wildcard:
            return "wildcard_suspect"
        if self.dangling_cname_candidate:
            return "dangling_cname_candidate"
        if self.dns_validated and len(self.sources) > 1:
            return "confirmed"
        if self.dns_validated:
            return "resolved"
        if "permutation" in self.methods or "bruteforce" in self.methods:
            return "generated"
        return "passive_only"

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "hostname": self.hostname,
            "root_domain": self.root_domain,
            "sources": sorted(self.sources),
            "methods": sorted(self.methods),
            "dns": self.dns,
            "http": self.http,
            "wildcard": self.wildcard,
            "dangling_cname_candidate": self.dangling_cname_candidate,
            "confidence": self.confidence,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }
        if self.provider_observations:
            payload["provider_observations"] = self.provider_observations
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetRecord":
        asset = cls(
            hostname=data["hostname"],
            root_domain=data["root_domain"],
            sources=set(data.get("sources", [])),
            methods=set(data.get("methods", [])),
            dns=dict(data.get("dns", {})),
            http=list(data.get("http", [])),
            provider_observations=dict(data.get("provider_observations", {})),
            wildcard=bool(data.get("wildcard", False)),
            dangling_cname_candidate=bool(data.get("dangling_cname_candidate", False)),
            first_seen=data.get("first_seen") or utc_now(),
            last_seen=data.get("last_seen") or utc_now(),
        )
        return asset


def source_statistics(assets: Iterable[AssetRecord]) -> Dict[str, int]:
    stats: Dict[str, int] = {}
    for asset in assets:
        for source in asset.sources:
            stats[source] = stats.get(source, 0) + 1
    return dict(sorted(stats.items(), key=lambda item: (-item[1], item[0])))

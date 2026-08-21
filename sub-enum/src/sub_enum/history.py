from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import AssetRecord, utc_now


def default_db_path() -> Path:
    return Path.home() / ".sub-enum" / "history.db"


def _connect(path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = path or default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_domain TEXT NOT NULL,
            profile TEXT NOT NULL,
            created_at TEXT NOT NULL,
            asset_count INTEGER NOT NULL,
            source_stats_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            scan_id INTEGER NOT NULL,
            hostname TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (scan_id, hostname),
            FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
        )
        """
    )
    return conn


def save_scan(
    root_domain: str,
    profile: str,
    assets: Iterable[AssetRecord],
    source_stats: Dict[str, int],
    db_path: Optional[Path] = None,
) -> int:
    asset_list = sorted(assets, key=lambda item: item.hostname)
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO scans(root_domain, profile, created_at, asset_count, source_stats_json) VALUES (?, ?, ?, ?, ?)",
            (root_domain, profile, utc_now(), len(asset_list), json.dumps(source_stats, sort_keys=True)),
        )
        scan_id = int(cursor.lastrowid)
        conn.executemany(
            "INSERT INTO assets(scan_id, hostname, payload_json) VALUES (?, ?, ?)",
            [
                (scan_id, asset.hostname, json.dumps(asset.to_dict(), sort_keys=True))
                for asset in asset_list
            ],
        )
        conn.commit()
        return scan_id
    finally:
        conn.close()


def recent_scans(root_domain: str, limit: int = 10, db_path: Optional[Path] = None) -> List[Dict[str, object]]:
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, root_domain, profile, created_at, asset_count, source_stats_json FROM scans WHERE root_domain=? ORDER BY id DESC LIMIT ?",
            (root_domain, max(1, limit)),
        ).fetchall()
        result: List[Dict[str, object]] = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "root_domain": row["root_domain"],
                    "profile": row["profile"],
                    "created_at": row["created_at"],
                    "asset_count": row["asset_count"],
                    "source_stats": json.loads(row["source_stats_json"]),
                }
            )
        return result
    finally:
        conn.close()


def load_scan_assets(scan_id: int, db_path: Optional[Path] = None) -> Dict[str, AssetRecord]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT hostname, payload_json FROM assets WHERE scan_id=? ORDER BY hostname",
            (scan_id,),
        ).fetchall()
        return {hostname: AssetRecord.from_dict(json.loads(payload)) for hostname, payload in rows}
    finally:
        conn.close()


def diff_recent(root_domain: str, db_path: Optional[Path] = None) -> Optional[Dict[str, object]]:
    scans = recent_scans(root_domain, limit=2, db_path=db_path)
    if len(scans) < 2:
        return None
    newest, previous = scans[0], scans[1]
    new_assets = load_scan_assets(int(newest["id"]), db_path=db_path)
    old_assets = load_scan_assets(int(previous["id"]), db_path=db_path)

    new_names = set(new_assets)
    old_names = set(old_assets)
    added = sorted(new_names - old_names)
    removed = sorted(old_names - new_names)
    changed: List[Dict[str, object]] = []

    for hostname in sorted(new_names & old_names):
        before = old_assets[hostname].to_dict()
        after = new_assets[hostname].to_dict()
        deltas: Dict[str, object] = {}
        for field in ("dns", "http", "wildcard", "dangling_cname_candidate", "confidence"):
            if before.get(field) != after.get(field):
                deltas[field] = {"before": before.get(field), "after": after.get(field)}
        if deltas:
            changed.append({"hostname": hostname, "changes": deltas})

    return {
        "new_scan": newest,
        "previous_scan": previous,
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def latest_source_stats(root_domain: str, db_path: Optional[Path] = None) -> Optional[Dict[str, int]]:
    scans = recent_scans(root_domain, limit=1, db_path=db_path)
    if not scans:
        return None
    return dict(scans[0]["source_stats"])  # type: ignore[arg-type]

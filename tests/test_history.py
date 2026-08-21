from sub_enum.history import diff_recent, recent_scans, save_scan
from sub_enum.models import AssetRecord, source_statistics


def test_history_and_diff(tmp_path):
    db = tmp_path / "history.db"
    first = AssetRecord("api.example.com", "example.com")
    first.observe("subfinder:crtsh", "passive")
    first.merge_dns({"a": ["203.0.113.10"], "validated": True})
    save_scan("example.com", "standard", [first], source_statistics([first]), db)

    changed = AssetRecord("api.example.com", "example.com")
    changed.observe("subfinder:crtsh", "passive")
    changed.merge_dns({"a": ["203.0.113.11"], "validated": True})
    added = AssetRecord("new.example.com", "example.com")
    added.observe("findomain", "passive")
    save_scan("example.com", "standard", [changed, added], source_statistics([changed, added]), db)

    assert len(recent_scans("example.com", db_path=db)) == 2
    diff = diff_recent("example.com", db_path=db)
    assert diff is not None
    assert diff["added"] == ["new.example.com"]
    assert diff["removed"] == []
    assert diff["changed"][0]["hostname"] == "api.example.com"

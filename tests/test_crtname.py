import io
import json
import socket
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest

from sub_enum.core import build_parser, scan_target
from sub_enum.models import AssetRecord, source_statistics
from sub_enum.tools import (
    _CIRCUIT_BREAKER_RATE_LIMITED,
    reset_circuit_breakers,
    run_crtname,
)
from sub_enum.utils import extract_apex_domain


@pytest.fixture(autouse=True)
def cleanup_circuit_breakers():
    reset_circuit_breakers()
    yield
    reset_circuit_breakers()


# Captured representative fixture from https://crt.name/v1/search?apex=example.com&format=json&dates=1
CRTNAME_SAMPLE_FIXTURE = [
    {"first_seen": "2009-07-03T20:37:11Z", "sub": "example.com"},
    {"first_seen": "2009-07-04T00:54:41Z", "sub": "dummy-host.example.com"},
    {"first_seen": "2009-11-20T15:42:25Z", "sub": "xri.example.com"},
    {"first_seen": "2009-11-20T15:42:30Z", "sub": "openid.example.com"},
    {"first_seen": "2026-05-03T19:50:40Z", "sub": "dev.example.com"},
    {"first_seen": "2026-06-21T18:50:32Z", "sub": "ns1.example.com"},
    {"first_seen": None, "sub": "0.0.1.example.com"},
    {"first_seen": None, "sub": "cloud.example.com"},
]


def test_extract_apex_domain_standard_and_multipart():
    assert extract_apex_domain("example.com") == "example.com"
    assert extract_apex_domain("api.example.com") == "example.com"
    assert extract_apex_domain("dev.staging.api.example.com") == "example.com"
    assert extract_apex_domain("example.co.uk") == "example.co.uk"
    assert extract_apex_domain("api.example.co.uk") == "example.co.uk"
    assert extract_apex_domain("dev.sub.example.com.au") == "example.com.au"
    assert extract_apex_domain("invalid") is None


def test_crtname_success_with_sample_fixture():
    raw_json = json.dumps(CRTNAME_SAMPLE_FIXTURE).encode("utf-8")
    mock_response = io.BytesIO(raw_json)
    setattr(mock_response, "status", 200)

    with patch("urllib.request.urlopen", return_value=mock_response):
        observations, run, meta = run_crtname("example.com", timeout=10)

    assert run.success is True
    assert run.error is None
    assert run.observations == 8
    assert "dev.example.com" in observations
    assert "crt.name" in observations["dev.example.com"]
    assert meta["dev.example.com"]["first_seen"] == "2026-05-03T19:50:40Z"
    assert "0.0.1.example.com" not in meta or "first_seen" not in meta["0.0.1.example.com"]


def test_crtname_apex_query_and_subdomain_scope_filter():
    # If user scans api.example.com, crt.name queries apex example.com,
    # but results are filtered back strictly to api.example.com and *.api.example.com
    fixture = [
        {"first_seen": "2024-01-01T00:00:00Z", "sub": "example.com"},
        {"first_seen": "2024-01-02T00:00:00Z", "sub": "foo.example.com"},
        {"first_seen": "2024-01-03T00:00:00Z", "sub": "api.example.com"},
        {"first_seen": "2024-01-04T00:00:00Z", "sub": "dev.api.example.com"},
    ]
    raw_json = json.dumps(fixture).encode("utf-8")
    mock_response = io.BytesIO(raw_json)
    setattr(mock_response, "status", 200)

    captured_url = []

    def mock_urlopen(req, timeout=None):
        captured_url.append(req.full_url)
        return io.BytesIO(raw_json)

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        observations, run, meta = run_crtname("api.example.com", timeout=10)

    assert "apex=example.com" in captured_url[0]
    assert run.success is True
    # Only in-scope candidates for api.example.com accepted:
    assert set(observations.keys()) == {"api.example.com", "dev.api.example.com"}
    assert run.observations == 2


def test_crtname_duplicate_entries_earliest_date_wins():
    fixture = [
        {"first_seen": "2024-05-01T12:00:00Z", "sub": "api.example.com"},
        {"first_seen": "2022-03-15T08:30:00Z", "sub": "api.example.com"},
        {"first_seen": "2023-01-01T00:00:00Z", "sub": "api.example.com"},
    ]
    raw_json = json.dumps(fixture).encode("utf-8")

    with patch("urllib.request.urlopen", return_value=io.BytesIO(raw_json)):
        observations, run, meta = run_crtname("example.com", timeout=10)

    assert run.observations == 1
    assert meta["api.example.com"]["first_seen"] == "2022-03-15T08:30:00Z"


def test_asset_record_observe_earliest_date_preservation():
    asset = AssetRecord("api.example.com", "example.com")
    asset.observe("crt.name", "passive", metadata={"first_seen": "2024-05-01T00:00:00Z"})
    assert asset.provider_observations["crt.name"]["first_seen"] == "2024-05-01T00:00:00Z"

    # Later observation with earlier historical date updates to earlier date
    asset.observe("crt.name", "passive", metadata={"first_seen": "2021-11-20T10:00:00Z"})
    assert asset.provider_observations["crt.name"]["first_seen"] == "2021-11-20T10:00:00Z"

    # Later observation with later date does NOT overwrite earlier date
    asset.observe("crt.name", "passive", metadata={"first_seen": "2025-01-01T00:00:00Z"})
    assert asset.provider_observations["crt.name"]["first_seen"] == "2021-11-20T10:00:00Z"


def test_crtname_scope_rejection_of_out_of_scope_and_boundary_tricks():
    fixture = [
        {"first_seen": "2024-01-01T00:00:00Z", "sub": "valid.example.com"},
        {"first_seen": "2024-01-01T00:00:00Z", "sub": "example.com.attacker.com"},
        {"first_seen": "2024-01-01T00:00:00Z", "sub": "api-example.com"},
        {"first_seen": "2024-01-01T00:00:00Z", "sub": "otherdomain.com"},
        {"first_seen": "2024-01-01T00:00:00Z", "sub": "invalid..example.com"},
    ]
    raw_json = json.dumps(fixture).encode("utf-8")

    with patch("urllib.request.urlopen", return_value=io.BytesIO(raw_json)):
        observations, run, _ = run_crtname("example.com", timeout=10)

    assert set(observations.keys()) == {"valid.example.com"}
    assert run.observations == 1


def test_crtname_empty_response_success():
    raw_json = b"[]"
    with patch("urllib.request.urlopen", return_value=io.BytesIO(raw_json)):
        observations, run, _ = run_crtname("example.com", timeout=10)

    assert run.success is True
    assert run.error is None
    assert run.observations == 0
    assert observations == {}


def test_crtname_http_429_rate_limit_circuit_breaker():
    http_err = urllib.error.HTTPError(
        url="https://crt.name/v1/search?apex=example.com",
        code=429,
        msg="Too Many Requests",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        _, run1, _ = run_crtname("example.com", timeout=10)

    assert run1.success is False
    assert run1.error == "rate_limited"
    assert "crt.name" in _CIRCUIT_BREAKER_RATE_LIMITED

    # Subsequent invocation should be short-circuited immediately without network call
    with patch("urllib.request.urlopen") as mock_urlopen:
        _, run2, _ = run_crtname("example2.com", timeout=10)
        mock_urlopen.assert_not_called()

    assert run2.success is False
    assert run2.error == "rate_limited"


def test_crtname_http_500_error():
    http_err = urllib.error.HTTPError(
        url="https://crt.name/v1/search?apex=example.com",
        code=500,
        msg="Internal Server Error",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        _, run, _ = run_crtname("example.com", timeout=10)

    assert run.success is False
    assert "HTTP 500" in (run.error or "")
    assert run.observations == 0


def test_crtname_network_timeout():
    with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
        _, run, _ = run_crtname("example.com", timeout=10)

    assert run.success is False
    assert "timed out" in (run.error or "")
    assert run.observations == 0


def test_crtname_url_error():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        _, run, _ = run_crtname("example.com", timeout=10)

    assert run.success is False
    assert "network_error" in (run.error or "")


def test_crtname_malformed_json():
    with patch("urllib.request.urlopen", return_value=io.BytesIO(b"<html>502 Bad Gateway</html>")):
        _, run, _ = run_crtname("example.com", timeout=10)

    assert run.success is False
    assert "malformed_json" in (run.error or "")


def test_crtname_response_too_large_protection():
    # Create stream exceeding 25MB limit
    huge_data = b"[" + b'{"sub":"a.example.com"},' * (2 * 1024 * 1024) + b'{"sub":"b.example.com"}]'
    with patch("urllib.request.urlopen", return_value=io.BytesIO(huge_data)):
        _, run, _ = run_crtname("example.com", timeout=10)

    assert run.success is False
    assert run.error == "response_too_large"


def test_provenance_merging_with_multiple_sources():
    asset = AssetRecord("api.example.com", "example.com")
    asset.observe("subfinder:crtsh", "passive")
    asset.observe("findomain", "passive")
    asset.observe("crt.name", "passive", metadata={"first_seen": "2024-04-20T10:00:00Z"})

    assert asset.sources == {"subfinder:crtsh", "findomain", "crt.name"}
    assert asset.methods == {"passive"}
    assert asset.provider_observations["crt.name"] == {"first_seen": "2024-04-20T10:00:00Z"}
    assert source_statistics([asset]) == {"crt.name": 1, "findomain": 1, "subfinder:crtsh": 1}


def test_cli_no_crtname_flag():
    parser = build_parser()
    args = parser.parse_args(["scan", "-d", "example.com", "--no-crtname"])
    assert args.no_crtname is True


def test_scan_target_passive_profile_integrates_crtname(tmp_path):
    from sub_enum.tools import ToolRun

    parser = build_parser()
    args = parser.parse_args(["scan", "-d", "example.com", "--profile", "passive", "--output-root", str(tmp_path), "--no-history"])

    mock_crt_raw = json.dumps([{"sub": "crt.example.com", "first_seen": "2024-01-01T00:00:00Z"}]).encode("utf-8")
    subfinder_run = ToolRun("subfinder", ["subfinder", "-d", "example.com"], True, 0.1, observations=1)

    with patch("sub_enum.core.run_subfinder", return_value=({"sub.example.com": {"subfinder:crtsh"}}, subfinder_run)), \
         patch("urllib.request.urlopen", return_value=io.BytesIO(mock_crt_raw)):
        code = scan_target("example.com", args)

    assert code == 0
    assets_file = tmp_path / "example.com" / "assets.jsonl"
    assert assets_file.exists()
    lines = [json.loads(line) for line in assets_file.read_text(encoding="utf-8").splitlines()]
    host_to_line = {item["hostname"]: item for item in lines}
    assert "crt.example.com" in host_to_line
    assert "crt.name" in host_to_line["crt.example.com"]["sources"]
    assert host_to_line["crt.example.com"]["provider_observations"]["crt.name"]["first_seen"] == "2024-01-01T00:00:00Z"


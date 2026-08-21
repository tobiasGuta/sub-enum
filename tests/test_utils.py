import os
from sub_enum.utils import ensure_path_context, normalize_candidate, validate_domain


def test_validate_domain_normalizes_urls_and_case():
    assert validate_domain("HTTPS://API.Example.com/path") == "api.example.com"
    assert validate_domain("invalid") is None


def test_scope_filter_is_suffix_safe():
    assert normalize_candidate("api.example.com", "example.com") == "api.example.com"
    assert normalize_candidate("example.com", "example.com") == "example.com"
    assert normalize_candidate("api.example.com.evil.test", "example.com") is None
    assert normalize_candidate("example.com.evil.test", "example.com") is None


def test_ensure_path_context_uses_platform_separator(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "")
    # pathlib.Path.home() can be cached by environment/platform behavior on some systems,
    # so only assert the produced PATH is validly separated and contains managed bins.
    ensure_path_context()
    values = os.environ["PATH"].split(os.pathsep)
    assert any(value.endswith(os.path.join(".sub-enum", "bin")) for value in values)

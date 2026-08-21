from sub_enum.tools import _dns_values, parse_httpx_output


def test_parse_httpx_output_legacy_helper():
    lines = [
        "https://admin.example.com | 200 | text/html",
        "http://test.example.com | 404 | text/html",
        "Some other text https://api.example.com/path?query=1 extra",
        "no-url-here",
    ]
    assert parse_httpx_output(lines) == {
        "https://admin.example.com",
        "http://test.example.com",
        "https://api.example.com/path?query=1",
    }


def test_dns_values_accepts_list_and_string():
    assert _dns_values({"a": ["1.1.1.1", "1.1.1.1"]}, "a") == ["1.1.1.1"]
    assert _dns_values({"cname": "edge.example.net."}, "cname") == ["edge.example.net"]

from sub_enum.core import build_parser


def test_scan_defaults_are_bounty_focused():
    parser = build_parser()
    args = parser.parse_args(["scan", "-d", "example.com"])
    assert args.profile == "standard"
    assert args.assetfinder is False
    assert args.no_permutations is False
    assert args.dns_backend == "auto"

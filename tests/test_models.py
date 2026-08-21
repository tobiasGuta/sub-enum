from sub_enum.models import AssetRecord, source_statistics


def test_asset_confidence_and_merge():
    asset = AssetRecord("api.example.com", "example.com")
    asset.observe("subfinder:crtsh", "passive")
    assert asset.confidence == "passive_only"

    asset.merge_dns({"a": ["203.0.113.10"], "validated": True})
    assert asset.confidence == "resolved"

    asset.observe("findomain", "passive")
    assert asset.confidence == "confirmed"
    assert source_statistics([asset]) == {"findomain": 1, "subfinder:crtsh": 1}


def test_generated_candidate_is_not_claimed_valid():
    asset = AssetRecord("dev.example.com", "example.com")
    asset.observe("alterx:enrich", "permutation")
    assert asset.confidence == "generated"
    assert not asset.dns_validated

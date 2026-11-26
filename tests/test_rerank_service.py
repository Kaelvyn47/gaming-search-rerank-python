from unittest.mock import patch

from src.rerank_service import Asset, rerank_assets


def test_rerank_keeps_live_assets_in_the_relevance_order() -> None:
    assets = [
        Asset("event", "Weekend arena event", "live_event", "live"),
        Asset("guide", "Crystal Cavern raid guide", "player_asset", "live"),
        Asset("queue", "Pending chat report", "moderation_queue", "queued"),
    ]
    envelope = {"ok": True, "data": [{"text": "Crystal Cavern raid guide", "score": 0.97}, {"text": "Weekend arena event", "score": 0.31}], "error": None, "metadata": {}}
    with patch("src.rerank_service._post_json", return_value=envelope) as request:
        ranked = rerank_assets("raid builds", assets)
    assert [item.asset.asset_id for item in ranked] == ["guide", "event"]
    request.assert_called_once()
    assert request.call_args.args[0] == "/v1/ai/rerank"

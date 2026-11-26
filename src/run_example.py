from rerank_service import Asset, rerank_assets


def main() -> None:
    assets = [
        Asset("a-17", "Crystal Cavern raid guide", "player_asset", "live"),
        Asset("e-04", "Weekend arena event", "live_event", "live"),
        Asset("m-22", "Pending chat report", "moderation_queue", "queued"),
    ]
    for item in rerank_assets("raid builds for new players", assets):
        print(f"{item.asset.asset_id}\t{item.score:.3f}\t{item.asset.title}")


if __name__ == "__main__":
    main()

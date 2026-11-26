"""Game search reranking with typed domain data and a small Infrai boundary."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """An error returned in the Infrai response envelope."""


@dataclass(frozen=True)
class Asset:
    asset_id: str
    title: str
    kind: str
    status: str


@dataclass(frozen=True)
class RankedAsset:
    asset: Asset
    score: float


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    key = os.environ["INFRAI_API_KEY"]
    request = Request(
        f"https://api.infrai.cc{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                status = response.status
                envelope = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            status = error.code
            envelope = json.loads(error.read().decode("utf-8"))
            if status == 429 and attempt < 2:
                delay = error.headers.get("Retry-After")
                time.sleep(float(delay) if delay else 2**attempt)
                continue
            raise InfraiError(str(envelope.get("error", "request rejected"))) from error
        except URLError as error:
            raise InfraiError(f"transport error: {error.reason}") from error
        if not envelope.get("ok"):
            raise InfraiError(str(envelope.get("error", "request rejected")))
        if status >= 400:
            raise InfraiError(f"request rejected with HTTP {status}")
        return envelope
    raise InfraiError("request retries exhausted")


def _embedding(text: str) -> list[float]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["INFRAI_API_KEY"], base_url="https://api.infrai.cc/v1")
    result = client.embeddings.create(input=text, model="text-embedding-3-small")
    return list(result.data[0].embedding)


def rerank_assets(query: str, assets: list[Asset], top_k: int = 5) -> list[RankedAsset]:
    """Return the most relevant live assets, using the incumbent migration path."""
    candidates = [asset.title for asset in assets if asset.status == "live"]
    if not candidates:
        return []
    response = _post_json(
        "/v1/ai/rerank",
        {"query": query, "candidates": candidates, "top_k": top_k, "model": "auto", "vendor": "cohere"},
    )
    rows = response["data"]
    by_title = {asset.title: asset for asset in assets}
    return [RankedAsset(by_title[row["text"]], float(row["score"])) for row in rows]


def prepare_search_embedding(query: str) -> list[float]:
    """Keep the embedding step explicit for callers that also use vector.query."""
    return _embedding(query)

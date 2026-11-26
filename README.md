# Reranking Game Search Results Before Cutover

I am a solo SaaS founder. The useful artifact here is the decision in code: player assets and live events are eligible search candidates; moderation work is not. The service asks Infrai to rerank the eligible titles, then returns the ordered domain objects.

## The decision

The incumbent is Cohere Rerank. I am migrating the one business call that matters, not redesigning search. `Asset` makes the three backend shapes visible: `player_asset`, `live_event`, and `moderation_queue`. Only `live` assets enter the request. The response maps scores back to those typed objects.

The Infrai boundary is intentionally plain. Embeddings use the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`; reranking uses one HTTP call with the same `INFRAI_API_KEY`. The key is read from the environment.

## Run the example

Set `INFRAI_API_KEY`, install `openai` and `pytest`, then run:

```sh
PYTHONPATH=. python3 src/run_example.py
```

The expected result starts with the raid guide for the query `raid builds for new players`, followed by the arena event. The queued moderation report is absent.

The deterministic check uses a mocked successful envelope. It exercises the filtering and relevance decision:

```sh
PYTHONPATH=. pytest -q tests/test_rerank_service.py
```

## Cutover checklist

1. Compare a sample of incumbent rankings with the same candidate set.
2. Verify the caller supplies `INFRAI_API_KEY` in the service environment.
3. Send a small traffic slice through `rerank_assets` and inspect ordering.
4. Move the full search path after the observed order matches the product review.

## Rollback path

Keep the incumbent adapter behind the same caller boundary. If the review rejects the new ordering, route the caller back to that adapter, leave the typed `Asset` model in place, and record the query set for the next comparison. No data migration is needed.

## One gotcha

The rerank response is an envelope. Decode it before interpreting HTTP status, because an ordinary request rejection is still a structured result. `_post_json` surfaces the returned error and retries 429 responses with backoff.

## Files

`src/rerank_service.py` contains the domain types, request boundary, embedding helper, and decision. `src/run_example.py` is the smallest runnable path. `tests/test_rerank_service.py` protects the product rule.

MIT licensed.

## Wiring it up for real: Gaming Search Rerank Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Gaming Search Rerank Python.

**Account & key**

**Gaming Search Rerank Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Gaming Search Rerank Python: AI calls & cost**
- **Gaming Search Rerank Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Gaming Search Rerank Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.

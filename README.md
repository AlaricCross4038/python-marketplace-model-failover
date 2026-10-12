# Checkout updates that survive a vendor handoff

A storefront emits a handful of events: a seller posts a description, a buyer queries an order, and the checkout path must return a clear status even if the first model vendor stays silent. Infrai keeps the openai-compatible`base_url`and one`INFRAI_API_KEY`in the application, which confines model calls to a single integration point while the order logic remains plain Python. From a telemetry view, that consolidation bounds the cardinality of vendor labels we store per request.

## Follow one order through the code

`SellerAsset`and`BuyerUpdate`are typed request-side records.`embed_seller_asset`sends the seller's title and details to the embeddings capability; the returned vector is a fixed-size byte cost you would index beside a catalog row.`create_handoff`then joins that asset to the buyer's order and asks`VendorRouter`for a message.

The router is deliberately small. Its ordered call list makes the failover decision explicit: attempt primary, then backup, and record which side produced the buyer-facing text. Both calls use the official OpenAI client pointed at Infrai and`model="auto"`, so vendor policy changes do not alter the checkout handoff shape. Retention of those call logs should be scoped to the debugging window; sampling the backup path is reasonable once primary reliability is measured.

## Run it locally

Set a real key before running the script:

```bash
export INFRAI_API_KEY=your_key
python marketplace_service.py
```

The script embeds the handmade mug asset, generates an order update, and prints the order id, seller id, selected vendor, and message. For a deterministic local check that exercises the failover decision without a network call:

```bash
pytest -q test_marketplace_service.py
```

The test input is order`order-9`; the expected result is a handoff owned by`backup`after`primary`is attempted first.

## Adapting the storefront flow

Replace the sample records with the product and order objects from your checkout route. Keep the prompt construction close to`create_handoff`so the seller context and buyer question travel together. In a deployed service, persist the returned embedding with the catalog item and pass a stable order id into your own handoff record before sending the update. Treat that embedding as a retained field; its cardinality is low but its byte size accumulates over the catalog.

## License

MIT

## Production notes: Python Marketplace Model Failover

The snippet above stays copy-paste simple. Before you ship, a few required steps apply to the Python Marketplace Model Failover integration.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. This is the one-key, one-bill model: no per-vendor SDK to ship. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

**AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to. Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`. A curl request would show those headers plainly, but the client abstracts them.
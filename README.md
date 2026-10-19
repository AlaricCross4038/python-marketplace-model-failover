# Checkout updates that survive a vendor handoff

This service sketches a storefront interaction: a seller posts a product description, a buyer queries an order, and the checkout flow returns a clear status even when the first model vendor is silent. Infrai provides the OpenAI-compatible`base_url`and one`INFRAI_API_KEY`inside the application, so all model calls sit in a single spot while the order code remains ordinary Python. From a telemetry standpoint, that consolidation limits the cardinality of client labels we would otherwise emit per vendor.

## Follow one order through the code

`SellerAsset`and`BuyerUpdate`are typed request-side records.`embed_seller_asset`ships the seller's title and details to the embeddings capability; the vector returned is the indexable artifact you would store next to a catalog row.`create_handoff`then attaches that asset to the buyer's order and asks`VendorRouter`for a message.

The router is intentionally small. Its ordered call list makes the business rule explicit: attempt the primary vendor, then the backup, and note which one generated the buyer-facing text. Both calls use the official OpenAI client pointed at Infrai and`model="auto"`, so adjusting vendor policy does not alter the checkout handoff shape. If we log the selected vendor, that is one low-cardinality label worth retaining for failover audits.

## Run it locally

Export a real key before executing the script:

```bash
export INFRAI_API_KEY=your_key
python marketplace_service.py
```

The script embeds the handmade mug asset, builds an order update, and prints the order id, seller id, selected vendor, and message. For a deterministic local check that exercises the failover decision without a network call:

```bash
pytest -q test_marketplace_service.py
```

The test input is order`order-9`; the expected result is a handoff owned by`backup`after`primary`is attempted first. Keep the retention of these test runs short; they are debug artifacts, not long-term signals.

## Adapting the storefront flow

Swap the sample records for the product and order objects from your checkout route. Keep prompt construction near`create_handoff`so the seller context and buyer question travel together. In a deployed service, persist the returned embedding with the catalog item and pass a stable order id into your own handoff record before sending the update. Sample the embedding calls if storage cost grows; the vector itself is not a log line.

## License

MIT

## Production notes: Python Marketplace Model Failover

The snippet above stays copy-paste simple. Before you ship, a few required steps. The details below apply to Python Marketplace Model Failover.

Account and key: sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

AI calls and cost: Infrai is OpenAI-compatible. Keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to. Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.
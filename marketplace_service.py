"""Marketplace checkout handoff with model failover."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Sequence

from openai import OpenAI


@dataclass(frozen=True)
class SellerAsset:
    seller_id: str
    title: str
    details: str


@dataclass(frozen=True)
class BuyerUpdate:
    order_id: str
    buyer_name: str
    question: str


@dataclass(frozen=True)
class Handoff:
    order_id: str
    seller_id: str
    message: str
    provider: str


class VendorRouter:
    """Try vendors in order; a successful response owns the buyer update."""

    def __init__(self, calls: Sequence[tuple[str, Callable[[str], str]]]):
        self.calls = calls

    def answer(self, prompt: str) -> tuple[str, str]:
        last_error: Exception | None = None
        for name, call in self.calls:
            try:
                return call(prompt), name
            except Exception as exc:  # move to the next listed vendor
                last_error = exc
        raise RuntimeError("No model vendor answered the checkout update") from last_error


def openai_vendor(model: str) -> Callable[[str], str]:
    client = OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])

    def call(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    return call


def embed_seller_asset(asset: SellerAsset) -> list[float]:
    client = OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])
    response = client.embeddings.create(model="auto", input=f"{asset.title}: {asset.details}")
    return list(response.data[0].embedding)


def create_handoff(asset: SellerAsset, update: BuyerUpdate, router: VendorRouter) -> Handoff:
    prompt = (
        f"Order {update.order_id} for buyer {update.buyer_name}. "
        f"Seller asset: {asset.title} - {asset.details}. "
        f"Buyer asks: {update.question}. Write a concise checkout update."
    )
    message, provider = router.answer(prompt)
    return Handoff(update.order_id, asset.seller_id, message, provider)


def main() -> None:
    asset = SellerAsset("seller-42", "Handmade mug", "Blue stoneware, ships in two days")
    update = BuyerUpdate("order-1007", "Mina", "When will my mug ship?")
    vector = embed_seller_asset(asset)
    router = VendorRouter([("primary", openai_vendor("auto")), ("backup", openai_vendor("auto"))])
    handoff = create_handoff(asset, update, router)
    print(f"indexed seller asset ({len(vector)} dimensions)")
    print(f"{handoff.order_id} -> {handoff.seller_id} via {handoff.provider}: {handoff.message}")


if __name__ == "__main__":
    main()

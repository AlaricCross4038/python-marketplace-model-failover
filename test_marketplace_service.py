from marketplace_service import BuyerUpdate, SellerAsset, VendorRouter, create_handoff


def test_checkout_handoff_uses_backup_after_primary_failure() -> None:
    attempts: list[str] = []

    def primary(_: str) -> str:
        attempts.append("primary")
        raise RuntimeError("vendor unavailable")

    def backup(prompt: str) -> str:
        attempts.append("backup")
        assert "order-9" in prompt
        return "Your order is queued for dispatch."

    handoff = create_handoff(
        SellerAsset("seller-7", "Canvas tote", "Ships tomorrow"),
        BuyerUpdate("order-9", "Kai", "Is it ready?"),
        VendorRouter([("primary", primary), ("backup", backup)]),
    )
    assert attempts == ["primary", "backup"]
    assert handoff.provider == "backup"
    assert handoff.seller_id == "seller-7"

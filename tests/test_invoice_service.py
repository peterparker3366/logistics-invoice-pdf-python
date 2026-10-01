import pytest

from src.invoice_service import LogisticsOrder, ProofOfDelivery, ShipmentEvent, ready_for_invoice


def test_invoice_waits_for_proof_and_cleared_exception():
    delivered = ShipmentEvent("delivered", "2026-09-03T16:20:00Z", "Singapore")
    base = LogisticsOrder("ORD-1", "Studio", "A", "B", 20.0, [delivered])
    assert ready_for_invoice(base) is False
    with_proof = LogisticsOrder("ORD-1", "Studio", "A", "B", 20.0, [delivered], [ProofOfDelivery("pod.jpg", "hash")])
    assert ready_for_invoice(with_proof) is True
    blocked = LogisticsOrder("ORD-1", "Studio", "A", "B", 20.0, [delivered], [ProofOfDelivery("pod.jpg", "hash")], "damaged carton")
    assert ready_for_invoice(blocked) is False

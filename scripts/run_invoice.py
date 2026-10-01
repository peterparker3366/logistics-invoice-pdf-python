import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.invoice_service import InfraiPdfClient, LogisticsOrder, ProofOfDelivery, ShipmentEvent, generate_invoice


def main() -> None:
    order = LogisticsOrder(
        order_id="ORD-2048",
        customer="Northline Media",
        origin="Shenzhen",
        destination="Singapore",
        amount=184.50,
        events=[ShipmentEvent("picked_up", "2026-09-01T09:00:00Z", "Shenzhen"), ShipmentEvent("delivered", "2026-09-03T16:20:00Z", "Singapore")],
        proof_files=[ProofOfDelivery("pod-2048.jpg", "demo-sha256")],
    )
    result = generate_invoice(order, InfraiPdfClient())
    print(result["data"])


if __name__ == "__main__":
    main()

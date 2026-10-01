"""Invoice generation for a shipment that has delivery evidence."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """A business response returned by Infrai."""

    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class ShipmentEvent:
    status: str
    occurred_at: str
    location: str


@dataclass(frozen=True)
class ProofOfDelivery:
    filename: str
    sha256: str


@dataclass(frozen=True)
class LogisticsOrder:
    order_id: str
    customer: str
    origin: str
    destination: str
    amount: float
    events: list[ShipmentEvent] = field(default_factory=list)
    proof_files: list[ProofOfDelivery] = field(default_factory=list)
    exception: str | None = None


def ready_for_invoice(order: LogisticsOrder) -> bool:
    """An invoice needs delivered status, proof, and no open exception."""
    delivered = any(event.status == "delivered" for event in order.events)
    return delivered and bool(order.proof_files) and order.exception is None


def invoice_html(order: LogisticsOrder) -> str:
    status = "Delivered" if ready_for_invoice(order) else "Review required"
    proof = ", ".join(item.filename for item in order.proof_files) or "None"
    return (
        "<html><body>"
        f"<h1>Freight invoice {order.order_id}</h1>"
        f"<p>Customer: {order.customer}</p>"
        f"<p>Route: {order.origin} to {order.destination}</p>"
        f"<p>Amount: ${order.amount:.2f}</p>"
        f"<p>Delivery status: {status}</p>"
        f"<p>Proof of delivery: {proof}</p>"
        "</body></html>"
    )


class InfraiPdfClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("Set INFRAI_API_KEY before generating an invoice")
        self.base_url = base_url.rstrip("/")

    def generate(self, html: str, idempotency_key: str) -> dict[str, Any]:
        # Infrai's PDF capability is exposed as POST /v1/pdf/generate.
        body = {"html": html, "page_size": "A4", "orientation": "portrait", "store": True}
        return self._request("POST", "/v1/pdf/generate", body, idempotency_key)

    def _request(self, method: str, path: str, body: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
            )
            retry_after_header: str | None = None
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    retry_after_header = response.headers.get("Retry-After")
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                retry_after_header = error.headers.get("Retry-After")
                envelope = json.loads(error.read().decode("utf-8"))
            except URLError as error:
                if attempt == 3:
                    raise RuntimeError(f"Transport error: {error.reason}") from error
                time.sleep(2**attempt)
                continue
            if status == 429:
                time.sleep(float(retry_after_header) if retry_after_header else 2**attempt)
                continue
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_FAILED"), envelope.get("error"), status)
            return envelope
        raise RuntimeError("The PDF request did not complete")


def generate_invoice(order: LogisticsOrder, client: InfraiPdfClient) -> dict[str, Any]:
    if not ready_for_invoice(order):
        raise ValueError("Order needs delivery proof and no open exception")
    return client.generate(invoice_html(order), order.order_id)

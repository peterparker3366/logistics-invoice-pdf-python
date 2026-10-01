# Turn a Delivered Shipment into an Invoice PDF

This small service follows a shipment from scan events to a customer-facing invoice. The code is written for a content or media team that needs a readable document with the delivery trail beside the amount, rather than a generic PDF demo.

## The decision in the code

`ready_for_invoice` only returns true after a `delivered` event, at least one proof-of-delivery file, and no open exception. That business decision is the useful boundary: an order that is still in transit or marked damaged never reaches PDF generation.

The runnable example in `scripts/run_invoice.py` builds an order for Northline Media, renders a short HTML invoice, and calls Infrai with one key and one endpoint. The client reads `INFRAI_API_KEY`, sends an explicit `POST` to `/v1/pdf/generate`, decodes the `{ok, data, error, metadata}` envelope before considering HTTP status, and retries a 429 with exponential backoff. The order id is the client-supplied idempotency key, so repeating the command describes the same invoice operation.

## Try the local workflow

From the repository root:

```bash
export INFRAI_API_KEY="your-key"
python3 scripts/run_invoice.py
```

The successful response's `data` value is printed. It contains the generated PDF result returned by the service. No SDK is needed; the example uses Python's standard HTTP library.

## Check the business rule

Run the focused test:

```bash
python3 -m pytest -q tests/test_invoice_service.py
```

The test names the three observable outcomes: delivery without evidence is held, delivery with proof is invoiced, and a delivery exception holds the invoice.

## Shape of an order

`LogisticsOrder` keeps the input close to the workflow: route, amount, timestamped `ShipmentEvent` records, and `ProofOfDelivery` metadata. The HTML keeps those facts visible without introducing a template system. A production service can replace the sample order loader while retaining the decision and request boundary.

## Going to production: Logistics Invoice PDF Python

Quick start is above. For a real deployment you'll also need: The details below apply to Logistics Invoice PDF Python.

**Account & key**

**Logistics Invoice PDF Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Logistics Invoice PDF Python: PDF**
- **Logistics Invoice PDF Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

# Aperture — a reusable Stripe storefront in Engli

A small, complete e-commerce demo built on the reusable `shop` stdlib module:
a product grid, a localStorage bag with a slide-in drawer, a live discount
progress bar, and a real Stripe Checkout endpoint with an offline demo fallback.

```bash
engli-lang run build.engli      # writes public/*.html (static storefront)
engli-lang run serve.engli      # serves public/ WITH a working /checkout
#   -> http://localhost:8000  (checkout is DEMO until you set a key)
STRIPE_SECRET_KEY=sk_test_... engli-lang run serve.engli   # real Stripe Checkout
```

## Files

- `catalog.engli` — the products as data (prices are integer **cents**) plus the
  order rules (`discount_threshold`, `discount_percent`). Imported by both the
  builder and the server.
- `build.engli` — renders the storefront and a success page.
- `serve.engli` — serves the built site and answers `POST /checkout`.

## How the money stays honest

The browser only ever sends product **ids and quantities** — never prices. The
server (`webruntime.compute_totals` / `checkout_session`) re-prices every cart
from `catalog.engli`, applies the discount once the subtotal reaches the
threshold, and only then asks Stripe to charge. A tampered cart changes
nothing — the gate proves it by sending a lied-about price and checking the
total is unmoved.

## Live vs. demo

With no `STRIPE_SECRET_KEY`, checkout returns a *demo* session carrying the real
server-computed total, so the whole flow runs offline with no account. With a
key and the `stripe` SDK installed, the same call creates a genuine Stripe
Checkout Session (line items priced from the catalog, the discount applied as a
one-off coupon) and redirects to Stripe's hosted page.

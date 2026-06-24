# Dummy Shop — Microservices

This is the **microservices** edition of Dummy Shop, decomposed from the original
single-process Flask monolith. The user-facing behaviour (the pages, the routes,
the checkout flow) is unchanged — what changed is that the three business concerns
now run as independent services, each owning its own datastore.

## Architecture

```
                        ┌────────────────────────────┐
        browser  ─────► │  gateway  (Flask + Jinja)   │  :8000   public entrypoint / BFF
                        └──────────────┬─────────────┘
                  ┌───────────────────┼────────────────────┐
                  ▼                   ▼                    ▼
        ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
        │ product-service  │ │  cart-service    │ │  order-service   │
        │  Flask  :8001    │ │  Flask  :8003    │ │  Flask  :8002    │
        └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
                 ▼                    ▼                    ▼
          product-db (MySQL)    cart-redis (Redis)   order-db (MySQL)

   order-service also calls product-service to snapshot price/name at order time.
```

| Service           | Port | Datastore           | Responsibility                                   |
| ----------------- | ---- | ------------------- | ------------------------------------------------ |
| `gateway`         | 8000 | session cookie only | Serves all HTML, orchestrates the other services |
| `product-service` | 8001 | `product-db` MySQL  | Product catalog (browse / detail), seed data     |
| `order-service`   | 8002 | `order-db` MySQL    | Orders + line items; snapshots product price     |
| `cart-service`    | 8003 | `cart-redis` Redis  | Per-browser cart (keyed by a session cart id)    |

### Why these boundaries?

The monolith had one database with `Product`, `Order`, and `OrderItem` tables joined
together. In the split:

- **No cross-service database joins.** `order-service` does not foreign-key into the
  product table. When an order is placed it calls `product-service` over HTTP and
  **snapshots** `product_id`, `name`, and `price` into its own `OrderItem` rows, so
  historical orders stay correct even if a product's price later changes.
- **The cart is ephemeral**, a natural fit for Redis (with a 7-day TTL) rather than a
  relational table. The cart id lives in the gateway's signed session cookie.
- **The gateway is a Backend-for-Frontend**: it keeps the original Jinja templates and
  routes, so the UI is byte-for-byte the same, but every data access is now an HTTP
  call to a service instead of a local DB query.

## Service APIs

**product-service**
- `GET /products` → list of products
- `GET /products/<id>` → one product (404 if missing)
- `GET /health`

**cart-service** (`<cart_id>` comes from the gateway session)
- `GET /carts/<cart_id>` → `{ items: { product_id: qty } }`
- `POST /carts/<cart_id>/items` body `{ product_id, quantity }`
- `DELETE /carts/<cart_id>/items/<product_id>`
- `DELETE /carts/<cart_id>` → clear
- `GET /health`

**order-service**
- `POST /orders` body `{ customer_name, customer_email, address, items:[{product_id, quantity}] }`
- `GET /orders` → all orders (newest first)
- `GET /orders/<id>` → one order
- `GET /health`

## Run it

```bash
docker compose up --build
```

Then open http://localhost:8000. The catalog is auto-seeded by `product-service` on
first start. The individual services are also exposed (8001/8002/8003) for debugging.

To run a single service locally without Docker, each one falls back to SQLite/localhost
defaults — e.g. `cd services/product-service && pip install -r requirements.txt && python app.py`.

## Layout

```
docker-compose.yml          # orchestrates all 7 containers
Jenkinsfile                 # CI: builds every service image
services/
  product-service/          # Flask + SQLAlchemy + MySQL
  order-service/            # Flask + SQLAlchemy + MySQL + requests
  cart-service/             # Flask + Redis
  gateway/                  # Flask + Jinja templates + static + requests
```

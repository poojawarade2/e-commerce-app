import os

import requests
from flask import Flask, jsonify, request

from models import db, Order, OrderItem

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///order.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:8001')
HTTP_TIMEOUT = float(os.environ.get('HTTP_TIMEOUT', '5'))

with app.app_context():
    db.create_all()


def fetch_product(product_id):
    resp = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}', timeout=HTTP_TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


@app.route('/health')
def health():
    return jsonify(status='ok', service='order-service')


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json(force=True, silent=True) or {}
    if not all(data.get(f) for f in ('customer_name', 'customer_email', 'address')):
        return jsonify(error='customer_name, customer_email and address are required'), 400
    line_items = data.get('items') or []
    if not line_items:
        return jsonify(error='order must contain at least one item'), 400

    # Resolve each line item against product-service so price/name are authoritative
    # snapshots, never trusting whatever the caller sent for price.
    resolved = []
    total = 0.0
    try:
        for li in line_items:
            pid = int(li['product_id'])
            qty = int(li.get('quantity', 1))
            if qty < 1:
                return jsonify(error=f'invalid quantity for product {pid}'), 400
            product = fetch_product(pid)
            if product is None:
                return jsonify(error=f'product {pid} not found'), 400
            price = float(product['price'])
            total += price * qty
            resolved.append({
                'product_id': pid,
                'product_name': product['name'],
                'quantity': qty,
                'price': price,
            })
    except (KeyError, ValueError, TypeError):
        return jsonify(error='each item needs a numeric product_id and quantity'), 400
    except requests.RequestException as exc:
        return jsonify(error=f'product-service unavailable: {exc}'), 502

    order = Order(
        customer_name=data['customer_name'],
        customer_email=data['customer_email'],
        address=data['address'],
        total=total,
    )
    db.session.add(order)
    db.session.flush()
    for item in resolved:
        db.session.add(OrderItem(order_id=order.id, **item))
    db.session.commit()
    return jsonify(order.to_dict()), 201


@app.route('/orders')
def list_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders])


@app.route('/orders/<int:order_id>')
def get_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return jsonify(error='Order not found'), 404
    return jsonify(order.to_dict())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=True)

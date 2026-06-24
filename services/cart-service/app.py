import os

import redis
from flask import Flask, jsonify, request

app = Flask(__name__)

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CART_TTL = int(os.environ.get('CART_TTL_SECONDS', 60 * 60 * 24 * 7))  # 7 days

r = redis.from_url(REDIS_URL, decode_responses=True)


def _key(cart_id):
    return f'cart:{cart_id}'


def _items(cart_id):
    raw = r.hgetall(_key(cart_id))
    return {pid: int(qty) for pid, qty in raw.items()}


@app.route('/health')
def health():
    try:
        r.ping()
        return jsonify(status='ok', service='cart-service')
    except redis.RedisError:
        return jsonify(status='degraded', service='cart-service'), 503


@app.route('/carts/<cart_id>')
def get_cart(cart_id):
    return jsonify(cart_id=cart_id, items=_items(cart_id))


@app.route('/carts/<cart_id>/items', methods=['POST'])
def add_item(cart_id):
    data = request.get_json(force=True, silent=True) or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    if product_id in (None, '') or quantity < 1:
        return jsonify(error='product_id and a positive quantity are required'), 400
    key = _key(cart_id)
    r.hincrby(key, str(product_id), quantity)
    r.expire(key, CART_TTL)
    return jsonify(cart_id=cart_id, items=_items(cart_id))


@app.route('/carts/<cart_id>/items/<product_id>', methods=['DELETE'])
def remove_item(cart_id, product_id):
    r.hdel(_key(cart_id), str(product_id))
    return jsonify(cart_id=cart_id, items=_items(cart_id))


@app.route('/carts/<cart_id>', methods=['DELETE'])
def clear_cart(cart_id):
    r.delete(_key(cart_id))
    return jsonify(cart_id=cart_id, items={})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)

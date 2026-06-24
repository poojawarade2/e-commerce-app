import os

from flask import Flask, jsonify

from models import db, Product
from seed import seed_products

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///product.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    seed_products()


@app.route('/health')
def health():
    return jsonify(status='ok', service='product-service')


@app.route('/products')
def list_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])


@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product is None:
        return jsonify(error='Product not found'), 404
    return jsonify(product.to_dict())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)

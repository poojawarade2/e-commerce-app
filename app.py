import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Product, Order, OrderItem

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
db.init_app(app)

with app.app_context():
    db.create_all()


def cart_items_and_total():
    cart = session.get('cart', {})
    items = []
    total = 0.0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            subtotal = product.price * qty
            total += subtotal
            items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return items, total


@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    Product.query.get_or_404(product_id)
    cart = session.get('cart', {})
    qty = max(1, int(request.form.get('quantity', 1)))
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session['cart'] = cart
    flash('Added to cart')
    return redirect(url_for('view_cart'))


@app.route('/cart')
def view_cart():
    items, total = cart_items_and_total()
    return render_template('cart.html', items=items, total=total)


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    items, total = cart_items_and_total()
    if not items:
        return redirect(url_for('index'))

    if request.method == 'POST':
        order = Order(
            customer_name=request.form['name'],
            customer_email=request.form['email'],
            address=request.form['address'],
            total=total,
        )
        db.session.add(order)
        db.session.flush()
        for it in items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=it['product'].id,
                quantity=it['quantity'],
                price=it['product'].price,
            ))
        db.session.commit()
        session['cart'] = {}
        return redirect(url_for('order_success', order_id=order.id))

    return render_template('checkout.html', items=items, total=total)


@app.route('/order/<int:order_id>')
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('order_success.html', order=order)


@app.route('/orders')
def list_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


if __name__ == '__main__':
    app.run(debug=True)


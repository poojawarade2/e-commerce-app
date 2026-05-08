from app import app
from models import db, Product

PRODUCTS = [
    {'name': 'Wireless Headphones', 'description': 'Noise-cancelling over-ear headphones with 30hr battery.', 'price': 2499.00, 'image_url': 'https://placehold.co/300x300?text=Headphones', 'stock': 15},
    {'name': 'Smart Watch', 'description': 'Fitness tracking, heart rate monitor, GPS.', 'price': 3999.00, 'image_url': 'https://placehold.co/300x300?text=Watch', 'stock': 20},
    {'name': 'Bluetooth Speaker', 'description': 'Portable, water-resistant, 12hr playback.', 'price': 1799.00, 'image_url': 'https://placehold.co/300x300?text=Speaker', 'stock': 25},
    {'name': 'Laptop Backpack', 'description': 'Fits 15.6 inch laptops, USB charging port.', 'price': 1299.00, 'image_url': 'https://placehold.co/300x300?text=Backpack', 'stock': 30},
    {'name': 'Mechanical Keyboard', 'description': 'RGB backlit, blue switches, USB-C.', 'price': 4499.00, 'image_url': 'https://placehold.co/300x300?text=Keyboard', 'stock': 10},
    {'name': 'Wireless Mouse', 'description': 'Ergonomic, 6 programmable buttons.', 'price': 899.00, 'image_url': 'https://placehold.co/300x300?text=Mouse', 'stock': 40},
]


def seed():
    with app.app_context():
        db.create_all()
        if Product.query.count() == 0:
            for p in PRODUCTS:
                db.session.add(Product(**p))
            db.session.commit()
            print(f'Seeded {len(PRODUCTS)} products')
        else:
            print('Products already exist, skipping seed')


if __name__ == '__main__':
    seed()

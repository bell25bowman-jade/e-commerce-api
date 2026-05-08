from __future__ import annotations

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from datetime import datetime
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

# MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:812288@localhost/ecommerce_api'

db = SQLAlchemy()
ma = Marshmallow()

db.init_app(app)
ma.init_app(app)


# Association Table (many-to-many)
order_product = db.Table(
    'order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
)

# User table
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    orders = db.relationship('Order', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.name}>"
    
# Order Table
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    products = db.relationship(
        'Product',
        secondary=order_product,
        backref='orders'
    )

    def __repr__(self):
        return f"<Order {self.id}>"

# Product Table
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Product {self.product_name}>"

# Create Tables (after all models are defined)
with app.app_context():
    db.create_all()

#------SCHEMAS-----

# User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True
        load_instance = True

# Product Schema
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        load_instance = True

# Order Schema
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True
        load_instance = True

user_schema = UserSchema()
users_schema = UserSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

#--------USER ROUTES-----------#

# GET all users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return users_schema.jsonify(users)

# GET user by ID
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return user_schema.jsonify(user)

# CREATE user
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json(force=True)

    new_user = User(
        name=data['name'],
        address=data['address'],
        email=data['email']
    )

    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user), 201

# UPDATE user
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)

    data = request.get_json(force=True)

    user.name = data.get('name', user.name)
    user.address = data.get('address', user.address)
    user.email = data.get('email', user.email)

    db.session.commit()

    return user_schema.jsonify(user)

# DELETE user
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"})

# ---------------- PRODUCT ROUTES ---------------- #

# GET all products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

# GET product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return product_schema.jsonify(product)

# CREATE product
@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json(force=True)

    new_product = Product(
        product_name=data['product_name'],
        price=data['price']
    )

    db.session.add(new_product)
    db.session.commit()

    return product_schema.jsonify(new_product), 201

#UPDATE product
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    
    data = request.get_json(force=True)
    
    product.product_name = data.get('product_name', product.product_name)
    product.price = data.get('price', product.price)
    
    db.session.commit()
    
    return product_schema.jsonify(product)
    

# DELETE product
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product deleted successfully"})

# ---------------- ORDER ROUTES ---------------- #

# GET all orders
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return orders_schema.jsonify(orders)

# GET order by ID
@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    return order_schema.jsonify(order)

# CREATE order
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json(force=True)

    new_order = Order(
        user_id=data['user_id']
    )

    db.session.add(new_order)
    db.session.commit()

    return order_schema.jsonify(new_order), 201

# ADD product to order
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):

    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)

    # Prevent duplicates
    if product in order.products:
        return jsonify({"message": "Product already in order"}), 400

    order.products.append(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Product already in order"}), 400

    return jsonify({"message": "Product added to order"})

# REMOVE product from order
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):

    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)

    if product not in order.products:
        return jsonify({"message": "Product not found in order"}), 404

    order.products.remove(product)

    db.session.commit()

    return jsonify({"message": "Product removed from order"})

# GET all orders for a user
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_by_user(user_id):

    orders = Order.query.filter_by(user_id=user_id).all()

    return orders_schema.jsonify(orders)

# GET all products for an order
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_order_products(order_id):

    order = Order.query.get_or_404(order_id)

    return products_schema.jsonify(order.products)

# Run Server
if __name__ == '__main__':
    app.run(debug=True)
    
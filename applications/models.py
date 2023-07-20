from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

database = SQLAlchemy()
migrate = Migrate()

class ProductCategory(database.Model):
    __tablename__ = "productcategory"

    id = database.Column(database.Integer, primary_key = True);
    productId = database.Column(database.Integer, database.ForeignKey("product.id"), nullable = False)
    categoryId = database.Column(database.Integer, database.ForeignKey("category.id"), nullable = False)

class Category(database.Model):
    __tablename__ = "category"

    id = database.Column(database.Integer, primary_key = True)
    name = database.Column(database.String(256), nullable = False)

    products = database.relationship("Product", secondary = ProductCategory.__table__, back_populates = "categories")

class DeliveryProduct(database.Model):
    __tablename__ = "deliveryproduct"

    id = database.Column(database.Integer, primary_key = True)
    deliveryId = database.Column(database.Integer, database.ForeignKey("delivery.id"), nullable = False)
    productId = database.Column(database.Integer, database.ForeignKey("product.id"), nullable = False)
    quantity = database.Column(database.Integer, nullable = False)

class Product(database.Model):
    __tablename__ = "product"

    id = database.Column(database.Integer, primary_key = True)
    name = database.Column(database.String(256), unique = True, nullable = False)
    price = database.Column(database.Float, nullable = False)

    categories = database.relationship("Category", secondary = ProductCategory.__table__, back_populates = "products")
    deliveries = database.relationship("Delivery", secondary = DeliveryProduct.__table__, back_populates = "products")

    def __repr__ ( self ):
        return f"<Product {self.name}, {self.price}>"

class Delivery(database.Model):
    __tablename__ = "delivery"

    id = database.Column(database.Integer, primary_key = True)
    price = database.Column(database.Double, nullable = False)
    status = database.Column(database.Enum('CREATED', 'PENDING', 'COMPLETE'), nullable = False)
    timestamp = database.Column(database.DateTime, nullable = False)
    email = database.Column(database.String(256), nullable = False)

    products = database.relationship("Product", secondary = DeliveryProduct.__table__, back_populates = "deliveries")
    contract = database.relationship("DeliveryContract", back_populates = "delivery", uselist = False )

    def __repr__ ( self ):
        return f"<Order {self.id}, {self.price}, {self.status}, {self.timestamp}, {self.email}>"

class DeliveryContract(database.Model):
    __tablename__ = "deliverycontract"

    deliveryId = database.Column(database.ForeignKey(Delivery.id), primary_key = True)
    contractAddress = database.Column(database.String(256), nullable = False)

    delivery = database.relationship ("Delivery", back_populates = "contract")
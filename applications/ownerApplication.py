from flask import Flask
from flask import request
from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from configuration import Configuration
from decorators import role_check
import xmlrpc.client
import os

from models import database
from models import Product
from models import Category
from models import ProductCategory


application = Flask ( __name__ )
application.config.from_object ( Configuration )

database.init_app ( application )
jwt = JWTManager ( application )
sparkapp = xmlrpc.client.ServerProxy(f"http://{os.environ['SPARKAPP_URL']}:8000")
# owner = Configuration.OWNER_ADDR

@application.route("/update", methods=["POST"])
@role_check ("owner")
def update():

    if "file" not in request.files:
        return jsonify(message = "Field file is missing."), 400

    content = request.files["file"].stream.read().decode()

    for idx, line in enumerate(content.split("\n")):
        
        currParams = line.split(",")

        #check if line is correct

        if(len(currParams) != 3):
            return jsonify(message = "Incorrect number of values on line " + str(idx) +"."), 400
        
        #check if price is valid

        try:
            float(currParams[2])
        except ValueError:
            return jsonify(message = "Incorrect price on line " + str(idx) +"."), 400
        
        if(float(currParams[2]) <= 0):
            return jsonify(message = "Incorrect price on line " + str(idx) +"."), 400

        #check if product exists

        if Product.query.filter(Product.name == currParams[1]).first() is not None:
            return jsonify(message = "Product " + currParams[1] + " already exists."), 400


    for idx, line in enumerate(content.split("\n")):
        
        currParams = line.split(",")
        
        newProduct = Product(
            name = currParams[1],
            price = float(currParams[2])
        )
        
        database.session.add(newProduct)
        database.session.commit()

        for categoryName in currParams[0].split("|"):
            if Category.query.filter(Category.name == categoryName).first() is None:

                newCategory = Category(
                    name = categoryName
                )

                database.session.add(newCategory)
                database.session.commit()
            
            category = Category.query.filter(Category.name == categoryName).first()

            newProductCategory = ProductCategory(
                productId = newProduct.id,
                categoryId = category.id
            )

            database.session.add(newProductCategory)
            database.session.commit()

    return {}, 200


@application.route("/product_statistics", methods=["GET"])
@role_check ("owner")
def productStatistics():

    return sparkapp.products()

@application.route("/category_statistics", methods=["GET"])
@role_check ("owner")
def categoryStatistics():

    return sparkapp.categories()

if(__name__ == "__main__"):
    HOST = "0.0.0.0" if ( "PRODUCTION" in os.environ ) else "127.0.0.1"
    application.run(debug = True, host = HOST)

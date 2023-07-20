from flask import Flask
from flask import request
from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from configuration import Configuration
from decorators import role_check
import os
import json
from datetime import datetime

from models import database
from models import Product
from models import Category
from models import Delivery
from models import DeliveryProduct
from models import DeliveryContract

from web3 import Web3
from web3 import HTTPProvider
from web3 import Account
from web3.exceptions import ContractLogicError

application = Flask ( __name__ )
application.config.from_object ( Configuration )

database.init_app ( application )
jwt = JWTManager ( application )

web3 = Web3(HTTPProvider(f"http://{os.environ['BLOCKCHAIN_URL']}:8545"))

owner = web3.eth.accounts[0]

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )

bytecode = read_file ( "./solidity/output/Order.bin" )
abi      = read_file ( "./solidity/output/Order.abi" )

# purchase_contract = web3.eth.contract(
# abi=purchase_contract_info["abi"],
# bytecode=purchase_contract_info["bytecode"]
# )

@application.route("/search", methods=["GET"])
@role_check ("customer")
def search():

    nameFilter = []
    categoryFilter = []

    if "name" in request.args:
        criterium = "name"
        nameFilter.append(
            getattr(Product, criterium).like(f"%{request.args[criterium]}%")
        )

    if "category" in request.args:
        criterium = "category"
        categoryFilter.append(
            getattr(Category, "name").like(f"%{request.args[criterium]}%")
        )

    products = Product.query.join(Product.categories).filter(*nameFilter).filter(*categoryFilter)

    response = {
        "categories": list(set(category.name for product in products for category in product.categories)),
        "products": [{
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "categories": [category.name for category in product.categories]
        } for product in products]
    }

    return jsonify(response)

@application.route("/status", methods=["GET"])
@role_check ("customer")
def status():

    identity = get_jwt_identity()
    deliveries = Delivery.query.filter(Delivery.email == identity).all()

    orders = []
    for delivery in deliveries:
        order = {
            "products": [],
            "price": delivery.price,
            "status": delivery.status,
            "timestamp": delivery.timestamp.isoformat()
        }

        for product in delivery.products:

            dp = DeliveryProduct.query.filter(DeliveryProduct.productId == product.id, DeliveryProduct.deliveryId == delivery.id).first()

            product_data = {
                "categories": [category.name for category in product.categories],
                "name": product.name,
                "price": product.price,
                "quantity": dp.quantity
            }
            order["products"].append(product_data)

        orders.append(order)

    response = {"orders": orders}
    return jsonify(response)

@application.route("/order", methods=["POST"])
@role_check ("customer")
def order():

    deliveryPrice = 0
    requestData = request.get_json()

    if "requests" not in requestData:
        return jsonify(message = "Field requests is missing."), 400


    for idx, currRequest in enumerate(requestData["requests"]):
        if "id" not in currRequest:
            return jsonify(message = "Product id is missing for request number " + str(idx) + "."), 400
        
        if "quantity" not in currRequest:
            return jsonify(message = "Product quantity is missing for request number " + str(idx) + "."), 400

        try:
            int(currRequest["id"])
        except ValueError:
            return jsonify(message = "Invalid product id for request number " + str(idx) + "."), 400

        if int(currRequest["id"]) <= 0:
            return jsonify(message = "Invalid product id for request number " + str(idx) + "."), 400

        
        try:
            int(currRequest["quantity"])
        except ValueError:
            return jsonify(message = "Invalid product quantity for request number " + str(idx) + "."), 400

        if int(currRequest["quantity"]) <= 0:
            return jsonify(message = "Invalid product quantity for request number " + str(idx) + "."), 400

        if Product.query.filter(Product.id == int(currRequest["id"])).first() is None:
            return jsonify(message = "Invalid product for request number " + str(idx) + "."), 400
        

        currPrice = database.session.query(Product.price).filter(Product.id == int(currRequest["id"])).first()
        deliveryPrice += currPrice[0] * int(currRequest["quantity"])


    if "address" not in requestData or len(requestData["address"]) == 0:
        return jsonify(message = "Field address is missing."), 400
    

    # if not web3.is_address(web3.to_hex(requestData["address"])):
    if not web3.is_address(requestData["address"]):
        return jsonify(message = "Invalid address."), 400

    # create delivery

    newDelivery = Delivery(
        price = deliveryPrice,
        status = "CREATED",
        timestamp = datetime.now(),
        email = get_jwt_identity()
    )

    database.session.add(newDelivery)
    database.session.commit()

    for currRequest in requestData["requests"]:

        newDeliveryProduct = DeliveryProduct(
            deliveryId = newDelivery.id, 
            productId = int(currRequest["id"]),
            quantity = int(currRequest["quantity"])
        )

        database.session.add(newDeliveryProduct)
        database.session.commit()

    #create and deploy contract

    contract = web3.eth.contract ( bytecode = bytecode, abi = abi )

    # customer = web3.to_hex(requestData["address"])
    customer = requestData["address"]

    transaction_hash = contract.constructor(customer).transact ({
        "from": owner
    })

    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    #store contractAddress

    newDeliveryContract = DeliveryContract(
        deliveryId = newDelivery.id,
        contractAddress = receipt.contractAddress
    )

    database.session.add(newDeliveryContract)
    database.session.commit()

    return jsonify(id = newDelivery.id), 200


@application.route("/delivered", methods=["POST"])
@role_check ("customer")
def delivered():

    requestData = request.get_json()

    if "id" not in requestData:
        return jsonify(message = "Missing order id."), 400
    
    try:
        int(requestData["id"])
    except ValueError:
        return jsonify(message = "Invalid order id."), 400
    
    if int(requestData["id"]) <= 0:
        return jsonify(message = "Invalid order id."), 400
    
    delivery = Delivery.query.filter(Delivery.id == int(requestData["id"])).first()

    if delivery is None or delivery.status != "PENDING":
        return jsonify(message = "Invalid order id."), 400

    if "keys" not in requestData or len(requestData["keys"]) == 0:
        return jsonify(message = "Missing keys."), 400
    
    if "passphrase" not in requestData or len(requestData["passphrase"]) == 0:
        return jsonify(message = "Missing passphrase."), 400

    try:
        newKeys = json.loads(requestData["keys"].replace("'", '"'))
        address = web3.to_checksum_address(newKeys["address"])
        private_key = Account.decrypt(newKeys, requestData["passphrase"]).hex()
    except:
        return jsonify(message = "Invalid credentials."), 400
    

    deliveryContract = DeliveryContract.query.filter(DeliveryContract.deliveryId == delivery.id).first()

    currContract = web3.eth.contract(address = deliveryContract.contractAddress, abi = abi)
    
    try:
        store_tx = currContract.functions.delivered().build_transaction(
            {
                "from": address,
                "nonce": web3.eth.get_transaction_count(address),
                "gasPrice": 21000
            }
        )

        signed_tx = web3.eth.account.sign_transaction(store_tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    except ContractLogicError as error:
        errorMessage = str(error)
        prefix = "execution reverted: VM Exception while processing transaction: revert "
        errorMessage = errorMessage[len(prefix):]

        result = {
            "message": errorMessage,
        }
        return jsonify(result), 400

    
    delivery.status = "COMPLETE"
    database.session.commit()

    return {}, 200

@application.route("/pay", methods=["POST"])
@role_check ("customer")
def pay():

    requestData = request.get_json()

    if "id" not in requestData:
        return jsonify(message = "Missing order id."), 400
    
    try:
        int(requestData["id"])
    except ValueError:
        return jsonify(message = "Invalid order id."), 400
    
    if int(requestData["id"]) <= 0:
        return jsonify(message = "Invalid order id."), 400
    
    if Delivery.query.filter(Delivery.id == requestData["id"]).first() is None:
        return jsonify(message = "Invalid order id."), 400
    

    if "keys" not in requestData or len(requestData["keys"]) == 0:
        return jsonify(message = "Missing keys."), 400
    
    if "passphrase" not in requestData or len(requestData["passphrase"]) == 0:
        return jsonify(message = "Missing passphrase."), 400

    try:
        newKeys = json.loads(requestData["keys"].replace("'", '"'))
        address = web3.to_checksum_address(newKeys["address"])
        private_key = Account.decrypt(newKeys, requestData["passphrase"]).hex()
    except:
        return jsonify(message = "Invalid credentials."), 400

    delivery = Delivery.query.filter(Delivery.id == requestData["id"]).first()

    if web3.eth.get_balance(address) < delivery.price:
        return jsonify(message = "Insufficient funds."), 400

    deliveryContract = DeliveryContract.query.filter(DeliveryContract.deliveryId == delivery.id).first()

    currContract = web3.eth.contract(address = deliveryContract.contractAddress, abi = abi)
    
    try:
        store_tx = currContract.functions.pay().build_transaction(
            {
                "from": address,
                "nonce": web3.eth.get_transaction_count(address),
                "gasPrice": 21000,
                "value": int(delivery.price)
            }
        )

        signed_tx = web3.eth.account.sign_transaction(store_tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    except ContractLogicError as error:
        errorMessage = str(error)
        prefix = "execution reverted: VM Exception while processing transaction: revert "
        errorMessage = errorMessage[len(prefix):]

        result = {
            "message": errorMessage,
        }
        return jsonify(result), 400

    return {}, 200


if(__name__ == "__main__"):
    HOST = "0.0.0.0" if ( "PRODUCTION" in os.environ ) else "127.0.0.1"
    application.run(debug = True, host = HOST)

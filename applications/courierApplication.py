from flask import Flask
from flask import request
from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from configuration import Configuration
from decorators import role_check
import os

from web3 import HTTPProvider
from web3 import Web3
from web3 import Account
from web3.exceptions import ContractLogicError

from models import database
from models import Delivery
from models import DeliveryContract

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

@application.route("/orders_to_deliver", methods=["GET"])
@role_check ("courier")
def ordersToDeliver():

    deliveries = Delivery.query.filter(Delivery.status == "CREATED")
    orders = [{"id": delivery.id, "email": delivery.email} for delivery in deliveries]
    return jsonify(orders=orders)

@application.route("/pick_up_order", methods=["POST"])
@role_check ("courier")
def pickUpOrder():

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
    if delivery is None or delivery.status != "CREATED":
        return jsonify(message = "Invalid order id."), 400
    
    if "address" not in requestData or len(requestData["address"]) == 0:
        return jsonify(message = "Missing address."), 400

    if not web3.is_address(requestData["address"]):
        return jsonify(message = "Invalid address."), 400
    
    courier = requestData["address"]

    deliveryContract = DeliveryContract.query.filter(DeliveryContract.deliveryId == delivery.id).first()

    currContract = web3.eth.contract(address = deliveryContract.contractAddress, abi = abi)

    try:
        transaction_hash = currContract.functions.pick_up_order(courier).transact ({
            "from": owner
        })
    except ContractLogicError as error:
        errorMessage = str(error)
        prefix = "execution reverted: VM Exception while processing transaction: revert "
        errorMessage = errorMessage[len(prefix):]

        result = {
            "message": errorMessage,
        }
        return jsonify(result), 400
    
    delivery.status = "PENDING"
    database.session.commit()

    return {}, 200


if(__name__ == "__main__"):
    HOST = "0.0.0.0" if ( "PRODUCTION" in os.environ ) else "127.0.0.1"
    application.run(debug = True, host = HOST)
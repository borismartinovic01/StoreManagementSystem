from flask import Flask
from flask import request
from flask import jsonify 
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token 
from flask_jwt_extended import jwt_required 
from flask_jwt_extended import get_jwt_identity 
from flask_jwt_extended import get_jwt

from configuration import Configuration

from models import database
from models import User
from models import Role
import os

application = Flask ( __name__ )
application.config.from_object ( Configuration )

database.init_app ( application )
jwt = JWTManager ( application )

@application.route("/register_customer", methods=["POST"])
def registerCustomer():

    requiredParams = ["forename", "surname", "email", "password"]
    requestData = request.get_json()

    for i in range(len(requiredParams)):
        if requiredParams[i] not in requestData or len(requestData[requiredParams[i]]) == 0:
            return jsonify(message = "Field " + requiredParams[i] + " is missing."), 400

    email = requestData["email"]
    if len(email) > 256:
        return jsonify(message = "Invalid email."), 400

    if "@" not in email:
        return jsonify(message = "Invalid email."), 400

    username, domain = email.split("@")

    if not username or not domain:
        return jsonify(message = "Invalid email."), 400

    if "." not in domain:
        return jsonify(message = "Invalid email."), 400

    domain_name, extension = domain.split(".")

    if not domain_name or not extension:
        return jsonify(message = "Invalid email."), 400

    if len(domain_name) < 1:
        return jsonify(message = "Invalid email."), 400

    if len(extension) < 2:
        return jsonify(message = "Invalid email."), 400

    if len(requestData["password"]) < 8:
        return jsonify(message = "Invalid password."), 400
    
    if User.query.filter(User.email == requestData["email"]).first() is not None:
        return jsonify(message = "Email already exists."), 400
    

    role = Role.query.filter(Role.name == "customer").first()

    newCustomer = User(
        email = requestData["email"],
        password = requestData["password"],
        forename = requestData["forename"],
        surname = requestData["surname"],
        roleId = role.id
    )

    database.session.add(newCustomer)
    database.session.commit()
    return {}, 200


@application.route("/register_courier", methods = ["POST"])
def registerCourier():

    requiredParams = ["forename", "surname", "email", "password"]
    requestData = request.get_json()

    for i in range(len(requiredParams)):
        if requiredParams[i] not in requestData or len(requestData[requiredParams[i]]) == 0:
            return jsonify(message = "Field " + requiredParams[i] + " is missing."), 400


    email = requestData["email"]
    if len(email) > 256:
        return jsonify(message = "Invalid email."), 400

    if "@" not in email:
        return jsonify(message = "Invalid email."), 400

    username, domain = email.split("@")

    if not username or not domain:
        return jsonify(message = "Invalid email."), 400

    if "." not in domain:
        return jsonify(message = "Invalid email."), 400

    domain_name, extension = domain.split(".")

    if not domain_name or not extension:
        return jsonify(message = "Invalid email."), 400
    
    if len(domain_name) < 1:
        return jsonify(message = "Invalid email."), 400

    if len(extension) < 2:
        return jsonify(message = "Invalid email."), 400

    if len(requestData["password"]) < 8:
        return jsonify(message = "Invalid password."), 400
    
    if User.query.filter(User.email == requestData["email"]).first() is not None:
        return jsonify(message = "Email already exists."), 400
    

    role = Role.query.filter(Role.name == "courier").first()

    newCourier = User(
        email = requestData["email"],
        password = requestData["password"],
        forename = requestData["forename"],
        surname = requestData["surname"],
        roleId = role.id
    )

    database.session.add(newCourier)
    database.session.commit()

    return {}, 200

@application.route("/login", methods = ["POST"])
def login():

    requiredParams = ["email", "password"]
    requestData = request.get_json()

    for i in range(len(requiredParams)):
        if requiredParams[i] not in requestData or len(requestData[requiredParams[i]]) == 0:
            return jsonify(message = "Field " + requiredParams[i] + " is missing."), 400


    email = requestData["email"]
    if len(email) > 256:
        return jsonify(message = "Invalid email."), 400

    if "@" not in email:
        return jsonify(message = "Invalid email."), 400

    username, domain = email.split("@")

    if not username or not domain:
        return jsonify(message = "Invalid email."), 400

    if "." not in domain:
        return jsonify(message = "Invalid email."), 400

    domain_name, extension = domain.split(".")

    if not domain_name or not extension:
        return jsonify(message = "Invalid email."), 400
    
    if len(domain_name) < 1:
        return jsonify(message = "Invalid email."), 400

    if len(extension) < 2:
        return jsonify(message = "Invalid email."), 400

    password = requestData["password"]

    user = User.query.filter(User.email == email, User.password == password).first()

    if user is None:
        return jsonify(message = "Invalid credentials."), 400

    role = Role.query.filter(Role.id == user.roleId).first()

    claims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": role.name
    }

    access_token = create_access_token(identity = user.email, additional_claims = claims)
    refresh_token = create_refresh_token(identity = user.email, additional_claims = claims)

    return jsonify(accessToken = access_token, refreshToken = refresh_token)


@application.route("/delete", methods = ["POST"])
@jwt_required()
def delete():
    
    identity = get_jwt_identity()
    user = User.query.filter(User.email == identity).first()

    if user is None:
        return jsonify(message = "Unknown user."), 400

    database.session.delete(user)
    database.session.commit()

    return {}, 200

if(__name__=="__main__"):
    HOST = "0.0.0.0" if ( "PRODUCTION" in os.environ ) else "127.0.0.1"
    application.run(debug = True, host = HOST)
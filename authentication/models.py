from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

database = SQLAlchemy()
migrate = Migrate()

class Role(database.Model):
    __tablename__ = "role"
    id = database.Column(database.Integer, primary_key = True);
    name = database.Column(database.String(256), nullable = False);

    users = database.relationship("User", back_populates = "role")

    def __init__ ( self, name):
        self.name = name

class User(database.Model):
    __tablename__ = "user"
    id = database.Column(database.Integer, primary_key = True);
    email = database.Column(database.String(256), unique = True, nullable = False);
    password = database.Column(database.String(256), nullable = False);
    forename = database.Column(database.String(256), nullable = False);
    surname = database.Column(database.String(256), nullable = False);
    roleId = database.Column(database.Integer, database.ForeignKey ( Role.id ), nullable = False);

    role = database.relationship("Role", back_populates = "users")

    def __init__ ( self, email, password, forename, surname, roleId):
        self.email = email
        self.password = password
        self.forename = forename
        self.surname = surname
        self.roleId = roleId

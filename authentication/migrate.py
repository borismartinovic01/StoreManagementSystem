from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate
from models import database, migrate, Role, User

application = Flask(__name__)
application.config.from_object(Configuration)

migrateObject = Migrate(application, database)

# if(not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
#     create_database(application.config["SQLALCHEMY_DATABASE_URI"])


database.init_app(application)
migrate.init_app ( application, database )

with application.app_context ( ):

    database.create_all ( )

    # admin_role = Role.query.filter ( Role.name == "admin" ).first ( )
    # user_role  = Role.query.filter ( Role.name == "user" ).first ( )

    # if ( admin_role is None ):
    #     database.session.add ( Role ( name = "admin" ) )

    # if ( user_role is None ):
    #     database.session.add ( Role ( name = "user" ) )

    # database.session.commit ( )

    database.session.add(Role(name = "owner"))
    database.session.add(Role(name = "customer"))
    database.session.add(Role(name = "courier"))

    database.session.commit()

    role = Role.query.filter(Role.name == "owner").first()

    owner = User(
        email = "onlymoney@gmail.com",
        password = "evenmoremoney",
        forename = "Scrooge",
        surname = "McDuck",
        roleId = role.id
    )

    database.session.add(owner)
    database.session.commit()
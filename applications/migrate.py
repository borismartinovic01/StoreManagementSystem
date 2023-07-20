from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate
from models import database, migrate

application = Flask(__name__)
application.config.from_object(Configuration)

migrateObject = Migrate(application, database)

database.init_app(application)
migrate.init_app ( application, database )

with application.app_context ( ):

    database.create_all ( )
    database.session.commit()
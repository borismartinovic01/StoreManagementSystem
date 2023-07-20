import os
from datetime import timedelta

DATABASE_URL = "storeDB" if ("PRODUCTION" in os.environ) else "localhost"

class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql://root:root@{DATABASE_URL}/store"
    JWT_SECRET_KEY = "JWT_SECRET_DEV_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes = 60);
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days = 30);

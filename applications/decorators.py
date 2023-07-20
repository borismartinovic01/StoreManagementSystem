from flask_jwt_extended import get_jwt
from flask_jwt_extended import jwt_required
from functools import wraps

def role_check ( role ):
    def decorator ( function ):
        @jwt_required ( )
        @wraps ( function )
        def wrapper ( *args, **kwargs ):
            claims = get_jwt ( )
            if ( role == claims["roles"] ):
                return function ( *args, **kwargs )
            else:
                return {"msg": "Missing Authorization Header"}, 401

        return wrapper

    return decorator
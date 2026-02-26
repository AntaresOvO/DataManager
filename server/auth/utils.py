import bcrypt
import jwt
import datetime
import config

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_token(user_id, username, role):
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=config.JWT_EXPIRATION)
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')

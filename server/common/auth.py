import functools
import jwt
from flask import request, g
import config
from common.response import error

def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '').removeprefix('Bearer ')
        if not token:
            return error(401, '未登录')
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
            g.current_user = payload
        except jwt.ExpiredSignatureError:
            return error(401, 'Token已过期')
        except jwt.InvalidTokenError:
            return error(401, 'Token无效')
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @functools.wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if g.current_user.get('role') != 'admin':
            return error(403, '权限不足')
        return f(*args, **kwargs)
    return wrapper

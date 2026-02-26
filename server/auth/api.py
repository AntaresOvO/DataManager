from flask import Blueprint, request, g
from common.response import success, error
from common.auth import login_required
from auth import crud, utils

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = (data or {}).get('username', '').strip()
    password = (data or {}).get('password', '')
    if not username or not password:
        return error(400, '用户名和密码不能为空')

    login_ip = request.remote_addr or '0.0.0.0'
    user = crud.get_user_by_username(username)

    if user is None or not utils.check_password(password, user['password']):
        crud.insert_login_log(user['id'] if user else None, username, login_ip, 0)
        return error(400, '用户名或密码错误')

    if user['status'] != 1:
        crud.insert_login_log(user['id'], username, login_ip, 0)
        return error(400, '账号已被禁用')

    token = utils.generate_token(user['id'], user['username'], user['role'])
    crud.update_last_login(user['id'])
    crud.insert_login_log(user['id'], username, login_ip, 1)

    return success({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'need_change_pwd': user['need_change_pwd']
        }
    }, '登录成功')

@bp.route('/userinfo', methods=['GET'])
@login_required
def userinfo():
    user = crud.get_user_by_id(g.current_user['user_id'])
    if user is None:
        return error(404, '用户不存在')
    return success(dict(user))

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    old_password = (data or {}).get('old_password', '')
    new_password = (data or {}).get('new_password', '')
    if not old_password or not new_password:
        return error(400, '旧密码和新密码不能为空')
    if len(new_password) < 6:
        return error(400, '新密码长度不能少于6位')

    user = crud.get_user_by_username(g.current_user['username'])
    if not utils.check_password(old_password, user['password']):
        return error(400, '旧密码错误')

    crud.update_password(user['id'], utils.hash_password(new_password))
    return success(msg='密码修改成功')

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    return success(msg='登出成功')

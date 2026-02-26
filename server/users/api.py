from flask import Blueprint, request
from common.response import success, error
from common.auth import admin_required
from users import crud
from auth.utils import hash_password

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('', methods=['GET'])
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 10, type=int), 100)
    keyword = request.args.get('keyword', '').strip()
    rows, total = crud.get_users(page, page_size, keyword)
    return success({'list': rows, 'total': total, 'page': page, 'page_size': page_size})

@bp.route('', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json()
    username = (data or {}).get('username', '').strip()
    password = (data or {}).get('password', '')
    role = (data or {}).get('role', 'user')
    if not username or not password:
        return error(400, '用户名和密码不能为空')
    if len(password) < 6:
        return error(400, '密码长度不能少于6位')
    if role not in ('admin', 'user'):
        return error(400, '角色值无效')
    if crud.get_user_by_username(username):
        return error(400, '用户名已存在')
    crud.create_user(username, hash_password(password), role)
    return success(msg='创建成功')

@bp.route('/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.get_json()
    role = (data or {}).get('role', 'user')
    status = (data or {}).get('status', 1)
    if role not in ('admin', 'user'):
        return error(400, '角色值无效')
    if status not in (0, 1):
        return error(400, '状态值无效')
    user = crud.get_user_by_id(user_id)
    if not user:
        return error(404, '用户不存在')
    crud.update_user(user_id, role, status)
    return success(msg='更新成功')

@bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = crud.get_user_by_id(user_id)
    if not user:
        return error(404, '用户不存在')
    if user['username'] == 'admin':
        return error(400, '不能删除默认管理员')
    crud.delete_user(user_id)
    return success(msg='删除成功')

@bp.route('/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    data = request.get_json()
    new_password = (data or {}).get('new_password', '')
    if not new_password or len(new_password) < 6:
        return error(400, '新密码长度不能少于6位')
    user = crud.get_user_by_id(user_id)
    if not user:
        return error(404, '用户不存在')
    crud.reset_password(user_id, hash_password(new_password))
    return success(msg='密码重置成功')

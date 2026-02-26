import json
from flask import Blueprint, request, g
from common.response import success, error
from common.auth import login_required
from forms import crud
from form_templates.crud import get_template_by_id

bp = Blueprint('forms', __name__, url_prefix='/api/forms')

@bp.route('', methods=['GET'])
@login_required
def list_forms():
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 10, type=int), 100)
    template_id = request.args.get('template_id', type=int)
    # 普通用户只能看自己的数据
    user_id = None if g.current_user['role'] == 'admin' else g.current_user['user_id']
    # 字段级搜索: search.field_name=value（兼容旧版）
    search = {}
    for key, value in request.args.items():
        if key.startswith('search.') and value.strip():
            search[key[7:]] = value.strip()
    # 带操作符的筛选: filters=[{field, op, value}, ...]
    filters = None
    filters_str = request.args.get('filters')
    if filters_str:
        try:
            filters = json.loads(filters_str)
        except (json.JSONDecodeError, TypeError):
            return error(400, 'filters 参数格式错误，需为 JSON 数组')
    rows, total = crud.get_form_data_list(page, page_size, template_id, user_id, search or None, filters,
                                           request.args.get('sort_field'), request.args.get('sort_order', 'desc'))
    return success({'list': rows, 'total': total, 'page': page, 'page_size': page_size})

@bp.route('/<int:data_id>', methods=['GET'])
@login_required
def get_form(data_id):
    item = crud.get_form_data_by_id(data_id)
    if not item:
        return error(404, '数据不存在')
    if g.current_user['role'] != 'admin' and item['user_id'] != g.current_user['user_id']:
        return error(403, '权限不足')
    return success(item)

@bp.route('', methods=['POST'])
@login_required
def create_form():
    data = request.get_json()
    template_id = (data or {}).get('template_id')
    form_data = (data or {}).get('data')
    if not template_id or form_data is None:
        return error(400, '模板ID和表单数据不能为空')
    tpl = get_template_by_id(template_id)
    if not tpl:
        return error(400, '模板不存在')
    crud.create_form_data(template_id, g.current_user['user_id'], form_data)
    return success(msg='提交成功')

@bp.route('/batch', methods=['POST'])
@login_required
def batch_create():
    data = request.get_json()
    template_id = (data or {}).get('template_id')
    items = (data or {}).get('items')
    if not template_id or not isinstance(items, list) or not items:
        return error(400, '模板ID和数据列表不能为空')
    tpl = get_template_by_id(template_id)
    if not tpl:
        return error(400, '模板不存在')
    count = crud.batch_create_form_data(template_id, g.current_user['user_id'], items)
    return success(msg=f'成功导入{count}条数据')

@bp.route('/<int:data_id>', methods=['PUT'])
@login_required
def update_form(data_id):
    item = crud.get_form_data_by_id(data_id)
    if not item:
        return error(404, '数据不存在')
    if g.current_user['role'] != 'admin' and item['user_id'] != g.current_user['user_id']:
        return error(403, '权限不足')
    data = request.get_json()
    form_data = (data or {}).get('data')
    if form_data is None:
        return error(400, '表单数据不能为空')
    crud.update_form_data(data_id, form_data)
    return success(msg='更新成功')

@bp.route('/<int:data_id>', methods=['DELETE'])
@login_required
def delete_form(data_id):
    item = crud.get_form_data_by_id(data_id)
    if not item:
        return error(404, '数据不存在')
    if g.current_user['role'] != 'admin' and item['user_id'] != g.current_user['user_id']:
        return error(403, '权限不足')
    crud.delete_form_data(data_id)
    return success(msg='删除成功')

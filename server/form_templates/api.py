from flask import Blueprint, request, g
from common.response import success, error
from common.auth import login_required, admin_required
from form_templates import crud
from form_templates.utils import validate_meta_data

bp = Blueprint('form_templates', __name__, url_prefix='/api/templates')

@bp.route('', methods=['GET'])
@login_required
def list_templates():
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 10, type=int), 100)
    keyword = request.args.get('keyword', '').strip()
    rows, total = crud.get_templates(page, page_size, keyword)
    return success({'list': rows, 'total': total, 'page': page, 'page_size': page_size})

@bp.route('/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    tpl = crud.get_template_by_id(template_id)
    if not tpl:
        return error(404, '模板不存在')
    return success(tpl)

@bp.route('', methods=['POST'])
@admin_required
def create_template():
    data = request.get_json()
    name = (data or {}).get('name', '').strip()
    remark = (data or {}).get('remark', '').strip()
    meta_data = (data or {}).get('meta_data')
    if not name:
        return error(400, '模板名称不能为空')
    ok, msg = validate_meta_data(meta_data)
    if not ok:
        return error(400, msg)
    if crud.get_template_by_name(name):
        return error(400, '模板名称已存在')
    crud.create_template(name, remark, meta_data, g.current_user['user_id'])
    return success(msg='创建成功')

@bp.route('/<int:template_id>', methods=['PUT'])
@admin_required
def update_template(template_id):
    tpl = crud.get_template_by_id(template_id)
    if not tpl:
        return error(404, '模板不存在')
    data = request.get_json()
    name = (data or {}).get('name', '').strip()
    remark = (data or {}).get('remark', '').strip()
    meta_data = (data or {}).get('meta_data')
    if not name:
        return error(400, '模板名称不能为空')
    ok, msg = validate_meta_data(meta_data)
    if not ok:
        return error(400, msg)
    if crud.get_template_by_name(name, exclude_id=template_id):
        return error(400, '模板名称已存在')
    crud.update_template(template_id, name, remark, meta_data)
    return success(msg='更新成功')

@bp.route('/<int:template_id>', methods=['DELETE'])
@admin_required
def delete_template(template_id):
    tpl = crud.get_template_by_id(template_id)
    if not tpl:
        return error(404, '模板不存在')
    crud.delete_template(template_id)
    return success(msg='删除成功')

from flask import Blueprint, request
from common.response import success
from common.auth import admin_required
from logs import crud

bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@bp.route('', methods=['GET'])
@admin_required
def list_logs():
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 10, type=int), 100)
    keyword = request.args.get('keyword', '').strip()
    rows, total = crud.get_login_logs(page, page_size, keyword)
    return success({'list': rows, 'total': total, 'page': page, 'page_size': page_size})

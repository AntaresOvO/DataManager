import json
import re
from database import get_db

ALLOWED_OPS = {'=', '!=', '>', '<', '>=', '<=', 'like', 'in', 'not_in', 'contains'}
# 字段名只允许字母、数字、下划线，防止 SQL 注入
_FIELD_RE = re.compile(r'^[a-zA-Z_]\w*$')

def _apply_filters(filters, conditions, params):
    """将筛选条件列表转换为 SQL WHERE 子句片段"""
    for f in filters:
        field, op, value = f.get('field'), f.get('op', '='), f.get('value')
        if not field or op not in ALLOWED_OPS or value is None or value == '':
            continue
        if not _FIELD_RE.match(field):
            continue
        expr = f"json_extract(fd.data, '$.{field}')"
        if op == 'like':
            conditions.append(f"{expr} LIKE ?")
            params.append(f'%{value}%')
        elif op in ('in', 'not_in'):
            items = [v.strip() for v in str(value).split(',') if v.strip()]
            if items:
                placeholders = ','.join(['?'] * len(items))
                neg = 'NOT ' if op == 'not_in' else ''
                conditions.append(f"{expr} {neg}IN ({placeholders})")
                params.extend(items)
        elif op == 'contains':
            # 用于 checkbox 等 JSON 数组字段，匹配数组中包含某个值
            # SQLite json_each 展开数组后判断是否存在目标值
            conditions.append(
                f"EXISTS (SELECT 1 FROM json_each(fd.data, '$.{field}') WHERE value = ?)"
            )
            params.append(value)
        else:
            # 数值比较时尝试转为数字，避免字符串与数字比较不一致
            v = value
            if op in ('>', '<', '>=', '<='):
                try:
                    v = int(value)
                except ValueError:
                    try:
                        v = float(value)
                    except ValueError:
                        pass
            conditions.append(f"{expr} {op} ?")
            params.append(v)

ALLOWED_SORT = {'id', 'create_time', 'update_time'}

def get_form_data_list(page=1, page_size=10, template_id=None, user_id=None, search=None, filters=None, sort_field=None, sort_order='desc'):
    db = get_db()
    offset = (page - 1) * page_size
    conditions = []
    params = []
    if template_id:
        conditions.append('fd.template_id = ?')
        params.append(template_id)
    if user_id:
        conditions.append('fd.user_id = ?')
        params.append(user_id)
    # 旧版模糊搜索（兼容）
    if search:
        for field, value in search.items():
            if not _FIELD_RE.match(field):
                continue
            conditions.append(f"json_extract(fd.data, '$.{field}') LIKE ?")
            params.append(f'%{value}%')
    # 新版：带操作符的筛选条件
    if filters:
        _apply_filters(filters, conditions, params)
    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

    # 排序
    order_dir = 'ASC' if sort_order == 'asc' else 'DESC'
    if sort_field and sort_field in ALLOWED_SORT:
        order_clause = f'ORDER BY fd.{sort_field} {order_dir}'
    elif sort_field and _FIELD_RE.match(sort_field):
        order_clause = f"ORDER BY json_extract(fd.data, '$.{sort_field}') {order_dir}"
    else:
        order_clause = f'ORDER BY fd.id {order_dir}'

    total = db.execute(f'SELECT COUNT(*) FROM form_data fd {where}', params).fetchone()[0]
    rows = db.execute(
        f'''SELECT fd.id, fd.template_id, fd.user_id, fd.data, fd.create_time, fd.update_time,
                   ft.name as template_name, ft.meta_data as template_meta, u.username
            FROM form_data fd
            LEFT JOIN form_template ft ON fd.template_id = ft.id
            LEFT JOIN user u ON fd.user_id = u.id
            {where} {order_clause} LIMIT ? OFFSET ?''',
        params + [page_size, offset]
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d['data'] = json.loads(d['data'])
        if d.get('template_meta'):
            d['template_meta'] = json.loads(d['template_meta'])
        result.append(d)
    return result, total

def get_form_data_by_id(data_id):
    db = get_db()
    row = db.execute(
        '''SELECT fd.*, ft.name as template_name, ft.meta_data as template_meta
           FROM form_data fd
           LEFT JOIN form_template ft ON fd.template_id = ft.id
           WHERE fd.id = ?''', (data_id,)
    ).fetchone()
    if row:
        d = dict(row)
        d['data'] = json.loads(d['data'])
        if d.get('template_meta'):
            d['template_meta'] = json.loads(d['template_meta'])
        return d
    return None

def create_form_data(template_id, user_id, data):
    db = get_db()
    db.execute(
        'INSERT INTO form_data (template_id, user_id, data) VALUES (?, ?, ?)',
        (template_id, user_id, json.dumps(data, ensure_ascii=False))
    )
    db.commit()

def batch_create_form_data(template_id, user_id, items):
    db = get_db()
    for data in items:
        db.execute(
            'INSERT INTO form_data (template_id, user_id, data) VALUES (?, ?, ?)',
            (template_id, user_id, json.dumps(data, ensure_ascii=False))
        )
    db.commit()
    return len(items)

def update_form_data(data_id, data):
    db = get_db()
    db.execute(
        "UPDATE form_data SET data = ?, update_time = datetime('now','localtime') WHERE id = ?",
        (json.dumps(data, ensure_ascii=False), data_id)
    )
    db.commit()

def delete_form_data(data_id):
    db = get_db()
    db.execute('DELETE FROM form_data WHERE id = ?', (data_id,))
    db.commit()

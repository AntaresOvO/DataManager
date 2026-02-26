import json
from database import get_db

def get_templates(page=1, page_size=10, keyword=''):
    db = get_db()
    offset = (page - 1) * page_size
    base_where = "WHERE name LIKE ?" if keyword else ""
    params = (f'%{keyword}%',) if keyword else ()

    total = db.execute(f'SELECT COUNT(*) FROM form_template {base_where}', params).fetchone()[0]
    rows = db.execute(
        f'SELECT id, name, remark, meta_data, creator_id, create_time, update_time FROM form_template {base_where} ORDER BY id DESC LIMIT ? OFFSET ?',
        params + (page_size, offset)
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d['meta_data'] = json.loads(d['meta_data'])
        result.append(d)
    return result, total

def get_template_by_id(template_id):
    db = get_db()
    row = db.execute('SELECT * FROM form_template WHERE id = ?', (template_id,)).fetchone()
    if row:
        d = dict(row)
        d['meta_data'] = json.loads(d['meta_data'])
        return d
    return None

def create_template(name, remark, meta_data, creator_id):
    db = get_db()
    db.execute(
        'INSERT INTO form_template (name, remark, meta_data, creator_id) VALUES (?, ?, ?, ?)',
        (name, remark, json.dumps(meta_data, ensure_ascii=False), creator_id)
    )
    db.commit()

def update_template(template_id, name, remark, meta_data):
    db = get_db()
    db.execute(
        "UPDATE form_template SET name = ?, remark = ?, meta_data = ?, update_time = datetime('now','localtime') WHERE id = ?",
        (name, remark, json.dumps(meta_data, ensure_ascii=False), template_id)
    )
    db.commit()

def delete_template(template_id):
    db = get_db()
    db.execute('DELETE FROM form_template WHERE id = ?', (template_id,))
    db.commit()

def get_template_by_name(name, exclude_id=None):
    db = get_db()
    if exclude_id:
        return db.execute('SELECT id FROM form_template WHERE name = ? AND id != ?', (name, exclude_id)).fetchone()
    return db.execute('SELECT id FROM form_template WHERE name = ?', (name,)).fetchone()

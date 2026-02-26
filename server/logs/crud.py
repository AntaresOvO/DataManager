from database import get_db

def get_login_logs(page=1, page_size=10, keyword=''):
    db = get_db()
    offset = (page - 1) * page_size
    base_where = "WHERE username LIKE ?" if keyword else ""
    params = (f'%{keyword}%',) if keyword else ()

    total = db.execute(f'SELECT COUNT(*) FROM login_log {base_where}', params).fetchone()[0]
    rows = db.execute(
        f'SELECT id, user_id, username, login_ip, login_status, login_time FROM login_log {base_where} ORDER BY id DESC LIMIT ? OFFSET ?',
        params + (page_size, offset)
    ).fetchall()
    return [dict(r) for r in rows], total

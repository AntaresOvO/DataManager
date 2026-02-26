from database import get_db

def get_users(page=1, page_size=10, keyword=''):
    db = get_db()
    offset = (page - 1) * page_size
    base_where = "WHERE username LIKE ?" if keyword else ""
    params = (f'%{keyword}%',) if keyword else ()

    total = db.execute(f'SELECT COUNT(*) FROM user {base_where}', params).fetchone()[0]
    rows = db.execute(
        f'SELECT id, username, role, status, need_change_pwd, create_time, last_login_time FROM user {base_where} ORDER BY id DESC LIMIT ? OFFSET ?',
        params + (page_size, offset)
    ).fetchall()
    return [dict(r) for r in rows], total

def create_user(username, hashed_password, role='user'):
    db = get_db()
    db.execute('INSERT INTO user (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, role))
    db.commit()

def update_user(user_id, role, status):
    db = get_db()
    db.execute('UPDATE user SET role = ?, status = ? WHERE id = ?', (role, status, user_id))
    db.commit()

def delete_user(user_id):
    db = get_db()
    db.execute('DELETE FROM user WHERE id = ?', (user_id,))
    db.commit()

def reset_password(user_id, hashed_password):
    db = get_db()
    db.execute('UPDATE user SET password = ?, need_change_pwd = 1 WHERE id = ?', (hashed_password, user_id))
    db.commit()

def get_user_by_id(user_id):
    db = get_db()
    return db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()

def get_user_by_username(username):
    db = get_db()
    return db.execute('SELECT id FROM user WHERE username = ?', (username,)).fetchone()

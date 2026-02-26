from database import get_db

def get_user_by_username(username):
    db = get_db()
    return db.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()

def get_user_by_id(user_id):
    db = get_db()
    return db.execute('SELECT id, username, role, status, need_change_pwd, create_time, last_login_time FROM user WHERE id = ?', (user_id,)).fetchone()

def update_last_login(user_id):
    db = get_db()
    db.execute("UPDATE user SET last_login_time = datetime('now','localtime') WHERE id = ?", (user_id,))
    db.commit()

def update_password(user_id, hashed_password):
    db = get_db()
    db.execute('UPDATE user SET password = ?, need_change_pwd = 0 WHERE id = ?', (hashed_password, user_id))
    db.commit()

def insert_login_log(user_id, username, login_ip, login_status):
    db = get_db()
    db.execute(
        'INSERT INTO login_log (user_id, username, login_ip, login_status) VALUES (?, ?, ?, ?)',
        (user_id, username, login_ip, login_status)
    )
    db.commit()

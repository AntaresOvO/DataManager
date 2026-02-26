import sqlite3
import bcrypt
from flask import g
import config

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(config.DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(config.DATABASE)
    db.execute('PRAGMA foreign_keys = ON')

    db.executescript('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            status INTEGER NOT NULL DEFAULT 1,
            need_change_pwd INTEGER NOT NULL DEFAULT 1,
            create_time DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
            last_login_time DATETIME
        );

        CREATE TABLE IF NOT EXISTS form_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            remark VARCHAR(200),
            meta_data TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            create_time DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
            update_time DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (creator_id) REFERENCES user(id)
        );

        CREATE TABLE IF NOT EXISTS form_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            create_time DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
            update_time DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (template_id) REFERENCES form_template(id),
            FOREIGN KEY (user_id) REFERENCES user(id)
        );

        CREATE TABLE IF NOT EXISTS login_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username VARCHAR(50) NOT NULL,
            login_ip VARCHAR(50) NOT NULL,
            login_status INTEGER NOT NULL DEFAULT 1,
            login_time DATETIME NOT NULL DEFAULT (datetime('now','localtime'))
        );
    ''')

    # 初始化默认管理员账号
    cursor = db.execute('SELECT id FROM user WHERE username = ?', ('admin',))
    if cursor.fetchone() is None:
        hashed = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
        db.execute(
            'INSERT INTO user (username, password, role, need_change_pwd) VALUES (?, ?, ?, ?)',
            ('admin', hashed, 'admin', 1)
        )
        db.commit()

    db.close()

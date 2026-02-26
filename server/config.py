import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = 'dev-secret-key-change-in-production'
JWT_EXPIRATION = 7200  # 2小时
DATABASE = os.path.join(BASE_DIR, 'data', 'app.db')

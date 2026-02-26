import os
from flask import Flask
import config
import database

def create_app():
    app = Flask(__name__, static_folder=None)
    app.config['SECRET_KEY'] = config.SECRET_KEY

    # 确保数据目录存在
    os.makedirs(os.path.dirname(config.DATABASE), exist_ok=True)

    # 初始化数据库
    database.init_db()

    # 注册关闭数据库连接
    app.teardown_appcontext(database.close_db)

    # 注册蓝图
    from auth.api import bp as auth_bp
    from users.api import bp as users_bp
    from form_templates.api import bp as templates_bp
    from forms.api import bp as forms_bp
    from logs.api import bp as logs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(forms_bp)
    app.register_blueprint(logs_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)

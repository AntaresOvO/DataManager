"""
API 接口测试 - Flask 表单管理系统
覆盖模块: auth / users / form_templates / forms
运行方式: cd server && pytest test_api.py -v
"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(__file__))

import config as _config


# ─────────────────────────── Fixtures ───────────────────────────

@pytest.fixture(scope='session')
def app():
    """使用临时数据库创建测试应用"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    _config.DATABASE = db_path

    from app import create_app
    application = create_app()
    application.config['TESTING'] = True
    yield application

    os.unlink(db_path)


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def admin_token(client):
    resp = client.post('/api/auth/login',
                       json={'username': 'admin', 'password': 'admin123'})
    return resp.get_json()['data']['token']


@pytest.fixture(scope='session')
def user_token(client, admin_token):
    """创建普通用户并返回其 token"""
    client.post('/api/users',
                json={'username': 'testuser', 'password': 'pass123', 'role': 'user'},
                headers=_ah(admin_token))
    resp = client.post('/api/auth/login',
                       json={'username': 'testuser', 'password': 'pass123'})
    return resp.get_json()['data']['token']


def _ah(token: str) -> dict:
    """构造 Authorization header"""
    return {'Authorization': f'Bearer {token}'}


# ─────────────────────────── Auth ───────────────────────────

class TestAuth:

    def test_login_success(self, client):
        resp = client.post('/api/auth/login',
                           json={'username': 'admin', 'password': 'admin123'})
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['code'] == 200
        assert 'token' in body['data']
        assert body['data']['user']['username'] == 'admin'
        assert body['data']['user']['role'] == 'admin'

    def test_login_wrong_password(self, client):
        resp = client.post('/api/auth/login',
                           json={'username': 'admin', 'password': 'wrongpass'})
        assert resp.status_code == 400
        assert resp.get_json()['code'] == 400

    def test_login_nonexistent_user(self, client):
        resp = client.post('/api/auth/login',
                           json={'username': 'nobody', 'password': 'pass123'})
        assert resp.status_code == 400

    def test_login_empty_username(self, client):
        resp = client.post('/api/auth/login',
                           json={'username': '', 'password': 'pass123'})
        assert resp.status_code == 400

    def test_login_empty_password(self, client):
        resp = client.post('/api/auth/login',
                           json={'username': 'admin', 'password': ''})
        assert resp.status_code == 400

    def test_login_empty_body(self, client):
        resp = client.post('/api/auth/login', json={})
        assert resp.status_code == 400

    def test_userinfo_authenticated(self, client, admin_token):
        resp = client.get('/api/auth/userinfo', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['username'] == 'admin'

    def test_userinfo_no_token(self, client):
        resp = client.get('/api/auth/userinfo')
        assert resp.status_code == 401

    def test_userinfo_invalid_token(self, client):
        resp = client.get('/api/auth/userinfo',
                          headers={'Authorization': 'Bearer bad.token.value'})
        assert resp.status_code == 401

    def test_change_password_success(self, client, admin_token):
        # 改回原密码，保持测试幂等
        resp = client.post('/api/auth/change-password',
                           json={'old_password': 'admin123', 'new_password': 'admin123'},
                           headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_change_password_wrong_old(self, client, admin_token):
        resp = client.post('/api/auth/change-password',
                           json={'old_password': 'wrongold', 'new_password': 'newpass123'},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_change_password_too_short(self, client, admin_token):
        resp = client.post('/api/auth/change-password',
                           json={'old_password': 'admin123', 'new_password': '123'},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_change_password_empty_fields(self, client, admin_token):
        resp = client.post('/api/auth/change-password',
                           json={},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_change_password_unauthenticated(self, client):
        resp = client.post('/api/auth/change-password',
                           json={'old_password': 'admin123', 'new_password': 'newpass123'})
        assert resp.status_code == 401

    def test_logout_success(self, client, admin_token):
        resp = client.post('/api/auth/logout', headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_logout_unauthenticated(self, client):
        resp = client.post('/api/auth/logout')
        assert resp.status_code == 401


# ─────────────────────────── Form Templates ───────────────────────────

VALID_META = [
    {'label': '姓名', 'type': 'text'},
    {'label': '年龄', 'type': 'number'},
    {'label': '性别', 'type': 'radio', 'options': ['男', '女']},
]


class TestFormTemplates:

    def test_list_templates_authenticated(self, client, admin_token):
        resp = client.get('/api/templates', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        assert 'list' in body['data']
        assert 'total' in body['data']

    def test_list_templates_unauthenticated(self, client):
        resp = client.get('/api/templates')
        assert resp.status_code == 401

    def test_list_templates_pagination(self, client, admin_token):
        resp = client.get('/api/templates?page=1&page_size=5', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['page'] == 1
        assert body['data']['page_size'] == 5

    def test_create_template_success(self, client, admin_token):
        resp = client.post('/api/templates',
                           json={'name': 'TestTpl', 'remark': '测试模板', 'meta_data': VALID_META},
                           headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_create_template_duplicate_name(self, client, admin_token):
        resp = client.post('/api/templates',
                           json={'name': 'TestTpl', 'remark': '', 'meta_data': VALID_META},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_template_empty_name(self, client, admin_token):
        resp = client.post('/api/templates',
                           json={'name': '', 'meta_data': VALID_META},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_template_invalid_meta_empty(self, client, admin_token):
        resp = client.post('/api/templates',
                           json={'name': 'BadTpl1', 'meta_data': []},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_template_invalid_meta_missing_label(self, client, admin_token):
        resp = client.post('/api/templates',
                           json={'name': 'BadTpl2',
                                 'meta_data': [{'type': 'text'}]},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_template_invalid_meta_bad_type(self, client, admin_token):
        resp = client.post('/api/templates',
                           json={'name': 'BadTpl3',
                                 'meta_data': [{'label': 'x', 'type': 'unknown'}]},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_template_radio_without_options(self, client, admin_token):
        resp = client.post('/api/templates',
                           json={'name': 'BadTpl4',
                                 'meta_data': [{'label': '选项', 'type': 'radio'}]},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_template_forbidden_for_normal_user(self, client, user_token):
        resp = client.post('/api/templates',
                           json={'name': 'UserTpl', 'meta_data': VALID_META},
                           headers=_ah(user_token))
        assert resp.status_code == 403

    def test_get_template_success(self, client, admin_token):
        # 先查列表拿到 id
        list_resp = client.get('/api/templates', headers=_ah(admin_token))
        tpl_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.get(f'/api/templates/{tpl_id}', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['id'] == tpl_id

    def test_get_template_not_found(self, client, admin_token):
        resp = client.get('/api/templates/99999', headers=_ah(admin_token))
        assert resp.status_code == 404

    def test_update_template_success(self, client, admin_token):
        list_resp = client.get('/api/templates', headers=_ah(admin_token))
        tpl_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.put(f'/api/templates/{tpl_id}',
                          json={'name': 'TestTpl', 'remark': '已更新', 'meta_data': VALID_META},
                          headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_update_template_not_found(self, client, admin_token):
        resp = client.put('/api/templates/99999',
                          json={'name': 'X', 'meta_data': VALID_META},
                          headers=_ah(admin_token))
        assert resp.status_code == 404

    def test_delete_template_not_found(self, client, admin_token):
        resp = client.delete('/api/templates/99999', headers=_ah(admin_token))
        assert resp.status_code == 404


# ─────────────────────────── Forms ───────────────────────────

def _get_template_id(client, admin_token):
    """获取第一个模板的 id（测试辅助）"""
    resp = client.get('/api/templates', headers=_ah(admin_token))
    return resp.get_json()['data']['list'][0]['id']


class TestForms:

    def test_create_form_success(self, client, admin_token):
        tpl_id = _get_template_id(client, admin_token)
        resp = client.post('/api/forms',
                           json={'template_id': tpl_id, 'data': {'姓名': '张三', '年龄': 25}},
                           headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_create_form_missing_template_id(self, client, admin_token):
        resp = client.post('/api/forms',
                           json={'data': {'姓名': '李四'}},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_form_invalid_template_id(self, client, admin_token):
        resp = client.post('/api/forms',
                           json={'template_id': 99999, 'data': {}},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_form_unauthenticated(self, client, admin_token):
        tpl_id = _get_template_id(client, admin_token)
        resp = client.post('/api/forms',
                           json={'template_id': tpl_id, 'data': {}})
        assert resp.status_code == 401

    def test_list_forms_admin_sees_all(self, client, admin_token):
        resp = client.get('/api/forms', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['total'] >= 1

    def test_list_forms_user_sees_own(self, client, user_token, admin_token):
        tpl_id = _get_template_id(client, admin_token)
        # 普通用户提交一条数据
        client.post('/api/forms',
                    json={'template_id': tpl_id, 'data': {'姓名': 'testuser数据'}},
                    headers=_ah(user_token))
        resp = client.get('/api/forms', headers=_ah(user_token))
        body = resp.get_json()
        assert body['code'] == 200
        # 普通用户只能看到自己的数据
        for item in body['data']['list']:
            assert item['username'] == 'testuser'

    def test_list_forms_filter_by_template(self, client, admin_token):
        tpl_id = _get_template_id(client, admin_token)
        resp = client.get(f'/api/forms?template_id={tpl_id}', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        for item in body['data']['list']:
            assert item['template_id'] == tpl_id

    def test_list_forms_invalid_filters_json(self, client, admin_token):
        resp = client.get('/api/forms?filters=not_json', headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_get_form_success(self, client, admin_token):
        list_resp = client.get('/api/forms', headers=_ah(admin_token))
        form_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.get(f'/api/forms/{form_id}', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['id'] == form_id

    def test_get_form_not_found(self, client, admin_token):
        resp = client.get('/api/forms/99999', headers=_ah(admin_token))
        assert resp.status_code == 404

    def test_get_form_permission_denied(self, client, admin_token, user_token):
        # admin 创建的数据，普通用户无权查看
        tpl_id = _get_template_id(client, admin_token)
        create_resp = client.post('/api/forms',
                                  json={'template_id': tpl_id, 'data': {'姓名': 'admin专属'}},
                                  headers=_ah(admin_token))
        assert create_resp.get_json()['code'] == 200
        # 找到 admin 创建的那条
        list_resp = client.get('/api/forms', headers=_ah(admin_token))
        admin_form = next(
            item for item in list_resp.get_json()['data']['list']
            if item['username'] == 'admin'
        )
        resp = client.get(f'/api/forms/{admin_form["id"]}', headers=_ah(user_token))
        assert resp.status_code == 403

    def test_update_form_success(self, client, admin_token):
        list_resp = client.get('/api/forms', headers=_ah(admin_token))
        form_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.put(f'/api/forms/{form_id}',
                          json={'data': {'姓名': '更新后', '年龄': 30}},
                          headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_update_form_not_found(self, client, admin_token):
        resp = client.put('/api/forms/99999',
                          json={'data': {}},
                          headers=_ah(admin_token))
        assert resp.status_code == 404

    def test_update_form_missing_data(self, client, admin_token):
        list_resp = client.get('/api/forms', headers=_ah(admin_token))
        form_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.put(f'/api/forms/{form_id}',
                          json={},
                          headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_batch_create_success(self, client, admin_token):
        tpl_id = _get_template_id(client, admin_token)
        items = [{'姓名': f'批量{i}', '年龄': i} for i in range(3)]
        resp = client.post('/api/forms/batch',
                           json={'template_id': tpl_id, 'items': items},
                           headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_batch_create_empty_items(self, client, admin_token):
        tpl_id = _get_template_id(client, admin_token)
        resp = client.post('/api/forms/batch',
                           json={'template_id': tpl_id, 'items': []},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_delete_form_success(self, client, admin_token):
        # 创建一条再删除
        tpl_id = _get_template_id(client, admin_token)
        client.post('/api/forms',
                    json={'template_id': tpl_id, 'data': {'姓名': '待删除'}},
                    headers=_ah(admin_token))
        list_resp = client.get('/api/forms', headers=_ah(admin_token))
        form_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.delete(f'/api/forms/{form_id}', headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_delete_form_not_found(self, client, admin_token):
        resp = client.delete('/api/forms/99999', headers=_ah(admin_token))
        assert resp.status_code == 404


# ─────────────────────────── Users ───────────────────────────

class TestUsers:

    def test_list_users_admin(self, client, admin_token):
        resp = client.get('/api/users', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['total'] >= 1
        usernames = [u['username'] for u in body['data']['list']]
        assert 'admin' in usernames

    def test_list_users_forbidden_for_normal_user(self, client, user_token):
        resp = client.get('/api/users', headers=_ah(user_token))
        assert resp.status_code == 403

    def test_list_users_unauthenticated(self, client):
        resp = client.get('/api/users')
        assert resp.status_code == 401

    def test_list_users_keyword_search(self, client, admin_token):
        resp = client.get('/api/users?keyword=admin', headers=_ah(admin_token))
        body = resp.get_json()
        assert body['code'] == 200
        for u in body['data']['list']:
            assert 'admin' in u['username']

    def test_create_user_success(self, client, admin_token):
        resp = client.post('/api/users',
                           json={'username': 'newuser1', 'password': 'pass123', 'role': 'user'},
                           headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_create_user_duplicate_username(self, client, admin_token):
        resp = client.post('/api/users',
                           json={'username': 'newuser1', 'password': 'pass123', 'role': 'user'},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_user_empty_username(self, client, admin_token):
        resp = client.post('/api/users',
                           json={'username': '', 'password': 'pass123', 'role': 'user'},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_user_short_password(self, client, admin_token):
        resp = client.post('/api/users',
                           json={'username': 'shortpwduser', 'password': '123', 'role': 'user'},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_user_invalid_role(self, client, admin_token):
        resp = client.post('/api/users',
                           json={'username': 'badroleuser', 'password': 'pass123', 'role': 'superadmin'},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_create_user_forbidden_for_normal_user(self, client, user_token):
        resp = client.post('/api/users',
                           json={'username': 'hacker', 'password': 'pass123', 'role': 'admin'},
                           headers=_ah(user_token))
        assert resp.status_code == 403

    def test_update_user_success(self, client, admin_token):
        # 找到 newuser1 的 id
        list_resp = client.get('/api/users?keyword=newuser1', headers=_ah(admin_token))
        user_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.put(f'/api/users/{user_id}',
                          json={'role': 'admin', 'status': 1},
                          headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_update_user_invalid_role(self, client, admin_token):
        list_resp = client.get('/api/users?keyword=newuser1', headers=_ah(admin_token))
        user_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.put(f'/api/users/{user_id}',
                          json={'role': 'invalid', 'status': 1},
                          headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_update_user_invalid_status(self, client, admin_token):
        list_resp = client.get('/api/users?keyword=newuser1', headers=_ah(admin_token))
        user_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.put(f'/api/users/{user_id}',
                          json={'role': 'user', 'status': 99},
                          headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_update_user_not_found(self, client, admin_token):
        resp = client.put('/api/users/99999',
                          json={'role': 'user', 'status': 1},
                          headers=_ah(admin_token))
        assert resp.status_code == 404

    def test_reset_password_success(self, client, admin_token):
        list_resp = client.get('/api/users?keyword=newuser1', headers=_ah(admin_token))
        user_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.post(f'/api/users/{user_id}/reset-password',
                           json={'new_password': 'newpass123'},
                           headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_reset_password_too_short(self, client, admin_token):
        list_resp = client.get('/api/users?keyword=newuser1', headers=_ah(admin_token))
        user_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.post(f'/api/users/{user_id}/reset-password',
                           json={'new_password': '123'},
                           headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_reset_password_not_found(self, client, admin_token):
        resp = client.post('/api/users/99999/reset-password',
                           json={'new_password': 'newpass123'},
                           headers=_ah(admin_token))
        assert resp.status_code == 404

    def test_delete_user_success(self, client, admin_token):
        list_resp = client.get('/api/users?keyword=newuser1', headers=_ah(admin_token))
        user_id = list_resp.get_json()['data']['list'][0]['id']
        resp = client.delete(f'/api/users/{user_id}', headers=_ah(admin_token))
        assert resp.get_json()['code'] == 200

    def test_delete_admin_forbidden(self, client, admin_token):
        list_resp = client.get('/api/users?keyword=admin', headers=_ah(admin_token))
        admin_id = next(
            u['id'] for u in list_resp.get_json()['data']['list']
            if u['username'] == 'admin'
        )
        resp = client.delete(f'/api/users/{admin_id}', headers=_ah(admin_token))
        assert resp.status_code == 400

    def test_delete_user_not_found(self, client, admin_token):
        resp = client.delete('/api/users/99999', headers=_ah(admin_token))
        assert resp.status_code == 404

    def test_delete_template_with_cleanup(self, client, admin_token):
        """先删除关联表单数据，再删除模板"""
        list_resp = client.get('/api/templates?keyword=TestTpl', headers=_ah(admin_token))
        items = list_resp.get_json()['data']['list']
        for tpl in items:
            # 删除该模板下所有表单数据
            forms_resp = client.get(f'/api/forms?template_id={tpl["id"]}&page_size=100',
                                    headers=_ah(admin_token))
            for form in forms_resp.get_json()['data']['list']:
                client.delete(f'/api/forms/{form["id"]}', headers=_ah(admin_token))
            resp = client.delete(f'/api/templates/{tpl["id"]}', headers=_ah(admin_token))
            assert resp.get_json()['code'] == 200

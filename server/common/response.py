from flask import jsonify

def success(data=None, msg='success'):
    return jsonify({'code': 200, 'msg': msg, 'data': data})

def error(code=400, msg='error'):
    return jsonify({'code': code, 'msg': msg, 'data': None}), code

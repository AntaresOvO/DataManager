import json

def validate_meta_data(meta_data):
    """校验模板元数据格式"""
    if not isinstance(meta_data, list) or len(meta_data) == 0:
        return False, '元数据必须是非空数组'
    valid_types = ('text', 'number', 'date', 'radio', 'checkbox')
    for i, field in enumerate(meta_data):
        if not isinstance(field, dict):
            return False, f'第{i+1}个字段必须是对象'
        if not field.get('label') or not field.get('type'):
            return False, f'第{i+1}个字段缺少label或type'
        if field['type'] not in valid_types:
            return False, f'第{i+1}个字段类型无效，支持: {", ".join(valid_types)}'
        if field['type'] in ('radio', 'checkbox') and not field.get('options'):
            return False, f'第{i+1}个字段类型为{field["type"]}时必须提供options'
    return True, ''

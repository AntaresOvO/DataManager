"""Create 2 sample templates with 1000 records each."""
import requests
import random
import time

BASE = "http://127.0.0.1:5000"
PASS = "Test123456"

# Login
token = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": PASS}).json()["data"]["token"]
H = {"Authorization": f"Bearer {token}"}

# Template 1: Employee Info
tpl1 = requests.post(f"{BASE}/api/templates", headers=H, json={
    "name": "员工信息表",
    "remark": "员工基本信息登记",
    "meta_data": [
        {"name": "name", "label": "姓名", "type": "text", "required": True},
        {"name": "age", "label": "年龄", "type": "number", "required": True},
        {"name": "gender", "label": "性别", "type": "radio", "required": True, "options": ["男", "女"]},
        {"name": "department", "label": "部门", "type": "radio", "required": True, "options": ["技术部", "市场部", "财务部", "人事部", "运营部"]},
        {"name": "entry_date", "label": "入职日期", "type": "date", "required": True},
        {"name": "skills", "label": "技能", "type": "checkbox", "required": False, "options": ["Python", "Java", "Vue", "React", "SQL", "Docker"]},
    ]
})
print(f"Template 1: {tpl1.json().get('msg')}")

# Template 2: Product Feedback
tpl2 = requests.post(f"{BASE}/api/templates", headers=H, json={
    "name": "产品反馈表",
    "remark": "用户产品使用反馈",
    "meta_data": [
        {"name": "product", "label": "产品名称", "type": "radio", "required": True, "options": ["产品A", "产品B", "产品C", "产品D"]},
        {"name": "rating", "label": "评分", "type": "number", "required": True},
        {"name": "usage_time", "label": "使用时长(月)", "type": "number", "required": True},
        {"name": "issues", "label": "遇到的问题", "type": "checkbox", "required": False, "options": ["界面复杂", "响应慢", "功能缺失", "文档不全", "兼容性差"]},
        {"name": "suggestion", "label": "改进建议", "type": "text", "required": False},
    ]
})
print(f"Template 2: {tpl2.json().get('msg')}")

# Get template IDs
tpls = requests.get(f"{BASE}/api/templates?page=1&page_size=100", headers=H).json()["data"]["list"]
tpl1_id = next(t["id"] for t in tpls if t["name"] == "员工信息表")
tpl2_id = next(t["id"] for t in tpls if t["name"] == "产品反馈表")

# Generate 1000 employee records
surnames = list("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜")
names = list("伟芳娜敏静丽强磊洋勇艳杰娟涛明超秀霞平刚桂英华建文辉力民志永健玲")
depts = ["技术部", "市场部", "财务部", "人事部", "运营部"]
skills = ["Python", "Java", "Vue", "React", "SQL", "Docker"]

items1 = []
for i in range(1000):
    items1.append({
        "name": random.choice(surnames) + random.choice(names) + random.choice(names),
        "age": random.randint(22, 55),
        "gender": random.choice(["男", "女"]),
        "department": random.choice(depts),
        "entry_date": f"202{random.randint(0,5)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "skills": random.sample(skills, random.randint(1, 4)),
    })

# Batch insert in chunks of 200
for start in range(0, 1000, 200):
    chunk = items1[start:start+200]
    r = requests.post(f"{BASE}/api/forms/batch", headers=H, json={"template_id": tpl1_id, "items": chunk})
    print(f"  员工信息表: inserted {start+len(chunk)}/1000 - {r.json().get('msg')}")

# Generate 1000 feedback records
products = ["产品A", "产品B", "产品C", "产品D"]
issues = ["界面复杂", "响应慢", "功能缺失", "文档不全", "兼容性差"]
suggestions = ["希望增加批量导出功能", "建议优化搜索体验", "希望支持移动端", "建议增加数据可视化", "希望提供API接口",
               "建议增加权限管理", "希望支持多语言", "建议优化加载速度", "希望增加通知功能", "建议改进UI设计"]

items2 = []
for i in range(1000):
    items2.append({
        "product": random.choice(products),
        "rating": random.randint(1, 10),
        "usage_time": random.randint(1, 36),
        "issues": random.sample(issues, random.randint(0, 3)),
        "suggestion": random.choice(suggestions) if random.random() > 0.3 else "",
    })

for start in range(0, 1000, 200):
    chunk = items2[start:start+200]
    r = requests.post(f"{BASE}/api/forms/batch", headers=H, json={"template_id": tpl2_id, "items": chunk})
    print(f"  产品反馈表: inserted {start+len(chunk)}/1000 - {r.json().get('msg')}")

print("\nDone! Created 2 templates with 1000 records each.")

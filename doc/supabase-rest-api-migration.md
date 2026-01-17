# Supabase REST API 迁移方案

## 为什么考虑迁移？

### 当前问题
- Docker 构建慢（依赖复杂）
- 版本冲突频繁（httpx、gotrue、pydantic）
- 镜像体积大（~100MB 依赖）

### 迁移收益
- 构建时间：2分钟 → 30秒
- 镜像体积：减少 100MB
- 依赖数量：10个 → 8个
- 版本冲突：消除

---

## PostgREST API 基础

Supabase 使用 PostgREST 自动生成 REST API，格式：
```
GET    /rest/v1/{table}?{filters}     # 查询
POST   /rest/v1/{table}                # 插入
PATCH  /rest/v1/{table}?{filters}     # 更新
DELETE /rest/v1/{table}?{filters}     # 删除
```

### 请求头
```python
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'  # 返回插入/更新后的数据
}
```

---

## 代码迁移示例

### 查询（filter）
**现在（supabase-py）：**
```python
users = supabase().table('users').select('*').eq('phone', phone).execute()
return users.data
```

**迁移后（REST API）：**
```python
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/users?phone=eq.{phone}',
    headers=headers
)
return response.json()
```

### 插入（insert）
**现在：**
```python
response = supabase().table('users').insert(user_data).execute()
return response.data[0]
```

**迁移后：**
```python
response = requests.post(
    f'{SUPABASE_URL}/rest/v1/users',
    headers=headers,
    json=user_data
)
return response.json()[0]
```

### 更新（update）
**现在：**
```python
response = supabase().table('users').update(user_data).eq('id', user_id).execute()
```

**迁移后：**
```python
response = requests.patch(
    f'{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}',
    headers=headers,
    json=user_data
)
```

---

## 完整实现（storage_supabase_rest.py）

```python
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

class SupabaseClient:
    """轻量级 Supabase REST API 客户端"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("请配置 SUPABASE_URL 和 SUPABASE_KEY")
        
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    
    def select(self, table, filters=None, order_by=None):
        """查询数据"""
        url = f"{self.base_url}/{table}"
        params = {}
        
        if filters:
            for key, value in filters.items():
                params[key] = f"eq.{value}"
        
        if order_by:
            params['order'] = order_by
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def insert(self, table, data):
        """插入数据"""
        url = f"{self.base_url}/{table}"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def update(self, table, data, filters):
        """更新数据"""
        url = f"{self.base_url}/{table}"
        params = {k: f"eq.{v}" for k, v in filters.items()}
        response = requests.patch(url, headers=self.headers, json=data, params=params)
        response.raise_for_status()
        return response.json()
    
    def delete(self, table, filters):
        """删除数据"""
        url = f"{self.base_url}/{table}"
        params = {k: f"eq.{v}" for k, v in filters.items()}
        response = requests.delete(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

# 全局客户端
_client = None

def get_client():
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
```

---

## 迁移步骤

1. **创建新文件** `storage_rest.py`（使用上面的代码）
2. **修改 User 类**：
   ```python
   def save(self):
       client = get_client()
       if self.id:
           result = client.update('users', user_data, {'id': self.id})
       else:
           result = client.insert('users', user_data)
           self.id = result[0]['id']
       return self
   ```
3. **测试**：先在本地测试所有功能
4. **切换**：`app.py` 改为 `from storage_rest import User, ...`
5. **更新 requirements.txt**：删除 `supabase==...`

---

## 参考资料

- [PostgREST API 文档](https://postgrest.org/en/stable/api.html)
- [Supabase REST API 参考](https://supabase.com/docs/guides/api)
- [过滤器语法](https://postgrest.org/en/stable/references/api/tables_views.html#horizontal-filtering)

---

## 更新时间
2026-01-18

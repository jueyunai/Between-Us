# 国产数据库服务替代方案

**背景**：Supabase 服务器在海外，魔搭部署可能存在跨境网络延迟

---

## 推荐方案对比

| 方案 | 类型 | 免费额度 | 延迟 | 难度 | 推荐度 |
|------|------|---------|------|------|--------|
| **腾讯云 CloudBase** | Serverless | ✅ 充足 | ⭐⭐⭐ 低 | ⭐⭐ 简单 | ⭐⭐⭐⭐⭐ |
| **阿里云 TableStore** | NoSQL | ⚠️ 有限 | ⭐⭐⭐ 低 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ |
| **华为云 GaussDB** | PostgreSQL | ⚠️ 按量 | ⭐⭐⭐ 低 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ |
| **LeanCloud** | BaaS | ✅ 充足 | ⭐⭐⭐ 低 | ⭐⭐ 简单 | ⭐⭐⭐⭐ |
| **本地 SQLite** | 文件数据库 | ✅ 免费 | ⭐⭐⭐ 极低 | ⭐ 极简 | ⭐⭐⭐ |

---

## 方案 1：腾讯云 CloudBase（推荐）⭐⭐⭐⭐⭐

### 优势
- ✅ **国内服务**：延迟低（< 50ms）
- ✅ **免费额度充足**：5GB 存储 + 5GB 流量/月
- ✅ **类似 Supabase**：提供数据库、存储、云函数
- ✅ **Python SDK 完善**：`tcb-python-sdk`
- ✅ **文档齐全**：中文文档，易上手

### 免费额度
- 数据库：5GB 存储
- 读操作：50,000 次/天
- 写操作：30,000 次/天
- 流量：5GB/月

### 快速开始
```bash
# 安装 SDK
pip install tcb-python-sdk

# 初始化
import tcb
app = tcb.init({
    'env': 'your-env-id',
    'secret_id': 'your-secret-id',
    'secret_key': 'your-secret-key'
})

# 数据库操作
db = app.database()
collection = db.collection('users')

# 插入
collection.add({
    'phone': '13800138000',
    'password': 'xxx'
})

# 查询
result = collection.where({'phone': '13800138000'}).get()
```

### 迁移难度
- **代码改动**：中等（需要重写 `storage_supabase.py`）
- **数据迁移**：简单（导出 JSON 后导入）
- **预计时间**：2-3 小时

### 参考资料
- 官网：https://cloud.tencent.com/product/tcb
- 文档：https://docs.cloudbase.net/

---

## 方案 2：阿里云 TableStore（推荐）⭐⭐⭐⭐

### 优势
- ✅ **国内服务**：延迟低
- ✅ **高性能**：NoSQL，适合高并发
- ✅ **Python SDK**：`tablestore`
- ✅ **稳定可靠**：阿里云基础设施

### 免费额度
- ⚠️ **按量计费**：无永久免费额度
- 💰 **成本**：约 ¥10-30/月（小型应用）

### 快速开始
```bash
# 安装 SDK
pip install tablestore

# 初始化
from tablestore import OTSClient
client = OTSClient(
    'endpoint',
    'access_key_id',
    'access_key_secret',
    'instance_name'
)

# 插入数据
from tablestore import Row, Condition
primary_key = [('phone', '13800138000')]
attribute_columns = [('password', 'xxx')]
row = Row(primary_key, attribute_columns)
client.put_row('users', row, Condition('IGNORE'))

# 查询数据
consumed, row, next_token = client.get_row(
    'users',
    [('phone', '13800138000')]
)
```

### 迁移难度
- **代码改动**：较大（NoSQL 模型不同）
- **数据迁移**：中等
- **预计时间**：4-6 小时

### 参考资料
- 官网：https://www.aliyun.com/product/ots
- 文档：https://help.aliyun.com/product/27278.html

---

## 方案 3：华为云 GaussDB（PostgreSQL）⭐⭐⭐⭐

### 优势
- ✅ **国内服务**：延迟低
- ✅ **PostgreSQL 兼容**：与 Supabase 相同
- ✅ **企业级**：高可用、高性能
- ✅ **迁移简单**：SQL 语句通用

### 免费额度
- ⚠️ **按量计费**：无永久免费额度
- 💰 **成本**：约 ¥50-100/月（最小规格）

### 快速开始
```bash
# 安装 psycopg2
pip install psycopg2-binary

# 连接数据库
import psycopg2
conn = psycopg2.connect(
    host='your-host',
    port=5432,
    database='your-db',
    user='your-user',
    password='your-password'
)

# 执行 SQL
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE phone = %s", ('13800138000',))
result = cursor.fetchall()
```

### 迁移难度
- **代码改动**：小（只需修改连接方式）
- **数据迁移**：简单（SQL 导出/导入）
- **预计时间**：1-2 小时

### 参考资料
- 官网：https://www.huaweicloud.com/product/gaussdb.html
- 文档：https://support.huaweicloud.com/gaussdb/

---

## 方案 4：LeanCloud（BaaS）⭐⭐⭐⭐

### 优势
- ✅ **国内服务**：延迟低
- ✅ **免费额度充足**：3GB 存储 + 30,000 次请求/天
- ✅ **Python SDK**：`leancloud-sdk`
- ✅ **类似 Supabase**：提供数据存储、云函数
- ✅ **老牌服务**：稳定可靠

### 免费额度
- 数据存储：3GB
- API 请求：30,000 次/天
- 文件存储：1GB

### 快速开始
```bash
# 安装 SDK
pip install leancloud

# 初始化
import leancloud
leancloud.init('app_id', 'app_key')

# 定义模型
User = leancloud.Object.extend('User')

# 插入数据
user = User()
user.set('phone', '13800138000')
user.set('password', 'xxx')
user.save()

# 查询数据
query = leancloud.Query('User')
query.equal_to('phone', '13800138000')
result = query.find()
```

### 迁移难度
- **代码改动**：中等（需要重写存储层）
- **数据迁移**：简单
- **预计时间**：2-3 小时

### 参考资料
- 官网：https://www.leancloud.cn/
- 文档：https://leancloud.cn/docs/

---

## 方案 5：本地 SQLite（最简单）⭐⭐⭐

### 优势
- ✅ **零延迟**：本地文件数据库
- ✅ **完全免费**：无任何费用
- ✅ **极简部署**：无需配置
- ✅ **Python 内置**：无需安装依赖

### 劣势
- ❌ **单机部署**：不支持多实例
- ❌ **无备份**：需要自己处理
- ❌ **并发有限**：写入并发较低

### 快速开始
```python
import sqlite3

# 连接数据库
conn = sqlite3.connect('emotion_helper.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE,
        password TEXT
    )
''')

# 插入数据
cursor.execute(
    "INSERT INTO users (phone, password) VALUES (?, ?)",
    ('13800138000', 'xxx')
)
conn.commit()

# 查询数据
cursor.execute("SELECT * FROM users WHERE phone = ?", ('13800138000',))
result = cursor.fetchone()
```

### 迁移难度
- **代码改动**：小（修改存储层）
- **数据迁移**：极简（已有 SQLite 文件）
- **预计时间**：1 小时

### 适用场景
- 单机部署
- 用户量小（< 1000）
- 对备份要求不高

---

## 推荐决策树

```
是否需要多实例部署？
├─ 是 → 腾讯云 CloudBase / LeanCloud
└─ 否 → 继续

是否需要 PostgreSQL 兼容？
├─ 是 → 华为云 GaussDB
└─ 否 → 继续

预算如何？
├─ 免费 → 腾讯云 CloudBase / LeanCloud / SQLite
└─ 付费 → 阿里云 TableStore / 华为云 GaussDB

用户量多大？
├─ < 1000 → SQLite（最简单）
├─ 1000-10000 → 腾讯云 CloudBase / LeanCloud
└─ > 10000 → 阿里云 TableStore / 华为云 GaussDB
```

---

## 我的推荐

### 场景 1：快速解决延迟问题（推荐）
**方案**：腾讯云 CloudBase

**理由**：
- 免费额度充足
- 国内服务，延迟低
- 迁移难度适中
- 文档完善

### 场景 2：最小改动
**方案**：华为云 GaussDB（PostgreSQL）

**理由**：
- PostgreSQL 兼容，SQL 通用
- 只需修改连接方式
- 迁移时间最短

### 场景 3：零成本方案
**方案**：本地 SQLite

**理由**：
- 完全免费
- 零延迟
- 极简部署
- 适合小型应用

---

## 迁移步骤（以腾讯云 CloudBase 为例）

### 1. 注册并创建环境
1. 访问 https://cloud.tencent.com/product/tcb
2. 开通云开发服务
3. 创建环境，获取环境 ID

### 2. 安装 SDK
```bash
pip install tcb-python-sdk
```

### 3. 创建新的存储层
创建 `storage_cloudbase.py`，实现与 `storage_supabase.py` 相同的接口

### 4. 数据迁移
```python
# 从 Supabase 导出
from storage_supabase import User, CoachChat, LoungeChat
users = User.all()

# 导入到 CloudBase
from storage_cloudbase import User as CloudBaseUser
for user in users:
    cb_user = CloudBaseUser(
        phone=user.phone,
        password=user.password
    )
    cb_user.save()
```

### 5. 修改 app.py
```python
# 修改导入
# from storage_supabase import User, ...
from storage_cloudbase import User, ...
```

### 6. 测试验证
```bash
python test_performance.py
```

---

## 成本对比（月费用）

| 方案 | 免费额度 | 超出后费用 | 小型应用 | 中型应用 |
|------|---------|-----------|---------|---------|
| Supabase | ✅ 充足 | $25/月 | ¥0 | ¥180 |
| 腾讯云 CloudBase | ✅ 充足 | 按量 | ¥0 | ¥20-50 |
| 阿里云 TableStore | ❌ 无 | 按量 | ¥10-30 | ¥50-100 |
| 华为云 GaussDB | ❌ 无 | 按量 | ¥50-100 | ¥200-500 |
| LeanCloud | ✅ 充足 | 按量 | ¥0 | ¥30-80 |
| SQLite | ✅ 免费 | ¥0 | ¥0 | ¥0 |

---

## 总结

### 最推荐：腾讯云 CloudBase
- 国内服务，延迟低
- 免费额度充足
- 迁移难度适中
- 性价比最高

### 备选方案
1. **LeanCloud**：老牌 BaaS，稳定可靠
2. **华为云 GaussDB**：PostgreSQL 兼容，迁移最简单
3. **SQLite**：零成本，适合小型应用

### 下一步
1. 先部署当前优化版本，测试延迟
2. 如果延迟 > 1s，考虑迁移到腾讯云 CloudBase
3. 如果延迟可接受（< 500ms），继续使用 Supabase

需要我帮你实现腾讯云 CloudBase 的迁移方案吗？

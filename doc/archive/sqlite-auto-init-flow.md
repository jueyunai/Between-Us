# SQLite 自动初始化流程

## 启动流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    启动应用                                  │
│                  python app.py                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              导入 storage_sqlite.py                          │
│         from storage_sqlite import User, ...                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              检测环境和数据库路径                             │
│   if os.path.exists('/mnt/workspace'):                     │
│       DB_PATH = '/mnt/workspace/emotion_helper.db'          │
│   else:                                                     │
│       DB_PATH = './emotion_helper.db'                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              自动执行 init_db()                              │
│              （模块加载时自动调用）                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              创建数据库连接                                   │
│         conn = sqlite3.connect(DB_PATH)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              创建表（如果不存在）                             │
│         CREATE TABLE IF NOT EXISTS users (...)              │
│         CREATE TABLE IF NOT EXISTS relationships (...)      │
│         CREATE TABLE IF NOT EXISTS coach_chats (...)        │
│         CREATE TABLE IF NOT EXISTS lounge_chats (...)       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              提交并关闭连接                                   │
│              conn.commit()                                  │
│              conn.close()                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              打印初始化成功日志                               │
│   [SQLite] 数据库初始化完成: /mnt/workspace/emotion_helper.db│
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              应用正常启动                                     │
│              Flask + SocketIO 服务运行                       │
│              ✅ 数据库可用                                    │
└─────────────────────────────────────────────────────────────┘
```

## 关键代码

### 1. 环境检测（storage_sqlite.py 第 13-16 行）

```python
# 自动检测环境，选择合适的数据库路径
if os.path.exists('/mnt/workspace'):
    DB_PATH = os.path.join('/mnt/workspace', 'emotion_helper.db')  # 生产环境
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'emotion_helper.db')  # 开发环境
```

### 2. 初始化函数（storage_sqlite.py 第 28-87 行）

```python
def init_db():
    """初始化数据库表"""
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建 4 张表（使用 IF NOT EXISTS 避免重复创建）
        cursor.execute('CREATE TABLE IF NOT EXISTS users (...)')
        cursor.execute('CREATE TABLE IF NOT EXISTS relationships (...)')
        cursor.execute('CREATE TABLE IF NOT EXISTS coach_chats (...)')
        cursor.execute('CREATE TABLE IF NOT EXISTS lounge_chats (...)')
        
        conn.commit()
        conn.close()
        print(f"[SQLite] 数据库初始化完成: {DB_PATH}", flush=True)
```

### 3. 自动调用（storage_sqlite.py 第 87 行）

```python
# 模块加载时自动执行
init_db()
```

## 首次启动 vs 后续启动

### 首次启动（数据库不存在）

```
检测到 /mnt/workspace/ 存在
    ↓
创建新文件: emotion_helper.db
    ↓
创建 4 张表
    ↓
数据库大小: ~8KB（空表）
    ↓
✅ 初始化完成
```

### 后续启动（数据库已存在）

```
检测到 emotion_helper.db 已存在
    ↓
连接现有数据库
    ↓
执行 CREATE TABLE IF NOT EXISTS（跳过已存在的表）
    ↓
数据完整保留
    ↓
✅ 直接使用
```

## 安全机制

### 1. 线程安全
```python
db_lock = Lock()  # 全局锁

with db_lock:
    # 所有数据库操作都在锁保护下进行
    conn = get_db_connection()
    # ... 操作
    conn.close()
```

### 2. 幂等性
```python
# 使用 IF NOT EXISTS 确保多次执行不会出错
CREATE TABLE IF NOT EXISTS users (...)
```

### 3. 自动提交
```python
conn.commit()  # 确保表创建成功
conn.close()   # 释放连接
```

## 验证方法

### 方法 1: 查看启动日志
```bash
python app.py

# 应该看到：
# [SQLite] 数据库初始化完成: /mnt/workspace/emotion_helper.db
# [启动] 使用 SQLite 本地数据库
```

### 方法 2: 检查文件
```bash
ls -lh /mnt/workspace/emotion_helper.db

# 应该看到文件存在，大小约 8-28KB
```

### 方法 3: 查看表结构
```bash
sqlite3 /mnt/workspace/emotion_helper.db ".tables"

# 应该看到：
# coach_chats  lounge_chats  relationships  users
```

### 方法 4: 运行测试
```bash
python test_sqlite.py

# 应该看到：
# ✅ 所有测试通过！
```

## 故障排查

### 问题 1: 权限不足
```
错误: unable to open database file
解决: 确保应用进程有 /mnt/workspace/ 的读写权限
```

### 问题 2: 磁盘空间不足
```
错误: disk I/O error
解决: 检查 /mnt/workspace/ 磁盘空间
```

### 问题 3: 数据库锁定
```
错误: database is locked
解决: 确保没有其他进程占用数据库文件
```

## 总结

✅ **完全自动化**: 无需手动创建数据库  
✅ **环境自适应**: 自动选择合适的存储路径  
✅ **幂等安全**: 多次启动不会出错  
✅ **线程安全**: 并发访问有保护  
✅ **零配置**: 开箱即用  

**只需启动应用，数据库自动就绪！**

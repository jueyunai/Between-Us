# Supabase 迁移指南

## 📋 迁移概述

本项目已从 JSON 文件存储迁移到 Supabase PostgreSQL 数据库。

**迁移方式**：方案 A（最小改动）
- 只修改存储层 `storage.py` → `storage_supabase.py`
- 业务逻辑代码 `app.py` 无需修改
- 保持原有 API 接口不变

## 🚀 快速开始

### 1. 注册 Supabase 账号

访问 https://supabase.com 注册账号（免费）

### 2. 创建项目

1. 点击 "New Project"
2. 填写项目信息：
   - Name: `emotion-helper`（或自定义）
   - Database Password: 设置强密码（记住它）
   - Region: 选择离你最近的区域（如 Singapore）
3. 等待项目创建完成（约 2 分钟）

### 3. 创建数据库表

1. 进入项目后，点击左侧菜单 "SQL Editor"
2. 点击 "New Query"
3. 复制 `supabase_schema.sql` 文件内容粘贴到编辑器
4. 点击 "Run" 执行 SQL

### 4. 获取 API 凭证

1. 点击左侧菜单 "Settings" → "API"
2. 复制以下信息：
   - **Project URL**（形如 `https://xxxxx.supabase.co`）
   - **anon public** key（一长串字符）

### 5. 配置环境变量

编辑 `.env` 文件，添加：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### 6. 安装依赖

```bash
pip install -r requirements.txt
```

### 7. 数据迁移（可选）

如果你有现有的 JSON 数据需要迁移：

```bash
python migrate_to_supabase.py
```

按提示操作，脚本会自动将 `data/` 目录下的 JSON 数据导入 Supabase。

### 8. 修改代码

在 `app.py` 第 4 行，将：

```python
from storage import User, Relationship, CoachChat, LoungeChat
```

改为：

```python
from storage_supabase import User, Relationship, CoachChat, LoungeChat
```

### 9. 启动应用

```bash
python app.py
```

访问 http://localhost:7860 测试功能。

## 🔍 验证迁移

### 测试清单

- [ ] 用户注册功能正常
- [ ] 用户登录功能正常
- [ ] 生成绑定码功能正常
- [ ] 伴侣绑定功能正常
- [ ] 个人教练聊天正常
- [ ] 情感客厅聊天正常
- [ ] 聊天记录保存正常
- [ ] 解绑功能正常

### 在 Supabase 中查看数据

1. 进入 Supabase 项目
2. 点击左侧菜单 "Table Editor"
3. 选择表查看数据：
   - `users` - 用户表
   - `relationships` - 关系表
   - `coach_chats` - 个人教练聊天记录
   - `lounge_chats` - 情感客厅聊天记录

## 📊 数据库结构

### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| phone | VARCHAR(20) | 手机号（唯一） |
| password | VARCHAR(200) | 密码 |
| binding_code | VARCHAR(20) | 绑定码（唯一） |
| partner_id | BIGINT | 伴侣ID（外键） |
| unbind_at | TIMESTAMPTZ | 解绑时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

### relationships（关系表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| user1_id | BIGINT | 用户1 ID |
| user2_id | BIGINT | 用户2 ID |
| room_id | VARCHAR(50) | 房间ID（唯一） |
| is_active | BOOLEAN | 是否激活 |
| created_at | TIMESTAMPTZ | 创建时间 |

### coach_chats（个人教练聊天记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| user_id | BIGINT | 用户ID |
| role | VARCHAR(20) | 角色（user/assistant） |
| content | TEXT | 消息内容 |
| reasoning_content | TEXT | AI思考过程 |
| created_at | TIMESTAMPTZ | 创建时间 |

### lounge_chats（情感客厅聊天记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| room_id | VARCHAR(50) | 房间ID |
| user_id | BIGINT | 用户ID（AI消息为NULL） |
| role | VARCHAR(20) | 角色（user/assistant） |
| content | TEXT | 消息内容 |
| created_at | TIMESTAMPTZ | 创建时间 |

## 🎯 优势对比

### JSON 文件存储

❌ 不支持并发写入  
❌ 数据量大时性能差  
❌ 无法做复杂查询  
❌ 无备份和恢复机制  

### Supabase PostgreSQL

✅ 支持高并发  
✅ 性能优秀（有索引）  
✅ 支持复杂 SQL 查询  
✅ 自动备份  
✅ 提供实时订阅功能  
✅ 免费额度充足（500MB 数据库，2GB 文件存储）  

## 🔧 常见问题

### Q1: 迁移后原来的 JSON 文件怎么办？

A: 建议保留 `data/` 目录作为备份，确认 Supabase 运行稳定后再删除。

### Q2: Supabase 免费额度够用吗？

A: 免费版提供：
- 500MB 数据库存储
- 2GB 文件存储
- 每月 50,000 次 API 请求
- 对于小型项目完全够用

### Q3: 如何回滚到 JSON 存储？

A: 在 `app.py` 中将导入改回：
```python
from storage import User, Relationship, CoachChat, LoungeChat
```

### Q4: 数据安全吗？

A: Supabase 提供：
- SSL/TLS 加密传输
- 行级安全策略（RLS）
- 自动备份
- 比本地 JSON 文件更安全

### Q5: 如何导出数据？

A: 在 Supabase SQL Editor 中执行：
```sql
COPY users TO '/tmp/users.csv' CSV HEADER;
```
或使用 Supabase Dashboard 的导出功能。

## 📝 技术细节

### 代码改动说明

1. **新增文件**：
   - `storage_supabase.py` - Supabase 存储层实现
   - `supabase_schema.sql` - 数据库表结构
   - `migrate_to_supabase.py` - 数据迁移脚本

2. **修改文件**：
   - `requirements.txt` - 添加 `supabase==2.3.4`
   - `.env.example` - 添加 Supabase 配置示例
   - `app.py` - 修改导入语句（1行）

3. **保持不变**：
   - 所有业务逻辑代码
   - API 接口
   - 前端代码

### 接口兼容性

`storage_supabase.py` 完全兼容原 `storage.py` 的接口：

```python
# 所有方法签名保持一致
User.get(id)
User.filter(**kwargs)
User.all()
user.save()

# 使用方式完全相同
user = User(phone="13800138000", password="123456")
user.generate_binding_code()
user.save()
```

## 🎓 下一步优化建议

1. **添加行级安全策略（RLS）**
   - 确保用户只能访问自己的数据
   - 在 Supabase Dashboard 中配置

2. **启用实时订阅**
   - 情感客厅可以使用 Supabase Realtime
   - 替代当前的 WebSocket 实现

3. **添加全文搜索**
   - PostgreSQL 支持全文搜索
   - 可以搜索聊天记录

4. **数据分析**
   - 使用 SQL 分析用户行为
   - 生成统计报表

## 📞 支持

如有问题，请查看：
- Supabase 官方文档：https://supabase.com/docs
- 项目 README.md
- 提交 Issue

---

**迁移完成时间**：2026-01-18  
**迁移方式**：方案 A（最小改动）  
**测试状态**：待测试

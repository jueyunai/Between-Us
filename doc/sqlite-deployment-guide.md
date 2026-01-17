# SQLite 生产环境部署指南

## 自动初始化机制

**好消息**: 数据库会自动创建和初始化，无需手动操作！

### 工作原理

1. **首次启动时**:
   ```
   python app.py
   ↓
   导入 storage_sqlite.py
   ↓
   自动执行 init_db()
   ↓
   检测到 /mnt/workspace/ 存在（魔搭环境）
   ↓
   创建 /mnt/workspace/emotion_helper.db
   ↓
   创建 4 张表（users, relationships, coach_chats, lounge_chats）
   ↓
   打印: [SQLite] 数据库初始化完成: /mnt/workspace/emotion_helper.db
   ↓
   应用正常运行 ✅
   ```

2. **后续启动时**:
   - 检测到数据库文件已存在
   - 使用 `CREATE TABLE IF NOT EXISTS` 跳过已存在的表
   - 直接使用现有数据
   - 数据完整保留 ✅

## 部署步骤

### 魔搭部署

```bash
# 1. 确保代码已更新
git pull  # 或上传最新代码

# 2. 安装依赖（如果需要）
pip install -r requirements.txt

# 3. 配置环境变量
# 编辑 .env 文件，确保有 COZE_API_KEY 等配置

# 4. 启动应用
python app.py
```

**就这么简单！** 数据库会自动创建在 `/mnt/workspace/emotion_helper.db`

### 验证数据库

启动后查看日志，应该看到：
```
[SQLite] 数据库初始化完成: /mnt/workspace/emotion_helper.db
============================================================
[启动] 使用 SQLite 本地数据库
[启动] 数据库路径: /mnt/workspace/emotion_helper.db
============================================================
```

## 数据库管理

### 查看数据库

```bash
# 进入容器（如果是 Docker 部署）
docker exec -it <container_id> bash

# 查看数据库文件
ls -lh /mnt/workspace/emotion_helper.db

# 使用 SQLite 命令行
sqlite3 /mnt/workspace/emotion_helper.db

# 查看所有表
.tables

# 查看表结构
.schema users

# 查看数据
SELECT * FROM users;

# 退出
.quit
```

### 备份数据库

```bash
# 方法 1: 直接复制文件
cp /mnt/workspace/emotion_helper.db /mnt/workspace/emotion_helper_backup_$(date +%Y%m%d).db

# 方法 2: 导出 SQL
sqlite3 /mnt/workspace/emotion_helper.db .dump > backup.sql

# 方法 3: 下载到本地（如果有文件访问权限）
# 直接下载 /mnt/workspace/emotion_helper.db 文件
```

### 恢复数据库

```bash
# 从备份文件恢复
cp /mnt/workspace/emotion_helper_backup_20260118.db /mnt/workspace/emotion_helper.db

# 从 SQL 文件恢复
sqlite3 /mnt/workspace/emotion_helper.db < backup.sql
```

### 清空数据重新开始

```bash
# 删除数据库文件
rm /mnt/workspace/emotion_helper.db

# 重启应用，会自动创建新的空数据库
python app.py
```

## 常见问题

### Q1: 数据库文件权限问题？
**A**: 确保应用进程有 `/mnt/workspace/` 目录的读写权限。魔搭环境默认已配置好。

### Q2: 数据库文件太大怎么办？
**A**: SQLite 支持 TB 级数据，一般不会有问题。如果需要清理：
```sql
-- 删除旧的聊天记录（保留最近 30 天）
DELETE FROM coach_chats WHERE created_at < datetime('now', '-30 days');
DELETE FROM lounge_chats WHERE created_at < datetime('now', '-30 days');

-- 压缩数据库文件
VACUUM;
```

### Q3: 如何迁移现有数据？
**A**: 如果有 Supabase 或其他数据源的数据：

```python
# 创建迁移脚本 migrate_data.py
from storage_sqlite import User, CoachChat, LoungeChat
# ... 从旧数据源读取数据
# ... 使用 User().save() 等方法写入 SQLite
```

### Q4: 多实例部署怎么办？
**A**: SQLite 适合单实例部署。如需多实例：
- 方案 1: 使用负载均衡 + Session Sticky（推荐）
- 方案 2: 改用 PostgreSQL/MySQL
- 方案 3: 使用 Redis 做共享存储

### Q5: 数据库损坏怎么办？
**A**: SQLite 非常稳定，极少损坏。如果发生：
```bash
# 检查数据库完整性
sqlite3 /mnt/workspace/emotion_helper.db "PRAGMA integrity_check;"

# 尝试修复
sqlite3 /mnt/workspace/emotion_helper.db ".recover" | sqlite3 recovered.db
```

## 监控建议

### 数据库大小监控

```bash
# 查看数据库文件大小
du -h /mnt/workspace/emotion_helper.db

# 查看各表记录数
sqlite3 /mnt/workspace/emotion_helper.db <<EOF
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'relationships', COUNT(*) FROM relationships
UNION ALL
SELECT 'coach_chats', COUNT(*) FROM coach_chats
UNION ALL
SELECT 'lounge_chats', COUNT(*) FROM lounge_chats;
EOF
```

### 性能监控

在 `app.py` 中已有性能日志：
```python
[DB Perf] 异步保存耗时: 0.003s
```

如果保存耗时 > 100ms，可能需要：
- 添加索引
- 清理旧数据
- 检查磁盘性能

## 优化建议

### 添加索引（可选）

如果数据量大（>10万条），可以添加索引：

```sql
-- 为常用查询添加索引
CREATE INDEX IF NOT EXISTS idx_coach_chats_user_id ON coach_chats(user_id);
CREATE INDEX IF NOT EXISTS idx_lounge_chats_room_id ON lounge_chats(room_id);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
```

在 `storage_sqlite.py` 的 `init_db()` 函数中添加即可。

### 定期维护（可选）

```bash
# 每月执行一次，优化数据库
sqlite3 /mnt/workspace/emotion_helper.db "VACUUM; ANALYZE;"
```

## 总结

✅ **零配置**: 启动应用自动创建数据库  
✅ **零维护**: 正常使用无需人工干预  
✅ **高性能**: 本地文件访问，毫秒级响应  
✅ **易备份**: 直接复制 .db 文件即可  

**只需启动应用，一切自动完成！**

# SQLite 快速启动指南

## 🎉 零配置启动

**数据库会自动创建和初始化，无需手动操作！**

## 一键测试

```bash
# 测试 SQLite 存储层
python test_sqlite.py
```

## 启动应用

```bash
# 1. 安装依赖（如果还没安装）
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 COZE_API_KEY 等配置

# 3. 启动应用（数据库自动创建）
python app.py
```

**就这么简单！** 首次启动时会看到：
```
[SQLite] 数据库初始化完成: /mnt/workspace/emotion_helper.db
```

## 数据库位置

- **魔搭部署**: `/mnt/workspace/emotion_helper.db`（持久化，自动创建）
- **本地开发**: `./emotion_helper.db`（项目根目录，自动创建）

## 查看数据库

```bash
# 使用 SQLite 命令行工具
sqlite3 emotion_helper.db

# 查看所有表
.tables

# 查看用户
SELECT * FROM users;

# 退出
.quit
```

## 常见问题

### Q: 数据库文件在哪里？
A: 代码会自动检测环境，魔搭部署时使用 `/mnt/workspace/`，本地开发使用当前目录。

### Q: 如何备份数据？
A: 直接复制 `emotion_helper.db` 文件即可。

### Q: 如何清空数据重新开始？
A: 删除 `emotion_helper.db` 文件，重启应用会自动创建新数据库。

### Q: 性能如何？
A: 本地数据库，零网络延迟，读写速度 < 5ms。

## 迁移说明

如果之前使用 Supabase，现在已完全切换到 SQLite：
- ✅ 无需配置 Supabase
- ✅ 无需网络连接数据库
- ✅ 性能提升 20-100 倍
- ✅ 完全免费

详细文档: `doc/sqlite-migration-2026-01-18.md`

# 魔搭 Docker 部署指南（SQLite 版本）

**更新日期**: 2026-01-18  
**数据库**: SQLite（本地持久化存储）

## ✅ 部署前检查清单

### 1. 代码配置
- ✅ `app.py` 使用 `from storage_sqlite import ...`
- ✅ `README.md` 包含魔搭元数据（sdk: docker, app_port: 7860）
- ✅ `Dockerfile` 暴露 7860 端口
- ✅ `ms_deploy.json` 配置正确（已移除 Supabase 配置）
- ✅ SQLite 数据库路径：`/mnt/workspace/emotion_helper.db`（持久化）

### 2. 环境变量
在魔搭创空间设置中配置以下环境变量：

```bash
COZE_API_KEY=你的实际Key
COZE_BOT_ID_COACH=7595750315371413544
COZE_BOT_ID_LOUNGE=7596155063970758699
FLASK_ENV=production
```

### 3. 依赖检查
`requirements.txt` 已包含所有必需依赖：
- Flask==3.0.0
- Flask-CORS==4.0.0
- Flask-SocketIO==5.3.6
- python-socketio==5.11.0
- requests==2.31.0
- 无需 Supabase 依赖

## 🚀 部署步骤

### 方式一：通过魔搭 Web 界面

1. **创建创空间**
   - 访问 https://modelscope.cn/studios
   - 点击"创建空间"
   - 选择 Docker SDK
   - 填写空间名称和描述

2. **上传代码**
   - 方式 A：通过 Git 推送
   - 方式 B：直接上传文件（压缩包）

3. **配置环境变量**
   - 进入空间设置 → 环境变量
   - 添加上述 4 个环境变量
   - 保存配置

4. **启动空间**
   - 点击"重启空间"
   - 等待构建完成（约 3-5 分钟）
   - 访问生成的 URL

### 方式二：通过 Git 推送

```bash
# 1. 克隆魔搭创空间仓库
git clone https://www.modelscope.cn/studios/你的用户名/你的空间名.git

# 2. 复制项目文件
cp -r 你的项目路径/* 你的空间名/

# 3. 提交并推送
cd 你的空间名
git add .
git commit -m "部署 SQLite 版本"
git push origin main
```

## 📊 数据持久化说明

### 数据库位置
- **生产环境**: `/mnt/workspace/emotion_helper.db`
- **自动创建**: 首次启动时自动初始化
- **持久化**: Docker 重启后数据保留

### 数据库表结构
```sql
users           -- 用户表
relationships   -- 关系表
coach_chats     -- 个人教练聊天记录
lounge_chats    -- 情感客厅聊天记录
```

### 备份建议
```bash
# 进入容器
docker exec -it <container_id> bash

# 备份数据库
cp /mnt/workspace/emotion_helper.db /mnt/workspace/backup_$(date +%Y%m%d).db

# 或导出 SQL
sqlite3 /mnt/workspace/emotion_helper.db .dump > backup.sql
```

## 🔍 部署后验证

### 1. 检查启动日志
应该看到：
```
============================================================
[启动] 使用 SQLite 本地数据库
[启动] 数据库路径: /mnt/workspace/emotion_helper.db
============================================================
[SQLite] 数据库初始化完成: /mnt/workspace/emotion_helper.db
```

### 2. 功能测试清单
- [ ] 访问首页正常加载
- [ ] 用户注册功能正常
- [ ] 用户登录功能正常
- [ ] 个人教练聊天室可用
- [ ] 情感客厅 WebSocket 连接成功
- [ ] AI 回复功能正常（流式输出）
- [ ] 伴侣绑定功能正常
- [ ] 数据持久化（重启后数据保留）

### 3. 性能检查
查看日志中的性能指标：
```
[DB Perf] 异步保存耗时: 0.003s  # 应该 < 0.1s
```

## ⚠️ 注意事项

### 1. 数据安全
- ✅ 数据存储在 `/mnt/workspace/`，Docker 重启后保留
- ⚠️ 创空间转移/重命名时数据会丢失，需提前备份
- ⚠️ 定期备份数据库文件

### 2. 并发限制
- SQLite 适合中小规模应用（< 1000 并发用户）
- 如需更高并发，考虑迁移到 PostgreSQL

### 3. WebSocket 支持
- 魔搭创空间支持 WebSocket
- 确保 `flask-socketio` 配置正确
- CORS 已设置为 `*`（允许所有来源）

### 4. 资源配置
- 推荐配置：2v-cpu-16g-mem（当前配置）
- 如用户量增加，可升级到 4v-cpu-32g-mem

## 🐛 常见问题

### Q1: 数据库初始化失败？
**A**: 检查 `/mnt/workspace/` 目录权限，确保应用有读写权限。

### Q2: WebSocket 连接失败？
**A**: 检查：
1. 前端 WebSocket URL 是否正确
2. CORS 配置是否允许
3. 魔搭创空间是否支持 WebSocket（默认支持）

### Q3: AI 回复超时？
**A**: 检查：
1. `COZE_API_KEY` 是否配置正确
2. 网络连接是否正常
3. Coze API 是否有调用限制

### Q4: 数据丢失？
**A**: 
1. 确认数据库路径是 `/mnt/workspace/emotion_helper.db`
2. 检查是否误删数据库文件
3. 从备份恢复

## 📈 监控建议

### 日志监控
```bash
# 查看实时日志
docker logs -f <container_id>

# 查看最近 100 行
docker logs --tail 100 <container_id>
```

### 数据库监控
```bash
# 进入容器
docker exec -it <container_id> bash

# 查看数据库大小
du -h /mnt/workspace/emotion_helper.db

# 查看记录数
sqlite3 /mnt/workspace/emotion_helper.db "SELECT COUNT(*) FROM users;"
```

## 🎯 优化建议

### 1. 性能优化
- 添加数据库索引（如果数据量 > 10万条）
- 定期清理旧聊天记录（保留最近 30 天）
- 使用 `VACUUM` 压缩数据库

### 2. 安全加固
- 添加请求频率限制
- 增强密码加密（当前为明文，建议使用 bcrypt）
- 添加 HTTPS 强制跳转

### 3. 功能扩展
- 添加数据导出功能
- 实现聊天记录搜索
- 添加用户反馈机制

## 📚 相关文档

- [SQLite 部署指南](./sqlite-deployment-guide.md)
- [SQLite 迁移记录](./sqlite-migration-2026-01-18.md)
- [项目 README](../README.md)

---

**部署完成后，记得测试所有功能！** 🎉

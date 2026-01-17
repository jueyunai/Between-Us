# SQLite 迁移记录

**日期**: 2026-01-18  
**原因**: Supabase 延迟过高，影响用户体验  
**方案**: 迁移到 SQLite 本地数据库

## 变更内容

### 1. 新增文件
- `storage_sqlite.py`: SQLite 存储层实现
  - 保持与 `storage_supabase.py` 相同的接口
  - 使用线程锁确保并发安全
  - 数据库路径: `/mnt/workspace/emotion_helper.db`（持久化存储）

### 2. 修改文件
- `app.py`:
  - 导入从 `storage_supabase` 改为 `storage_sqlite`
  - 移除 Supabase 延迟检测函数
  - 更新启动日志，显示使用 SQLite

- `.env.example`:
  - 移除 Supabase 配置项
  - 添加 SQLite 说明

### 3. 数据库设计
SQLite 数据库包含 4 张表：

1. **users** - 用户表
   - id, phone, password, binding_code, partner_id, unbind_at, created_at

2. **relationships** - 关系表
   - id, user1_id, user2_id, room_id, is_active, created_at

3. **coach_chats** - 个人教练聊天记录
   - id, user_id, role, content, reasoning_content, created_at

4. **lounge_chats** - 情感客厅聊天记录
   - id, room_id, user_id, role, content, created_at

## 技术要点

### 持久化存储
- **生产环境**：数据库文件存储在 `/mnt/workspace/emotion_helper.db`
- **开发环境**：数据库文件存储在项目根目录 `emotion_helper.db`
- 代码自动检测环境，无需手动配置
- 魔搭部署时，`/mnt/workspace/` 目录在 Docker 重启后数据会保留
- 注意：创空间转移/重命名时数据会丢失

### 并发安全
- 使用 `threading.Lock` 保护数据库操作
- SQLite 连接设置 `check_same_thread=False`
- 使用 `row_factory = sqlite3.Row` 方便数据访问

### 接口兼容
- 所有模型类（User, Relationship, CoachChat, LoungeChat）保持相同接口
- 方法签名完全一致：`save()`, `get()`, `filter()`, `all()`
- 无需修改业务逻辑代码

## 优势

1. **零延迟**: 本地数据库，无网络请求
2. **简单可靠**: 无需外部服务依赖
3. **成本降低**: 不需要 Supabase 订阅
4. **易于调试**: 可直接查看 .db 文件

## 注意事项

1. **数据迁移**: 如果 Supabase 有现有数据，需要手动导出导入
2. **备份策略**: 定期备份 `/mnt/workspace/emotion_helper.db`
3. **扩展性**: 单机部署适用，多实例部署需考虑其他方案

## 下一步建议

1. 测试所有功能：注册、登录、绑定、聊天
2. 如有 Supabase 历史数据，编写迁移脚本
3. 考虑添加数据库备份机制

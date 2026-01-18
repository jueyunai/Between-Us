# 清理：移除 Socket.IO 相关文件

**日期**：2026-01-18  
**类型**：代码清理

## 背景

项目已从 Socket.IO 方案迁移到短轮询方案，但保留了一些旧的 Socket.IO 相关文件和路由。

## 清理内容

### 删除的文件
1. **`templates/lounge.html`** - Socket.IO 版本的情感客厅页面
   - 已被 `templates/lounge_polling.html` 完全替代
   - 包含 Socket.IO 客户端代码
   - 不再使用

2. **`templates/lounge_debug.html`** - 调试页面
   - 仅用于开发调试
   - 生产环境不需要

### 删除的路由（app.py）
1. **`/lounge/websocket`** - WebSocket 版本路由
   - 返回已删除的 `lounge.html`
   - 标记为"备用"但实际未使用

2. **`/lounge/debug`** - 调试路由
   - 返回已删除的 `lounge_debug.html`
   - 仅用于开发调试

### 保留的文件
- **`templates/lounge_polling.html`** - 当前使用的轮询版本
- **`/lounge` 路由** - 返回 `lounge_polling.html`

## 技术说明

### 为什么弃用 Socket.IO？
1. **部署兼容性**：魔搭平台对 WebSocket 支持不稳定
2. **简化架构**：短轮询方案更简单，易于维护
3. **性能足够**：对于情感客厅的使用场景，轮询延迟可接受

### 短轮询方案
- 客户端每秒轮询一次 `/api/lounge/messages/new?since_id=X`
- 服务器返回新消息（如果有）
- 无需维护 WebSocket 连接

## 影响评估

### 无影响
- 用户体验无变化（已在使用轮询方案）
- 功能完全一致
- 性能无明显差异

### 正面影响
- 代码库更清晰
- 减少维护负担
- 避免混淆（只有一个客厅实现）

## 后续建议

1. **依赖清理**：检查 `requirements.txt` 是否还需要 `flask-socketio`
2. **文档更新**：确保部署文档中移除 Socket.IO 相关说明
3. **测试验证**：确认客厅功能正常工作

## 验证清单

- [x] 删除 `templates/lounge.html`
- [x] 删除 `templates/lounge_debug.html`
- [x] 删除 `/lounge/websocket` 路由
- [x] 删除 `/lounge/debug` 路由
- [x] 保留 `/lounge` 路由指向 `lounge_polling.html`
- [ ] 测试客厅功能正常
- [ ] 检查是否需要移除 `flask-socketio` 依赖

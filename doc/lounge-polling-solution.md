# 情感客厅短轮询方案

## 背景
Socket.IO 在魔搭平台上遇到兼容性问题（404 错误），改用短轮询方案替代 WebSocket 长连接。

## 方案对比

| 特性 | WebSocket/Socket.IO | 短轮询 |
|------|---------------------|--------|
| 实时性 | 极好（毫秒级） | 良好（1-2秒延迟） |
| 服务器压力 | 低 | 中等 |
| 实现复杂度 | 高 | 低 |
| 平台兼容性 | 可能有问题 | 完美兼容 |
| 适用场景 | 高频实时通信 | 低频聊天 |

**结论**：情感客厅是两人聊天场景，消息频率不高，短轮询完全够用。

## 技术实现

### 前端（lounge_polling.html）

**核心机制**：
```javascript
// 每 1.5 秒检查一次新消息
setInterval(async () => {
    const response = await fetch(`/api/lounge/messages/new?since_id=${lastMessageId}`);
    const data = await response.json();
    if (data.messages.length > 0) {
        // 有新消息，更新界面
        messages.push(...data.messages);
        renderMessages();
    }
}, 1500);
```

**优势**：
- 无需 WebSocket 依赖
- 自动重连（HTTP 请求失败会自动重试）
- 兼容所有平台

### 后端 API

#### 1. `/api/lounge/messages/new` - 获取新消息
```python
@app.route('/api/lounge/messages/new', methods=['GET'])
def get_new_lounge_messages():
    since_id = request.args.get('since_id', 0, type=int)
    # 返回 ID > since_id 的所有新消息
    new_messages = [msg for msg in all_messages if msg.id > since_id]
    return jsonify({'success': True, 'messages': new_messages})
```

#### 2. `/api/lounge/send` - 发送消息
```python
@app.route('/api/lounge/send', methods=['POST'])
def send_lounge_message():
    msg = LoungeChat(room_id=room_id, user_id=user_id, content=content)
    msg.save()
    return jsonify({'success': True, 'message': msg.to_dict()})
```

#### 3. `/api/lounge/call_ai` - 召唤 AI
```python
@app.route('/api/lounge/call_ai', methods=['POST'])
def call_lounge_ai():
    # 调用 Coze API（非流式）
    ai_reply = call_coze_api(...)
    ai_msg = LoungeChat(room_id=room_id, role='assistant', content=ai_reply)
    ai_msg.save()
    return jsonify({'success': True, 'message': ai_msg.to_dict()})
```

## 性能优化

### 1. 轮询间隔
- **当前设置**：1.5 秒
- **可调整范围**：1-3 秒
- **建议**：根据实际使用情况调整，消息频率高可缩短到 1 秒

### 2. 数据库查询优化
- 使用 `since_id` 参数，只查询新消息
- 避免每次都加载全部历史记录

### 3. 前端优化
- 只在有新消息时才重新渲染
- 使用 `lastMessageId` 跟踪最新消息

## 用户体验

### 优点
- ✅ 稳定可靠，无连接断开问题
- ✅ 实现简单，易于调试
- ✅ 兼容所有浏览器和平台

### 缺点
- ⚠️ 有 1-2 秒延迟（可接受）
- ⚠️ 服务器请求稍多（可优化）

### 实际体验
对于情感客厅这种场景：
- 两人对话，不是高频消息轰炸
- 1-2 秒延迟完全可以接受
- 用户感知不到明显差异

## 部署说明

1. **无需额外依赖**：移除了 eventlet、Socket.IO 相关依赖
2. **简化配置**：不需要配置 WebSocket 路由
3. **即时生效**：重新部署后立即可用

## 路由说明

- `/lounge` - 默认使用短轮询版本（推荐）
- `/lounge/websocket` - WebSocket 版本（备用，如果平台支持可切换）

## 日期
2026-01-18

# 情感客厅AI消息优化

## 修改时间
2026-01-18

## 修改目标
优化情感客厅@教练功能，减少重复消息传输，降低API消耗

## 核心改动

### 1. 数据库层（storage_sqlite.py）

**新增字段**：
- `lounge_chats` 表添加 `sent_to_ai` 字段（INTEGER，默认0）
- 用于标记消息是否已传给AI

**模型更新**：
- `LoungeChat.__init__` 增加 `sent_to_ai` 参数
- `LoungeChat.to_dict()` 返回 `sent_to_ai` 字段
- `LoungeChat.save()` 保存 `sent_to_ai` 状态
- `LoungeChat.from_row()` 读取 `sent_to_ai` 状态

**数据库迁移**：
- `init_db()` 函数增加自动迁移逻辑
- 检测已存在的表，自动添加 `sent_to_ai` 字段
- 兼容旧数据库，无需手动迁移

### 2. 业务逻辑层（app.py）

**消息格式优化**：
```python
# 修改前
"请基于以上对话内容，作为情感调解专家，提供建设性的沟通建议，帮助双方理解彼此：\n今天心情不好\n怎么了？\n..."

# 修改后
"用户A：今天心情不好\n用户B：怎么了？\n用户A：工作压力大\n用户B：我理解你"
```

**关键改进**：
1. **去掉固定提示词**：让AI根据智能体配置自主判断角色
2. **添加说话人标识**：使用手机号作为昵称（格式：`昵称：消息内容`）
3. **过滤已传消息**：只传 `sent_to_ai=False` 的消息
4. **限制消息数量**：最多传最近10条未发送的消息
5. **标记已传消息**：传给AI后立即标记 `sent_to_ai=True`

**实现逻辑**：
```python
# 1. 获取房间的两个用户，建立昵称映射
user_map = {user1.id: user1.phone, user2.id: user2.phone}

# 2. 筛选未传给AI的用户消息
unsent_messages = [msg for msg in all_history if msg.role == "user" and not msg.sent_to_ai]

# 3. 限制最近10条
messages_to_send = unsent_messages[-10:]

# 4. 格式化消息（昵称：内容）
formatted_messages = [f"{user_map[msg.user_id]}：{msg.content}" for msg in messages_to_send]

# 5. 调用AI后标记已传
for msg in messages_to_send:
    msg.sent_to_ai = True
    msg.save()
```

## 效果对比

### 修改前
- 每次@教练都传最近10条消息（包括已传过的）
- 消息格式无说话人标识
- 有固定提示词占用token

### 修改后
- 只传未发送过的新消息（最多10条）
- 消息格式清晰：`昵称：内容`
- 无固定提示词，节省token
- **显著降低API消耗**（尤其是频繁@教练的场景）

## 兼容性
- 自动数据库迁移，无需手动操作
- 旧数据默认 `sent_to_ai=0`（未传）
- 不影响现有功能

## 下一步建议
1. 观察生产环境API消耗变化
2. 如需要，可考虑添加"重置标记"功能（让用户手动清除已传标记）
3. 可在前端显示"已分析X条消息"提示

# 情感客厅 AI 思考状态同步

## 需求
当用户 A 点击"@教练"召唤 AI 时，用户 B 的界面也要同步显示"情感教练正在分析..."的过渡状态。

## 方案选择

### 方案 1：数据库状态标记（已采用）⭐
**原理**：在数据库中保存一条特殊的"思考中"消息，轮询时两个用户都能看到

**优点**：
- ✅ 简单可靠，符合短轮询架构
- ✅ 两个用户自动同步，无需额外逻辑
- ✅ 刷新页面后状态也能保持
- ✅ 无需修改数据库结构

## 实现细节

### 后端实现（app.py）

```python
@app.route('/api/lounge/call_ai', methods=['POST'])
def call_lounge_ai():
    # 1. 立即保存"思考中"占位消息
    thinking_msg = LoungeChat(
        room_id=room_id, 
        user_id=None, 
        role='assistant', 
        content='🎯 情感教练正在分析...'
    )
    thinking_msg.save()  # 获得 ID
    
    # 2. 调用 AI（可能需要几秒）
    ai_reply = call_coze_api(...)
    
    # 3. 更新同一条消息为真实回复
    thinking_msg.content = ai_reply
    thinking_msg.save()
    
    return jsonify({'success': True, 'message': thinking_msg.to_dict()})
```

**关键点**：
- 使用同一个消息对象，先保存占位内容，后更新为真实回复
- 不会产生两条消息，只有一条记录
- 两个用户的轮询都会获取到这条消息的变化

### 前端实现（lounge_polling.html）

**简化前端逻辑**：
```javascript
async function callAI() {
    // 直接调用 API，不需要本地添加占位消息
    const response = await fetch('/api/lounge/call_ai', {
        method: 'POST',
        body: JSON.stringify({ room_id: roomId })
    });
    
    // 服务器已经保存了消息，轮询会自动获取
    // 立即检查一次新消息，加快显示速度
    await checkNewMessages();
}
```

**渲染逻辑**：
```javascript
function renderMessages() {
    messages.forEach((msg) => {
        if (msg.role === 'assistant') {
            // 如果是"思考中"消息，添加动画效果
            if (msg.content === '🎯 情感教练正在分析...') {
                messageDiv.classList.add('ai-thinking');
            }
        }
    });
}
```

**CSS 动画**：
```css
.ai-thinking {
    opacity: 0.7;
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 0.7; }
    50% { opacity: 1; }
}
```

## 工作流程

### 用户 A 触发 AI
1. 用户 A 点击"@教练"按钮
2. 前端调用 `/api/lounge/call_ai`
3. 后端立即保存"思考中"消息（ID=123）
4. 后端开始调用 Coze API（耗时 3-5 秒）
5. 后端更新消息 ID=123 为真实回复
6. 返回给用户 A

### 用户 B 自动同步
1. 用户 B 的轮询（每 1.5 秒）检查新消息
2. 第一次轮询：获取到"思考中"消息（ID=123），显示动画
3. 第二次轮询：获取到更新后的消息（ID=123），显示真实回复
4. 前端检测到内容变化，自动更新界面

## 技术优势

### 1. 自动同步
- 无需额外的同步逻辑
- 利用现有的轮询机制
- 两个用户看到的状态完全一致

### 2. 状态持久化
- 刷新页面后，"思考中"状态依然可见
- 不会因为网络波动丢失状态

### 3. 简单可靠
- 不需要修改数据库结构
- 不需要新增 API 接口
- 代码改动最小

### 4. 性能优化
- 只有一条数据库记录（更新而非新增）
- 轮询频率不变（1.5 秒）
- 无额外的网络请求

## 用户体验

### 用户 A（触发者）
1. 点击按钮后，立即看到"思考中"消息
2. 3-5 秒后，消息自动更新为 AI 回复
3. 体验流畅，无闪烁

### 用户 B（观察者）
1. 1.5 秒内看到"思考中"消息（轮询延迟）
2. 3-5 秒后，消息自动更新为 AI 回复
3. 感知到 AI 正在工作，不会觉得卡顿

## 边界情况处理

### 1. AI 调用失败
- 更新消息为错误提示："AI 调用失败，请稍后重试"
- 两个用户都能看到错误信息

### 2. 网络中断
- 消息已保存在数据库，恢复后可见
- 轮询会自动重连

### 3. 并发调用
- `isAIThinking` 标志防止重复调用
- 数据库更新操作是原子的

## 日期
2026-01-18

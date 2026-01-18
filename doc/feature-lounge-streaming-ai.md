# 客厅AI流式输出功能

## 功能说明
将客厅的AI回复从"等待完成后一次性显示"升级为"实时流式输出"，完全照搬个人教练的流式效果，包括：
- 实时显示思考过程（可折叠）
- 实时显示正文内容（打字机效果）
- 流式光标动画

## 实现方案

### 后端：新增流式API

创建 `/api/lounge/call_ai/stream` 接口，使用 SSE（Server-Sent Events）推送流式数据：

```python
@app.route('/api/lounge/call_ai/stream', methods=['POST'])
def call_lounge_ai_stream():
    def generate():
        # 调用 Coze API（流式）
        for line in response.iter_lines():
            # 解析 SSE 事件
            if current_event == 'conversation.message.delta':
                # 增量推送思考过程和正文
                yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning})}\n\n"
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
            
            elif current_event == 'conversation.message.completed':
                # 推送完成信号
                yield f"data: {json.dumps({'type': 'reasoning_done'})}\n\n"
        
        # 保存到数据库
        ai_msg.save()
        yield f"data: {json.dumps({'type': 'done', ...})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')
```

### 前端：流式接收和渲染

修改 `callAI()` 函数，使用 Fetch API 的流式读取：

```javascript
async function callAI() {
    // 创建流式消息占位
    const streamingMsg = {
        id: 'streaming_' + Date.now(),
        isStreaming: true
    };
    messages.push(streamingMsg);
    renderMessages();

    // 调用流式API
    const response = await fetch('/api/lounge/call_ai/stream', ...);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // 解析 SSE 数据
        const lines = decoder.decode(value).split('\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'reasoning') {
                    // 实时更新思考过程
                    reasoningText += data.content;
                    updateStreamingMessage(...);
                }
                else if (data.type === 'content') {
                    // 实时更新正文
                    answerText += data.content;
                    updateStreamingMessage(...);
                }
                else if (data.type === 'done') {
                    // 完成，重新加载历史
                    await checkNewMessages();
                }
            }
        }
    }
}
```

### 实时更新函数

```javascript
function updateStreamingMessage(msgId, reasoning, content, isThinking) {
    // 找到流式消息的 DOM 元素
    const msgEl = document.querySelector(`[data-msg-id="${msgId}"]`);
    
    // 更新思考过程
    if (reasoning) {
        thinkingContent.textContent = reasoning;
        if (isThinking) {
            thinkingToggle.innerHTML = '🧠 思考中...';
        } else {
            thinkingToggle.innerHTML = '🧠 思考过程（点击展开）';
        }
    }
    
    // 更新正文内容
    answerContent.innerHTML = formatMessageContent(content, true);
    if (isThinking) {
        answerContent.innerHTML += '<span class="streaming-cursor"></span>';
    }
    
    // 滚动到底部
    container.scrollTop = container.scrollHeight;
}
```

## 用户体验

### 流式效果
1. 用户发送"@教练"消息
2. **立即显示**"🎯 情感教练正在分析..."
3. **实时显示**思考过程（逐字输出）
4. 思考完成后，按钮变为"🧠 思考过程（点击展开）"
5. **实时显示**正文内容（打字机效果）
6. 显示流式光标动画
7. 完成后移除光标，保存到数据库

### 与短轮询版本对比
| 特性 | 短轮询版本 | 流式版本 |
|------|-----------|---------|
| 响应速度 | 3-5秒后一次性显示 | 实时逐字显示 |
| 思考过程 | 等待完成后显示 | 实时显示 |
| 用户体验 | 等待焦虑 | 流畅自然 |
| 技术复杂度 | 低 | 中 |

## 技术细节

### SSE vs WebSocket
选择 SSE（Server-Sent Events）而不是 WebSocket：
- **单向通信**：AI回复只需服务器推送，不需要双向
- **简单易用**：基于 HTTP，无需额外协议
- **自动重连**：浏览器自动处理断线重连
- **兼容性好**：所有现代浏览器支持

### 流式光标动画
```css
.streaming-cursor {
    display: inline-block;
    width: 2px;
    height: 1em;
    background: var(--home-accent);
    animation: blink 0.8s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
```

### 数据同步
- 流式输出时，消息只存在前端（临时）
- 完成后，后端保存到数据库
- 前端重新加载历史，确保数据一致
- 另一个用户通过短轮询获取完整消息

## 兼容性

### 保留短轮询接口
为了兼容性，保留原有的 `/api/lounge/call_ai` 接口：
- 流式版本：`/api/lounge/call_ai/stream`（新）
- 短轮询版本：`/api/lounge/call_ai`（保留）

### 降级方案
如果流式API失败，可以回退到短轮询：
```javascript
try {
    // 尝试流式API
    await callAIStream();
} catch (error) {
    // 降级到短轮询
    await callAIPolling();
}
```

## 修改文件
- `app.py` - 新增 `/api/lounge/call_ai/stream` 接口
- `templates/lounge_polling.html` - 修改 `callAI()` 和 `renderMessages()` 函数

## 测试验证
1. ✅ 发送"@教练"消息
2. ✅ 实时显示"思考中..."
3. ✅ 实时显示思考过程（逐字输出）
4. ✅ 思考完成后，按钮变为"点击展开"
5. ✅ 实时显示正文内容（打字机效果）
6. ✅ 显示流式光标动画
7. ✅ 完成后保存到数据库
8. ✅ 另一个用户能看到完整消息

## 与个人教练的一致性
- ✅ 相同的流式输出效果
- ✅ 相同的思考过程折叠样式
- ✅ 相同的流式光标动画
- ✅ 相同的用户体验

---
**实现时间**: 2026-01-18  
**影响范围**: 情感客厅（`/lounge` 路由）  
**用户体验**: ⭐⭐⭐⭐⭐ 完美（与个人教练一致）

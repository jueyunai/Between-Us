# 修复：AI 回复时禁用发送按钮

**日期**：2026-01-18  
**类型**：功能优化 / Bug 修复

## 问题描述

在个人教练和情感客厅页面，用户可以在 AI 正在生成回复时继续发送消息，这可能导致：
1. 多次触发 AI 请求，造成资源浪费
2. 消息顺序混乱
3. 用户体验不佳

## 解决方案

### 1. 个人教练页面（coach.html）
- **已有机制**：使用 `isStreaming` 标志控制发送状态
- **现有逻辑**：
  - 发送消息时设置 `isStreaming = true` 并禁用按钮
  - 流式传输完成后恢复 `isStreaming = false` 并启用按钮
- **状态**：✅ 无需修改，已正确实现

### 2. 情感客厅页面（lounge.html）
- **新增机制**：添加 `isAIResponding` 标志控制发送状态
- **实现逻辑**：
  1. 监听 `ai_thinking_start` 事件时设置 `isAIResponding = true`
  2. 监听 `ai_stream` 的 `done` 事件时设置 `isAIResponding = false`
  3. 在 `sendMessage()` 函数中检查状态，如果 AI 正在回复则提示用户
  4. 新增 `updateSendButtonState()` 函数统一管理按钮状态
  5. Enter 键处理函数中也检查 AI 回复状态

## 修改文件

- `templates/lounge.html`

## 技术细节

### 按钮状态管理
```javascript
// 新增状态标志
let isAIResponding = false;

// 统一的按钮状态更新函数
function updateSendButtonState() {
    const sendBtn = document.querySelector('.send-btn');
    if (sendBtn) {
        sendBtn.disabled = isAIResponding;
        if (isAIResponding) {
            sendBtn.style.opacity = '0.5';
            sendBtn.style.cursor = 'not-allowed';
        } else {
            sendBtn.style.opacity = '1';
            sendBtn.style.cursor = 'pointer';
        }
    }
}
```

### 事件监听
```javascript
// AI 开始回复时禁用
socket.on('ai_thinking_start', () => {
    isAIResponding = true;
    updateSendButtonState();
    // ...
});

// AI 回复完成时启用
socket.on('ai_stream', (data) => {
    if (data.type === 'done') {
        isAIResponding = false;
        updateSendButtonState();
    }
});
```

### 发送拦截
```javascript
function sendMessage() {
    if (isAIResponding) {
        showToast('教练正在回复中，请稍候...', 'info');
        return;
    }
    // ...
}

function handleEnter(event) {
    if (event.key === 'Enter' && !isAIResponding) {
        sendMessage();
    }
}
```

## 用户体验改进

1. **视觉反馈**：按钮禁用时透明度降低，鼠标样式变为 `not-allowed`
2. **友好提示**：尝试发送时显示 Toast 提示"教练正在回复中，请稍候..."
3. **多重保护**：
   - 按钮点击拦截
   - Enter 键拦截
   - 函数内部状态检查

## 测试建议

1. 在个人教练页面发送消息，验证 AI 回复期间按钮是否禁用
2. 在情感客厅页面使用 `@教练` 触发 AI，验证按钮状态
3. 测试 Enter 键和点击按钮两种发送方式
4. 验证 AI 回复完成后按钮是否正确恢复

## 注意事项

- 两个页面使用不同的变量名（`isStreaming` vs `isAIResponding`），但逻辑一致
- 客厅页面使用 Socket.IO 事件驱动，需要监听特定事件来更新状态
- 教练页面使用 Fetch API 流式读取，在 finally 块中恢复状态

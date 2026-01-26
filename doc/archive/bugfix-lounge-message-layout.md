# 修复：情感客厅消息布局问题

**日期**: 2026-01-18  
**类型**: Bug修复

## 问题描述

在情感客厅中，对方（Ta）的消息显示在右边，但应该显示在左边（与教练消息一样）。

### 预期行为
- 自己的消息：右边（粉紫色气泡）
- 对方的消息：左边（白色气泡）
- 教练的消息：左边（白色气泡，橙色边框）

### 实际行为
对方的消息显示在右边，与自己的消息位置相同。

## 根本原因

在 `templates/lounge_polling.html` 的 `renderMessages()` 函数中，消息的 CSS class 设置有误：

```javascript
// 错误的代码
messageDiv.className = `message ${msg.role}`;
```

这里直接使用了 `msg.role` 字段，但对于用户消息，`msg.role` 可能不准确。实际上应该根据 `msg.user_id` 来判断：
- 如果 `msg.user_id === userId`：应该是 `message user`（右边）
- 如果 `msg.user_id !== userId`：应该是 `message partner`（左边）

## 解决方案

重构 `renderMessages()` 函数，先判断消息类型，再设置正确的 CSS class：

```javascript
// 修复后的代码
let messageClass = 'message';

if (msg.role === 'assistant') {
    messageClass += ' assistant';  // 教练消息，左边
} else if (msg.user_id === userId) {
    messageClass += ' user';       // 自己的消息，右边
} else {
    messageClass += ' partner';    // 对方的消息，左边
}

messageDiv.className = messageClass;
```

## 相关文件

- `templates/lounge_polling.html` - 修复消息布局逻辑

## 测试验证

刷新情感客厅页面后：
- ✅ 自己的消息显示在右边（粉紫色气泡）
- ✅ 对方的消息显示在左边（白色气泡）
- ✅ 教练的消息显示在左边（白色气泡，橙色边框）
- ✅ 头像位置正确（自己右边，对方和教练左边）

## 附加修复

同时修复了 AI 消息的 Markdown 格式渲染问题（见 `doc/bugfix-ai-markdown-format.md`）。

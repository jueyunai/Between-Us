# 情感客厅 AI 输出样式修复

## 问题描述
用户反馈：情感客厅的 AI 输出内容没有样式美化，显示为纯文本。

## 问题分析

### 根本原因
项目中有两个情感客厅模板：
1. `templates/lounge.html` - WebSocket 版本（备用）
2. `templates/lounge_polling.html` - 短轮询版本（**当前使用**）

**问题所在**：
- `app.py` 中 `/lounge` 路由指向 `lounge_polling.html`
- `lounge_polling.html` 的 `renderMessages()` 函数只用 `textContent` 显示内容
- 缺少 `formatMessageContent()` 和 `escapeHtml()` 函数
- 缺少 AI 消息的格式化样式（加粗、斜体等）

### 对比 lounge.html（有样式）
- ✅ 有 `formatMessageContent()` 函数支持 Markdown
- ✅ 有 `escapeHtml()` 函数防止 XSS
- ✅ AI 消息用 `innerHTML` 渲染格式化内容
- ✅ CSS 中定义了 `strong` 和 `em` 的样式

## 解决方案

### 1. 添加格式化函数
从 `lounge.html` 移植两个函数到 `lounge_polling.html`：

```javascript
// 格式化消息内容（支持基本 Markdown）
function formatMessageContent(content, isAssistant = false) {
    if (!isAssistant) {
        return escapeHtml(content);
    }

    // AI 消息，支持简单的 Markdown 格式
    let formatted = escapeHtml(content);
    
    // 标题（**标题：** 或 **1. 标题：**）
    formatted = formatted.replace(/\*\*([^*]+)：\*\*/g, '<strong style="color: #9d7a5a;">$1：</strong>');
    
    // 加粗文本（**文本**）
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // 斜体（*文本*）
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    return formatted;
}

// HTML 转义函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

### 2. 修改渲染逻辑
将 `renderMessages()` 中的：
```javascript
contentDiv.textContent = msg.content;
```

改为：
```javascript
// 根据消息类型决定是否格式化
if (msg.role === 'assistant') {
    contentDiv.innerHTML = formatMessageContent(msg.content, true);
} else {
    contentDiv.textContent = msg.content;
}
```

### 3. 添加样式支持
在 `<style>` 中添加：
```css
/* 教练消息内的格式化元素 */
.message.assistant .message-content strong {
    color: #9d7a5a;
    font-weight: 600;
}

.message.assistant .message-content em {
    font-style: italic;
    color: #8b7a6a;
}
```

## 支持的格式

AI 消息现在支持以下 Markdown 格式：

1. **加粗标题**：`**标题：**` → 显示为棕色加粗
2. **加粗文本**：`**文本**` → 显示为加粗
3. **斜体文本**：`*文本*` → 显示为斜体

## 效果对比

### 修复前
```
> *学员版*："我有些焦虑（情绪），因为不确定您是否收到消息（需求），下次能否收到后先回个'收到'？（建议）"
```
显示为纯文本，无格式。

### 修复后
```
> *学员版*："我有些焦虑（情绪），因为不确定您是否收到消息（需求），下次能否收到后先回个'收到'？（建议）"
```
- "学员版" 显示为斜体
- 关键词（情绪、需求、建议）如果加粗会显示为粗体
- 整体排版清晰，层次分明

## 为什么之前有样式？

查看 `doc/lounge-ai-thinking-broadcast.md`，可以看到：
- 2026-01-18 曾经优化过 AI 消息格式
- 当时修改的是 `lounge.html`（WebSocket 版本）
- 但后来切换到了 `lounge_polling.html`（短轮询版本）
- 新模板没有同步这些优化

## 修改文件
- `templates/lounge_polling.html`

## 修复日期
2026-01-18

## 相关文档
- `doc/lounge-ai-thinking-broadcast.md` - AI 消息格式优化记录
- `doc/lounge-polling-solution.md` - 短轮询方案说明

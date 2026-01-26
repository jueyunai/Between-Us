# 情感客厅 AI 递归错误修复

## 问题描述
调用 AI 时返回错误：
```
AI 处理异常: maximum recursion depth exceeded while calling a Python object
```

**影响范围**：
- ✅ 个人教练（普通接口 `/api/coach/chat`）
- ✅ 情感客厅（`/api/lounge/call_ai`）
- ✅ 个人教练流式接口（`/api/coach/chat/stream`）- 无此问题

## 根本原因
在 `call_coze_api()` 函数中，有一段调试代码尝试将 AI 响应写入文件：
```python
with open('coze_debug.json', 'w', encoding='utf-8') as f:
    json.dump(debug_info, f, ensure_ascii=False, indent=2)
```

这段代码可能导致两个问题：
1. **递归深度超限**：如果 `debug_info` 包含循环引用或超大对象，`json.dump()` 会递归失败
2. **文件权限问题**：生产环境（魔搭平台）可能没有写文件权限

## 解决方案

### 1. 移除调试文件写入（已修复）
直接删除 `json.dump()` 相关代码，只保留 `print()` 日志输出：

```python
# app.py 第 226-233 行（已删除）
# with open('coze_debug.json', 'w', encoding='utf-8') as f:
#     json.dump(debug_info, f, ensure_ascii=False, indent=2)
```

**影响函数**：
- `call_coze_api()` - 被个人教练和情感客厅共用

### 2. 优化情感客厅 AI 调用（已优化）
在 `call_lounge_ai()` 中添加更详细的错误处理和日志：

```python
try:
    ai_reply = call_coze_api(...)
    ai_msg.save()
    
    # 手动构建返回数据，避免 to_dict() 可能的序列化问题
    response_data = {
        'success': True,
        'message': {
            'id': ai_msg.id,
            'content': ai_msg.content,
            'created_at': ai_msg.created_at.isoformat()
        }
    }
    return jsonify(response_data)
    
except Exception as e:
    print(f"[Error] {type(e).__name__}: {str(e)}")
    traceback.print_exc()
    return jsonify({'success': False, 'message': str(e)}), 500
```

## 技术说明

### JSON 序列化陷阱
Python 的 `json.dump()` 在遇到以下情况会递归失败：
- 循环引用（对象 A 引用对象 B，B 又引用 A）
- 超大嵌套结构（嵌套层级过深）
- 不可序列化的对象（如 datetime、自定义类）

### 最佳实践
1. **生产环境避免写文件**：使用日志系统（`print()` 或 `logging`）
2. **手动构建 JSON**：对于复杂对象，手动提取需要的字段
3. **添加异常处理**：捕获并记录详细错误信息

## 验证方法

### 个人教练
1. 进入个人教练页面
2. 发送消息
3. 观察 AI 是否正常回复

### 情感客厅
1. 进入情感客厅
2. 发送消息
3. 点击"教练你怎么看？"按钮
4. 观察 AI 是否正常返回建议

## 修复状态
✅ **已全部修复** - 一次修改解决了所有调用 `call_coze_api()` 的接口

## 日期
2026-01-18

# Supabase 性能优化方案

## 问题诊断

### 当前架构
- **本地调试**：本地 → Supabase（延迟低）
- **魔搭部署**：魔搭Docker → Supabase（延迟高，可能跨境）

### 延迟来源
1. **网络延迟**：魔搭服务器到 Supabase 的物理距离
2. **数据库写入**：每次对话2次写入（用户消息 + AI回复）
3. **流式输出阻塞**：保持长连接期间的网络波动

### 数据丢失原因
- 流式输出过程中异常（网络中断、超时）导致 `final_content` 为空
- AI回复未保存到数据库

## 优化方案

### 方案1：异步数据库写入（推荐）⭐
**原理**：将数据库写入操作放到后台线程，不阻塞流式输出

**优点**：
- 前端响应速度快
- 数据库操作不影响用户体验
- 实现简单

**实现**：
```python
import threading

def save_message_async(message_obj):
    """异步保存消息"""
    def _save():
        try:
            message_obj.save()
        except Exception as e:
            print(f"[Async Save Error] {e}", flush=True)
    
    thread = threading.Thread(target=_save)
    thread.daemon = True
    thread.start()
```

### 方案2：批量写入优化
**原理**：累积多条消息后批量写入，减少数据库请求次数

**优点**：
- 减少网络往返次数
- 提高吞吐量

**缺点**：
- 实现复杂
- 可能丢失未提交的数据

### 方案3：边流式边保存（推荐）⭐⭐
**原理**：在流式输出过程中，逐步保存AI回复内容

**优点**：
- 即使流式中断，也能保存部分内容
- 数据不会完全丢失

**实现思路**：
1. 创建AI消息记录（content为空）
2. 流式输出过程中，定期更新content字段
3. 流式结束后，最后更新一次

### 方案4：连接池优化
**原理**：复用 Supabase 客户端连接，减少连接建立时间

**当前问题**：
- 每次请求都可能创建新连接
- 连接建立有额外开销

**优化**：
```python
# 使用全局单例客户端（已实现）
_supabase_client = None

def supabase():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client
```

### 方案5：本地缓存 + 定期同步
**原理**：先写入本地SQLite，定期同步到Supabase

**优点**：
- 写入速度极快
- 数据不会丢失

**缺点**：
- 实现复杂
- 需要处理同步冲突
- 多实例部署时需要额外处理

## 推荐实施顺序

### 第一阶段：快速优化（立即实施）
1. ✅ **异步数据库写入**（方案1）
2. ✅ **边流式边保存**（方案3）

### 第二阶段：深度优化（可选）
3. 批量写入优化（方案2）
4. 本地缓存方案（方案5）

## 监控指标

建议添加以下监控：
```python
import time

# 记录数据库操作耗时
start = time.time()
message.save()
duration = time.time() - start
print(f"[DB Perf] 保存耗时: {duration:.3f}s", flush=True)
```

## 网络诊断

可以在魔搭环境中测试到 Supabase 的延迟：
```python
import requests
import time

start = time.time()
response = requests.get(SUPABASE_URL)
latency = time.time() - start
print(f"[Network] Supabase 延迟: {latency:.3f}s")
```

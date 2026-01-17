# 情感客厅历史数据问题修复

## 问题描述
用户反馈：情感客厅看不到历史数据，输入内容后数据库没更新

## 问题分析

### 1. 根本原因
**Supabase 时间戳格式问题**：Supabase 返回的 `created_at` 字段微秒位数不足6位（如 `.38424` 只有5位），导致 Python 的 `datetime.fromisoformat()` 解析失败。

示例错误：
```
Invalid isoformat string: '2026-01-17T22:18:43.31477+00:00'
```

### 2. 影响范围
- `User.from_dict()` - 用户数据加载
- `Relationship.from_dict()` - 关系数据加载  
- `CoachChat.from_dict()` - 个人教练聊天记录加载
- `LoungeChat.from_dict()` - **情感客厅聊天记录加载（核心问题）**

## 修复方案

### 修改文件：`storage_supabase.py`

在所有模型的 `from_dict()` 方法中添加时间格式容错处理：

```python
created_at = data.get('created_at')
if created_at and isinstance(created_at, str):
    try:
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    except ValueError as e:
        # 处理微秒位数不足的情况
        print(f"[Debug] 时间格式解析失败: {created_at}, 错误: {e}")
        if '+' in created_at:
            time_part, tz_part = created_at.rsplit('+', 1)
            if '.' in time_part:
                base, microseconds = time_part.rsplit('.', 1)
                # 补齐到6位
                microseconds = microseconds.ljust(6, '0')
                created_at = f"{base}.{microseconds}+{tz_part}"
                created_at = datetime.fromisoformat(created_at)
            else:
                created_at = datetime.fromisoformat(created_at)
        else:
            created_at = None
```

### 修复的模型
1. ✅ `User.from_dict()`
2. ✅ `Relationship.from_dict()`
3. ✅ `CoachChat.from_dict()`
4. ✅ `LoungeChat.from_dict()`

## 验证结果

### 后端测试
```bash
python debug_lounge_data.py
```
结果：✅ 成功加载13条历史消息

### API 测试
```bash
python test_lounge_api.py
```
结果：
- ✅ 登录成功
- ✅ 获取房间信息成功（room_3_4）
- ✅ 获取历史记录成功（15条消息）

### 数据库操作测试
```bash
python test_lounge_flow.py
```
结果：
- ✅ 查询历史记录成功
- ✅ 保存新消息成功
- ✅ 验证消息已保存

## 调试工具

### 1. 数据检查脚本
- `debug_lounge_data.py` - 检查所有情感客厅数据
- `check_user_password.py` - 查看用户密码
- `test_lounge_flow.py` - 模拟完整用户流程
- `test_lounge_api.py` - 测试 API 端点

### 2. 调试页面
- `/lounge/debug` - 浏览器端调试页面，显示用户信息、房间信息、历史记录

## 当前状态

✅ **后端完全正常**：
- 数据库读写正常
- API 返回正确数据
- WebSocket 消息保存正常

⚠️ **前端待验证**：
- 需要在浏览器中访问 `/lounge/debug` 确认前端是否能正确接收数据
- 如果调试页面显示正常，则问题在 `lounge.html` 的 JavaScript 渲染逻辑

## 下一步

1. 启动应用：`python app.py`
2. 登录用户（手机：19928786380，密码：123）
3. 访问 `http://localhost:7860/lounge/debug` 查看数据
4. 如果调试页面正常，检查 `templates/lounge.html` 的 `renderMessages()` 函数

## 技术要点

### Supabase 时间戳格式
- Supabase PostgreSQL 返回的时间戳可能微秒位数不足6位
- Python `datetime.fromisoformat()` 要求微秒必须是6位
- 解决方案：用 `ljust(6, '0')` 补齐到6位

### 时间格式示例
```
错误格式: 2026-01-17T22:18:43.31477+00:00  (5位微秒)
正确格式: 2026-01-17T22:18:43.314770+00:00 (6位微秒)
```

## 日期
2026-01-18

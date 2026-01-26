# 功能：昵称支持

**日期**：2026-01-18  
**类型**：新功能

## 需求描述

用户希望能够设置个性化昵称，而不是默认使用手机号后4位作为显示名称。

## 功能设计

### 1. 昵称规则
- **非必填**：注册时可以不填，默认使用手机号后4位
- **长度限制**：最长20个字符
- **可修改**：在个人中心可以随时修改昵称

### 2. 显示逻辑
- 如果用户设置了昵称，优先显示昵称
- 如果没有设置昵称，显示手机号后4位
- 适用于所有需要显示用户名称的地方（个人中心、情感客厅等）

## 实现细节

### 1. 数据库层（storage_sqlite.py）

#### 表结构变更
```sql
-- 为 users 表添加 nickname 字段
ALTER TABLE users ADD COLUMN nickname TEXT;
```

#### 模型更新
```python
class User:
    def __init__(self, phone, password, nickname=None, ...):
        self.nickname = nickname
        # ...
    
    def to_dict(self):
        return {
            'nickname': self.nickname,
            # ...
        }
```

#### 自动迁移
- 启动时自动检测并添加 `nickname` 字段
- 兼容旧数据（没有昵称的用户）

### 2. 后端 API（app.py）

#### 注册接口更新
```python
@app.route('/api/register', methods=['POST'])
def register():
    nickname = data.get('nickname', '').strip()
    
    # 验证昵称长度
    if nickname and len(nickname) > 20:
        return error('昵称最长20个字符')
    
    # 如果没有提供昵称，使用手机号后4位
    if not nickname:
        nickname = phone[-4:]
    
    user = User(phone=phone, password=password, nickname=nickname)
```

#### 新增昵称更新接口
```python
@app.route('/api/user/update_nickname', methods=['POST'])
def update_nickname():
    # 验证登录状态
    # 验证昵称长度
    # 更新用户昵称
```

#### 用户信息接口更新
```python
@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    return {
        'nickname': user.nickname or user.phone[-4:]
    }
```

### 3. 前端页面

#### 注册页面（login.html）
- 添加昵称输入框（非必填）
- 添加字符数限制提示
- 设置 `maxlength="20"` 属性

```html
<div class="input-group">
    <label>昵称（选填）</label>
    <input type="text" id="registerNickname" 
           placeholder="不填默认为手机号后4位" 
           maxlength="20">
    <small>最长20个字符</small>
</div>
```

#### 个人中心（profile.html）
- 显示当前昵称
- 添加"修改昵称"按钮
- 新增修改昵称模态框

```html
<div class="user-info">
    <p><strong>昵称：</strong><span id="userNickname">--</span></p>
</div>

<button onclick="showEditNicknameModal()">修改昵称</button>

<!-- 修改昵称模态框 -->
<div id="editNicknameModal" class="modal-overlay">
    <div class="modal-card">
        <h2>修改昵称</h2>
        <input type="text" id="newNickname" maxlength="20">
        <button onclick="updateNickname()">确认修改</button>
    </div>
</div>
```

#### 情感客厅（lounge.html）
- 使用昵称显示用户和伴侣名称
- 更新顶部情侣栏显示逻辑

```javascript
// 使用昵称，如果没有昵称则用手机号后4位
userNickname = userData.user.nickname || userPhone.slice(-4);
partnerNickname = partnerData.user.nickname || partnerPhone.slice(-4);
```

## 修改文件清单

### 后端
- `storage_sqlite.py`
  - 添加 `nickname` 字段到 User 模型
  - 更新 `__init__`、`to_dict`、`from_row`、`save` 方法
  - 添加数据库迁移逻辑

- `app.py`
  - 更新 `/api/register` 接口支持昵称
  - 新增 `/api/user/update_nickname` 接口
  - 更新 `/api/user/<int:user_id>` 接口返回昵称

### 前端
- `templates/login.html`
  - 添加昵称输入框
  - 更新注册函数传递昵称参数

- `templates/profile.html`
  - 添加昵称显示
  - 添加修改昵称按钮
  - 新增修改昵称模态框
  - 实现昵称更新逻辑

- `templates/lounge_polling.html` ⚠️ **重要**
  - 更新昵称获取逻辑（使用 `nickname` 字段）
  - 这是实际使用的客厅页面（轮询方案）

## 重要发现

### 文件混淆问题
在实现过程中发现项目有两个客厅页面：
1. **`templates/lounge.html`** - Socket.IO 版本（已弃用）
2. **`templates/lounge_polling.html`** - 轮询版本（实际使用）

最初错误地修改了 `lounge.html`，导致昵称功能不生效。

### 解决方案
1. 修复了正确的文件 `lounge_polling.html`
2. 删除了已弃用的 Socket.IO 相关文件
3. 清理了无用的路由

详见：`doc/cleanup-socketio-2026-01-18.md`

## 用户体验

### 注册流程
1. 用户填写手机号和密码（必填）
2. 可选填写昵称（最长20字符）
3. 如果不填昵称，系统自动使用手机号后4位
4. 注册成功后可在个人中心修改

### 修改昵称流程
1. 进入个人中心
2. 点击"修改昵称"按钮
3. 在弹窗中输入新昵称（最长20字符）
4. 点击"确认修改"
5. 显示成功提示，页面自动刷新显示新昵称

### 显示优先级
1. 优先显示用户设置的昵称
2. 如果没有昵称，显示手机号后4位
3. 适用于所有显示用户名称的场景

## 数据兼容性

### 旧用户处理
- 已注册的用户 `nickname` 字段为 `NULL`
- 前端显示时自动降级到手机号后4位
- 用户可随时在个人中心设置昵称

### 数据库迁移
- 启动时自动检测 `nickname` 字段是否存在
- 如果不存在，自动执行 `ALTER TABLE` 添加字段
- 不影响现有数据，向后兼容

## 测试建议

### 功能测试
1. 注册新用户，不填昵称，验证默认显示手机号后4位
2. 注册新用户，填写昵称，验证显示自定义昵称
3. 在个人中心修改昵称，验证更新成功
4. 测试昵称长度限制（超过20字符应提示错误）
5. 测试空昵称提交（应提示错误）

### 兼容性测试
1. 使用旧账号登录，验证显示手机号后4位
2. 旧账号设置昵称后，验证显示新昵称
3. 在情感客厅验证双方昵称正确显示

### 边界测试
1. 测试特殊字符昵称（emoji、中英文混合）
2. 测试恰好20字符的昵称
3. 测试空格开头/结尾的昵称（应自动 trim）

## 注意事项

1. **字符计数**：20个字符限制是按字符数计算，不是字节数（支持中文、emoji）
2. **前端验证**：使用 `maxlength="20"` 和 JavaScript 验证双重保护
3. **后端验证**：必须在后端再次验证长度，防止绕过前端限制
4. **空格处理**：使用 `.strip()` 自动去除首尾空格
5. **数据库迁移**：自动迁移逻辑确保平滑升级，无需手动操作

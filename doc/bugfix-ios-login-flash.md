# Bug 修复：iOS 登录闪退问题

**修复日期**：2026-01-18  
**问题类型**：Session Cookie 配置缺失  
**影响范围**：iOS 设备（Safari + 微信浏览器）

---

## 问题描述

### 症状
- **环境**：魔搭 Docker 部署（HTTPS）
- **现象**：苹果手机上登录后会"闪一下"被退出
  - iOS Safari 浏览器：❌ 闪退
  - iOS 微信浏览器：❌ 闪退
  - Android 微信/浏览器：✅ 正常

### 用户体验
1. 输入账号密码，点击登录
2. 页面跳转到首页
3. 立即又跳回登录页（"闪一下"）
4. 无法正常使用

---

## 问题分析

### 根本原因
**Session Cookie 缺少安全属性配置，被 iOS 系统拒绝存储**

### 技术细节

#### 原有代码
```python
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['JSON_AS_ASCII'] = False

CORS(app)
```

**问题**：
- ❌ 没有配置 `SESSION_COOKIE_SECURE`
- ❌ 没有配置 `SESSION_COOKIE_SAMESITE`
- ❌ 没有配置 `SESSION_COOKIE_HTTPONLY`
- ❌ 登录时没有设置 `session.permanent`

#### 登录流程分析
```
1. 用户登录 → POST /api/login
2. 后端设置 session['user_id'] = user.id
3. Flask 发送 Set-Cookie 响应头：
   Set-Cookie: session=xxx; Path=/; HttpOnly
   ❌ 缺少 Secure 和 SameSite 标志
   
4. iOS 检测到：HTTPS 页面 + Cookie 没有 Secure 标志
   → iOS 安全策略：拒绝存储此 Cookie ❌
   
5. 前端跳转到 /home
6. /home 调用 /api/user/info 检查登录状态
7. 请求中没有 Cookie（因为第4步被拒绝了）
8. 后端返回 401 未登录
9. 前端跳转回登录页 → "闪一下"
```

### 为什么 Android 正常，iOS 不行？

| 平台 | Cookie 安全策略 | 行为 |
|------|----------------|------|
| **iOS Safari** | 从 iOS 13 开始强制执行严格策略 | HTTPS 下必须有 Secure 标志 |
| **iOS 微信** | 继承 iOS Safari 策略 | 同上 |
| **Android** | 相对宽松 | 允许不完整的 Cookie 配置 |

### 魔搭部署环境
- 访问地址：`https://xxx.modelscope.cn`（HTTPS）
- Flask 内部：`http://0.0.0.0:7860`（HTTP）
- 反向代理：魔搭提供的 Nginx

**关键点**：前端访问是 HTTPS，所以 Cookie 必须有 `Secure` 标志

---

## 解决方案

### 修改内容

#### 1. 添加 Session Cookie 配置
**文件**：`app.py`  
**位置**：第 18-20 行后

```python
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['JSON_AS_ASCII'] = False  # 支持中文 JSON 响应

# Session Cookie 配置（修复 iOS 登录闪退问题）
app.config['SESSION_COOKIE_SECURE'] = True      # HTTPS 环境必须
app.config['SESSION_COOKIE_HTTPONLY'] = True    # 防止 JS 访问
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # iOS 必需，允许顶级导航
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 7天有效期

CORS(app)
```

**配置说明**：
- `SESSION_COOKIE_SECURE = True`
  - 告诉浏览器"这个 Cookie 只能在 HTTPS 下使用"
  - iOS 必需，否则拒绝存储
  
- `SESSION_COOKIE_HTTPONLY = True`
  - 防止 JavaScript 访问 Cookie
  - 提高安全性，防止 XSS 攻击
  
- `SESSION_COOKIE_SAMESITE = 'Lax'`
  - 允许顶级导航（页面跳转）携带 Cookie
  - `Strict`：完全禁止跨站（可能导致跳转失败）
  - `Lax`：允许安全的跨站请求（推荐）
  - `None`：允许所有跨站（需要 Secure=True）
  
- `PERMANENT_SESSION_LIFETIME = timedelta(days=7)`
  - Session 有效期 7 天
  - 默认是关闭浏览器就过期

#### 2. 修改登录函数
**文件**：`app.py`  
**函数**：`login()`

```python
@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    phone = data.get('phone')
    password = data.get('password')

    users = User.filter(phone=phone, password=password)
    user = users[0] if users else None
    if not user:
        return jsonify({'success': False, 'message': '手机号或密码错误'}), 401

    # 设置 session（永久会话，使用配置的过期时间）
    session.permanent = True  # 🔥 新增：使用 PERMANENT_SESSION_LIFETIME
    session['user_id'] = user.id

    return jsonify({
        'success': True,
        'message': '登录成功',
        'user': user.to_dict()
    })
```

**修改说明**：
- 添加 `session.permanent = True`
- 使 Session 使用 `PERMANENT_SESSION_LIFETIME` 的过期时间（7天）
- 而不是默认的"关闭浏览器就过期"

---

## 修复后的 Cookie 响应头

### 修复前
```
Set-Cookie: session=xxx; Path=/; HttpOnly
```
❌ 缺少 `Secure` 和 `SameSite`

### 修复后
```
Set-Cookie: session=xxx; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=604800
```
✅ 完整的安全属性

---

## 测试验证

### 测试清单
- [ ] iOS Safari 浏览器登录
- [ ] iOS 微信浏览器登录
- [ ] Android 微信浏览器登录（确保不影响）
- [ ] 登录后刷新页面，Session 保持
- [ ] 7天后 Session 自动过期

### 预期结果
1. iOS 设备登录成功后不再闪退
2. Session 正常保持 7 天
3. 所有平台功能正常

### 验证方法

#### 方法 1：查看 HTTP 响应头
使用 Safari 开发者工具（连接 Mac）：
1. 打开"网络"标签
2. 登录
3. 查看 `/api/login` 响应的 `Set-Cookie` 头
4. 确认包含 `Secure; HttpOnly; SameSite=Lax`

#### 方法 2：查看服务器日志
```bash
docker logs -f <container_id>
```

登录后应该看到：
```
[Login] 用户登录成功: user_id=xxx
```

访问 `/home` 时应该看到正常的请求，而不是 401 错误。

---

## 注意事项

### 1. 本地开发环境
如果在本地 HTTP 环境下开发（`http://localhost:7860`）：

```python
# 根据环境动态配置
import os

IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION  # 生产环境才启用
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

**当前配置**：直接设置为 `True`，因为主要在魔搭 HTTPS 环境部署。

### 2. 反向代理配置
如果修复后仍有问题，可能需要确保反向代理正确传递 HTTPS 信息：

```python
from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
```

**当前状态**：魔搭默认配置应该已处理，暂不需要。

### 3. Session 安全性
- ✅ `HttpOnly`：防止 XSS 攻击
- ✅ `Secure`：防止中间人攻击
- ✅ `SameSite=Lax`：防止 CSRF 攻击
- ⚠️ 密码仍为明文存储，建议后续使用 bcrypt 加密

---

## 相关资源

### iOS Cookie 策略文档
- [Safari Cookie 策略](https://webkit.org/blog/10218/full-third-party-cookie-blocking-and-more/)
- [iOS 13+ Cookie 变更](https://developer.apple.com/documentation/safari-release-notes)

### Flask Session 文档
- [Flask Session 配置](https://flask.palletsprojects.com/en/2.3.x/config/#SESSION_COOKIE_SECURE)
- [Flask Session 安全](https://flask.palletsprojects.com/en/2.3.x/security/)

### 相关 Bug 修复
- [bugfix-login-issue.md](./bugfix-login-issue.md) - 时间格式解析问题

---

## 总结

**问题**：iOS 登录闪退  
**原因**：Session Cookie 缺少安全属性，被 iOS 拒绝存储  
**解决**：添加 `Secure`、`HttpOnly`、`SameSite` 配置  
**影响**：修复 iOS 设备登录问题，不影响其他平台  
**状态**：✅ 已修复，待部署验证

---

**修复人员**：AI Assistant  
**测试状态**：⏳ 待部署后验证

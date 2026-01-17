---
title: 情感陪伴助手
emoji: 💝
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
---

# 💝 情感陪伴助手

一款面向亲密关系用户的 AI 辅助沟通工具，通过双聊天室模式实现个人情感梳理与双人共同沟通。

## ✨ 核心功能

### 1. 用户登录与绑定
- ✅ 极简登录（手机号 + 密码，无需验证）
- ✅ 伴侣绑定功能（生成绑定码，复制分享）
- ✅ 绑定仪式感（礼花动效）
- ✅ 解绑与冷静期（1个月冷静期，可撤销）

### 2. 个人教练聊天室
- ✅ 一对一 AI 情感辅导
- ✅ 上下文记忆对话
- ✅ 聊天记录导出功能
- ✅ 数据隔离（与情感客厅独立）

### 3. 情感客厅聊天室
- ✅ 双人实时聊天（WebSocket）
- ✅ AI 助手可召唤（@AI 或双击图标）
- ✅ AI 基于双方对话提供建议
- ✅ 永久会话保存

## 🚀 快速开始

### 方式一：使用 Supabase（推荐）

**优势**：支持高并发、自动备份、免费额度充足

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置 Supabase**
```bash
# 使用快速配置脚本
bash setup_supabase.sh

# 或手动配置（详见 doc/supabase-migration-guide.md）
```

3. **修改代码**

在 `app.py` 第 4 行，将：
```python
from storage import User, Relationship, CoachChat, LoungeChat
```
改为：
```python
from storage_supabase import User, Relationship, CoachChat, LoungeChat
```

4. **启动应用**
```bash
python app.py
```

5. **访问应用**

打开浏览器访问：`http://localhost:7860`

📖 **详细文档**：[Supabase 迁移指南](doc/supabase-migration-guide.md)

---

### 方式二：使用 JSON 文件存储（开发测试）

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写 AI API Key：
```
COZE_API_KEY=your-coze-api-key-here
COZE_BOT_ID_COACH=your-coach-bot-id
COZE_BOT_ID_LOUNGE=your-lounge-bot-id
```

3. **运行项目**
```bash
python app.py
```

4. **访问应用**

打开浏览器访问：`http://localhost:7860`

> ⚠️ **注意**：JSON 存储不支持并发，仅适合开发测试，生产环境请使用 Supabase

## 📱 使用流程

1. **注册/登录** → 输入手机号和密码（可随意填写）
2. **绑定伴侣** → 生成绑定码发送给伴侣，或输入伴侣的绑定码
3. **个人教练** → 与 AI 一对一倾诉，梳理个人情感
4. **情感客厅** → 与伴侣聊天，需要时召唤 AI 助手

## 🎨 技术栈

### 后端
- **Flask** - Web 框架
- **Flask-SocketIO** - WebSocket 实时通信
- **SQLAlchemy** - ORM 数据库
- **OpenAI API** - AI 对话能力（可替换为扣子 SDK）

### 前端
- **HTML/CSS/JavaScript** - 原生开发
- **Socket.IO** - 客户端 WebSocket

### 数据库
- **Supabase PostgreSQL** - 生产环境数据库（推荐）
- **JSON 文件存储** - 开发测试备选方案

## 📂 项目结构

```
emotion-helper/
├── app.py                      # 主应用文件
├── storage.py                  # JSON 文件存储（开发测试）
├── storage_supabase.py         # Supabase 存储（生产环境）
├── models.py                   # 数据库模型（未使用）
├── migrate_to_supabase.py      # 数据迁移脚本
├── supabase_schema.sql         # Supabase 表结构
├── setup_supabase.sh           # Supabase 快速配置脚本
├── requirements.txt            # Python 依赖
├── .env.example               # 环境变量示例
├── doc/
│   └── supabase-migration-guide.md  # Supabase 迁移指南
├── data/                      # JSON 数据目录（可选）
├── static/
│   ├── css/
│   │   └── common.css         # 公共样式
│   ├── js/
│   └── images/
└── templates/
    ├── login.html             # 登录页面
    ├── home.html              # 主页
    ├── profile.html           # 个人中心
    ├── coach.html             # 个人教练聊天室
    └── lounge.html            # 情感客厅聊天室
```

## 🔧 自定义 AI 模型

### 使用扣子 SDK

在 `app.py` 中替换 OpenAI 客户端为扣子 SDK：

```python
# 替换 OpenAI 导入
from coze import Coze  # 扣子 SDK

# 初始化扣子客户端
coze_client = Coze(api_key=os.getenv("COZE_API_KEY"))

# 在 coach_chat 和 handle_call_ai 函数中替换 AI 调用逻辑
```

## 🎯 功能特色

### 个人教练
- 专注于个人情感梳理
- AI 扮演心理教练角色
- 支持导出对话记录
- 数据完全私密

### 情感客厅
- 双人实时通信
- AI 不主动插话，仅在召唤时响应
- AI 基于双方对话提供建议
- 永久保存聊天记录

### 仪式感设计
- 绑定成功礼花特效
- 温馨界面设计
- 情感化交互体验

## 📝 注意事项

1. **API Key 配置**：请确保配置有效的 Coze API Key
2. **数据安全**：生产环境请使用 HTTPS 和更强的密码加密
3. **数据库选择**：
   - 开发测试：可使用 JSON 文件存储
   - 生产环境：强烈推荐使用 Supabase PostgreSQL
4. **并发支持**：JSON 存储不支持并发，多用户同时访问请使用 Supabase

## 🎓 路演展示建议

### 海报内容
- 产品名称：情感陪伴助手
- Slogan：用 AI 守护每一段亲密关系
- 核心功能图示（个人教练 + 情感客厅）
- 扫码体验二维码

### 产品介绍（5分钟）
1. **痛点分析**（1分钟）- 情侣沟通障碍问题
2. **产品演示**（2分钟）- 现场演示注册、绑定、聊天
3. **核心价值**（1分钟）- AI 辅助沟通的优势
4. **商业模式**（1分钟）- 会员订阅、企业服务

## 📄 开源协议

MIT License

## 🙏 致谢

感谢使用情感陪伴助手！希望 AI 能帮助更多人建立更好的亲密关系。

---

**Made with ❤️ by Claude Code**

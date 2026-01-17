---
title: 情感陪伴助手
emoji: 💝
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
---

# 💝 情感陪伴助手 Between Us

一款面向亲密关系用户的 AI 辅助沟通工具，通过双聊天室模式实现个人情感梳理与双人共同沟通。基于 Flask + Supabase 构建，支持实时通信和云端数据存储。

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

### 环境要求
- Python 3.8+
- Supabase 账号（免费）
- Coze API Key（用于 AI 对话）

### 部署步骤

1. **克隆项目**
```bash
git clone https://github.com/jueyunai/Between-Us.git
cd Between-Us
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必要配置：
```env
# Coze AI 配置
COZE_API_KEY=your-coze-api-key-here
COZE_BOT_ID_COACH=your-coach-bot-id
COZE_BOT_ID_LOUNGE=your-lounge-bot-id

# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Flask 配置
SECRET_KEY=your-secret-key-here
```

4. **初始化 Supabase 数据库**

在 Supabase 控制台的 SQL Editor 中执行 `supabase_schema.sql` 文件内容，创建所需表结构。

📖 **详细指南**：[Supabase 迁移指南](doc/supabase-migration-guide.md)

5. **启动应用**
```bash
python app.py
```

6. **访问应用**

打开浏览器访问：`http://localhost:7860`

### Docker 部署

```bash
docker build -t between-us .
docker run -p 7860:7860 --env-file .env between-us
```

## 📱 使用流程

1. **注册/登录** → 输入手机号和密码（可随意填写）
2. **绑定伴侣** → 生成绑定码发送给伴侣，或输入伴侣的绑定码
3. **个人教练** → 与 AI 一对一倾诉，梳理个人情感
4. **情感客厅** → 与伴侣聊天，需要时召唤 AI 助手

## 🎨 技术栈

### 后端
- **Flask** - Web 框架
- **Flask-SocketIO** - WebSocket 实时通信
- **Supabase** - 云端 PostgreSQL 数据库
- **Coze API** - AI 对话能力

### 前端
- **HTML/CSS/JavaScript** - 原生开发
- **Socket.IO** - 客户端 WebSocket 实时通信

### 部署
- **Docker** - 容器化部署
- **ModelScope** - 国内部署平台（可选）

## 📂 项目结构

```
Between-Us/
├── app.py                      # Flask 主应用
├── storage_supabase.py         # Supabase 数据存储层
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 配置
├── .env.example               # 环境变量模板
├── supabase_schema.sql        # 数据库表结构
├── doc/                       # 项目文档
│   ├── supabase-migration-guide.md      # Supabase 迁移指南
│   ├── decision-log.md                  # 技术决策记录
│   ├── cleanup-2026-01-18.md           # 代码清理记录
│   └── ...
├── static/
│   ├── css/
│   │   └── common.css         # 公共样式
│   ├── js/                    # JavaScript 文件
│   ├── images/                # 图片资源
│   └── fonts/                 # 字体文件
└── templates/
    ├── login.html             # 登录页面
    ├── home.html              # 主页
    ├── profile.html           # 个人中心
    ├── coach.html             # 个人教练聊天室
    ├── lounge.html            # 情感客厅聊天室
    └── lounge_debug.html      # 调试页面
```

## 🔧 配置说明

### Coze AI 配置

项目使用 Coze API 提供 AI 对话能力，需要配置两个 Bot：

1. **个人教练 Bot**：用于一对一情感辅导
2. **情感客厅 Bot**：用于双人沟通场景的建议

在 `.env` 文件中配置：
```env
COZE_API_KEY=your-api-key
COZE_BOT_ID_COACH=coach-bot-id
COZE_BOT_ID_LOUNGE=lounge-bot-id
```

### Supabase 配置

1. 在 [Supabase](https://supabase.com) 创建项目
2. 在 SQL Editor 中执行 `supabase_schema.sql` 创建表
3. 获取项目 URL 和 anon key 填入 `.env`

详细步骤参考：[Supabase 迁移指南](doc/supabase-migration-guide.md)

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

1. **环境变量**：请确保 `.env` 文件配置完整且不要提交到 Git
2. **数据安全**：生产环境请使用 HTTPS 和强密码策略
3. **Supabase 配额**：免费版有请求限制，注意监控使用量
4. **AI 调用成本**：Coze API 按调用次数计费，建议设置预算提醒

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

## 🔗 相关链接

- [GitHub 仓库](https://github.com/jueyunai/Between-Us)
- [Supabase 迁移指南](doc/supabase-migration-guide.md)
- [技术决策记录](doc/decision-log.md)

## 🙏 致谢

感谢使用情感陪伴助手！希望 AI 能帮助更多人建立更好的亲密关系。

---

**Made with ❤️ for Better Relationships**

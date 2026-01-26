# Between Us - AI 情感陪伴助手

面向亲密关系的 AI 辅助沟通工具，通过个人教练和情感客厅两种模式，帮助伴侣更好地理解彼此、化解矛盾。

## 项目架构

```
Between-Us/
├── frontend/          # Taro + React 前端（支持小程序/H5）
├── backend/           # Flask 后端 API
├── doc/               # 项目文档
│   ├── decision-log.md    # 技术决策记录
│   └── archive/           # 历史文档归档
└── .env.example       # 环境变量模板
```

## 技术栈

### 前端
- **Taro 4.1** - 跨端框架
- **React + TypeScript** - 开发语言
- **NutUI** - 组件库
- **Sass** - 样式预处理

### 后端
- **Flask** - Web 框架
- **Supabase** - PostgreSQL 数据库
- **Coze API** - AI 对话能力
- **JWT** - 用户认证

## 核心功能

### 个人教练
- 一对一 AI 情感辅导
- 上下文记忆对话
- 数据完全私密

### 情感客厅
- 伴侣实时聊天
- @AI 召唤助手
- AI 基于双方对话提供建议

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 配置环境变量
python app.py
```

### 前端

```bash
cd frontend
npm install

# 开发
npm run dev:h5      # H5 开发
npm run dev:weapp   # 微信小程序开发

# 构建
npm run build:h5
npm run build:weapp
```

## 环境配置

编辑 `backend/.env`：

```env
# Coze AI 配置
COZE_API_KEY=your-coze-api-key
COZE_BOT_ID_COACH=your-coach-bot-id
COZE_BOT_ID_LOUNGE=your-lounge-bot-id

# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# JWT 配置
JWT_SECRET=your-jwt-secret
SECRET_KEY=your-flask-secret
```

## 支持平台

- 微信小程序
- H5 网页
- 支付宝小程序
- 抖音小程序
- 更多...

## License

MIT

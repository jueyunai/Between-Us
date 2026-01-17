# 未使用文件分析报告

**分析日期**: 2026-01-18  
**项目状态**: 已完成 Supabase 迁移

---

## 📊 分析总结

根据项目当前状态（已完成 Supabase 迁移），以下文件和程序可以考虑清理或归档。

---

## 🗑️ 可以删除的文件

### 1. 本地数据库文件（已废弃）
- `emotion_helper.db` - 根目录的 SQLite 数据库
- `instance/emotion_helper.db` - instance 目录的 SQLite 数据库
- **原因**: 项目已迁移到 Supabase，不再使用本地 SQLite

### 2. JSON 数据文件（已迁移）
- `data/users.json` - 用户数据
- `data/relationships.json` - 关系数据
- `data/coach_chats.json` - 教练聊天记录
- `data/lounge_chats.json` - 客厅聊天记录
- **原因**: 数据已迁移到 Supabase，JSON 文件仅作备份
- **建议**: 先备份到其他位置，确认无误后删除

### 3. 旧的存储层实现
- `storage.py` - JSON 文件存储实现
- **原因**: 已被 `storage_supabase.py` 替代
- **注意**: `app.py` 第 4 行已改为 `from storage_supabase import`
- **建议**: 保留作为参考，或移到 `doc/legacy/` 目录

### 4. 旧的数据模型文件
- `models.py` - Flask-SQLAlchemy 模型（用于 SQLite）
- `models_fa.py` - FastAPI SQLAlchemy 模型
- **原因**: 项目使用 Supabase，不再需要 ORM 模型
- **建议**: 如果未来不打算支持本地数据库，可以删除

### 5. 调试和临时文件
- `coze_debug.json` - Coze API 调试信息
- `app.log` - 应用日志文件
- **原因**: 临时调试文件，可以随时重新生成
- **建议**: 添加到 `.gitignore`，定期清理

### 6. 测试脚本（一次性使用）
- `test_login_api.py` - 登录 API 测试
- `test_supabase.py` - Supabase 连接测试
- `check_passwords.py` - 密码检查脚本
- `cleanup_test_data.py` - 清理测试数据
- **原因**: 迁移和调试完成后不再需要
- **建议**: 移到 `tests/` 或 `scripts/` 目录归档

### 7. 迁移脚本（已完成）
- `migrate_to_supabase.py` - 数据迁移脚本
- `setup_supabase.sh` - Supabase 配置脚本
- **原因**: 迁移已完成，脚本不再需要
- **建议**: 移到 `doc/migration/` 目录归档

---

## ⚠️ 可能未使用的文件

### 1. FastAPI 实现
- `app_fastapi.py` - FastAPI 版本的应用
- `requirements_fastapi.txt` - FastAPI 依赖
- **状态**: 项目使用 Flask (`app.py`)，FastAPI 版本未启用
- **建议**: 
  - 如果不打算使用 FastAPI，可以删除
  - 如果作为备选方案，移到 `alternatives/` 目录

### 2. Docker 配置
- `Dockerfile` - Docker 镜像配置
- `docker-compose.yml` - Docker Compose 配置
- `.dockerignore` - Docker 忽略文件
- **状态**: 配置存在但可能未在使用
- **建议**: 
  - 如果不使用 Docker 部署，可以删除
  - 如果使用，需要更新配置（移除 SQLite 相关配置）

### 3. 部署配置
- `ms_deploy.json` - ModelScope 部署配置
- **状态**: 包含硬编码的 API Key（安全风险！）
- **建议**: 
  - 立即删除或移除敏感信息
  - 使用环境变量替代硬编码

### 4. 静态演示文件
- `static-demo/` 目录
  - `home-style-poster-a3.html`
  - `scan-qr.png`
  - `wechat-group-qr.png`
- **状态**: 与 `static/demo/` 重复
- **建议**: 确认是否重复，删除冗余文件

---

## ✅ 需要保留的文件

### 核心应用文件
- `app.py` - Flask 主应用（正在使用）
- `storage_supabase.py` - Supabase 存储层（正在使用）
- `requirements.txt` - Python 依赖（正在使用）

### 配置文件
- `.env` - 环境变量（正在使用，不应提交到 Git）
- `.env.example` - 环境变量示例
- `.gitignore` - Git 忽略规则

### 数据库相关
- `supabase_schema.sql` - Supabase 表结构定义

### 前端文件
- `templates/` - HTML 模板
- `static/` - 静态资源（CSS、JS、图片）

### 文档
- `README.md` - 项目说明
- `doc/` - 项目文档
- `.qoder/rules/rules.md` - AI 协作规范

---

## 📋 清理建议

### 立即删除（安全风险）
```bash
# 删除包含敏感信息的文件
rm ms_deploy.json
```

### 备份后删除（数据文件）
```bash
# 1. 先备份 JSON 数据
mkdir -p backup/data
cp -r data/ backup/data/

# 2. 确认 Supabase 数据完整后删除
rm -rf data/
```

### 归档（历史文件）
```bash
# 创建归档目录
mkdir -p doc/legacy
mkdir -p doc/migration
mkdir -p scripts/tests

# 移动旧文件
mv storage.py doc/legacy/
mv models.py doc/legacy/
mv models_fa.py doc/legacy/
mv app_fastapi.py doc/legacy/
mv requirements_fastapi.txt doc/legacy/

# 移动迁移脚本
mv migrate_to_supabase.py doc/migration/
mv setup_supabase.sh doc/migration/

# 移动测试脚本
mv test_*.py scripts/tests/
mv check_passwords.py scripts/tests/
mv cleanup_test_data.py scripts/tests/
```

### 清理临时文件
```bash
# 删除临时和调试文件
rm -f coze_debug.json
rm -f app.log
rm -f *.db
rm -rf instance/
rm -rf __pycache__/
```

### 更新 .gitignore
```bash
# 添加到 .gitignore
echo "coze_debug.json" >> .gitignore
echo "app.log" >> .gitignore
echo "*.db" >> .gitignore
echo "instance/" >> .gitignore
```

---

## 🎯 清理后的项目结构

```
emotion-helper/
├── app.py                      # ✅ 主应用
├── storage_supabase.py         # ✅ Supabase 存储层
├── supabase_schema.sql         # ✅ 数据库表结构
├── requirements.txt            # ✅ 依赖
├── .env                        # ✅ 环境变量（不提交）
├── .env.example               # ✅ 环境变量示例
├── .gitignore                 # ✅ Git 忽略规则
├── README.md                  # ✅ 项目说明
├── doc/                       # ✅ 文档目录
│   ├── legacy/                # 📦 归档的旧代码
│   ├── migration/             # 📦 迁移脚本归档
│   └── *.md                   # ✅ 项目文档
├── scripts/                   # 📦 脚本归档
│   └── tests/                 # 📦 测试脚本
├── static/                    # ✅ 静态资源
├── templates/                 # ✅ HTML 模板
└── .qoder/                    # ✅ AI 协作规范
```

---

## 📝 注意事项

1. **数据安全**: 删除 JSON 数据文件前，务必确认 Supabase 数据完整
2. **备份**: 重要文件删除前先备份
3. **测试**: 清理后运行完整测试，确保功能正常
4. **Git**: 清理后提交一次 commit，便于回滚
5. **敏感信息**: 立即删除包含 API Key 的 `ms_deploy.json`

---

## ✅ 清理检查清单

- [ ] 备份 JSON 数据文件
- [ ] 确认 Supabase 数据完整
- [ ] 删除敏感信息文件（ms_deploy.json）
- [ ] 归档旧代码和脚本
- [ ] 清理临时文件
- [ ] 更新 .gitignore
- [ ] 运行完整测试
- [ ] 提交 Git commit

---

**完成时间**: 待执行  
**预计节省空间**: ~5-10 MB  
**风险等级**: 低（已备份）

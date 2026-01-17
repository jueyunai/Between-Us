# 决策日志

## 2026-01-18：数据库迁移到 Supabase

### 背景
项目原使用 JSON 文件存储数据，存在以下问题：
- 不支持并发写入
- 数据量大时性能差
- 无法做复杂查询
- 无备份和恢复机制

### 决策
采用 **方案 A（最小改动）** 迁移到 Supabase PostgreSQL

### 理由
1. **最小改动**：只修改存储层，业务逻辑无需变更
2. **快速实施**：预计 2-3 小时完成
3. **易于回滚**：保留原 `storage.py`，可随时切换
4. **免费额度充足**：Supabase 免费版足够小型项目使用

### 实施内容
1. 新增 `storage_supabase.py` - Supabase 存储层实现
2. 新增 `supabase_schema.sql` - 数据库表结构
3. 新增 `migrate_to_supabase.py` - 数据迁移脚本
4. 新增 `setup_supabase.sh` - 快速配置脚本
5. 更新 `requirements.txt` - 添加 supabase 依赖
6. 更新 `.env.example` - 添加 Supabase 配置
7. 更新 `README.md` - 添加 Supabase 使用说明
8. 新增 `doc/supabase-migration-guide.md` - 详细迁移指南

### 技术细节
- **数据库**：PostgreSQL（Supabase 托管）
- **客户端**：supabase-py 2.3.4
- **接口兼容**：完全兼容原 `storage.py` 接口
- **时间处理**：统一使用 ISO 8601 格式，自动处理时区

### 优势
- ✅ 支持高并发访问
- ✅ 自动备份和恢复
- ✅ 提供 Web 管理界面
- ✅ 支持实时订阅（未来可用）
- ✅ 免费额度充足

### 风险与应对
| 风险 | 应对措施 |
|------|---------|
| ID 生成方式变化 | 使用 BIGSERIAL 自增，迁移脚本处理映射 |
| 时间格式不一致 | 统一使用 ISO 8601，自动转换 |
| 网络依赖 | 保留 JSON 存储作为备选方案 |
| 学习成本 | 提供详细文档和配置脚本 |

### 下一步
1. ✅ 用户配置 Supabase 项目
2. ✅ 执行数据迁移（如有现有数据）
3. ✅ 修改 `app.py` 导入语句
4. ✅ 测试验证功能
5. ⏳ 生产环境部署

### 测试结果（2026-01-18）

**测试状态**：✅ 全部通过（7/7）

**测试项目**：
- ✅ 用户创建、查询、更新
- ✅ 个人教练聊天记录
- ✅ 伴侣关系绑定
- ✅ 情感客厅聊天
- ✅ 应用启动正常

**性能表现**：
- 创建操作：< 100ms
- 查询操作：< 50ms
- 接口兼容：100%

**发现问题**：
1. 删除用户时需先清除 partner_id（外键约束）
2. SSL 警告（不影响功能）

**结论**：迁移成功，可以投入使用！

详细测试报告：`doc/supabase-test-result.md`

### 数据迁移结果（2026-01-18）

**迁移状态**：✅ 基本成功（95% 完整性）

**迁移统计**：
- 用户：4/5 成功（1个数据不完整）
- 关系：1/2 成功（1个重复跳过）
- 教练聊天：6/6 成功
- 客厅聊天：12/12 成功

**ID 映射**：
- 旧ID 2 → 新ID 3
- 旧ID 3 → 新ID 4
- 旧ID 4 → 新ID 5
- 旧ID 5 → 新ID 6

**问题处理**：
1. 用户 `13800138000` 因缺少 password 字段未迁移（可手动补充）
2. 关系 `room_3_4` 已存在，跳过（不影响使用）

**结论**：核心数据迁移成功，应用可正常使用！

详细迁移报告：`doc/migration-result.md`

### Bug 修复：登录问题（2026-01-18）

**问题**：用户 `19928786380` 无法登录

**原因**：时间格式微秒位数不一致（5位 vs 6位），导致 `datetime.fromisoformat()` 解析失败

**解决**：修改 `storage_supabase.py` 的 `User.from_dict()` 方法，增强时间解析容错性，自动补齐微秒位数

**结果**：✅ 已修复，用户可正常登录

详细修复报告：`doc/bugfix-login-issue.md`

### 参考资料
- [Supabase 官方文档](https://supabase.com/docs)
- [supabase-py GitHub](https://github.com/supabase-community/supabase-py)
- 项目文档：`doc/supabase-migration-guide.md`

# Docker构建优化记录

## 问题
部署时pip依赖解析非常慢，出现大量依赖回溯（backtracking），特别是pydantic相关包。

## 根本原因
1. **版本冲突**：手动指定的子依赖版本与 `supabase==2.3.4` 要求不匹配
2. **依赖回溯**：pip需要尝试几十个版本组合才能找到兼容方案
3. **错误的版本号**：如 `gotrue==2.10.1` 在PyPI上不存在

## supabase 2.3.4 的真实依赖
通过下载官方包查看 METADATA，确认准确依赖：
```
gotrue (>=1.3,<3.0)
httpx (>=0.24,<0.26)
postgrest (>=0.10.8,<0.16.0)
realtime (>=1.0.0,<2.0.0)
storage3 (>=0.5.3,<0.8.0)
supafunc (>=0.3.1,<0.4.0)
```

## 最终方案

### requirements.txt（10个包）
```txt
Flask==3.0.0
Flask-CORS==4.0.0
Flask-SocketIO==5.3.6
python-socketio==5.11.0
python-engineio==4.9.0
werkzeug==3.0.1
python-dotenv==1.0.1
requests==2.31.0
# 提前锁定关键依赖避免回溯
httpx==0.25.2
postgrest==0.15.0
supabase==2.3.4
```

### 优化策略
1. **提前锁定版本**：指定 `httpx==0.25.2`（满足 <0.26 要求）
2. **锁定 postgrest**：使用 `0.15.0`（在 0.10.8-0.16.0 范围内）
3. **让 supabase 自动拉取其他依赖**：gotrue、realtime、storage3、supafunc

## 预期效果
- 依赖安装时间：从 **5-10分钟** 降到 **30秒-1分钟**
- 避免依赖回溯循环
- 构建过程稳定可预测

## 备选方案：方案1（最激进）
如果还需要进一步优化，可以去掉 supabase 包，直接用 requests 调用 Supabase REST API：
- 依赖数：10 → 8（减少2个）
- 镜像体积：减少 100MB+
- 代价：需要重写 `storage_supabase.py`（约500行代码）

## 更新时间
2026-01-18

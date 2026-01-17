# 数据库调试手册 (Database Debugging Manual)

本手册用于辅助开发人员在调试过程中快速操作数据库，主要针对用户绑定、解绑及数据清理等常见场景。

## 1. 数据库基础信息
- **数据库路径**: `./instance/emotion_helper.db`
- **查看方式**:
  - **命令行**: `sqlite3 ./instance/emotion_helper.db`
  - **VSCode**: 推荐使用 `SQLite Viewer` 或 `SQLTools` 插件。

---

## 2. 常用调试场景 SQL

### 2.1 强制解除用户绑定关系
用于重置绑定流程测试。该操作会清除用户的伴侣状态并删除关系记录。

```sql
-- 1. 重置用户的伴侣 ID 和解绑冷静期状态
UPDATE users 
SET partner_id = NULL, 
    unbind_at = NULL 
WHERE id IN (2, 3);

-- 2. 删除关系表中的绑定记录
DELETE FROM relationships 
WHERE (user1_id = 2 AND user2_id = 3) OR (user1_id = 3 AND user2_id = 2);
```

### 2.2 查询用户及关系状态
快速确认当前数据库中的用户数据。

```sql
-- 查看所有用户的 ID、手机号、绑定码和伴侣 ID
SELECT id, phone, binding_code, partner_id, unbind_at FROM users;

-- 查看所有激活的伴侣关系
SELECT * FROM relationships WHERE is_active = 1;
```

### 2.3 清理聊天记录
重置对话上下文，测试 AI 的初始回复逻辑。

```sql
-- 清理指定用户的“个人教练”聊天记录
DELETE FROM coach_chats WHERE user_id = 2;

-- 清理指定房间的“情感客厅”聊天记录
DELETE FROM lounge_chats WHERE room_id = 'room_2_3';
```

### 2.4 手动修改数据
```sql
-- 手动指定用户的绑定码（方便输入测试）
UPDATE users SET binding_code = 'DEBUG1' WHERE id = 2;

-- 手动修改用户手机号
UPDATE users SET phone = '13800138000' WHERE id = 1;
```

---

## 3. 终端快捷命令 (One-Liners)

在 macOS/Linux 终端中可以直接运行以下命令完成操作：

- **快速查看用户列表**:
  ```bash
  sqlite3 ./instance/emotion_helper.db "SELECT id, phone, partner_id FROM users;"
  ```

- **一键解绑用户 2 和 3**:
  ```bash
  sqlite3 ./instance/emotion_helper.db "UPDATE users SET partner_id=NULL, unbind_at=NULL WHERE id IN (2,3); DELETE FROM relationships WHERE (user1_id=2 AND user2_id=3) OR (user1_id=3 AND user2_id=2);"
  ```

---

## 4. 注意事项
1. **Flask 路径**: 注意 Flask 默认将 SQLite 数据库放在 `instance/` 文件夹下。
2. **操作备份**: 在进行大规模 `DELETE` 操作前，建议先执行 `cp instance/emotion_helper.db instance/emotion_helper.db.bak` 进行备份。
3. **数据一致性**: `partner_id` 在 `users` 表中是双向指向的，手动修改时需确保 A 指向 B 的同时 B 也指向 A。

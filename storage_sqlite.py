# -*- coding: utf-8 -*-
"""
SQLite 存储层实现
保持与 storage_supabase.py 相同的接口，底层使用 SQLite
"""
import sqlite3
import os
from datetime import datetime
import secrets
from threading import Lock

# 数据库路径 - 使用持久化目录（生产环境）或当前目录（开发环境）
if os.path.exists('/mnt/workspace'):
    DB_PATH = os.path.join('/mnt/workspace', 'emotion_helper.db')
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'emotion_helper.db')

# 线程锁，确保数据库操作线程安全
db_lock = Lock()


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
    return conn


def init_db():
    """初始化数据库表"""
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nickname TEXT,
                binding_code TEXT,
                partner_id INTEGER,
                unbind_at TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 关系表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                room_id TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 个人教练聊天记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coach_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                reasoning_content TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 情感客厅聊天记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lounge_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                user_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                reasoning_content TEXT,
                sent_to_ai INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 数据库迁移：为已存在的 lounge_chats 表添加 sent_to_ai 字段
        try:
            cursor.execute("SELECT sent_to_ai FROM lounge_chats LIMIT 1")
        except sqlite3.OperationalError:
            # 字段不存在，需要添加
            print("[SQLite] 迁移：为 lounge_chats 表添加 sent_to_ai 字段", flush=True)
            cursor.execute("ALTER TABLE lounge_chats ADD COLUMN sent_to_ai INTEGER DEFAULT 0")
            print("[SQLite] 迁移完成", flush=True)
        
        # 数据库迁移：为已存在的 lounge_chats 表添加 reasoning_content 字段
        try:
            cursor.execute("SELECT reasoning_content FROM lounge_chats LIMIT 1")
        except sqlite3.OperationalError:
            # 字段不存在，需要添加
            print("[SQLite] 迁移：为 lounge_chats 表添加 reasoning_content 字段", flush=True)
            cursor.execute("ALTER TABLE lounge_chats ADD COLUMN reasoning_content TEXT")
            print("[SQLite] 迁移完成", flush=True)
        
        # 数据库迁移：为已存在的 users 表添加 nickname 字段
        try:
            cursor.execute("SELECT nickname FROM users LIMIT 1")
        except sqlite3.OperationalError:
            # 字段不存在，需要添加
            print("[SQLite] 迁移：为 users 表添加 nickname 字段", flush=True)
            cursor.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
            print("[SQLite] 迁移完成", flush=True)
        
        conn.commit()
        conn.close()
        print(f"[SQLite] 数据库初始化完成: {DB_PATH}", flush=True)


# 启动时初始化数据库
init_db()


class User:
    """用户模型"""
    
    def __init__(self, phone, password, nickname=None, binding_code=None, partner_id=None, unbind_at=None, created_at=None, id=None):
        self.id = id
        self.phone = phone
        self.password = password
        self.nickname = nickname
        self.binding_code = binding_code
        self.partner_id = partner_id
        self.unbind_at = unbind_at
        self.created_at = created_at or datetime.now()
    
    def generate_binding_code(self):
        """生成6位绑定码"""
        self.binding_code = secrets.token_hex(3).upper()
        return self.binding_code
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'nickname': self.nickname,
            'binding_code': self.binding_code,
            'partner_id': self.partner_id,
            'has_partner': self.partner_id is not None,
            'unbind_at': self.unbind_at.isoformat() if isinstance(self.unbind_at, datetime) else self.unbind_at,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @staticmethod
    def from_row(row):
        """从数据库行创建用户对象"""
        if not row:
            return None
        
        created_at = row['created_at']
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None
        
        unbind_at = row['unbind_at']
        if unbind_at and isinstance(unbind_at, str):
            try:
                unbind_at = datetime.fromisoformat(unbind_at)
            except ValueError:
                unbind_at = None
        
        # 兼容旧数据：如果没有 nickname 字段，设为 None
        try:
            nickname = row['nickname']
        except (KeyError, IndexError):
            nickname = None
        
        return User(
            id=row['id'],
            phone=row['phone'],
            password=row['password'],
            nickname=nickname,
            binding_code=row['binding_code'],
            partner_id=row['partner_id'],
            unbind_at=unbind_at,
            created_at=created_at
        )
    
    def save(self):
        """保存用户信息"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            unbind_at_str = self.unbind_at.isoformat() if isinstance(self.unbind_at, datetime) else self.unbind_at
            created_at_str = self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
            
            try:
                if self.id:
                    # 更新现有用户
                    cursor.execute('''
                        UPDATE users 
                        SET phone=?, password=?, nickname=?, binding_code=?, partner_id=?, unbind_at=?
                        WHERE id=?
                    ''', (self.phone, self.password, self.nickname, self.binding_code, self.partner_id, unbind_at_str, self.id))
                else:
                    # 创建新用户
                    cursor.execute('''
                        INSERT INTO users (phone, password, nickname, binding_code, partner_id, unbind_at, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (self.phone, self.password, self.nickname, self.binding_code, self.partner_id, unbind_at_str, created_at_str))
                    self.id = cursor.lastrowid
                
                conn.commit()
                return self
            except Exception as e:
                print(f"[SQLite Error] 保存用户失败: {e}", flush=True)
                raise
            finally:
                conn.close()
    
    @staticmethod
    def get(id):
        """根据ID获取用户"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id=?', (id,))
            row = cursor.fetchone()
            conn.close()
            return User.from_row(row) if row else None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤用户"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            values = []
            for key, value in kwargs.items():
                conditions.append(f"{key}=?")
                values.append(value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM users WHERE {where_clause}"
            
            cursor.execute(query, values)
            rows = cursor.fetchall()
            conn.close()
            
            return [User.from_row(row) for row in rows]
    
    @staticmethod
    def all():
        """获取所有用户"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            rows = cursor.fetchall()
            conn.close()
            return [User.from_row(row) for row in rows]


class Relationship:
    """关系绑定模型"""
    
    def __init__(self, user1_id, user2_id, room_id, is_active=True, created_at=None, id=None):
        self.id = id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.room_id = room_id
        self.is_active = is_active
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'room_id': self.room_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'is_active': self.is_active
        }
    
    @staticmethod
    def from_row(row):
        """从数据库行创建关系对象"""
        if not row:
            return None
        
        created_at = row['created_at']
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None
        
        return Relationship(
            id=row['id'],
            user1_id=row['user1_id'],
            user2_id=row['user2_id'],
            room_id=row['room_id'],
            is_active=bool(row['is_active']),
            created_at=created_at
        )
    
    def save(self):
        """保存关系信息"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            created_at_str = self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
            
            try:
                if self.id:
                    # 更新现有关系
                    cursor.execute('''
                        UPDATE relationships 
                        SET user1_id=?, user2_id=?, room_id=?, is_active=?
                        WHERE id=?
                    ''', (self.user1_id, self.user2_id, self.room_id, int(self.is_active), self.id))
                else:
                    # 创建新关系
                    cursor.execute('''
                        INSERT INTO relationships (user1_id, user2_id, room_id, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (self.user1_id, self.user2_id, self.room_id, int(self.is_active), created_at_str))
                    self.id = cursor.lastrowid
                
                conn.commit()
                return self
            except Exception as e:
                print(f"[SQLite Error] 保存关系失败: {e}", flush=True)
                raise
            finally:
                conn.close()
    
    @staticmethod
    def get(id):
        """根据ID获取关系"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM relationships WHERE id=?', (id,))
            row = cursor.fetchone()
            conn.close()
            return Relationship.from_row(row) if row else None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤关系"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            conditions = []
            values = []
            for key, value in kwargs.items():
                conditions.append(f"{key}=?")
                values.append(value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM relationships WHERE {where_clause}"
            
            cursor.execute(query, values)
            rows = cursor.fetchall()
            conn.close()
            
            return [Relationship.from_row(row) for row in rows]
    
    @staticmethod
    def all():
        """获取所有关系"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM relationships')
            rows = cursor.fetchall()
            conn.close()
            return [Relationship.from_row(row) for row in rows]


class CoachChat:
    """个人教练聊天记录模型"""
    
    def __init__(self, user_id, role, content, reasoning_content=None, created_at=None, id=None):
        self.id = id
        self.user_id = user_id
        self.role = role
        self.content = content
        self.reasoning_content = reasoning_content
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'reasoning_content': self.reasoning_content,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @staticmethod
    def from_row(row):
        """从数据库行创建聊天记录对象"""
        if not row:
            return None
        
        created_at = row['created_at']
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None
        
        return CoachChat(
            id=row['id'],
            user_id=row['user_id'],
            role=row['role'],
            content=row['content'],
            reasoning_content=row['reasoning_content'],
            created_at=created_at
        )
    
    def save(self):
        """保存聊天记录"""
        import time
        save_start = time.time()
        
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            created_at_str = self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
            
            try:
                if self.id:
                    # 更新现有记录
                    print(f"[DB] 更新教练聊天记录 ID={self.id}, role={self.role}, content_len={len(self.content)}", flush=True)
                    cursor.execute('''
                        UPDATE coach_chats 
                        SET user_id=?, role=?, content=?, reasoning_content=?
                        WHERE id=?
                    ''', (self.user_id, self.role, self.content, self.reasoning_content, self.id))
                else:
                    # 创建新记录
                    print(f"[DB] 创建教练聊天记录 user_id={self.user_id}, role={self.role}, content_len={len(self.content)}", flush=True)
                    cursor.execute('''
                        INSERT INTO coach_chats (user_id, role, content, reasoning_content, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (self.user_id, self.role, self.content, self.reasoning_content, created_at_str))
                    self.id = cursor.lastrowid
                    print(f"[DB] ✓ 教练聊天记录已创建，ID={self.id}", flush=True)
                
                conn.commit()
                elapsed = time.time() - save_start
                print(f"[DB] ✓ 教练聊天记录保存成功，耗时: {elapsed:.3f}s", flush=True)
                return self
            except Exception as e:
                print(f"[DB] ❌ 保存教练聊天记录失败: {e}", flush=True)
                import traceback
                print(f"[DB] 异常堆栈:\n{traceback.format_exc()}", flush=True)
                raise
            finally:
                conn.close()
    
    @staticmethod
    def get(id):
        """根据ID获取聊天记录"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM coach_chats WHERE id=?', (id,))
            row = cursor.fetchone()
            conn.close()
            return CoachChat.from_row(row) if row else None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤聊天记录"""
        import time
        query_start = time.time()
        
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            conditions = []
            values = []
            for key, value in kwargs.items():
                conditions.append(f"{key}=?")
                values.append(value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM coach_chats WHERE {where_clause} ORDER BY created_at ASC"
            
            print(f"[DB] 查询教练聊天记录: {kwargs}", flush=True)
            cursor.execute(query, values)
            rows = cursor.fetchall()
            conn.close()
            
            result = [CoachChat.from_row(row) for row in rows]
            elapsed = time.time() - query_start
            print(f"[DB] ✓ 查询完成，返回 {len(result)} 条记录，耗时: {elapsed:.3f}s", flush=True)
            
            return result
    
    @staticmethod
    def all():
        """获取所有聊天记录"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM coach_chats ORDER BY created_at ASC')
            rows = cursor.fetchall()
            conn.close()
            return [CoachChat.from_row(row) for row in rows]


class LoungeChat:
    """情感客厅聊天记录模型"""
    
    def __init__(self, room_id, content, role, user_id=None, reasoning_content=None, sent_to_ai=False, created_at=None, id=None):
        self.id = id
        self.room_id = room_id
        self.user_id = user_id
        self.role = role
        self.content = content
        self.reasoning_content = reasoning_content
        self.sent_to_ai = sent_to_ai
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'reasoning_content': self.reasoning_content,
            'sent_to_ai': self.sent_to_ai,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @staticmethod
    def from_row(row):
        """从数据库行创建聊天记录对象"""
        if not row:
            return None
        
        created_at = row['created_at']
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None
        
        # 兼容旧数据：如果没有 reasoning_content 字段，设为 None
        try:
            reasoning_content = row['reasoning_content']
        except (KeyError, IndexError):
            reasoning_content = None
        
        return LoungeChat(
            id=row['id'],
            room_id=row['room_id'],
            user_id=row['user_id'],
            role=row['role'],
            content=row['content'],
            reasoning_content=reasoning_content,
            sent_to_ai=bool(row['sent_to_ai']),
            created_at=created_at
        )
    
    def save(self):
        """保存聊天记录"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            created_at_str = self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
            
            try:
                if self.id:
                    # 更新现有记录
                    cursor.execute('''
                        UPDATE lounge_chats 
                        SET room_id=?, user_id=?, role=?, content=?, reasoning_content=?, sent_to_ai=?
                        WHERE id=?
                    ''', (self.room_id, self.user_id, self.role, self.content, self.reasoning_content, int(self.sent_to_ai), self.id))
                else:
                    # 创建新记录
                    cursor.execute('''
                        INSERT INTO lounge_chats (room_id, user_id, role, content, reasoning_content, sent_to_ai, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (self.room_id, self.user_id, self.role, self.content, self.reasoning_content, int(self.sent_to_ai), created_at_str))
                    self.id = cursor.lastrowid
                
                conn.commit()
                return self
            except Exception as e:
                print(f"[SQLite Error] 保存客厅聊天记录失败: {e}", flush=True)
                raise
            finally:
                conn.close()
    
    @staticmethod
    def get(id):
        """根据ID获取聊天记录"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM lounge_chats WHERE id=?', (id,))
            row = cursor.fetchone()
            conn.close()
            return LoungeChat.from_row(row) if row else None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤聊天记录"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            conditions = []
            values = []
            for key, value in kwargs.items():
                conditions.append(f"{key}=?")
                values.append(value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM lounge_chats WHERE {where_clause} ORDER BY created_at ASC"
            
            cursor.execute(query, values)
            rows = cursor.fetchall()
            conn.close()
            
            return [LoungeChat.from_row(row) for row in rows]
    
    @staticmethod
    def all():
        """获取所有聊天记录"""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM lounge_chats ORDER BY created_at ASC')
            rows = cursor.fetchall()
            conn.close()
            return [LoungeChat.from_row(row) for row in rows]

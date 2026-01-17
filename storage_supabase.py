# -*- coding: utf-8 -*-
"""
Supabase 存储层实现
保持与原 storage.py 相同的接口，底层使用 Supabase PostgreSQL
"""
import os
from datetime import datetime
import secrets
from supabase import create_client, Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化 Supabase 客户端
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("请在 .env 文件中配置 SUPABASE_URL 和 SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class User:
    """用户模型"""
    
    def __init__(self, phone, password, binding_code=None, partner_id=None, unbind_at=None, created_at=None, id=None):
        self.id = id
        self.phone = phone
        self.password = password
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
            'binding_code': self.binding_code,
            'partner_id': self.partner_id,
            'has_partner': self.partner_id is not None,
            'unbind_at': self.unbind_at.isoformat() if isinstance(self.unbind_at, datetime) else self.unbind_at,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建用户对象"""
        if not data:
            return None
        
        # 处理时间字段 - 兼容不同格式
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError as e:
                # 处理微秒位数不足的情况
                print(f"[Debug] 时间格式解析失败: {created_at}, 错误: {e}")
                # 尝试手动补齐微秒位数
                if '+' in created_at:
                    time_part, tz_part = created_at.rsplit('+', 1)
                    if '.' in time_part:
                        base, microseconds = time_part.rsplit('.', 1)
                        # 补齐到6位
                        microseconds = microseconds.ljust(6, '0')
                        created_at = f"{base}.{microseconds}+{tz_part}"
                        created_at = datetime.fromisoformat(created_at)
                    else:
                        created_at = datetime.fromisoformat(created_at)
                else:
                    created_at = None
        
        unbind_at = data.get('unbind_at')
        if unbind_at and isinstance(unbind_at, str):
            try:
                unbind_at = datetime.fromisoformat(unbind_at.replace('Z', '+00:00'))
            except ValueError:
                unbind_at = None
        
        return User(
            id=data.get('id'),
            phone=data.get('phone'),
            password=data.get('password'),
            binding_code=data.get('binding_code'),
            partner_id=data.get('partner_id'),
            unbind_at=unbind_at,
            created_at=created_at
        )
    
    def save(self):
        """保存用户信息"""
        user_data = {
            'phone': self.phone,
            'password': self.password,
            'binding_code': self.binding_code,
            'partner_id': self.partner_id,
            'unbind_at': self.unbind_at.isoformat() if isinstance(self.unbind_at, datetime) else self.unbind_at,
        }
        
        # 移除 None 值
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        try:
            if self.id:
                # 更新现有用户
                response = supabase.table('users').update(user_data).eq('id', self.id).execute()
                if response.data:
                    return self
            else:
                # 创建新用户
                response = supabase.table('users').insert(user_data).execute()
                if response.data and len(response.data) > 0:
                    self.id = response.data[0]['id']
                    self.created_at = datetime.fromisoformat(response.data[0]['created_at'].replace('Z', '+00:00'))
            return self
        except Exception as e:
            print(f"[Supabase Error] 保存用户失败: {e}")
            raise
    
    @staticmethod
    def get(id):
        """根据ID获取用户"""
        try:
            response = supabase.table('users').select('*').eq('id', id).execute()
            if response.data and len(response.data) > 0:
                return User.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"[Supabase Error] 获取用户失败: {e}")
            return None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤用户"""
        try:
            query = supabase.table('users').select('*')
            for key, value in kwargs.items():
                query = query.eq(key, value)
            response = query.execute()
            
            # 调试日志
            print(f"[Debug] User.filter 查询条件: {kwargs}")
            print(f"[Debug] 查询结果数量: {len(response.data)}")
            if response.data:
                for user in response.data:
                    print(f"[Debug] 找到用户: phone={user.get('phone')}, password={user.get('password')}")
            
            return [User.from_dict(data) for data in response.data]
        except Exception as e:
            print(f"[Supabase Error] 过滤用户失败: {e}")
            return []
    
    @staticmethod
    def all():
        """获取所有用户"""
        try:
            response = supabase.table('users').select('*').execute()
            return [User.from_dict(data) for data in response.data]
        except Exception as e:
            print(f"[Supabase Error] 获取所有用户失败: {e}")
            return []


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
    def from_dict(data):
        """从字典创建关系对象"""
        if not data:
            return None
        
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError as e:
                # 处理微秒位数不足的情况
                print(f"[Debug] Relationship 时间格式解析失败: {created_at}, 错误: {e}")
                if '+' in created_at:
                    time_part, tz_part = created_at.rsplit('+', 1)
                    if '.' in time_part:
                        base, microseconds = time_part.rsplit('.', 1)
                        # 补齐到6位
                        microseconds = microseconds.ljust(6, '0')
                        created_at = f"{base}.{microseconds}+{tz_part}"
                        created_at = datetime.fromisoformat(created_at)
                    else:
                        created_at = datetime.fromisoformat(created_at)
                else:
                    created_at = None
        
        return Relationship(
            id=data.get('id'),
            user1_id=data.get('user1_id'),
            user2_id=data.get('user2_id'),
            room_id=data.get('room_id'),
            is_active=data.get('is_active', True),
            created_at=created_at
        )
    
    def save(self):
        """保存关系信息"""
        relationship_data = {
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'room_id': self.room_id,
            'is_active': self.is_active
        }
        
        try:
            if self.id:
                # 更新现有关系
                response = supabase.table('relationships').update(relationship_data).eq('id', self.id).execute()
            else:
                # 创建新关系
                response = supabase.table('relationships').insert(relationship_data).execute()
                if response.data and len(response.data) > 0:
                    self.id = response.data[0]['id']
                    self.created_at = datetime.fromisoformat(response.data[0]['created_at'].replace('Z', '+00:00'))
            return self
        except Exception as e:
            print(f"[Supabase Error] 保存关系失败: {e}")
            raise
    
    @staticmethod
    def get(id):
        """根据ID获取关系"""
        try:
            response = supabase.table('relationships').select('*').eq('id', id).execute()
            if response.data and len(response.data) > 0:
                return Relationship.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"[Supabase Error] 获取关系失败: {e}")
            return None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤关系"""
        try:
            query = supabase.table('relationships').select('*')
            for key, value in kwargs.items():
                query = query.eq(key, value)
            response = query.execute()
            return [Relationship.from_dict(data) for data in response.data]
        except Exception as e:
            print(f"[Supabase Error] 过滤关系失败: {e}")
            return []
    
    @staticmethod
    def all():
        """获取所有关系"""
        try:
            response = supabase.table('relationships').select('*').execute()
            return [Relationship.from_dict(data) for data in response.data]
        except Exception as e:
            print(f"[Supabase Error] 获取所有关系失败: {e}")
            return []


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
    def from_dict(data):
        """从字典创建聊天记录对象"""
        if not data:
            return None
        
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError as e:
                # 处理微秒位数不足的情况
                print(f"[Debug] CoachChat 时间格式解析失败: {created_at}, 错误: {e}")
                if '+' in created_at:
                    time_part, tz_part = created_at.rsplit('+', 1)
                    if '.' in time_part:
                        base, microseconds = time_part.rsplit('.', 1)
                        # 补齐到6位
                        microseconds = microseconds.ljust(6, '0')
                        created_at = f"{base}.{microseconds}+{tz_part}"
                        created_at = datetime.fromisoformat(created_at)
                    else:
                        created_at = datetime.fromisoformat(created_at)
                else:
                    created_at = None
        
        return CoachChat(
            id=data.get('id'),
            user_id=data.get('user_id'),
            role=data.get('role'),
            content=data.get('content'),
            reasoning_content=data.get('reasoning_content'),
            created_at=created_at
        )
    
    def save(self):
        """保存聊天记录"""
        chat_data = {
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'reasoning_content': self.reasoning_content
        }
        
        # 移除 None 值
        chat_data = {k: v for k, v in chat_data.items() if v is not None}
        
        try:
            if self.id:
                # 更新现有记录
                response = supabase.table('coach_chats').update(chat_data).eq('id', self.id).execute()
            else:
                # 创建新记录
                response = supabase.table('coach_chats').insert(chat_data).execute()
                if response.data and len(response.data) > 0:
                    self.id = response.data[0]['id']
                    self.created_at = datetime.fromisoformat(response.data[0]['created_at'].replace('Z', '+00:00'))
            return self
        except Exception as e:
            print(f"[Supabase Error] 保存教练聊天记录失败: {e}")
            raise
    
    @staticmethod
    def get(id):
        """根据ID获取聊天记录"""
        try:
            response = supabase.table('coach_chats').select('*').eq('id', id).execute()
            if response.data and len(response.data) > 0:
                return CoachChat.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"[Supabase Error] 获取教练聊天记录失败: {e}")
            return None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤聊天记录"""
        try:
            query = supabase.table('coach_chats').select('*')
            for key, value in kwargs.items():
                query = query.eq(key, value)
            # 按创建时间排序
            response = query.order('created_at', desc=False).execute()
            return [CoachChat.from_dict(data) for data in response.data]
        except Exception as e:
            print(f"[Supabase Error] 过滤教练聊天记录失败: {e}")
            return []
    
    @staticmethod
    def all():
        """获取所有聊天记录"""
        try:
            response = supabase.table('coach_chats').select('*').order('created_at', desc=False).execute()
            return [CoachChat.from_dict(data) for data in response.data]
        except Exception as e:
            print(f"[Supabase Error] 获取所有教练聊天记录失败: {e}")
            return []


class LoungeChat:
    """情感客厅聊天记录模型"""
    
    def __init__(self, room_id, content, role, user_id=None, created_at=None, id=None):
        self.id = id
        self.room_id = room_id
        self.user_id = user_id
        self.role = role
        self.content = content
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建聊天记录对象"""
        if not data:
            return None
        
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError as e:
                # 处理微秒位数不足的情况
                print(f"[Debug] LoungeChat 时间格式解析失败: {created_at}, 错误: {e}")
                if '+' in created_at:
                    time_part, tz_part = created_at.rsplit('+', 1)
                    if '.' in time_part:
                        base, microseconds = time_part.rsplit('.', 1)
                        # 补齐到6位
                        microseconds = microseconds.ljust(6, '0')
                        created_at = f"{base}.{microseconds}+{tz_part}"
                        created_at = datetime.fromisoformat(created_at)
                    else:
                        created_at = datetime.fromisoformat(created_at)
                else:
                    created_at = None
        
        return LoungeChat(
            id=data.get('id'),
            room_id=data.get('room_id'),
            user_id=data.get('user_id'),
            role=data.get('role'),
            content=data.get('content'),
            created_at=created_at
        )
    
    def save(self):
        """保存聊天记录"""
        chat_data = {
            'room_id': self.room_id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content
        }
        
        try:
            if self.id:
                # 更新现有记录
                response = supabase.table('lounge_chats').update(chat_data).eq('id', self.id).execute()
            else:
                # 创建新记录
                response = supabase.table('lounge_chats').insert(chat_data).execute()
                if response.data and len(response.data) > 0:
                    self.id = response.data[0]['id']
                    self.created_at = datetime.fromisoformat(response.data[0]['created_at'].replace('Z', '+00:00'))
            return self
        except Exception as e:
            print(f"[Supabase Error] 保存客厅聊天记录失败: {e}")
            raise
    
    @staticmethod
    def get(id):
        """根据ID获取聊天记录"""
        try:
            response = supabase.table('lounge_chats').select('*').eq('id', id).execute()
            if response.data and len(response.data) > 0:
                return LoungeChat.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"[Supabase Error] 获取客厅聊天记录失败: {e}")
            return None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤聊天记录"""
        try:
            query = supabase.table('lounge_chats').select('*')
            for key, value in kwargs.items():
                query = query.eq(key, value)
            # 按创建时间排序
            response = query.order('created_at', desc=False).execute()
            return [LoungeChat.from_dict(data) for data in response.data]
        except Exception as e:
            print(f"[Supabase Error] 过滤客厅聊天记录失败: {e}")
            return []
    
    @staticmethod
    def all():
        """获取所有聊天记录"""
        try:
            response = supabase.table('lounge_chats').select('*').order('created_at', desc=False).execute()
            return [LoungeChat.from_dict(data) for data in response.data]
        except Exception as e:
            print(f"[Supabase Error] 获取所有客厅聊天记录失败: {e}")
            return []

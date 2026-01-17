# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
import secrets

# 数据存储目录
DATA_DIR = 'data'

# 确保数据目录存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class JSONStorage:
    """JSON文件存储类"""
    
    def __init__(self, filename):
        self.filename = os.path.join(DATA_DIR, filename)
        self.data = self._load()
    
    def _load(self):
        """加载JSON文件数据"""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"next_id": 1, "data": []}
    
    def _save(self):
        """保存数据到JSON文件"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2, default=self._json_default)
    
    def _json_default(self, obj):
        """JSON序列化处理"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def get_next_id(self):
        """获取下一个ID"""
        id = self.data["next_id"]
        self.data["next_id"] += 1
        return id
    
    def create(self, item):
        """创建新数据项"""
        item["id"] = self.get_next_id()
        if "created_at" not in item and hasattr(item, "created_at"):
            item["created_at"] = datetime.now()
        self.data["data"].append(item)
        self._save()
        return item
    
    def get(self, id):
        """根据ID获取数据项"""
        for item in self.data["data"]:
            if item["id"] == id:
                return item
        return None
    
    def update(self, id, updates):
        """更新数据项"""
        for i, item in enumerate(self.data["data"]):
            if item["id"] == id:
                self.data["data"][i].update(updates)
                self._save()
                return self.data["data"][i]
        return None
    
    def delete(self, id):
        """删除数据项"""
        for i, item in enumerate(self.data["data"]):
            if item["id"] == id:
                del self.data["data"][i]
                self._save()
                return True
        return False
    
    def filter(self, **kwargs):
        """根据条件过滤数据项"""
        results = []
        for item in self.data["data"]:
            match = True
            for key, value in kwargs.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                results.append(item)
        return results
    
    def all(self):
        """获取所有数据项"""
        return self.data["data"]
    
    def order_by(self, field, reverse=False):
        """根据字段排序"""
        return sorted(self.data["data"], key=lambda x: x.get(field, 0), reverse=reverse)
    
    def limit(self, n):
        """限制返回数据项数量"""
        return self.data["data"][:n]

# 初始化存储实例
users_store = JSONStorage('users.json')
relationships_store = JSONStorage('relationships.json')
coach_chats_store = JSONStorage('coach_chats.json')
lounge_chats_store = JSONStorage('lounge_chats.json')

# 数据模型类
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
            'unbind_at': self.unbind_at,
            'created_at': self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建用户对象"""
        # 创建数据副本，避免修改原数据
        data_copy = data.copy()
        # 移除has_partner字段，因为它是计算属性，不在__init__方法中定义
        data_copy.pop('has_partner', None)
        
        if 'created_at' in data_copy and isinstance(data_copy['created_at'], str):
            data_copy['created_at'] = datetime.fromisoformat(data_copy['created_at'])
        if 'unbind_at' in data_copy and isinstance(data_copy['unbind_at'], str):
            data_copy['unbind_at'] = datetime.fromisoformat(data_copy['unbind_at'])
        return User(**data_copy)
    
    def save(self):
        """保存用户信息"""
        user_data = {
            'phone': self.phone,
            'password': self.password,  # 保存密码
            'binding_code': self.binding_code,
            'partner_id': self.partner_id,
            'unbind_at': self.unbind_at,
            'created_at': self.created_at
        }
        if self.id:
            # 更新数据时，先获取当前数据，保留密码
            current_data = users_store.get(self.id)
            if current_data and 'password' in current_data:
                user_data['password'] = current_data['password']
            users_store.update(self.id, user_data)
        else:
            data = users_store.create(user_data)
            self.id = data['id']
        return self
    
    @staticmethod
    def get(id):
        """根据ID获取用户"""
        data = users_store.get(id)
        return User.from_dict(data) if data else None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤用户"""
        results = users_store.filter(**kwargs)
        return [User.from_dict(data) for data in results]
    
    @staticmethod
    def all():
        """获取所有用户"""
        results = users_store.all()
        return [User.from_dict(data) for data in results]

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
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建关系对象"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return Relationship(**data)
    
    def save(self):
        """保存关系信息"""
        if self.id:
            relationships_store.update(self.id, self.to_dict())
        else:
            data = relationships_store.create(self.to_dict())
            self.id = data['id']
        return self
    
    @staticmethod
    def get(id):
        """根据ID获取关系"""
        data = relationships_store.get(id)
        return Relationship.from_dict(data) if data else None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤关系"""
        results = relationships_store.filter(**kwargs)
        return [Relationship.from_dict(data) for data in results]
    
    @staticmethod
    def all():
        """获取所有关系"""
        results = relationships_store.all()
        return [Relationship.from_dict(data) for data in results]

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
            'created_at': self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建聊天记录对象"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return CoachChat(**data)
    
    def save(self):
        """保存聊天记录"""
        if self.id:
            coach_chats_store.update(self.id, self.to_dict())
        else:
            data = coach_chats_store.create(self.to_dict())
            self.id = data['id']
        return self
    
    @staticmethod
    def get(id):
        """根据ID获取聊天记录"""
        data = coach_chats_store.get(id)
        return CoachChat.from_dict(data) if data else None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤聊天记录"""
        results = coach_chats_store.filter(**kwargs)
        return [CoachChat.from_dict(data) for data in results]
    
    @staticmethod
    def all():
        """获取所有聊天记录"""
        results = coach_chats_store.all()
        return [CoachChat.from_dict(data) for data in results]
    
    @staticmethod
    def order_by(field, reverse=False):
        """根据字段排序"""
        results = sorted(coach_chats_store.all(), key=lambda x: x.get(field, 0), reverse=reverse)
        return [CoachChat.from_dict(data) for data in results]
    
    @staticmethod
    def limit(n):
        """限制返回数量"""
        results = coach_chats_store.all()[:n]
        return [CoachChat.from_dict(data) for data in results]

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
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return LoungeChat(**data)
    
    def save(self):
        """保存聊天记录"""
        if self.id:
            lounge_chats_store.update(self.id, self.to_dict())
        else:
            data = lounge_chats_store.create(self.to_dict())
            self.id = data['id']
        return self
    
    @staticmethod
    def get(id):
        """根据ID获取聊天记录"""
        data = lounge_chats_store.get(id)
        return LoungeChat.from_dict(data) if data else None
    
    @staticmethod
    def filter(**kwargs):
        """根据条件过滤聊天记录"""
        results = lounge_chats_store.filter(**kwargs)
        return [LoungeChat.from_dict(data) for data in results]
    
    @staticmethod
    def all():
        """获取所有聊天记录"""
        results = lounge_chats_store.all()
        return [LoungeChat.from_dict(data) for data in results]
    
    @staticmethod
    def order_by(field, reverse=False):
        """根据字段排序"""
        results = sorted(lounge_chats_store.all(), key=lambda x: x.get(field, 0), reverse=reverse)
        return [LoungeChat.from_dict(data) for data in results]
    
    @staticmethod
    def limit(n):
        """限制返回数量"""
        results = lounge_chats_store.all()[:n]
        return [LoungeChat.from_dict(data) for data in results]

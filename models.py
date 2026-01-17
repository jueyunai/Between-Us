# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    binding_code = db.Column(db.String(20), unique=True)  # 绑定码
    partner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 伴侣ID
    unbind_at = db.Column(db.DateTime, nullable=True)  # 解绑时间
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关系
    coach_chats = db.relationship('CoachChat', backref='user', lazy='dynamic')

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
            'unbind_at': self.unbind_at.isoformat() if self.unbind_at else None
        }


class Relationship(db.Model):
    """关系绑定表"""
    __tablename__ = 'relationships'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.String(50), unique=True, nullable=False)  # 情感客厅房间ID
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)  # 是否激活状态

    def to_dict(self):
        return {
            'id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'room_id': self.room_id,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class CoachChat(db.Model):
    """个人教练聊天记录"""
    __tablename__ = 'coach_chats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)
    reasoning_content = db.Column(db.Text, nullable=True)  # AI 思考过程
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'reasoning_content': self.reasoning_content,
            'created_at': self.created_at.isoformat()
        }


class LoungeChat(db.Model):
    """情感客厅聊天记录"""
    __tablename__ = 'lounge_chats'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # AI消息时为None
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

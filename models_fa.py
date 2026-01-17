# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import secrets

DATABASE_URL = "sqlite:///./emotion_helper.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password = Column(String(200), nullable=False)
    binding_code = Column(String(20), unique=True)
    partner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    unbind_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

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


class Relationship(Base):
    """关系绑定表"""
    __tablename__ = 'relationships'

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user2_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    room_id = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'room_id': self.room_id,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class CoachChat(Base):
    """个人教练聊天记录"""
    __tablename__ = 'coach_chats'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }


class LoungeChat(Base):
    """情感客厅聊天记录"""
    __tablename__ = 'lounge_chats'

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

# 创建所有表
Base.metadata.create_all(bind=engine)

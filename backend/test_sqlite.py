#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 存储层测试脚本
验证数据库功能是否正常
"""

from storage_sqlite import User, Relationship, CoachChat, LoungeChat
import os

def test_user():
    """测试用户功能"""
    print("\n=== 测试用户功能 ===")
    
    # 创建用户
    user = User(phone="13800138000", password="test123")
    user.generate_binding_code()
    user.save()
    print(f"✅ 创建用户: {user.phone}, ID: {user.id}, 绑定码: {user.binding_code}")
    
    # 查询用户
    found_user = User.get(user.id)
    print(f"✅ 查询用户: {found_user.phone}")
    
    # 过滤用户
    users = User.filter(phone="13800138000")
    print(f"✅ 过滤用户: 找到 {len(users)} 个")
    
    return user

def test_relationship(user1, user2):
    """测试关系功能"""
    print("\n=== 测试关系功能 ===")
    
    # 创建关系
    room_id = f"room_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}"
    rel = Relationship(
        user1_id=user1.id,
        user2_id=user2.id,
        room_id=room_id
    )
    rel.save()
    print(f"✅ 创建关系: {room_id}")
    
    # 查询关系
    found_rel = Relationship.get(rel.id)
    print(f"✅ 查询关系: {found_rel.room_id}")
    
    return rel

def test_coach_chat(user):
    """测试教练聊天"""
    print("\n=== 测试教练聊天 ===")
    
    # 创建聊天记录
    chat1 = CoachChat(user_id=user.id, role="user", content="你好")
    chat1.save()
    print(f"✅ 保存用户消息: {chat1.content}")
    
    chat2 = CoachChat(user_id=user.id, role="assistant", content="你好！有什么可以帮助你的吗？")
    chat2.save()
    print(f"✅ 保存AI回复: {chat2.content}")
    
    # 查询历史
    history = CoachChat.filter(user_id=user.id)
    print(f"✅ 查询历史: 共 {len(history)} 条")
    
    return history

def test_lounge_chat(room_id, user_id):
    """测试客厅聊天"""
    print("\n=== 测试客厅聊天 ===")
    
    # 创建聊天记录
    chat1 = LoungeChat(room_id=room_id, user_id=user_id, role="user", content="大家好")
    chat1.save()
    print(f"✅ 保存用户消息: {chat1.content}")
    
    chat2 = LoungeChat(room_id=room_id, user_id=None, role="assistant", content="欢迎来到情感客厅！")
    chat2.save()
    print(f"✅ 保存AI回复: {chat2.content}")
    
    # 查询历史
    history = LoungeChat.filter(room_id=room_id)
    print(f"✅ 查询历史: 共 {len(history)} 条")
    
    return history

def main():
    """主测试流程"""
    print("="*60)
    print("SQLite 存储层测试")
    print("="*60)
    
    try:
        # 测试用户
        user1 = test_user()
        user2 = User(phone="13900139000", password="test456")
        user2.save()
        print(f"✅ 创建第二个用户: {user2.phone}")
        
        # 测试关系
        rel = test_relationship(user1, user2)
        
        # 测试教练聊天
        test_coach_chat(user1)
        
        # 测试客厅聊天
        test_lounge_chat(rel.room_id, user1.id)
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        
        # 显示数据库路径
        from storage_sqlite import DB_PATH
        print(f"\n数据库文件: {DB_PATH}")
        if os.path.exists(DB_PATH):
            size = os.path.getsize(DB_PATH)
            print(f"文件大小: {size} 字节")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

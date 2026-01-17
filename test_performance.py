#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本 - 测试 Supabase 连接和数据库操作性能
"""
import time
import requests
from storage_supabase import User, CoachChat, SUPABASE_URL

def test_network_latency():
    """测试网络延迟"""
    print("\n" + "="*60)
    print("测试 1：网络延迟检测")
    print("="*60)
    
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL 未配置")
        return
    
    try:
        start = time.time()
        response = requests.get(SUPABASE_URL, timeout=5)
        latency = time.time() - start
        
        print(f"✅ Supabase URL: {SUPABASE_URL}")
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 延迟: {latency:.3f}s")
        
        if latency > 1.0:
            print(f"⚠️  警告：延迟较高（> 1s），可能影响用户体验")
        elif latency > 0.5:
            print(f"⚠️  提示：延迟中等（> 0.5s），建议优化")
        else:
            print(f"✅ 延迟正常（< 0.5s）")
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")

def test_db_operations():
    """测试数据库操作性能"""
    print("\n" + "="*60)
    print("测试 2：数据库操作性能")
    print("="*60)
    
    # 测试查询
    print("\n[查询测试]")
    start = time.time()
    users = User.all()
    query_time = time.time() - start
    print(f"✅ 查询所有用户: {len(users)} 条记录")
    print(f"✅ 耗时: {query_time:.3f}s")
    
    # 测试创建（使用测试数据）
    print("\n[创建测试]")
    test_phone = f"test_{int(time.time())}"
    start = time.time()
    test_user = User(phone=test_phone, password="test123")
    test_user.save()
    create_time = time.time() - start
    print(f"✅ 创建测试用户: {test_phone}")
    print(f"✅ 耗时: {create_time:.3f}s")
    
    # 测试更新
    print("\n[更新测试]")
    start = time.time()
    test_user.generate_binding_code()
    test_user.save()
    update_time = time.time() - start
    print(f"✅ 更新绑定码: {test_user.binding_code}")
    print(f"✅ 耗时: {update_time:.3f}s")
    
    # 性能评估
    print("\n[性能评估]")
    total_time = query_time + create_time + update_time
    print(f"总耗时: {total_time:.3f}s")
    
    if total_time < 0.5:
        print("✅ 性能优秀")
    elif total_time < 1.0:
        print("✅ 性能良好")
    elif total_time < 2.0:
        print("⚠️  性能一般，建议优化")
    else:
        print("❌ 性能较差，需要优化")

def test_concurrent_writes():
    """测试并发写入（模拟异步保存）"""
    print("\n" + "="*60)
    print("测试 3：并发写入性能")
    print("="*60)
    
    import threading
    
    def save_message():
        test_msg = CoachChat(
            user_id=1,
            role='user',
            content=f'测试消息 {time.time()}'
        )
        start = time.time()
        test_msg.save()
        duration = time.time() - start
        print(f"  线程 {threading.current_thread().name}: {duration:.3f}s")
    
    print("\n启动 5 个并发写入...")
    threads = []
    start = time.time()
    
    for i in range(5):
        thread = threading.Thread(target=save_message, name=f"Thread-{i+1}")
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start
    print(f"\n✅ 5 个并发写入完成")
    print(f"✅ 总耗时: {total_time:.3f}s")
    print(f"✅ 平均耗时: {total_time/5:.3f}s")

def main():
    print("\n" + "="*60)
    print("Supabase 性能测试")
    print("="*60)
    
    try:
        test_network_latency()
        test_db_operations()
        test_concurrent_writes()
        
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

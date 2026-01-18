# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, session, Response, stream_with_context
from flask_cors import CORS
from storage_sqlite import User, Relationship, CoachChat, LoungeChat
from datetime import datetime, timedelta
import secrets
import os
import requests
import json
import threading
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['JSON_AS_ASCII'] = False  # 支持中文 JSON 响应

CORS(app)

# Coze API 配置
COZE_API_URL = "https://api.coze.cn/v3/chat"
COZE_API_KEY = os.getenv("COZE_API_KEY", "")
COZE_BOT_ID_COACH = os.getenv("COZE_BOT_ID_COACH", "")
COZE_BOT_ID_LOUNGE = os.getenv("COZE_BOT_ID_LOUNGE", "")

# ==================== 性能优化工具 ====================
def save_message_async(message_obj):
    """异步保存消息到数据库（不阻塞主线程）"""
    def _save():
        try:
            start = time.time()
            message_obj.save()
            duration = time.time() - start
            print(f"[DB Perf] 异步保存耗时: {duration:.3f}s", flush=True)
        except Exception as e:
            print(f"[Async Save Error] {e}", flush=True)
    
    thread = threading.Thread(target=_save)
    thread.daemon = True
    thread.start()

# Supabase 延迟检测已移除（改用 SQLite）

def call_coze_api(user_phone, message, bot_id, conversation_history=None):
    """
    调用 Coze API（使用流式响应）
    :param user_phone: 用户手机号（作为 user_id）
    :param message: 用户消息
    :param bot_id: Bot ID
    :param conversation_history: 对话历史（可选）
    :return: AI 回复内容
    """
    if not COZE_API_KEY or not bot_id:
        return "AI 服务未配置，请在 .env 文件中设置 COZE_API_KEY 和 BOT_ID。"

    try:
        import json
        headers = {
            'Authorization': f'Bearer {COZE_API_KEY}',
            'Content-Type': 'application/json'
        }

        # 构建消息列表
        messages = []
        if conversation_history:
            for msg in conversation_history:
                msg_type = "question" if msg["role"] == "user" else "answer"
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "content_type": "text",
                    "type": msg_type
                })

        # 添加当前消息
        messages.append({
            "role": "user",
            "content": message,
            "content_type": "text",
            "type": "question"
        })

        payload = {
            "bot_id": bot_id,
            "user_id": user_phone,
            "stream": True,  # 使用流式响应
            "auto_save_history": True,
            "additional_messages": messages
        }

        print(f"\n{'='*60}", flush=True)
        print(f"[Coze API] 发送请求", flush=True)
        print(f"[Coze API] Payload: {json.dumps(payload, ensure_ascii=False)}", flush=True)

        response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=60, stream=True)
        response.raise_for_status()

        # 检查响应内容类型
        content_type = response.headers.get('Content-Type', '')
        print(f"[Coze API] 响应 Content-Type: {content_type}", flush=True)

        # 处理流式响应
        # 只使用 conversation.message.completed 事件中的完整内容，忽略中间的片段
        completed_content = None
        has_stream_data = False
        current_event = None  # 跟踪 SSE event 类型
        
        for line in response.iter_lines():
            if line:
                has_stream_data = True
                try:
                    line_text = line.decode('utf-8')
                    print(f"[Coze Stream] {line_text}", flush=True)

                    # 处理 SSE 格式 - event: 行
                    if line_text.startswith('event:'):
                        current_event = line_text[6:].strip()
                        continue

                    # 处理 SSE 格式 - data: 行
                    if line_text.startswith('data:'):
                        json_str = line_text[5:].strip()
                        if json_str == '[DONE]' or json_str == '"[DONE]"':
                            break
                        
                        if not json_str:
                            continue

                        try:
                            data = json.loads(json_str)
                        except json.JSONDecodeError:
                            continue
                        
                        if not isinstance(data, dict):
                            continue
                        
                        # 过滤掉所有元数据消息
                        msg_type = data.get('msg_type')
                        if msg_type:
                            continue

                        # 只处理完成事件，使用之前记录的 event 类型
                        if current_event == 'conversation.message.completed':
                            # Coze API 返回的数据格式：role 和 content 直接在 data 中
                            role = data.get('role')
                            msg_type_field = data.get('type')  # answer, follow_up, verbose 等
                            content = data.get('content', '')
                            
                            print(f"[Coze API] 完成事件: role={role}, type={msg_type_field}, content_len={len(content) if content else 0}", flush=True)
                            
                            # 跳过 verbose 类型（内部日志）
                            if msg_type_field == 'verbose':
                                continue
                            
                            if role == 'assistant' and isinstance(content, str) and content:
                                # 优先使用 answer 类型的回复，follow_up 作为备选
                                if msg_type_field == 'answer':
                                    completed_content = content
                                    print(f"[Coze API] 收到 answer 回复，内容长度: {len(content)}", flush=True)
                                elif msg_type_field == 'follow_up' and not completed_content:
                                    # 如果还没有 answer，暂存 follow_up
                                    completed_content = content
                                    print(f"[Coze API] 收到 follow_up 回复，内容长度: {len(content)}", flush=True)

                except UnicodeDecodeError as e:
                    print(f"[Coze API] 解码错误: {e}", flush=True)
                    continue
                except Exception as e:
                    print(f"[Coze API] 处理流式数据异常: {type(e).__name__}: {e}", flush=True)
                    continue
        
        # 如果没有收到流式数据，尝试解析为普通 JSON
        if not has_stream_data:
            try:
                result = response.json()
                print(f"[Coze API] 非流式响应: {result}", flush=True)
                if isinstance(result, dict) and result.get("code") == 0:
                    data = result.get("data", {})
                    if isinstance(data, dict):
                        messages = data.get("messages", [])
                        if isinstance(messages, list):
                            for msg in messages:
                                if isinstance(msg, dict) and msg.get("role") == "assistant":
                                    content = msg.get("content", "")
                                    if isinstance(content, str) and content:
                                        completed_content = content
                                        break
            except Exception as e:
                print(f"[Coze API] 解析非流式响应失败: {e}", flush=True)

        # 清理文本：移除可能混入的JSON字符串和重复内容
        final_content = completed_content
        if final_content:
            import re
            # 移除所有JSON格式的字符串（包括嵌套的）
            # 匹配 { 开头 } 结尾的JSON对象
            while True:
                # 移除简单的JSON对象
                new_content = re.sub(r'\{[^{}]*"msg_type"[^{}]*\}', '', final_content)
                # 移除嵌套的JSON对象（处理转义的情况）
                new_content = re.sub(r'\{[^{}]*"data"[^{}]*"[^{}]*"[^{}]*\}', '', new_content)
                if new_content == final_content:
                    break
                final_content = new_content
            
            # 移除多余的空白字符，但保留换行符
            final_content = re.sub(r'[ ]+', ' ', final_content).strip()
            
            # 移除行首和行尾的空格
            final_content = '\n'.join(line.strip() for line in final_content.split('\n'))
            
            # 智能去重：检测并移除重复的句子或段落
            # 如果内容重复（前一半等于后一半），只保留一半
            half_len = len(final_content) // 2
            if half_len > 20:  # 至少20个字符才判断重复
                if final_content[:half_len] == final_content[half_len:]:
                    final_content = final_content[:half_len]
                # 检查是否有明显的重复模式（如连续两次相同）
                elif len(final_content) > 40:
                    # 尝试找到重复的句子
                    sentences = re.split(r'[。！？\n]', final_content)
                    if len(sentences) > 2:
                        # 检查是否有连续重复的句子
                        cleaned_sentences = []
                        for i, sent in enumerate(sentences):
                            if i == 0 or sent != sentences[i-1]:
                                cleaned_sentences.append(sent)
                        if len(cleaned_sentences) < len(sentences):
                            final_content = '。'.join(cleaned_sentences)
        
        print(f"[Coze API] 完成事件内容长度: {len(completed_content) if completed_content else 0}", flush=True)
        print(f"[Coze API] 清理后内容长度: {len(final_content) if final_content else 0}", flush=True)
        print(f"[Coze API] 最终回复: {final_content[:200] if final_content else 'None'}...", flush=True)
        print(f"{'='*60}\n", flush=True)

        if final_content:
            return final_content
        else:
            return "AI 未返回有效回复，请稍后重试"

    except requests.exceptions.Timeout:
        return "AI 响应超时，请稍后再试"
    except requests.exceptions.RequestException as e:
        print(f"[Coze API] 请求错误: {str(e)}", flush=True)
        return f"AI 调用失败: {str(e)}"
    except Exception as e:
        print(f"[Coze API] 处理异常: {str(e)}", flush=True)
        return f"AI 处理异常: {str(e)}"

# ==================== 用户认证 API ====================
@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    nickname = data.get('nickname', '').strip()  # 昵称非必填

    if not phone or not password:
        return jsonify({'success': False, 'message': '手机号和密码不能为空'}), 400
    
    # 验证昵称长度（如果提供）
    if nickname and len(nickname) > 20:
        return jsonify({'success': False, 'message': '昵称最长20个字符'}), 400

    # 检查用户是否已存在
    existing_users = User.filter(phone=phone)
    if existing_users:
        return jsonify({'success': False, 'message': '该手机号已注册'}), 400

    # 创建新用户（如果没有提供昵称，使用手机号后4位）
    if not nickname:
        nickname = phone[-4:] if len(phone) >= 4 else phone
    
    user = User(phone=phone, password=password, nickname=nickname)
    user.generate_binding_code()
    user.save()

    return jsonify({
        'success': True,
        'message': '注册成功',
        'user': user.to_dict()
    })


@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    phone = data.get('phone')
    password = data.get('password')

    users = User.filter(phone=phone, password=password)
    user = users[0] if users else None
    if not user:
        return jsonify({'success': False, 'message': '手机号或密码错误'}), 401

    # 设置 session
    session['user_id'] = user.id

    return jsonify({
        'success': True,
        'message': '登录成功',
        'user': user.to_dict()
    })


@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.pop('user_id', None)
    return jsonify({'success': True, 'message': '登出成功'})


@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    """获取用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    user = User.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    return jsonify({
        'success': True,
        'user': user.to_dict()
    })


@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """根据ID获取用户信息（只返回基本信息）"""
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    user = User.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    # 只返回基本信息，保护隐私
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'phone': user.phone,
            'nickname': user.nickname if user.nickname else (user.phone[-4:] if len(user.phone) >= 4 else user.phone)
        }
    })


@app.route('/api/user/update_nickname', methods=['POST'])
def update_nickname():
    """更新用户昵称"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    nickname = data.get('nickname', '').strip()

    if not nickname:
        return jsonify({'success': False, 'message': '昵称不能为空'}), 400

    if len(nickname) > 20:
        return jsonify({'success': False, 'message': '昵称最长20个字符'}), 400

    user = User.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    user.nickname = nickname
    user.save()

    return jsonify({
        'success': True,
        'message': '昵称更新成功',
        'user': user.to_dict()
    })


# ==================== 伴侣绑定 API ====================
@app.route('/api/binding/code', methods=['GET'])
def get_binding_code():
    """获取绑定码"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    user = User.get(user_id)
    if not user.binding_code:
        user.generate_binding_code()
        user.save()

    return jsonify({
        'success': True,
        'binding_code': user.binding_code
    })


@app.route('/api/binding/bind', methods=['POST'])
def bind_partner():
    """使用绑定码绑定伴侣"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    binding_code = data.get('binding_code')

    user = User.get(user_id)
    partners = User.filter(binding_code=binding_code)
    partner = partners[0] if partners else None

    if not partner:
        return jsonify({'success': False, 'message': '绑定码无效'}), 400

    if partner.id == user.id:
        return jsonify({'success': False, 'message': '不能绑定自己'}), 400

    if user.partner_id or partner.partner_id:
        return jsonify({'success': False, 'message': '您或对方已有伴侣'}), 400

    # 建立绑定关系
    user.partner_id = partner.id
    partner.partner_id = user.id

    # 创建情感客厅房间
    room_id = f"room_{min(user.id, partner.id)}_{max(user.id, partner.id)}"
    relationship = Relationship(
        user1_id=min(user.id, partner.id),
        user2_id=max(user.id, partner.id),
        room_id=room_id
    )
    relationship.save()
    user.save()
    partner.save()

    return jsonify({
        'success': True,
        'message': '绑定成功！',
        'room_id': room_id
    })


@app.route('/api/binding/unbind', methods=['POST'])
def unbind_partner():
    """解绑伴侣"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    user = User.get(user_id)
    if not user.partner_id:
        return jsonify({'success': False, 'message': '您还没有绑定伴侣'}), 400

    partner = User.get(user.partner_id)

    # 设置解绑时间（1个月冷静期）
    unbind_time = datetime.now()
    user.unbind_at = unbind_time
    partner.unbind_at = unbind_time

    # 冷静期内关系保持活跃，不停用
    # relationships = Relationship.filter(
    #     user1_id=min(user.id, partner.id),
    #     user2_id=max(user.id, partner.id)
    # )
    # if relationships:
    #     relationship = relationships[0]
    #     relationship.is_active = False
    #     relationship.save()

    user.save()
    partner.save()

    return jsonify({
        'success': True,
        'message': '已发起解绑，1个月冷静期后生效',
        'unbind_at': unbind_time.isoformat()
    })


@app.route('/api/binding/cancel_unbind', methods=['POST'])
def cancel_unbind():
    """撤销解绑"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    user = User.get(user_id)
    if not user.unbind_at:
        return jsonify({'success': False, 'message': '没有待撤销的解绑'}), 400

    # 检查是否在冷静期内
    if isinstance(user.unbind_at, str):
        user.unbind_at = datetime.fromisoformat(user.unbind_at)
    cool_down_end = user.unbind_at + timedelta(days=30)
    if datetime.now() > cool_down_end:
        return jsonify({'success': False, 'message': '冷静期已过，无法撤销'}), 400

    partner = User.get(user.partner_id)
    user.unbind_at = None
    partner.unbind_at = None

    # 关系一直是活跃的，无需恢复
    # relationships = Relationship.filter(
    #     user1_id=min(user.id, partner.id),
    #     user2_id=max(user.id, partner.id)
    # )
    # if relationships:
    #     relationship = relationships[0]
    #     relationship.is_active = True
    #     relationship.save()

    user.save()
    partner.save()

    return jsonify({
        'success': True,
        'message': '已撤销解绑'
    })


# ==================== 个人教练聊天室 API ====================
@app.route('/api/coach/chat', methods=['POST'])
def coach_chat():
    """个人教练聊天"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    message = data.get('message')

    if not message:
        return jsonify({'success': False, 'message': '消息不能为空'}), 400

    # 获取用户信息
    user = User.get(user_id)
    user_phone = user.phone

    # 保存用户消息
    user_msg = CoachChat(user_id=user_id, role='user', content=message)
    user_msg.save()

    # 获取历史对话（最近5条，避免消息过长）
    all_history = CoachChat.filter(user_id=user_id)
    all_history.sort(key=lambda x: x.created_at, reverse=True)
    history = all_history[:5]
    conversation_history = [{"role": msg.role, "content": msg.content} for msg in reversed(history)]

    # 调用 Coze API
    ai_reply = call_coze_api(
        user_phone=user_phone,
        message=message,
        bot_id=COZE_BOT_ID_COACH,
        conversation_history=conversation_history[:-1] if conversation_history else None  # 排除当前消息
    )

    # 保存 AI 回复
    ai_msg = CoachChat(user_id=user_id, role='assistant', content=ai_reply)
    ai_msg.save()

    return jsonify({
        'success': True,
        'message': ai_reply
    })


@app.route('/api/coach/history', methods=['GET'])
def get_coach_history():
    """获取个人教练聊天记录"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    history = CoachChat.filter(user_id=user_id)
    history.sort(key=lambda x: x.created_at)

    return jsonify({
        'success': True,
        'messages': [msg.to_dict() for msg in history]
    })


@app.route('/api/debug/config', methods=['GET'])
def debug_config():
    """调试接口：检查配置"""
    return jsonify({
        'success': True,
        'config': {
            'COZE_API_KEY': '已配置' if COZE_API_KEY else '未配置',
            'COZE_API_KEY_length': len(COZE_API_KEY) if COZE_API_KEY else 0,
            'COZE_BOT_ID_COACH': COZE_BOT_ID_COACH or '未配置',
            'COZE_BOT_ID_LOUNGE': COZE_BOT_ID_LOUNGE or '未配置',
            'COZE_API_URL': COZE_API_URL,
            'DB_PATH': DB_PATH,
            'FLASK_ENV': os.getenv('FLASK_ENV', 'development')
        }
    })


@app.route('/api/coach/chat/stream', methods=['POST'])
def coach_chat_stream():
    """个人教练流式聊天 - 实时推送思考过程和正文"""
    print(f"\n{'='*60}", flush=True)
    print(f"[Coach Stream] 收到流式聊天请求", flush=True)
    
    user_id = session.get('user_id')
    if not user_id:
        print(f"[Coach Stream] 用户未登录", flush=True)
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    message = data.get('message')
    print(f"[Coach Stream] 用户ID: {user_id}", flush=True)
    print(f"[Coach Stream] 消息内容: {message[:50]}..." if len(message) > 50 else f"[Coach Stream] 消息内容: {message}", flush=True)

    if not message:
        print(f"[Coach Stream] 消息为空", flush=True)
        return jsonify({'success': False, 'message': '消息不能为空'}), 400

    # 获取用户信息
    print(f"[Coach Stream] 开始获取用户信息...", flush=True)
    user = User.get(user_id)
    user_phone = user.phone
    print(f"[Coach Stream] 用户手机号: {user_phone}", flush=True)

    # 异步保存用户消息（不阻塞）
    print(f"[Coach Stream] 开始保存用户消息到数据库...", flush=True)
    user_msg = CoachChat(user_id=user_id, role='user', content=message)
    save_message_async(user_msg)
    print(f"[Coach Stream] 用户消息已提交异步保存", flush=True)

    # 获取历史对话（最近5条）
    print(f"[Coach Stream] 开始读取历史对话...", flush=True)
    all_history = CoachChat.filter(user_id=user_id)
    print(f"[Coach Stream] 数据库返回历史记录数: {len(all_history)}", flush=True)
    all_history.sort(key=lambda x: x.created_at, reverse=True)
    history = all_history[:5]
    conversation_history = [{"role": msg.role, "content": msg.content} for msg in reversed(history)]
    print(f"[Coach Stream] 构建对话历史完成，共 {len(conversation_history)} 条", flush=True)

    def generate():
        """流式生成器"""
        print(f"[Coach Stream] 进入流式生成器", flush=True)
        
        if not COZE_API_KEY or not COZE_BOT_ID_COACH:
            print(f"[Coach Stream] ❌ AI服务未配置: COZE_API_KEY={bool(COZE_API_KEY)}, BOT_ID={bool(COZE_BOT_ID_COACH)}", flush=True)
            yield f"data: {json.dumps({'type': 'error', 'content': 'AI 服务未配置'}, ensure_ascii=False)}\n\n"
            return
        
        print(f"[Coach Stream] ✓ API配置检查通过", flush=True)

        try:
            headers = {
                'Authorization': f'Bearer {COZE_API_KEY}',
                'Content-Type': 'application/json'
            }

            # 构建消息列表
            messages = []
            if conversation_history:
                for msg in conversation_history[:-1]:  # 排除当前消息
                    msg_type = "question" if msg["role"] == "user" else "answer"
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"],
                        "content_type": "text",
                        "type": msg_type
                    })

            messages.append({
                "role": "user",
                "content": message,
                "content_type": "text",
                "type": "question"
            })

            payload = {
                "bot_id": COZE_BOT_ID_COACH,
                "user_id": user_phone,
                "stream": True,
                "auto_save_history": True,
                "additional_messages": messages
            }

            print(f"[Coach Stream] 准备调用 Coze API", flush=True)
            print(f"[Coach Stream] API URL: {COZE_API_URL}", flush=True)
            print(f"[Coach Stream] Bot ID: {COZE_BOT_ID_COACH}", flush=True)
            print(f"[Coach Stream] User ID: {user_phone}", flush=True)
            print(f"[Coach Stream] 消息数量: {len(messages)}", flush=True)
            
            api_start_time = time.time()
            response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=60, stream=True)
            print(f"[Coach Stream] API响应状态码: {response.status_code}", flush=True)
            print(f"[Coach Stream] API响应耗时: {time.time() - api_start_time:.3f}s", flush=True)
            response.raise_for_status()

            current_event = None
            final_content = ""
            reasoning_content = ""
            line_count = 0
            
            # 预先创建AI消息记录（边流式边保存策略）
            print(f"[Coach Stream] 创建AI消息记录...", flush=True)
            ai_msg = CoachChat(
                user_id=user_id, 
                role='assistant', 
                content="",  # 初始为空
                reasoning_content=None
            )
            db_save_start = time.time()
            ai_msg.save()  # 先保存一次，获取ID
            print(f"[Coach Stream] AI消息记录已保存，ID: {ai_msg.id if hasattr(ai_msg, 'id') else 'N/A'}，耗时: {time.time() - db_save_start:.3f}s", flush=True)
            last_save_time = time.time()
            save_interval = 2.0  # 每2秒保存一次
            
            print(f"[Coach Stream] 开始读取流式响应...", flush=True)

            for line in response.iter_lines():
                if line:
                    line_count += 1
                    try:
                        line_text = line.decode('utf-8')
                        
                        if line_count <= 5 or line_count % 10 == 0:  # 只打印前5行和每10行
                            print(f"[Coach Stream] 第{line_count}行: {line_text[:100]}...", flush=True)

                        # 处理 event: 行
                        if line_text.startswith('event:'):
                            current_event = line_text[6:].strip()
                            print(f"[Coach Stream] 事件类型: {current_event}", flush=True)
                            continue

                        # 处理 data: 行
                        if line_text.startswith('data:'):
                            json_str = line_text[5:].strip()
                            if json_str == '[DONE]' or json_str == '"[DONE]"':
                                print(f"[Coach Stream] 收到完成信号 [DONE]", flush=True)
                                break

                            if not json_str:
                                continue

                            try:
                                data = json.loads(json_str)
                            except json.JSONDecodeError:
                                continue

                            if not isinstance(data, dict):
                                continue

                            # 跳过元数据消息
                            if data.get('msg_type'):
                                continue

                            role = data.get('role')
                            msg_type_field = data.get('type')

                            # 处理流式内容 (delta 事件)
                            if current_event == 'conversation.message.delta' and role == 'assistant' and msg_type_field == 'answer':
                                # 思考过程 (reasoning_content)
                                reasoning = data.get('reasoning_content', '')
                                if reasoning:
                                    reasoning_content += reasoning
                                    print(f"[Coach Stream] 收到思考内容，长度: {len(reasoning)}", flush=True)
                                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning}, ensure_ascii=False)}\n\n"

                                # 正文内容 (content)
                                content = data.get('content', '')
                                if content:
                                    final_content += content
                                    if len(final_content) % 50 < len(content):  # 每50字符打印一次
                                        print(f"[Coach Stream] 累计正文长度: {len(final_content)}", flush=True)
                                    yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"
                                    
                                    # 定期保存（边流式边保存，防止数据丢失）
                                    current_time = time.time()
                                    if current_time - last_save_time >= save_interval:
                                        print(f"[Coach Stream] 定期保存中间结果...", flush=True)
                                        ai_msg.content = final_content
                                        ai_msg.reasoning_content = reasoning_content if reasoning_content else None
                                        save_message_async(ai_msg)
                                        last_save_time = current_time

                            # 处理完成事件
                            elif current_event == 'conversation.message.completed' and role == 'assistant':
                                if msg_type_field == 'answer':
                                    # 思考完成信号
                                    yield f"data: {json.dumps({'type': 'reasoning_done'}, ensure_ascii=False)}\n\n"
                                elif msg_type_field == 'follow_up':
                                    # 跳过 follow_up
                                    pass

                    except Exception as e:
                        print(f"[Stream Error] {e}", flush=True)
                        continue

            # 最终保存完整内容
            if final_content:
                ai_msg.content = final_content
                ai_msg.reasoning_content = reasoning_content if reasoning_content else None
                ai_msg.save()  # 同步保存最终版本
                print(f"[Coach Stream] 最终保存内容长度: {len(final_content)}", flush=True)
            else:
                # 如果没有内容，删除之前创建的空记录
                print(f"[Coach Stream] 未收到AI回复，删除空记录", flush=True)

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'final_content': final_content, 'reasoning_content': reasoning_content}, ensure_ascii=False)}\n\n"

        except Exception as e:
            print(f"[Stream API Error] {e}", flush=True)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


# ==================== 情感客厅聊天室 API ====================
@app.route('/api/lounge/room', methods=['GET'])
def get_lounge_room():
    """获取情感客厅房间信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    user = User.get(user_id)
    if not user.partner_id:
        return jsonify({'success': False, 'message': '您还没有绑定伴侣'}), 400

    # 查找用户相关的活跃关系（user1_id 或 user2_id 等于当前用户）
    all_relationships = Relationship.all()
    relationships = [
        r for r in all_relationships 
        if (r.user1_id == user.id or r.user2_id == user.id) and r.is_active
    ]
    relationship = relationships[0] if relationships else None

    if not relationship:
        return jsonify({'success': False, 'message': '未找到有效的关系'}), 404

    return jsonify({
        'success': True,
        'room_id': relationship.room_id
    })


@app.route('/api/lounge/history', methods=['GET'])
def get_lounge_history():
    """获取情感客厅聊天记录"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    user = User.get(user_id)
    # 查找用户相关的关系
    all_relationships = Relationship.all()
    relationships = [
        r for r in all_relationships 
        if r.user1_id == user.id or r.user2_id == user.id
    ]
    relationship = relationships[0] if relationships else None

    if not relationship:
        return jsonify({'success': False, 'message': '未找到房间'}), 404

    history = LoungeChat.filter(room_id=relationship.room_id)
    history.sort(key=lambda x: x.created_at)

    return jsonify({
        'success': True,
        'messages': [msg.to_dict() for msg in history]
    })


@app.route('/api/lounge/messages/new', methods=['GET'])
def get_new_lounge_messages():
    """获取新消息（短轮询）"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    since_id = request.args.get('since_id', 0, type=int)
    
    user = User.get(user_id)
    all_relationships = Relationship.all()
    relationships = [
        r for r in all_relationships 
        if r.user1_id == user.id or r.user2_id == user.id
    ]
    relationship = relationships[0] if relationships else None

    if not relationship:
        return jsonify({'success': False, 'message': '未找到房间'}), 404

    # 获取所有消息，筛选出 ID 大于 since_id 的
    all_messages = LoungeChat.filter(room_id=relationship.room_id)
    new_messages = [msg for msg in all_messages if msg.id > since_id]
    new_messages.sort(key=lambda x: x.created_at)

    return jsonify({
        'success': True,
        'messages': [msg.to_dict() for msg in new_messages]
    })


@app.route('/api/lounge/send', methods=['POST'])
def send_lounge_message():
    """发送消息到情感客厅（短轮询版本）"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    room_id = data.get('room_id')
    content = data.get('content')

    if not content:
        return jsonify({'success': False, 'message': '消息不能为空'}), 400

    # 保存消息
    msg = LoungeChat(room_id=room_id, user_id=user_id, role='user', content=content)
    msg.save()

    return jsonify({
        'success': True,
        'message': msg.to_dict()
    })


@app.route('/api/lounge/call_ai', methods=['POST'])
def call_lounge_ai():
    """召唤 AI 助手（短轮询版本 - 非流式）"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    try:
        data = request.json
        room_id = data.get('room_id')

        # 获取房间的两个用户
        all_relationships = Relationship.all()
        relationships = [
            r for r in all_relationships 
            if r.room_id == room_id
        ]
        relationship = relationships[0] if relationships else None
        
        if not relationship:
            return jsonify({'success': False, 'message': '未找到房间关系'}), 404
        
        user1 = User.get(relationship.user1_id)
        user2 = User.get(relationship.user2_id)
        
        # 创建用户ID到昵称的映射（使用手机号后4位）
        user_map = {
            user1.id: user1.phone[-4:] if user1.phone else "用户1",
            user2.id: user2.phone[-4:] if user2.phone else "用户2"
        }

        # 获取所有未传给AI的用户消息（按时间顺序）
        all_history = LoungeChat.filter(room_id=room_id)
        # 只取用户消息且未传给AI的
        unsent_messages = [
            msg for msg in all_history 
            if msg.role == "user" and not msg.sent_to_ai
        ]
        unsent_messages.sort(key=lambda x: x.created_at)
        
        # 限制最近10条
        messages_to_send = unsent_messages[-10:] if len(unsent_messages) > 10 else unsent_messages

        if not messages_to_send:
            ai_reply = "暂时没有新的对话内容可供分析哦～"
            reasoning_content = None
        else:
            # 构建消息内容：昵称：消息内容
            formatted_messages = []
            for msg in messages_to_send:
                nickname = user_map.get(msg.user_id, "未知用户")
                formatted_messages.append(f"{nickname}：{msg.content}")
            
            conversation_text = "\n".join(formatted_messages)
            
            # 调用 Coze API 并提取思考过程
            print(f"[Lounge AI] 开始调用 Coze API，消息数量: {len(messages_to_send)}", flush=True)
            print(f"[Lounge AI] 传入内容:\n{conversation_text}", flush=True)
            
            # 调用流式API并提取思考过程和正文
            ai_reply, reasoning_content = call_coze_api_with_reasoning(
                user_phone=room_id,
                message=conversation_text,
                bot_id=COZE_BOT_ID_LOUNGE
            )
            
            print(f"[Lounge AI] Coze API 返回，回复长度: {len(ai_reply)}, 思考长度: {len(reasoning_content) if reasoning_content else 0}", flush=True)
            
            # 标记这些消息已传给AI
            for msg in messages_to_send:
                msg.sent_to_ai = True
                msg.save()
            print(f"[Lounge AI] 已标记 {len(messages_to_send)} 条消息为已传给AI", flush=True)

        # 保存AI回复消息（新建，不是更新）
        ai_msg = LoungeChat(
            room_id=room_id, 
            user_id=None, 
            role='assistant', 
            content=ai_reply,
            reasoning_content=reasoning_content
        )
        ai_msg.save()
        print(f"[Lounge AI] 已保存AI回复消息，ID: {ai_msg.id}", flush=True)

        # 手动构建返回数据
        response_data = {
            'success': True,
            'message': {
                'id': ai_msg.id,
                'room_id': ai_msg.room_id,
                'user_id': ai_msg.user_id,
                'role': ai_msg.role,
                'content': ai_msg.content,
                'reasoning_content': ai_msg.reasoning_content,
                'created_at': ai_msg.created_at.isoformat() if hasattr(ai_msg.created_at, 'isoformat') else str(ai_msg.created_at)
            }
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"[Lounge AI Error] {type(e).__name__}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'AI 调用失败: {str(e)}'
        }), 500


@app.route('/api/lounge/call_ai/stream', methods=['POST'])
def call_lounge_ai_stream():
    """召唤 AI 助手（流式版本）"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    room_id = data.get('room_id')

    def generate():
        """流式生成器"""
        try:
            # 获取房间的两个用户
            all_relationships = Relationship.all()
            relationships = [
                r for r in all_relationships 
                if r.room_id == room_id
            ]
            relationship = relationships[0] if relationships else None
            
            if not relationship:
                yield f"data: {json.dumps({'type': 'error', 'content': '未找到房间关系'}, ensure_ascii=False)}\n\n"
                return
            
            user1 = User.get(relationship.user1_id)
            user2 = User.get(relationship.user2_id)
            
            # 创建用户ID到昵称的映射（使用手机号后4位）
            user_map = {
                user1.id: user1.phone[-4:] if user1.phone else "用户1",
                user2.id: user2.phone[-4:] if user2.phone else "用户2"
            }

            # 获取所有未传给AI的用户消息
            all_history = LoungeChat.filter(room_id=room_id)
            unsent_messages = [
                msg for msg in all_history 
                if msg.role == "user" and not msg.sent_to_ai
            ]
            unsent_messages.sort(key=lambda x: x.created_at)
            
            messages_to_send = unsent_messages[-10:] if len(unsent_messages) > 10 else unsent_messages

            if not messages_to_send:
                yield f"data: {json.dumps({'type': 'content', 'content': '暂时没有新的对话内容可供分析哦～'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'final_content': '暂时没有新的对话内容可供分析哦～', 'reasoning_content': None}, ensure_ascii=False)}\n\n"
                return

            # 构建消息内容
            formatted_messages = []
            for msg in messages_to_send:
                nickname = user_map.get(msg.user_id, "未知用户")
                formatted_messages.append(f"{nickname}：{msg.content}")
            
            conversation_text = "\n".join(formatted_messages)
            
            print(f"[Lounge AI Stream] 开始调用 Coze API", flush=True)

            # 调用 Coze API（流式）
            headers = {
                'Authorization': f'Bearer {COZE_API_KEY}',
                'Content-Type': 'application/json'
            }

            payload = {
                "bot_id": COZE_BOT_ID_LOUNGE,
                "user_id": room_id,
                "stream": True,
                "auto_save_history": True,
                "additional_messages": [{
                    "role": "user",
                    "content": conversation_text,
                    "content_type": "text",
                    "type": "question"
                }]
            }

            response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=60, stream=True)
            response.raise_for_status()

            current_event = None
            final_content = ""
            reasoning_content = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        line_text = line.decode('utf-8')

                        if line_text.startswith('event:'):
                            current_event = line_text[6:].strip()
                            continue

                        if line_text.startswith('data:'):
                            json_str = line_text[5:].strip()
                            if json_str == '[DONE]' or json_str == '"[DONE]"':
                                break
                            
                            if not json_str:
                                continue

                            try:
                                coze_data = json.loads(json_str)
                            except json.JSONDecodeError:
                                continue
                            
                            if not isinstance(coze_data, dict):
                                continue
                            
                            # 跳过元数据消息
                            if coze_data.get('msg_type'):
                                continue

                            # 处理流式增量事件
                            if current_event == 'conversation.message.delta':
                                role = coze_data.get('role')
                                msg_type_field = coze_data.get('type')
                                
                                if role == 'assistant' and msg_type_field == 'answer':
                                    # 思考过程
                                    reasoning = coze_data.get('reasoning_content', '')
                                    if reasoning:
                                        reasoning_content += reasoning
                                        yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning}, ensure_ascii=False)}\n\n"
                                    
                                    # 正文内容
                                    content = coze_data.get('content', '')
                                    if content:
                                        final_content += content
                                        yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"

                            # 处理完成事件
                            elif current_event == 'conversation.message.completed':
                                role = coze_data.get('role')
                                msg_type_field = coze_data.get('type')
                                
                                if role == 'assistant' and msg_type_field == 'answer':
                                    # 思考完成信号
                                    yield f"data: {json.dumps({'type': 'reasoning_done'}, ensure_ascii=False)}\n\n"

                    except Exception as e:
                        print(f"[Lounge Stream Error] {e}", flush=True)
                        continue

            # 标记消息已传给AI
            for msg in messages_to_send:
                msg.sent_to_ai = True
                msg.save()

            # 保存AI回复
            if final_content:
                ai_msg = LoungeChat(
                    room_id=room_id,
                    user_id=None,
                    role='assistant',
                    content=final_content,
                    reasoning_content=reasoning_content if reasoning_content else None
                )
                ai_msg.save()
                print(f"[Lounge AI Stream] 已保存AI回复，ID: {ai_msg.id}", flush=True)

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'final_content': final_content, 'reasoning_content': reasoning_content}, ensure_ascii=False)}\n\n"

        except Exception as e:
            print(f"[Lounge Stream API Error] {e}", flush=True)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


def call_coze_api_with_reasoning(user_phone, message, bot_id):
    """
    调用 Coze API 并提取思考过程和正文
    :return: (content, reasoning_content) 元组
    """
    if not COZE_API_KEY or not bot_id:
        return "AI 服务未配置", None

    try:
        import json
        headers = {
            'Authorization': f'Bearer {COZE_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            "bot_id": bot_id,
            "user_id": user_phone,
            "stream": True,
            "auto_save_history": True,
            "additional_messages": [{
                "role": "user",
                "content": message,
                "content_type": "text",
                "type": "question"
            }]
        }

        print(f"[Coze API] 发送请求（带思考过程提取）", flush=True)
        response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=60, stream=True)
        response.raise_for_status()

        completed_content = None
        reasoning_content = None
        current_event = None
        
        for line in response.iter_lines():
            if line:
                try:
                    line_text = line.decode('utf-8')

                    if line_text.startswith('event:'):
                        current_event = line_text[6:].strip()
                        continue

                    if line_text.startswith('data:'):
                        json_str = line_text[5:].strip()
                        if json_str == '[DONE]' or json_str == '"[DONE]"':
                            break
                        
                        if not json_str:
                            continue

                        try:
                            data = json.loads(json_str)
                        except json.JSONDecodeError:
                            continue
                        
                        if not isinstance(data, dict):
                            continue
                        
                        # 跳过元数据消息
                        if data.get('msg_type'):
                            continue

                        # 处理完成事件
                        if current_event == 'conversation.message.completed':
                            role = data.get('role')
                            msg_type_field = data.get('type')
                            content = data.get('content', '')
                            reasoning = data.get('reasoning_content', '')
                            
                            # 跳过 verbose 类型
                            if msg_type_field == 'verbose':
                                continue
                            
                            if role == 'assistant' and isinstance(content, str) and content:
                                if msg_type_field == 'answer':
                                    completed_content = content
                                    if reasoning:
                                        reasoning_content = reasoning
                                    print(f"[Coze API] 收到 answer 回复，正文长度: {len(content)}, 思考长度: {len(reasoning) if reasoning else 0}", flush=True)

                except Exception as e:
                    print(f"[Coze API] 处理流式数据异常: {type(e).__name__}: {e}", flush=True)
                    continue

        if completed_content:
            return completed_content, reasoning_content
        else:
            return "AI 未返回有效回复", None

    except Exception as e:
        print(f"[Coze API] 请求错误: {str(e)}", flush=True)
        return f"AI 调用失败: {str(e)}", None


# ==================== 前端路由 ====================
@app.route('/')
def index():
    """首页"""
    return render_template('login.html')


@app.route('/home')
def home():
    """主页"""
    return render_template('home.html')

@app.route('/profile')
def profile():
    """个人中心"""
    return render_template('profile.html')


@app.route('/coach')
def coach():
    """个人教练"""
    return render_template('coach.html')


@app.route('/lounge')
def lounge():
    """情感客厅（短轮询版本）"""
    return render_template('lounge_polling.html')


if __name__ == '__main__':
    import os
    from storage_sqlite import DB_PATH
    
    print("\n" + "="*60, flush=True)
    print("[启动] 使用 SQLite 本地数据库", flush=True)
    print(f"[启动] 数据库路径: {DB_PATH}", flush=True)
    print("[启动] 情感客厅使用短轮询方案（无需 WebSocket）", flush=True)
    print("="*60 + "\n", flush=True)
    
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=7860)

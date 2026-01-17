# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, session, Response, stream_with_context
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from storage import User, Relationship, CoachChat, LoungeChat
from datetime import datetime, timedelta
import secrets
import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

app.config['JSON_AS_ASCII'] = False  # 支持中文 JSON 响应


CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Coze API 配置
COZE_API_URL = "https://api.coze.cn/v3/chat"
COZE_API_KEY = os.getenv("COZE_API_KEY", "")
COZE_BOT_ID_COACH = os.getenv("COZE_BOT_ID_COACH", "")
COZE_BOT_ID_LOUNGE = os.getenv("COZE_BOT_ID_LOUNGE", "")

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

        # 保存调试信息
        debug_info = {
            "completed_content": completed_content,
            "final_content": final_content,
            "content_length": len(final_content) if final_content else 0
        }
        with open('coze_debug.json', 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, ensure_ascii=False, indent=2)

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

    if not phone or not password:
        return jsonify({'success': False, 'message': '手机号和密码不能为空'}), 400

    # 检查用户是否已存在
    existing_users = User.filter(phone=phone)
    if existing_users:
        return jsonify({'success': False, 'message': '该手机号已注册'}), 400

    # 创建新用户
    user = User(phone=phone, password=password)
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
            'phone': user.phone  # 用于显示昵称
        }
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

    # 停用关系
    relationships = Relationship.filter(
        user1_id=min(user.id, partner.id),
        user2_id=max(user.id, partner.id)
    )
    if relationships:
        relationship = relationships[0]
        relationship.is_active = False
        relationship.save()

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

    # 恢复关系
    relationships = Relationship.filter(
        user1_id=min(user.id, partner.id),
        user2_id=max(user.id, partner.id)
    )
    if relationships:
        relationship = relationships[0]
        relationship.is_active = True
        relationship.save()

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


@app.route('/api/coach/chat/stream', methods=['POST'])
def coach_chat_stream():
    """个人教练流式聊天 - 实时推送思考过程和正文"""
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

    # 获取历史对话（最近5条）
    all_history = CoachChat.filter(user_id=user_id)
    all_history.sort(key=lambda x: x.created_at, reverse=True)
    history = all_history[:5]
    conversation_history = [{"role": msg.role, "content": msg.content} for msg in reversed(history)]

    def generate():
        """流式生成器"""
        if not COZE_API_KEY or not COZE_BOT_ID_COACH:
            yield f"data: {json.dumps({'type': 'error', 'content': 'AI 服务未配置'}, ensure_ascii=False)}\n\n"
            return

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

            response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=60, stream=True)
            response.raise_for_status()

            current_event = None
            final_content = ""
            reasoning_content = ""

            for line in response.iter_lines():
                if line:
                    try:
                        line_text = line.decode('utf-8')

                        # 处理 event: 行
                        if line_text.startswith('event:'):
                            current_event = line_text[6:].strip()
                            continue

                        # 处理 data: 行
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

                            role = data.get('role')
                            msg_type_field = data.get('type')

                            # 处理流式内容 (delta 事件)
                            if current_event == 'conversation.message.delta' and role == 'assistant' and msg_type_field == 'answer':
                                # 思考过程 (reasoning_content)
                                reasoning = data.get('reasoning_content', '')
                                if reasoning:
                                    reasoning_content += reasoning
                                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning}, ensure_ascii=False)}\n\n"

                                # 正文内容 (content)
                                content = data.get('content', '')
                                if content:
                                    final_content += content
                                    yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"

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

            # 保存 AI 回复到存储（包含思考过程）
            if final_content:
                ai_msg = CoachChat(
                    user_id=user_id, 
                    role='assistant', 
                    content=final_content,
                    reasoning_content=reasoning_content if reasoning_content else None
                )
                ai_msg.save()

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


# ==================== WebSocket 实时通信 ====================
@socketio.on('join_lounge')
def handle_join_lounge(data):
    """加入情感客厅房间"""
    room_id = data.get('room_id')
    user_id = data.get('user_id')

    join_room(room_id)
    emit('user_joined', {'user_id': user_id}, room=room_id)


@socketio.on('send_message')
def handle_send_message(data):
    """发送消息到情感客厅"""
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    content = data.get('content')

    # 保存消息
    msg = LoungeChat(room_id=room_id, user_id=user_id, role='user', content=content)
    msg.save()

    # 广播消息，并告知前端是否需要触发 AI
    is_calling_ai = '@AI' in content or '@ai' in content or '@教练' in content
    emit('new_message', {**msg.to_dict(), 'trigger_ai': is_calling_ai}, room=room_id)


@socketio.on('call_ai')
def handle_call_ai(data):
    """召唤 AI 助手（流式输出）"""
    room_id = data.get('room_id')

    # 获取最近的对话记录（最近10条）
    all_history = LoungeChat.filter(room_id=room_id)
    all_history.sort(key=lambda x: x.created_at, reverse=True)
    history = all_history[:10]

    # 构建对话历史（排除 AI 的回复，只保留用户对话）
    latest_message = ""
    for msg in reversed(history):
        if msg.role == "user":
            latest_message += f"{msg.content}\n"

    # 如果没有对话记录，返回提示
    if not latest_message.strip():
        ai_reply = "暂时没有对话内容可供分析哦～"
        ai_msg = LoungeChat(room_id=room_id, user_id=None, role='assistant', content=ai_reply)
        ai_msg.save()
        emit('ai_stream', {'type': 'delta', 'content': ai_reply}, room=room_id)
        emit('ai_stream', {'type': 'done'}, room=room_id)
        return

    # 使用流式 API 调用
    if not COZE_API_KEY or not COZE_BOT_ID_LOUNGE:
        ai_reply = "AI 服务未配置"
        ai_msg = LoungeChat(room_id=room_id, user_id=None, role='assistant', content=ai_reply)
        ai_msg.save()
        emit('ai_stream', {'type': 'delta', 'content': ai_reply}, room=room_id)
        emit('ai_stream', {'type': 'done'}, room=room_id)
        return

    try:
        headers = {
            'Authorization': f'Bearer {COZE_API_KEY}',
            'Content-Type': 'application/json'
        }

        messages = [{
            "role": "user",
            "content": "请基于以上对话内容，作为情感调解专家，提供建设性的沟通建议，帮助双方理解彼此：\n" + latest_message,
            "content_type": "text",
            "type": "question"
        }]

        payload = {
            "bot_id": COZE_BOT_ID_LOUNGE,
            "user_id": room_id,
            "stream": True,
            "auto_save_history": True,
            "additional_messages": messages
        }

        response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=60, stream=True)
        response.raise_for_status()

        current_event = None
        final_content = ""

        for line in response.iter_lines():
            if line:
                try:
                    line_text = line.decode('utf-8')

                    # 处理 event: 行
                    if line_text.startswith('event:'):
                        current_event = line_text[6:].strip()
                        continue

                    # 处理 data: 行
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

                        role = data.get('role')
                        msg_type_field = data.get('type')

                        # 处理流式内容 (delta 事件)
                        if current_event == 'conversation.message.delta' and role == 'assistant' and msg_type_field == 'answer':
                            content = data.get('content', '')
                            if content:
                                final_content += content
                                # 流式推送到前端
                                emit('ai_stream', {'type': 'delta', 'content': content}, room=room_id)
                                socketio.sleep(0)  # 让出控制权，确保消息及时发送

                        # 处理完成事件
                        elif current_event == 'conversation.message.completed' and role == 'assistant':
                            if msg_type_field == 'answer':
                                # 流式结束信号
                                emit('ai_stream', {'type': 'done'}, room=room_id)

                except Exception as e:
                    print(f"[Lounge Stream Error] {e}", flush=True)
                    continue

        # 保存 AI 消息到存储
        if final_content:
            ai_msg = LoungeChat(room_id=room_id, user_id=None, role='assistant', content=final_content)
            ai_msg.save()
        else:
            # 如果没有收到内容，发送默认消息
            ai_reply = "AI 未返回有效回复，请稍后重试"
            ai_msg = LoungeChat(room_id=room_id, user_id=None, role='assistant', content=ai_reply)
            ai_msg.save()
            emit('ai_stream', {'type': 'delta', 'content': ai_reply}, room=room_id)
            emit('ai_stream', {'type': 'done'}, room=room_id)

    except Exception as e:
        print(f"[Lounge AI Error] {e}", flush=True)
        ai_reply = f"AI 调用失败: {str(e)}"
        ai_msg = LoungeChat(room_id=room_id, user_id=None, role='assistant', content=ai_reply)
        ai_msg.save()
        emit('ai_stream', {'type': 'delta', 'content': ai_reply}, room=room_id)
        emit('ai_stream', {'type': 'done'}, room=room_id)


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
    """情感客厅"""
    return render_template('lounge.html')


if __name__ == '__main__':
    import os
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=7860, allow_unsafe_werkzeug=True)

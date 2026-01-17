# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models_fa import SessionLocal, User, Relationship, CoachChat, LoungeChat
from datetime import datetime, timedelta
import secrets
import os
import requests
from dotenv import load_dotenv
from typing import Optional
import json
from pydantic import BaseModel

# 加载环境变量
load_dotenv()

app = FastAPI(title="情感陪伴助手")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Coze API 配置
COZE_API_URL = "https://api.coze.cn/v3/chat"
COZE_API_KEY = os.getenv("COZE_API_KEY", "")
COZE_BOT_ID_COACH = os.getenv("COZE_BOT_ID_COACH", "")
COZE_BOT_ID_LOUNGE = os.getenv("COZE_BOT_ID_LOUNGE", "")

# Session 存储 (简单内存存储，生产环境应使用 Redis)
session_storage = {}

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Session 依赖
def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in session_storage:
        return None
    user_id = session_storage[session_id]
    return db.query(User).filter(User.id == user_id).first()

# Pydantic 模型
class LoginRequest(BaseModel):
    phone: str
    password: str

class RegisterRequest(BaseModel):
    phone: str
    password: str

class BindRequest(BaseModel):
    binding_code: str

class ChatRequest(BaseModel):
    message: str

# Coze API 调用函数
async def call_coze_api_stream(user_phone: str, message: str, bot_id: str, conversation_history=None):
    """调用 Coze API (流式)"""
    if not COZE_API_KEY or not bot_id:
        return "AI 服务未配置"

    try:
        headers = {
            'Authorization': f'Bearer {COZE_API_KEY}',
            'Content-Type': 'application/json'
        }

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

        response = requests.post(COZE_API_URL, headers=headers, json=payload, stream=True, timeout=30)
        response.raise_for_status()

        # 处理流式响应
        full_content = ""
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                print(f"[Coze Stream] {line_text}", flush=True)

                if line_text.startswith('data:'):
                    try:
                        json_str = line_text[5:].strip()
                        if json_str == '[DONE]':
                            break

                        data = json.loads(json_str)
                        event = data.get('event')

                        if event == 'message':
                            # 提取消息内容
                            message_data = data.get('message', {})
                            if message_data.get('role') == 'assistant':
                                content = message_data.get('content', '')
                                full_content += content

                        elif event == 'conversation.message.completed':
                            # 消息完成
                            message_data = data.get('message', {})
                            if message_data.get('role') == 'assistant':
                                full_content = message_data.get('content', '')

                    except json.JSONDecodeError as e:
                        print(f"[Coze API] JSON 解析错误: {e}", flush=True)
                        continue

        print(f"[Coze API] 完整回复: {full_content}", flush=True)
        print(f"{'='*60}\n", flush=True)

        if full_content:
            return full_content
        else:
            return "AI 未返回有效回复"

    except requests.exceptions.Timeout:
        return "AI 响应超时"
    except Exception as e:
        print(f"[Coze API] 错误: {str(e)}", flush=True)
        return f"AI 调用失败: {str(e)}"

# ==================== 前端路由 ====================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/coach", response_class=HTMLResponse)
async def coach(request: Request):
    return templates.TemplateResponse("coach.html", {"request": request})

@app.get("/lounge", response_class=HTMLResponse)
async def lounge(request: Request):
    return templates.TemplateResponse("lounge.html", {"request": request})

# ==================== 用户认证 API ====================
@app.post("/api/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone == req.phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该手机号已注册")

    user = User(phone=req.phone, password=req.password)
    user.generate_binding_code()
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"success": True, "message": "注册成功", "user": user.to_dict()}

@app.post("/api/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == req.phone, User.password == req.password).first()
    if not user:
        raise HTTPException(status_code=401, detail="手机号或密码错误")

    session_id = secrets.token_hex(32)
    session_storage[session_id] = user.id

    response = JSONResponse({
        "success": True,
        "message": "登录成功",
        "user": user.to_dict()
    })
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

@app.post("/api/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id in session_storage:
        del session_storage[session_id]

    response = JSONResponse({"success": True, "message": "登出成功"})
    response.delete_cookie("session_id")
    return response

@app.get("/api/user/info")
async def get_user_info(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    return {"success": True, "user": user.to_dict()}

# ==================== 伴侣绑定 API ====================
@app.get("/api/binding/code")
async def get_binding_code(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    if not user.binding_code:
        user.generate_binding_code()
        db.commit()

    return {"success": True, "binding_code": user.binding_code}

@app.post("/api/binding/bind")
async def bind_partner(req: BindRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    partner = db.query(User).filter(User.binding_code == req.binding_code).first()
    if not partner:
        raise HTTPException(status_code=400, detail="绑定码无效")

    if partner.id == user.id:
        raise HTTPException(status_code=400, detail="不能绑定自己")

    if user.partner_id or partner.partner_id:
        raise HTTPException(status_code=400, detail="您或对方已有伴侣")

    user.partner_id = partner.id
    partner.partner_id = user.id

    room_id = f"room_{min(user.id, partner.id)}_{max(user.id, partner.id)}"
    relationship = Relationship(
        user1_id=min(user.id, partner.id),
        user2_id=max(user.id, partner.id),
        room_id=room_id
    )
    db.add(relationship)
    db.commit()

    return {"success": True, "message": "绑定成功！", "room_id": room_id}

@app.post("/api/binding/unbind")
async def unbind_partner(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    if not user.partner_id:
        raise HTTPException(status_code=400, detail="您还没有绑定伴侣")

    partner = db.query(User).filter(User.id == user.partner_id).first()
    unbind_time = datetime.now()
    user.unbind_at = unbind_time
    partner.unbind_at = unbind_time

    relationship = db.query(Relationship).filter(
        ((Relationship.user1_id == user.id) & (Relationship.user2_id == partner.id)) |
        ((Relationship.user1_id == partner.id) & (Relationship.user2_id == user.id))
    ).first()
    if relationship:
        relationship.is_active = False

    db.commit()

    return {"success": True, "message": "已发起解绑，1个月冷静期后生效", "unbind_at": unbind_time.isoformat()}

@app.post("/api/binding/cancel_unbind")
async def cancel_unbind(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    if not user.unbind_at:
        raise HTTPException(status_code=400, detail="没有待撤销的解绑")

    cool_down_end = user.unbind_at + timedelta(days=30)
    if datetime.now() > cool_down_end:
        raise HTTPException(status_code=400, detail="冷静期已过，无法撤销")

    partner = db.query(User).filter(User.id == user.partner_id).first()
    user.unbind_at = None
    if partner:
        partner.unbind_at = None

    relationship = db.query(Relationship).filter(
        ((Relationship.user1_id == user.id) & (Relationship.user2_id == user.partner_id)) |
        ((Relationship.user1_id == user.partner_id) & (Relationship.user2_id == user.id))
    ).first()
    if relationship:
        relationship.is_active = True

    db.commit()

    return {"success": True, "message": "已撤销解绑"}

# ==================== 个人教练聊天室 API ====================
@app.post("/api/coach/chat")
async def coach_chat(req: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    if not req.message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 保存用户消息
    user_msg = CoachChat(user_id=user.id, role='user', content=req.message)
    db.add(user_msg)

    # 获取历史对话
    history = db.query(CoachChat).filter(CoachChat.user_id == user.id).order_by(CoachChat.created_at.desc()).limit(5).all()
    conversation_history = [{"role": msg.role, "content": msg.content} for msg in reversed(history)]

    # 调用 Coze API
    ai_reply = await call_coze_api_stream(
        user_phone=user.phone,
        message=req.message,
        bot_id=COZE_BOT_ID_COACH,
        conversation_history=conversation_history[:-1] if conversation_history else None
    )

    # 保存 AI 回复
    ai_msg = CoachChat(user_id=user.id, role='assistant', content=ai_reply)
    db.add(ai_msg)
    db.commit()

    return {"success": True, "message": ai_reply}

@app.get("/api/coach/history")
async def get_coach_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    history = db.query(CoachChat).filter(CoachChat.user_id == user.id).order_by(CoachChat.created_at).all()
    return {"success": True, "messages": [msg.to_dict() for msg in history]}

# ==================== 情感客厅 API ====================
@app.get("/api/lounge/room")
async def get_lounge_room(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    if not user.partner_id:
        raise HTTPException(status_code=400, detail="您还没有绑定伴侣")

    relationship = db.query(Relationship).filter(
        ((Relationship.user1_id == user.id) | (Relationship.user2_id == user.id)) &
        (Relationship.is_active == True)
    ).first()

    if not relationship:
        raise HTTPException(status_code=404, detail="未找到有效的关系")

    return {"success": True, "room_id": relationship.room_id}

@app.get("/api/lounge/history")
async def get_lounge_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    relationship = db.query(Relationship).filter(
        (Relationship.user1_id == user.id) | (Relationship.user2_id == user.id)
    ).first()

    if not relationship:
        raise HTTPException(status_code=404, detail="未找到房间")

    history = db.query(LoungeChat).filter(LoungeChat.room_id == relationship.room_id).order_by(LoungeChat.created_at).all()
    return {"success": True, "messages": [msg.to_dict() for msg in history]}

# ==================== WebSocket ====================
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

@app.websocket("/ws/lounge/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, db: Session = Depends(get_db)):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")

            if event == "send_message":
                user_id = data.get("user_id")
                content = data.get("content")

                msg = LoungeChat(room_id=room_id, user_id=user_id, role='user', content=content)
                db.add(msg)
                db.commit()
                db.refresh(msg)

                await manager.broadcast({
                    "event": "new_message",
                    "message": msg.to_dict()
                }, room_id)

            elif event == "call_ai":
                history = db.query(LoungeChat).filter(LoungeChat.room_id == room_id).order_by(LoungeChat.created_at.desc()).limit(10).all()
                conversation_history = []
                latest_message = ""

                for msg in reversed(history):
                    if msg.role == "user":
                        latest_message += f"{msg.content}\n"
                        conversation_history.append({"role": "user", "content": msg.content})

                if not latest_message.strip():
                    ai_reply = "暂时没有对话内容可供分析哦～"
                else:
                    ai_reply = await call_coze_api_stream(
                        user_phone=room_id,
                        message="请基于以上对话内容，作为情感调解专家，提供建设性的沟通建议：\n" + latest_message,
                        bot_id=COZE_BOT_ID_LOUNGE,
                        conversation_history=None
                    )

                ai_msg = LoungeChat(room_id=room_id, user_id=None, role='assistant', content=ai_reply)
                db.add(ai_msg)
                db.commit()
                db.refresh(ai_msg)

                await manager.broadcast({
                    "event": "new_message",
                    "message": ai_msg.to_dict()
                }, room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

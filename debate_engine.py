"""
辩论引擎API模块
Debate Engine API Module
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1/debate", tags=["debate"])

# 数据模型
class DebateSession(BaseModel):
    session_id: str
    topic: str
    position: str  # 'pro' or 'con'
    created_at: datetime
    status: str = "active"
    arguments: List = []

class Argument(BaseModel):
    argument_id: str
    session_id: str
    content: str
    author: str
    type: str  # 'opening', 'argument', 'rebuttal', 'closing'
    created_at: datetime

class Rebuttal(BaseModel):
    rebuttal_id: str
    argument_id: str
    content: str
    author: str
    created_at: datetime

# 内存存储
debate_sessions = {}

@router.post("/start")
async def start_debate(topic: str, position: str):
    """发起辩论"""
    if position not in ['pro', 'con']:
        raise HTTPException(status_code=400, detail="position must be 'pro' or 'con'")
    
    session_id = f"debate_{uuid.uuid4().hex[:8]}"
    session = DebateSession(
        session_id=session_id,
        topic=topic,
        position=position,
        created_at=datetime.now(),
        status="active",
        arguments=[]
    )
    debate_sessions[session_id] = session
    return {
        "status": "success",
        "session_id": session_id,
        "topic": topic,
        "position": position
    }

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取辩论详情"""
    if session_id not in debate_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return debate_sessions[session_id]

@router.post("/argument")
async def add_argument(session_id: str, content: str, author: str = "AI", argument_type: str = "argument"):
    """添加论点"""
    if session_id not in debate_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    argument_id = f"arg_{uuid.uuid4().hex[:8]}"
    argument = Argument(
        argument_id=argument_id,
        session_id=session_id,
        content=content,
        author=author,
        type=argument_type,
        created_at=datetime.now()
    )
    debate_sessions[session_id].arguments.append(argument)
    return {
        "status": "success",
        "argument_id": argument_id
    }

@router.get("/list")
async def list_debates():
    """列出所有辩论"""
    return {
        "total": len(debate_sessions),
        "sessions": list(debate_sessions.values())
    }

@router.post("/close/{session_id}")
async def close_debate(session_id: str):
    """结束辩论"""
    if session_id not in debate_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    debate_sessions[session_id].status = "closed"
    return {"status": "success", "session_id": session_id}

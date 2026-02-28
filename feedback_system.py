"""
用户反馈系统模块
设计v1.0
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

# 数据模型
class Feedback(BaseModel):
    id: str
    user_id: str
    type: str  # 'bug', 'feature', 'general'
    content: str
    contact: Optional[str] = None
    status: str = "pending"  # pending, reviewing, resolved, rejected
    created_at: datetime
    updated_at: datetime
    response: Optional[str] = None

# 内存存储
feedbacks = {}

@router.post("/submit")
async def submit_feedback(
    user_id: str,
    feedback_type: str,
    content: str,
    contact: Optional[str] = None
):
    """提交反馈"""
    feedback_id = f"fb_{uuid.uuid4().hex[:8]}"
    now = datetime.now()
    feedback = Feedback(
        id=feedback_id,
        user_id=user_id,
        type=feedback_type,
        content=content,
        contact=contact,
        status="pending",
        created_at=now,
        updated_at=now
    )
    feedbacks[feedback_id] = feedback
    return {"status": "success", "id": feedback_id}

@router.get("/list")
async def list_feedbacks(status: Optional[str] = None):
    """列出反馈"""
    if status:
        return {"list": [f for f in feedbacks.values() if f.status == status]}
    return {"list": list(feedbacks.values())}

@router.get("/{feedback_id}")
async def get_feedback(feedback_id: str):
    """获取反馈详情"""
    if feedback_id not in feedbacks:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedbacks[feedback_id]

@router.put("/{feedback_id}/respond")
async def respond_feedback(feedback_id: str, response: str):
    """回复反馈"""
    if feedback_id not in feedbacks:
        raise HTTPException(status_code=404, detail="Feedback not found")
    feedbacks[feedback_id].response = response
    feedbacks[feedback_id].status = "resolved"
    feedbacks[feedback_id].updated_at = datetime.now()
    return {"status": "success"}

@router.put("/{feedback_id}/status")
async def update_status(feedback_id: str, status: str):
    """更新状态"""
    if feedback_id not in feedbacks:
        raise HTTPException(status_code=404, detail="Feedback not found")
    feedbacks[feedback_id].status = status
    feedbacks[feedback_id].updated_at = datetime.now()
    return {"status": "success"}

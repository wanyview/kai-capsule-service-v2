#!/usr/bin/env python3
"""
反馈系统 API 服务
"""
from fastapi import FastAPI, Query
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import uuid

app = FastAPI(title="反馈系统 API", version="1.0.0")

FEEDBACK_DB = "/Users/wanyview/clawd/capsule_service_v2/feedback.db"

def init_db():
    conn = sqlite3.connect(FEEDBACK_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'suggestion',
            contact TEXT,
            status TEXT DEFAULT 'pending',
            reply TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

class FeedbackRequest(BaseModel):
    content: str
    type: str = "suggestion"
    contact: str = None

class FeedbackReply(BaseModel):
    reply: str

class FeedbackStatus(BaseModel):
    status: str

@app.post("/api/v1/feedback")
async def submit_feedback(request: FeedbackRequest):
    fid = f"fb_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    now = datetime.now().isoformat()
    conn = sqlite3.connect(FEEDBACK_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (fid, request.content, request.type, request.contact, "pending", None, now, now)
    )
    conn.commit()
    conn.close()
    return {"id": fid, "status": "pending", "message": "反馈已提交"}

@app.get("/api/v1/feedback")
async def list_feedback(
    status: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    conn = sqlite3.connect(FEEDBACK_DB)
    cursor = conn.cursor()
    query = "SELECT * FROM feedback WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    cursor.execute(query + " ORDER BY created_at DESC", params)
    all_feedback = cursor.fetchall()
    conn.close()
    offset = (page - 1) * limit
    return {
        "feedback": [
            {"id": f[0], "content": f[1], "type": f[2], "status": f[4], "created_at": f[6]}
            for f in all_feedback[offset:offset+limit]
        ],
        "total": len(all_feedback)
    }

@app.post("/api/v1/feedback/{fid}/reply")
async def reply_feedback(fid: str, request: FeedbackReply):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(FEEDBACK_DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE feedback SET reply = ?, updated_at = ? WHERE id = ?", (request.reply, now, fid))
    conn.commit()
    conn.close()
    return {"message": "回复成功"}

if __name__ == "__main__":
    import uvicorn
    print("反馈系统 API 启动中... 端口: 8006")
    uvicorn.run(app, host="0.0.0.0", port=8006)

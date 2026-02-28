# 反馈系统 API

## 接口列表

### 1. 提交反馈
POST /api/v1/feedback
```json
{
  "content": "用户反馈内容",
  "type": "bug|feature|suggestion",
  "contact": "联系方式(可选)"
}
```

### 2. 获取反馈列表
GET /api/v1/feedback?status=pending&page=1&limit=10

### 3. 回复反馈
POST /api/v1/feedback/{id}/reply
```json
{
  "reply": "回复内容"
}
```

### 4. 更新反馈状态
PATCH /api/v1/feedback/{id}
```json
{
  "status": "resolved|ignored"
}
```

## 状态码
- pending: 待处理
- resolved: 已解决
- ignored: 已忽略

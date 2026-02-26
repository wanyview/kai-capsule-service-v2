# CAPSULE_TOKEN.md - 知识胶囊Token系统

> 版本: 1.0
> 更新时间: 2026-02-26

## 概述

知识胶囊Token系统用于管理胶囊的访问权限、同步状态和跨平台认证。

## Token结构

```json
{
  "token_id": "tok_xxxxx",
  "capsule_id": "capsule_xxxxx",
  "type": "read" | "write" | "sync",
  "platform": "kaihub" | "matrix" | "external",
  "permissions": ["pull", "push", "delete"],
  "expires_at": "2026-03-01T00:00:00Z",
  "created_by": "kai",
  "created_at": "2026-02-26T00:00:00Z"
}
```

## Token类型

| 类型 | 权限 | 用途 |
|------|------|------|
| read | 读取胶囊 | 外部系统拉取 |
| write | 写入胶囊 | 外部系统推送 |
| sync | 同步权限 | 双向同步 |

## API端点

### 创建Token

```http
POST /api/v1/token/create
Authorization: Bearer <admin_token>

{
  "capsule_id": "capsule_001",
  "type": "read",
  "platform": "matrix",
  "expires_in_days": 30
}
```

### 验证Token

```http
POST /api/v1/token/validate
Authorization: Bearer <token>

{
  "capsule_id": "capsule_001",
  "action": "pull"
}
```

### 撤销Token

```http
POST /api/v1/token/revoke
Authorization: Bearer <admin_token>

{
  "token_id": "tok_xxxxx"
}
```

## 跨平台对接

### 附中矩阵 Token 流程

1. **申请Token**: 附中矩阵向KaiHub申请API Token
2. **验证通过**: KaiHub管理员审批并生成Token
3. **使用Token**: 附中矩阵在请求头中携带Token
4. **自动续期**: Token过期前自动提示续期

### 请求示例

```bash
# 拉取胶囊
curl -X POST http://kaihub:8005/api/v1/capsule/pull \
  -H "Authorization: Bearer tok_matrix_001" \
  -H "Content-Type: application/json" \
  -d '{"domain": "ai", "limit": 10}'

# 推送胶囊
curl -X POST http://kaihub:8005/api/v1/capsule/sync \
  -H "Authorization: Bearer tok_matrix_001" \
  -H "Content-Type: application/json" \
  -d '{"title": "新胶囊", "content": "..."}'
```

## 安全考虑

- Token有效期最长90天
- 支持IP白名单限制
- 记录所有Token使用日志
- 异常访问自动封禁

## 错误码

| 错误码 | 说明 |
|--------|------|
| 401 | Token无效或已过期 |
| 403 | 权限不足 |
| 404 | 胶囊不存在 |
| 429 | 请求频率超限 |

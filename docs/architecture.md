# 合同管理系统-评测 当前架构

## 系统目标与边界

合同管理系统-评测 (contract-mgmt-eval) 是一个基于 Web 的合同全生命周期管理演示系统，覆盖用户认证、角色权限管理、合同 CRUD 与状态流转、附件管理、操作审计日志五大核心功能模块。

**边界**: 本地演示系统，不含 OAuth/SSO/LDAP 集成，不含真实合同数据，不含在线支付或电子签章。

## 技术栈与选择理由

| 层 | 技术 | 理由 |
|---|---|---|
| 前端 | React 18 + TypeScript | 类型安全，组件化开发，生态成熟 |
| 构建 | Vite 5 | 快速 HMR，原生 TS 支持，构建产物小 |
| 路由 | React Router v6 | 声明式路由，支持 basename 配置 |
| HTTP | Axios 1.x | 拦截器支持 JWT 自动注入 |
| 状态管理 | React Context + useReducer | 仅管理认证状态，无需引入 Redux |
| 后端 | Python 3.11+ FastAPI | 异步高性能，自动 OpenAPI 文档，Pydantic 校验 |
| ORM | SQLAlchemy 2.x | Python ORM 标准，支持 SQLite/PostgreSQL |
| 数据库 | SQLite | 零配置，适合演示和开发 |
| 认证 | python-jose + passlib[bcrypt] | JWT HS256 + bcrypt 密码哈希 |
| 部署 | Uvicorn + Nginx | ASGI server + 反向代理 |

## 模块职责与依赖

### 审计日志 (v0.0.2 新增)

- **后端**: `middleware/audit.py` 提供 `AuditLogger` 依赖注入类，从 Request 提取客户端真实 IP（优先 X-Real-IP → X-Forwarded-For 首个非内网 IP → request.client.host）。独立于 `get_current_user`，仅依赖 `Request`。
- **后端**: `services/audit_log_service.py` — 审计日志只读查询，JOIN users 表获取 username，支持按 action/user_search/user_id/date range 筛选，按 created_at DESC 分页。
- **后端**: `routers/audit_logs.py` — `GET /api/audit-logs` 端点，仅 admin 可访问。
- **前端**: `pages/AuditLogPage.tsx` — 审计日志页面（筛选栏 + 表格 + 分页），仅 admin 可见。
- **IP 获取**: 兼容链 X-Real-IP → X-Forwarded-For (首个非内网) → request.client.host。
- **数据库**: AuditLog 表新增 `ip_address` VARCHAR(45) 字段，通过幂等迁移函数自动添加。

### 前端模块

```
frontend/src/
├── api/          API 调用层，封装 Axios 请求，对应后端各 router
├── components/   可复用 UI 组件 (Layout, Navbar, ProtectedRoute, Pagination, etc.)
├── contexts/     全局状态 (AuthContext: user, token, login/logout)
├── pages/        页面组件，每个路由对应一个页面
├── types/        全局 TypeScript 类型定义
└── utils/        工具函数
```

依赖方向: pages → api + contexts + components → types

### 后端模块

```
backend/app/
├── routers/      HTTP 层：接收请求、参数校验、调用 service、返回响应
├── services/     业务逻辑层：认证、授权、状态流转、数据校验
├── models/       SQLAlchemy ORM 模型定义
├── schemas/      Pydantic 请求/响应 schema
├── middleware/   认证中间件 (JWT 解析、角色检查)
└── utils/        工具函数 (密码哈希、JWT 签发、审计日志)
```

依赖方向: routers → services → models (SQLAlchemy session)
            routers → schemas
            routers → middleware (Depends 注入)

## 数据流、状态流与外部接口

### 认证数据流

```
Browser                    FastAPI                    Database
  │                          │                          │
  │  POST /api/auth/login    │                          │
  │  {username, password}    │                          │
  │ ─────────────────────────>                          │
  │                          │  SELECT user BY username │
  │                          │ ─────────────────────────>
  │                          │  <── user + password_hash│
  │                          │  verify_password()       │
  │                          │  create_access_token()   │
  │  <── {access_token}      │                          │
  │                          │                          │
  │  GET /api/contracts      │                          │
  │  Authorization: Bearer X │                          │
  │ ─────────────────────────>                          │
  │                          │  get_current_user()      │
  │                          │  decode JWT → user_id    │
  │                          │  <── user (active?)       │
  │                          │  SELECT contracts        │
  │                          │ ─────────────────────────>
  │  <── [contracts...]      │  <── rows                │
```

### 合同状态流转

```
              ┌──────────────┐
              │    draft     │
              └──────┬───────┘
                     │ activate (sign_date required)
                     ▼
              ┌──────────────┐
         ┌─── │    active    │ ───┐
         │    └──────────────┘    │
         │ terminate              │ expire
         ▼                        ▼
  ┌──────────────┐        ┌──────────────┐
  │  terminated  │        │   expired    │
  └──────────────┘        └──────────────┘
     (终态)                   (终态)
```

### 角色权限矩阵

| 操作 | admin | user | 未认证 |
|------|-------|------|--------|
| 注册/登录/密码重置 | ✓ | ✓ | ✓ |
| 查看个人信息 | ✓ | ✓ | ✗ |
| 用户管理 CRUD | ✓ | ✗ | ✗ |
| 查看合同列表 | ✓ (全部) | ✓ (本人) | ✗ |
| 创建合同 | ✓ | ✓ | ✗ |
| 编辑/删除合同 | ✓ (全部) | ✓ (本人) | ✗ |
| 合同状态流转 | ✓ (全部) | ✓ (本人) | ✗ |
| 附件上传/下载/删除 | ✓ | ✓ (本人合同) | ✗ |

### API Endpoints 总览

| 方法 | 路径 | 认证 | 角色 | 描述 |
|------|------|------|------|------|
| POST | /api/auth/register | ✗ | - | 注册 |
| POST | /api/auth/login | ✗ | - | 登录 |
| POST | /api/auth/logout | ✗ | - | 登出 |
| POST | /api/auth/password-reset | ✗ | - | 密码重置 |
| GET | /api/users | ✓ | admin | 用户列表 |
| POST | /api/users | ✓ | admin | 创建用户 |
| GET | /api/users/me | ✓ | - | 当前用户 |
| GET | /api/users/{id} | ✓ | admin | 用户详情 |
| PUT | /api/users/{id} | ✓ | admin | 更新用户 |
| PATCH | /api/users/{id}/status | ✓ | admin | 启用/禁用 |
| GET | /api/contracts | ✓ | - | 合同列表 (搜索/筛选/分页) |
| POST | /api/contracts | ✓ | - | 创建合同 |
| GET | /api/contracts/{id} | ✓ | - | 合同详情 |
| PUT | /api/contracts/{id} | ✓ | - | 更新合同 |
| DELETE | /api/contracts/{id} | ✓ | - | 删除合同 |
| PATCH | /api/contracts/{id}/status | ✓ | - | 状态流转 |
| POST | /api/contracts/{id}/attachments | ✓ | - | 上传附件 |
| GET | /api/contracts/{id}/attachments | ✓ | - | 附件列表 |
| GET | /api/attachments/{id}/download | ✓ | - | 下载附件 |
| DELETE | /api/attachments/{id} | ✓ | - | 删除附件 |
| GET | /api/audit-logs | ✓ | admin | 审计日志列表 (筛选+分页) |
| GET | /healthz | ✗ | - | 健康检查 |

## 测试策略

### 后端测试 (pytest)
- **单元测试**: service 层业务逻辑，使用 mock 隔离数据库
- **集成测试**: API 端点完整流程，使用 TestClient + 内存 SQLite
- **覆盖目标**: 认证模块、用户管理 CRUD、合同 CRUD + 状态流转、附件上传/下载/删除、权限边界
- **测试数据**: 每个测试函数独立创建 fixture 数据，不依赖种子数据

### 前端验证
- 功能验证 checklist：逐流程手动走查
- 浏览器 DevTools 检查网络请求和状态管理

### 自测脚本
- 后端: `cd backend && python -m pytest tests/ -v`
- 自测输出保存到 `evidence/claude/self-test-0.0.1.txt`

## 部署拓扑

```
                    Nginx :80
                       │
          /projects/contract-mgmt-eval/
                       │
                 proxy_pass
                       │
              Uvicorn :19006
                       │
            ┌──────────┴──────────┐
            │                     │
     FastAPI (API)        FastAPI (Static)
     /api/*               mount frontend/dist/
            │
       SQLite DB
    backend/contract_mgmt.db
```

- **Base Path**: `/projects/contract-mgmt-eval/`
- **公网 URL**: http://120.24.117.67/projects/contract-mgmt-eval/
- **Health Check**: GET `/projects/contract-mgmt-eval/healthz` → `{"status":"ok"}`
- **启动命令**: `uvicorn app.main:app --host 0.0.0.0 --port 19006 --root-path /projects/contract-mgmt-eval`

## 安全边界

- **认证**: JWT HS256，24h 过期，token 存储在 localStorage
- **密码**: bcrypt 12 rounds，不存储明文
- **权限**: Depends 注入 get_current_user / require_admin，service 层二次校验资源归属
- **文件上传**: 扩展名 + MIME type 双重校验，UUID 重命名存储，10MB 大小限制
- **审计日志**: 关键操作写入 AuditLog 表 (user.login, contract.create, attachment.upload 等)
- **CORS**: 演示环境允许所有来源，生产环境需限制
- **SQLite**: 单文件数据库，PRAGMA foreign_keys = ON 确保引用完整性

## 已知技术债

- 无 Alembic 迁移：演示阶段使用 create_all，后续需引入 Alembic
- 无 refresh token 机制：token 过期需重新登录
- 密码重置为演示版直接返回新密码：生产环境需邮件验证链接
- 附件预览仅支持浏览器原生支持的格式 (PDF)
- 无 WebSocket 实时通知
- 无国际化 (i18n)

## 关联 ADR 与最近变更

- 2026-06-18: iteration/0.0.1 启动，初版架构确立
- 2026-06-18: iteration/0.0.2 — 操作审计日志模块，新增 `GET /api/audit-logs` API、`AuditLogger` 依赖注入、前端审计日志页面
- ADR-002: 审计日志记录方式 — FastAPI 依赖注入 (`docs/decisions/ADR-002-审计日志记录方式.md`)
- ADR-003: 客户端 IP 获取策略 — 三层兼容链 (`docs/decisions/ADR-003-客户端IP获取策略.md`)
- ADR-004: 数据库迁移策略 — 手动幂等 ALTER TABLE (`docs/decisions/ADR-004-数据库迁移策略.md`)

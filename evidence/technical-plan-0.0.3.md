# Technical Plan — 0.0.3 合同模板功能

## 概述

为合同管理系统新增合同模板功能。管理员可创建、编辑、删除（软删除）合同模板；用户创建合同时可从模板下拉选择快速填充字段。

### 来源事件

- **owner_input**: e000031 (2026-06-18T12:20:41Z)
- **hermes item_added**: e000032 (iteration=0.0.3)

---

## 1. 业务模型

### 1.1 ContractTemplate 实体

新增 `contract_templates` 表：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| name | VARCHAR(200) | NOT NULL | 模板名称 |
| category | VARCHAR(100) | NOT NULL, DEFAULT '' | 分类标签（如"采购合同"、"服务合同"） |
| party_a_default | VARCHAR(200) | NULL | 甲方默认值 |
| party_b_default | VARCHAR(200) | NULL | 乙方默认值 |
| content | TEXT | NOT NULL, DEFAULT '' | 合同正文模板，支持 `{{变量}}` 占位符 |
| amount_min | FLOAT | NULL | 预设金额范围下限 |
| amount_max | FLOAT | NULL | 预设金额范围上限 |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT FALSE | 软删除标记 |
| created_by | INTEGER | FK → users.id, NOT NULL | 创建者 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 最后更新时间 |

### 1.2 占位符格式

- 格式: `{{变量名}}`
- 常用占位符: `{{甲方}}`, `{{乙方}}`, `{{金额}}`, `{{日期}}`, `{{合同编号}}`
- 创建合同时，系统将模板正文中的占位符替换为合同表单实际值

---

## 2. API 设计

### 2.1 模板管理 API（管理员专属）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/templates | 模板列表（支持搜索/分页，不含已软删除） |
| POST | /api/templates | 创建模板 |
| GET | /api/templates/{id} | 模板详情 |
| PUT | /api/templates/{id} | 更新模板 |
| DELETE | /api/templates/{id} | 软删除模板 |

### 2.2 模板下拉 API（所有登录用户）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/templates/dropdown | 获取可用模板列表（id, name, category），供「从模板创建」下拉使用 |

### 2.3 权限要求

- 模板 CRUD: 仅 admin
- 模板下拉: 所有已认证用户

---

## 3. 后端实施

### 3.1 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/models/template.py` | 新建 | ContractTemplate ORM 模型 |
| `backend/app/models/__init__.py` | 修改 | 导出 ContractTemplate |
| `backend/app/schemas/template.py` | 新建 | Pydantic schema（TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse, TemplateDropdownItem） |
| `backend/app/services/template_service.py` | 新建 | 模板业务逻辑（CRUD + 软删除 + 占位符替换） |
| `backend/app/routers/templates.py` | 新建 | 模板 API 路由 |
| `backend/app/main.py` | 修改 | 注册模板路由，版本号升级到 0.0.3 |

### 3.2 关键设计决策

- **软删除**: 使用 `is_deleted` 布尔字段，查询时默认过滤 `is_deleted=False`
- **占位符替换**: 在 template_service 中提供 `render_template(template, contract_data)` 工具函数
- **审计日志**: 模板创建/编辑/删除记录审计日志（action: `template.create`, `template.update`, `template.delete`）
- **迁移策略**: 新表通过 `Base.metadata.create_all()` 自动创建，无需手动迁移

---

## 4. 前端实施

### 4.1 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/types/index.ts` | 修改 | 新增 ContractTemplate 相关类型 |
| `frontend/src/api/templates.ts` | 新建 | 模板 API 调用层 |
| `frontend/src/pages/TemplateListPage.tsx` | 新建 | 模板管理列表页（admin only） |
| `frontend/src/pages/TemplateFormPage.tsx` | 新建 | 模板创建/编辑表单页（admin only） |
| `frontend/src/pages/ContractFormPage.tsx` | 修改 | 新增「从模板创建」下拉选项 |
| `frontend/src/components/Navbar.tsx` | 修改 | 新增「模板管理」导航入口（admin only） |
| `frontend/src/App.tsx` | 修改 | 注册模板管理路由 |

### 4.2 页面设计

#### TemplateListPage
- 表格展示：模板名称、分类、创建时间、操作按钮
- 搜索：按名称/分类筛选
- 操作：新建、编辑、删除（确认对话框，软删除）
- 分页：每页 20 条

#### TemplateFormPage
- 表单字段：模板名称、分类标签、甲方默认值、乙方默认值、合同正文（支持占位符）、金额范围（min/max）
- 占位符帮助：输入框旁显示可用占位符列表
- 模式：创建 / 编辑（通过 URL param `:id` 判断）

#### ContractFormPage 变更
- 在「新建合同」模式下，顶部增加「从模板创建」下拉选择
- 选择模板后自动填充：标题、甲方、乙方、合同内容、金额
- 用户仍可修改自动填充的字段

---

## 5. 路由设计

### 5.1 后端路由

```
GET    /api/templates           → list_templates (admin)
POST   /api/templates           → create_template (admin)
GET    /api/templates/dropdown  → list_templates_dropdown (authenticated)
GET    /api/templates/{id}      → get_template (admin)
PUT    /api/templates/{id}      → update_template (admin)
DELETE /api/templates/{id}      → delete_template (admin, soft-delete)
```

### 5.2 前端路由

```
/templates          → TemplateListPage (AdminRoute)
/templates/new      → TemplateFormPage (AdminRoute)
/templates/:id/edit → TemplateFormPage (AdminRoute)
```

---

## 6. 数据库变更

- 新增 `contract_templates` 表，通过 `Base.metadata.create_all()` 自动创建
- 无需手动 ALTER TABLE 迁移（全新表）
- 无需修改现有表结构

---

## 7. 自测策略

### 7.1 后端测试 (pytest)

- `tests/test_templates.py`: 
  - 创建模板（admin 成功 / 非 admin 403）
  - 获取模板列表（含搜索、分页、软删除过滤）
  - 获取模板详情
  - 更新模板
  - 软删除模板（验证 is_deleted 标记、查询时过滤）
  - 模板下拉列表（含权限校验）
  - 占位符替换逻辑单元测试

### 7.2 前端验证

- 模板管理页面加载和筛选
- 创建/编辑/删除模板流程
- 创建合同时选择模板填充
- 权限控制（非 admin 看不到模板管理入口）

### 7.3 运行命令

```bash
# 后端测试
cd backend && python -m pytest tests/ -v

# 前端 lint
cd frontend && npm run lint
```

---

## 8. 风险与注意事项

1. **软删除一致性**: 确保所有查询端点默认过滤 `is_deleted=False`，避免已删除模板出现在列表和下拉中
2. **占位符转义**: 模板内容中的 `{{` `}}` 字面量需正确处理，避免误替换
3. **模板删除后合同不受影响**: 已通过模板创建的合同独立存在，删除模板不影响已有合同
4. **版本令牌**: 前端资源 URL 带 `?v=0.0.3`，HTML 响应通过 `Cache-Control: no-cache` 头控制缓存
5. **basePath**: 所有路由使用 `/projects/contract-mgmt-eval` 前缀

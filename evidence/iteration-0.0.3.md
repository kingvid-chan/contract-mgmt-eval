# Iteration 0.0.3 — 合同模板功能 任务拆解

## 概述

为合同管理系统新增合同模板功能。管理员可创建和管理合同模板，用户创建合同时可从模板下拉选择快速填充。

## 来源

- **owner_event**: e000031 (2026-06-18T12:20:41Z)
- **request_id**: eval-20260618-004-contract-template
- **hermes item_added**: e000032

## 任务列表

### T1: 后端 — ContractTemplate 数据模型

**文件**:
- `backend/app/models/template.py` (新建) — SQLAlchemy ORM 模型
- `backend/app/models/__init__.py` (修改) — 导出 ContractTemplate

**验收标准**:
- ContractTemplate 模型包含所有字段：id, name, category, party_a_default, party_b_default, content, amount_min, amount_max, is_deleted, created_by, created_at, updated_at
- is_deleted 默认 False
- created_by 外键关联 users.id

### T2: 后端 — Pydantic Schema

**文件**:
- `backend/app/schemas/template.py` (新建)

**验收标准**:
- TemplateCreate: name(必填), category(可选), party_a_default(可选), party_b_default(可选), content(可选), amount_min(可选), amount_max(可选)
- TemplateUpdate: 所有业务字段可选
- TemplateResponse: 包含所有输出字段 + creator_username
- TemplateDropdownItem: id, name, category
- TemplateListResponse: total, items

### T3: 后端 — Template Service 业务逻辑

**文件**:
- `backend/app/services/template_service.py` (新建)

**验收标准**:
- list_templates: 支持搜索(name/category), 分页, 过滤 is_deleted=False, admin 接口
- list_templates_dropdown: 返回未删除模板的 id/name/category, 所有登录用户可调用
- create_template: 创建模板, 记录审计日志 template.create
- get_template: 获取单个模板, 不存在抛 404
- update_template: 更新模板, 记录审计日志 template.update
- soft_delete_template: 设置 is_deleted=True, 记录审计日志 template.delete
- render_template_content: 将模板 content 中的 {{变量}} 替换为实际值

### T4: 后端 — Template API 路由

**文件**:
- `backend/app/routers/templates.py` (新建)

**验收标准**:
- GET /api/templates: admin only, 搜索/分页
- POST /api/templates: admin only, 创建模板
- GET /api/templates/dropdown: 所有认证用户, 返回下拉列表
- GET /api/templates/{id}: admin only, 模板详情
- PUT /api/templates/{id}: admin only, 更新模板
- DELETE /api/templates/{id}: admin only, 软删除
- 所有端点错误处理完备

### T5: 后端 — 注册路由 & 版本升级

**文件**:
- `backend/app/main.py` (修改)

**验收标准**:
- 注册 templates router
- 版本号从 0.0.2 升级到 0.0.3
- 启动时 contract_templates 表自动创建

### T6: 前端 — TypeScript 类型 & API 层

**文件**:
- `frontend/src/types/index.ts` (修改) — 新增 ContractTemplate 接口
- `frontend/src/api/templates.ts` (新建) — API 调用

**验收标准**:
- ContractTemplate 类型完整
- API 函数: listTemplates, listTemplatesDropdown, createTemplate, getTemplate, updateTemplate, deleteTemplate

### T7: 前端 — 模板管理列表页

**文件**:
- `frontend/src/pages/TemplateListPage.tsx` (新建)

**验收标准**:
- 表格展示模板：名称、分类、创建时间、操作
- 搜索框：按名称/分类筛选
- 分页：每页 20 条
- 新建按钮 → 跳转 /templates/new
- 编辑按钮 → 跳转 /templates/:id/edit
- 删除按钮 → 确认对话框 → 软删除

### T8: 前端 — 模板创建/编辑表单页

**文件**:
- `frontend/src/pages/TemplateFormPage.tsx` (新建)

**验收标准**:
- 表单字段：模板名称、分类、甲方默认值、乙方默认值、正文内容、金额下限、金额上限
- 占位符帮助提示：{{甲方}}、{{乙方}}、{{金额}}、{{日期}}、{{合同编号}}
- 创建模式：POST /api/templates
- 编辑模式：先从 GET /api/templates/{id} 加载，再 PUT 更新
- 保存后跳转模板列表

### T9: 前端 — 路由和导航注册

**文件**:
- `frontend/src/App.tsx` (修改) — 添加模板路由
- `frontend/src/components/Navbar.tsx` (修改) — 添加「模板管理」导航

**验收标准**:
- /templates, /templates/new, /templates/:id/edit 路由在 AdminRoute 下
- 导航栏「模板管理」仅 admin 可见

### T10: 前端 — ContractFormPage 集成模板选择

**文件**:
- `frontend/src/pages/ContractFormPage.tsx` (修改)

**验收标准**:
- 新建合同时，顶部显示「从模板创建」下拉选择器
- 下拉选项格式: "模板名称 (分类)"
- 选择模板后自动填充：标题(模板名称)、甲方、乙方、内容、金额
- 用户仍可修改自动填充的字段
- 编辑模式下不显示模板选择器

### T11: 后端测试

**文件**:
- `backend/tests/test_templates.py` (新建)

**验收标准**:
- test_create_template_admin_success
- test_create_template_non_admin_forbidden
- test_list_templates_with_search_pagination
- test_list_templates_excludes_deleted
- test_get_template_detail
- test_update_template
- test_soft_delete_template
- test_dropdown_authenticated
- test_dropdown_excludes_deleted
- test_render_template_content (单元测试)

### T12: 自测 & 文档同步

**输出**:
- `evidence/claude/self-test-0.0.3.txt`
- `evidence/claude/handoff-0.0.3.json`
- `docs/iterations/0.0.3.md` (本文档)
- 更新 `docs/architecture.md` (模块职责、API Endpoints 总览)

**验收标准**:
- pytest 全部通过
- 前端 lint 无错误
- handoff 文件 ready_for_verification=true

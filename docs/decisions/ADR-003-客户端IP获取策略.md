# ADR-003: 客户端 IP 获取策略 — 三层兼容链

**状态**: 已采纳  
**日期**: 2026-06-18  
**迭代**: 0.0.2

## 背景

项目部署在 Nginx 反向代理后，FastAPI 的 `request.client.host` 只能拿到 `127.0.0.1`。需要通过代理头获取真实客户端 IP。需要防止伪造和 CDN/代理 IP 污染。

## 方案对比

| 方案 | 做法 | 优点 | 缺点 |
|------|------|------|------|
| A: 仅 X-Forwarded-For | 读取第一个非内网 IP | 代理链标准 | 需解析逗号分隔、需防范伪造 |
| B: 仅 X-Real-IP | Nginx 单独设置的真实 IP | 最简单直接 | 依赖 Nginx 配置 |
| **C: 三层兼容链** | X-Real-IP → X-Forwarded-For → client.host | 最可靠、覆盖所有场景 | 稍复杂 |

## 决策

选择 **方案 C — 三层兼容链**。

优先级：
1. **X-Real-IP** header — Nginx 直接设置的真实客户端 IP，最可靠
2. **X-Forwarded-For** — 代理链，提取第一个非内网 IP（过滤 10.x, 172.16-31.x, 192.168.x, 127.x）
3. **request.client.host** — 直连场景 fallback

内网 IP 过滤规则：
- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`
- `127.0.0.0/8`

## 影响

- `AuditLogger._extract_client_ip()` 方法实现此逻辑
- 测试客户端场景下 IP 为 `testclient`（Starlette TestClient 默认行为）
- 生产环境正确部署 Nginx 后，可获取真实公网 IP

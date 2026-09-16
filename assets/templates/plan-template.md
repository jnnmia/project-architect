# Implementation Plan: [FEATURE_NAME]

**Branch**: `[FEATURE_BRANCH]` | **Date**: [YYYY-MM-DD] | **Spec**: `specs/[FEATURE_NAME]/spec.md`

## 1. 架构与技术选型概要 (Summary & Architecture)

[提取业务规范中的核心需求，概述本次方案采用的技术路线与架构分层模式]

## 2. 技术上下文与约束基线 (Technical Context)

- **语言与运行环境**: [如 Python 3.12, Node.js 20 LTS, Go 1.22]
- **核心框架与库**: [核心依赖清单与选型理由]
- **数据持久化**: [如 SQLite, PostgreSQL, 文件缓存 或 N/A]
- **测试框架**: [如 pytest, vitest, go test]
- **目标运行平台**: [如 Windows / Linux / macOS / 浏览器环境]
- **非功能量化指标**: [如 进程内存 < 50MB, 冷启动 < 100ms, P95 响应 < 200ms, 离线可用]

## 3. 核心规则自检 (Rules Check)

> [!NOTE]
> 在方案设计与接口规划阶段，对照项目核心规则自检，说明设计实现方式或特殊考量。

| 审查原则 | 检查结果 | 设计说明 / 凭证 | 特殊说明 (若正常则填 N/A) |
|---|---|---|---|
| **1. 架构分离与单一职责** | [PASS / FAIL] | [说明核心业务模块如何与展现/传输层解耦] | N/A |
| **2. 测试先行与质量保障** | [PASS / FAIL] | [指出测试用例路径及验证计划] | N/A |
| **3. 依赖与资源节约** | [PASS / FAIL] | [说明依赖选型理由与资源释放机制] | N/A |
| **4. 安全防护与环境兼容** | [PASS / FAIL] | [说明输入防御、路径安全及跨平台支持] | N/A |

## 4. 目录与工程拓扑 (Project Layout)

```text
[展示本次特性涉及的核心目录结构与文件职责]
```

## 5. 分阶段落地路线 (Execution Phases)

### Phase 0: 调研与技术验证 (Research & Spike)
- 消除待澄清点 (NEEDS CLARIFICATION)，产出关键技术验证脚本。

### Phase 1: 数据模型与接口契约 (Data Model & Contracts)
- 定义核心数据结构、状态机与接口协议规范，冻结 Public API。

### Phase 2: 任务拆解与测试先行 (Tasks & Implementation)
- 交付可独立验证的任务列表，严格按照红-绿-重构循环执行。

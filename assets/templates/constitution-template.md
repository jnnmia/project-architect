<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 -> 1.0.0
Bump rationale: Initial ratification of project constitution.

Principles defined:
  I.   Architectural Separation & Single Responsibility
  II.  Test-Backed Quality Gate (NON-NEGOTIABLE)
  III. Dependency & Resource Discipline
  IV.  Security, Privacy & Environmental Compatibility

Templates reviewed for alignment:
  [x] plan-template.md: Constitution Check gate configured
  [x] spec-template.md: Requirements trace to principles
  [x] tasks-template.md: Testing and quality tasks included
-->

# [PROJECT_NAME] Constitution

## Overview
[PROJECT_NAME] 是一个 [PROJECT_PURPOSE_SUMMARY]。本文档为该项目具有最高法律效力的治理准则与工程纪律，对所有功能设计、代码实现、测试门禁与重构行为具有不可协商的约束力。

---

## Core Principles

### I. 架构分离与单一职责 (Architectural Separation & Single Responsibility)
- 系统各层之间 MUST 保持单向依赖与解耦，严禁跨层反向调用或循环依赖。
- 业务逻辑 MUST 与传输协议、界面展现（CLI/Web/GUI）严格分离，保持核心逻辑独立可测。
- 公共接口与内部实现 MUST 明确区分，私有模块禁止跨包边界直接引用。

*Rationale:* 明确的分层边界与职责单一性能显著降低系统认知负载，避免随着业务复杂度上升导致架构腐化。

### II. 测试先行与质量门禁 (Test-Backed Quality Gate - NON-NEGOTIABLE)
- 所有行为变更 MUST 附带自动化测试覆盖，测试套件是合并与发布的硬性门禁（Hard Gate）。
- 关键业务流程与接口变更 MUST 遵循测试先行流程：明确预期 -> 编写失败测试 -> 实现代码 -> 测试通过 -> 重构。
- 单元测试与端到端测试 MUST 隔离外部网络依赖，通过 Mock/Stub 实现确定性离线执行。

*Rationale:* 无自动化测试保障的重构是系统不稳定性的根源。测试是规格说明书的代码化表达。

### III. 依赖与资源节约纪律 (Dependency & Resource Discipline)
- 引入任何新第三方依赖 MUST 具备明确的架构论证（Rationale），优先使用标准库或既有依赖。
- 资源操作（文件句柄、数据库连接、网络套接字）MUST 严格保证释放与幂等性。
- 核心逻辑性能指标与内存占用 MUST 符合项目约束基线，严禁无上限的内存驻留。

*Rationale:* 依赖膨胀会急剧增加维护成本、安全风险与打包体积；资源泄露在长时间运行下会导致服务崩溃。

### IV. 安全合规与环境兼容 (Security, Privacy & Environmental Compatibility)
- 源码与配置文件中 MUST NOT 包含任何明文敏感信息（密码、Token、私钥、内部凭据）。
- 所有涉及文件系统与外部输入的操作 MUST 防御路径穿越、非法注入与权限越权。
- 核心能力与辅助脚本 MUST 保持跨平台兼容性，严禁硬编码特定平台独占的不可移植特性。

*Rationale:* 安全合规是不可逾越的红线；跨平台兼容保障了团队不同环境协同的一致性。

---

## Development Workflow & Quality Gates

开发生命周期严格遵循以下流转门禁：
1. **Spec 阶段**：定义用户需求与验收场景，清晰划分 MUST / SHOULD 范围。
2. **Plan 阶段**：制定技术方案，必须通过前置 Constitution Check（宪法审查），确认未违反任何核心原则。
3. **Tasks 阶段**：将架构要求、测试先行用例与非功能性指标落实为独立任务卡片。
4. **Implement 阶段**：按任务落地实现与测试，禁止超范围篡改无关模块。
5. **Verify 阶段**：全量测试套件执行通过，确认满足所有质量门禁。

---

## Governance & Amendment

1. **不可协商性**：本宪法原则是项目的顶层规范。日常功能开发或方案设计中若发现冲突，必须调整功能设计，严禁未经修宪擅自稀释或忽略原则。
2. **版本化管理 (SemVer)**：
   - **MAJOR**：删除、废弃或重大修改既有不可协商原则。
   - **MINOR**：新增原则、新增章节或实质性扩充指导范围。
   - **PATCH**：文字勘误、格式微调、非语义性润色。
3. **修宪流程**：修改宪法必须独立提交 PR/Commit，且必须在顶部附带完整的 Sync Impact Report。

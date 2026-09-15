<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 -> 1.0.0
Bump rationale: Initial baseline of project ground rules.

Principles defined:
  I.   Architectural Separation & Single Responsibility
  II.  Test-Backed Quality Gate (NON-NEGOTIABLE)
  III. Dependency & Resource Discipline
  IV.  Security, Privacy & Environmental Compatibility

Templates reviewed for alignment:
  [x] plan-template.md: Rules Check configured
  [x] spec-template.md: Requirements trace to principles
  [x] tasks-template.md: Testing and quality tasks included
-->

# [PROJECT_NAME] Constitution

## Overview
[PROJECT_NAME] 是一个 [PROJECT_PURPOSE_SUMMARY]。本文档明确该项目的核心工程规范与底线规则，供功能设计、代码实现与自动化检查共同遵循。

---

## Core Principles

### I. 架构分离与单一职责 (Architectural Separation & Single Responsibility)
- 系统各层之间 MUST 保持单向依赖与解耦，严禁跨层反向调用或循环依赖。
- 业务逻辑 MUST 与传输协议、界面展现（CLI/Web/GUI）严格分离，保持核心逻辑独立可测。
- 公共接口与内部实现 MUST 明确区分，私有模块禁止跨包边界直接引用。

*Rationale:* 保持清晰的分层边界，核心业务逻辑不依赖具体展现或协议，便于独立单测与模块替换。

### II. 测试先行与质量保障 (Test-Backed Quality Gate - NON-NEGOTIABLE)
- 所有行为变更 MUST 附带自动化测试覆盖，测试套件执行通过作为功能合并的基础条件。
- 关键业务流程与接口变更 MUST 遵循测试先行流程：明确预期 -> 编写失败测试 -> 实现代码 -> 测试通过 -> 重构。
- 单元测试与集成测试 MUST 隔离外部网络依赖，通过 Mock/Stub 实现确定性离线执行。

*Rationale:* 核心逻辑需要自动化测试保护，避免后续改动引入回归缺陷。

### III. 依赖与资源节约 (Dependency & Resource Discipline)
- 引入任何新第三方依赖 MUST 具备明确的架构论证（Rationale），优先使用标准库或既有依赖。
- 资源操作（文件句柄、数据库连接、网络套接字）MUST 显式释放并保证操作幂等。
- 核心逻辑性能指标与内存占用 MUST 符合项目约束基线，严禁无上限的内存驻留。

*Rationale:* 控制第三方包数量可减少依赖冲突与打包体积；显式释放资源避免长期运行泄漏。

### IV. 安全防护与环境兼容 (Security, Privacy & Environmental Compatibility)
- 源码与配置文件中 MUST NOT 包含任何明文敏感信息（密码、Token、私钥、内部凭据）。
- 所有涉及文件系统与外部输入的操作 MUST 防御路径穿越、非法注入与权限越权。
- 核心能力与辅助脚本 MUST 保持跨平台兼容性，严禁硬编码特定平台独占的不可移植特性。

*Rationale:* 杜绝敏感凭据提交，保证脚本在不同操作系统上表现一致。

---

## Development Workflow & Checkpoints

开发流程建议按以下阶段推进：
1. **Spec 阶段**：定义用户需求与验收场景，清晰划分 MUST / SHOULD 范围。
2. **Plan 阶段**：制定技术方案，对照核心原则自检，确认未违反分层与依赖约束。
3. **Tasks 阶段**：将架构要求、测试用例与非功能性指标落实为独立任务卡片。
4. **Implement 阶段**：按任务落地实现与测试，禁止超范围改动无关模块。
5. **Verify 阶段**：全量测试套件执行通过，确认满足各项检查项。

---

## Rules Maintenance

1. **规则遵循**：新功能设计与代码实现需遵守既定规则。若现有规则与新场景冲突，应先评估并显式更新规则文档，不应私下绕过。
2. **版本管理 (SemVer)**：
   - **MAJOR**：删除、废弃或重大修改既有核心原则。
   - **MINOR**：新增原则、新增检查章节或扩充指导范围。
   - **PATCH**：文字勘误、格式微调、非语义性润色。
3. **变更记录**：修改核心原则时，需说明修改原因并在提交记录或文件顶部记录变更内容。

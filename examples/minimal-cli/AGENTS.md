# audioclip - Agent Governance

> 项目核心工程规范与底线规则定义于 [.specify/memory/constitution.md](./.specify/memory/constitution.md)。


<!-- RULES START -->
## Project Governance & Principles (Automated)
Constitutional Single Source of Truth: `.specify/memory/constitution.md`
Binding Architectural & Quality Invariants:
### I. 架构分离与单一职责 (Architectural Separation & Single Responsibility)
- 系统各层之间 MUST 保持单向依赖与解耦，严禁跨层反向调用或循环依赖。
- 业务逻辑 MUST 与传输协议、界面展现（CLI/Web/GUI）严格分离，保持核心逻辑独立可测。
- 公共接口与内部实现 MUST 明确区分，私有模块禁止跨包边界直接引用。
### II. 测试先行与质量门禁 (Test-Backed Quality Gate - NON-NEGOTIABLE)
- 所有行为变更 MUST 附带自动化测试覆盖，测试套件是合并与发布的硬性门禁（Hard Gate）。
- 关键业务流程与接口变更 MUST 遵循测试先行流程：明确预期 -> 编写失败测试 -> 实现代码 -> 测试通过 -> 重构。
- 单元测试与端到端测试 MUST 隔离外部网络依赖，通过 Mock/Stub 实现确定性离线执行。
### III. 依赖与资源节约纪律 (Dependency & Resource Discipline)
- 引入任何新第三方依赖 MUST 具备明确的架构论证（Rationale），优先使用标准库或既有依赖。
- 资源操作（文件句柄、数据库连接、网络套接字）MUST 严格保证释放与幂等性。
- 核心逻辑性能指标与内存占用 MUST 符合项目约束基线，严禁无上限的内存驻留。
### IV. 安全合规与环境兼容 (Security, Privacy & Environmental Compatibility)
- 源码与配置文件中 MUST NOT 包含任何明文敏感信息（密码、Token、私钥、内部凭据）。
- 所有涉及文件系统与外部输入的操作 MUST 防御路径穿越、非法注入与权限越权。
- 核心能力与辅助脚本 MUST 保持跨平台兼容性，严禁硬编码特定平台独占的不可移植特性。

Hard Execution Gates:
1. Every proposed plan MUST pass the Constitution Check gate with Evidence.
2. Automated test suite and scope guards are non-negotiable hard gates.
3. Never modify application source files when performing rule/constitution maintenance.
<!-- RULES END -->

# Tasks: [FEATURE_NAME]

**Branch**: `[FEATURE_BRANCH]` | **Spec**: `specs/[FEATURE_NAME]/spec.md` | **Plan**: `specs/[FEATURE_NAME]/plan.md`

## 1. 任务规划与覆盖矩阵 (Traceability Matrix)

每个任务建议关联到需求编号（如 `[REQ-01]`）或核心规则编号（如 `[RULE-02]`），保持改动目标明确可溯源。
标记说明：`[P]` 代表可并行执行；`[S]` 代表串行依赖前置任务。

| 任务编号 | 关联需求 | 类别 | 描述 | 目标文件 |
|---|---|---|---|---|
| `TASK-001` | `[RULE-01]` | 基础脚手架 | 建立模块目录骨架与类型定义 | `src/models/` |
| `TASK-002` | `[RULE-02]` | 测试先行 | 编写第一阶段失败测试套件 | `tests/test_core.py` |
| `TASK-003` | `[REQ-01]` | 业务特性 | 实现核心业务状态机 | `src/services/` |

---

## 2. 分阶段任务清单 (Task Breakdown)

### Phase 1: 基础设施与契约定义 (Setup & Contracts)
- [ ] `TASK-001` [P] [RULE-01] 建立目录结构与抽象接口契约
  - *目标文件*: `src/core/contracts.py`
  - *验证命令*: `pytest tests/test_contracts.py`

### Phase 2: 测试先行桩与前置用例 (Test-First Harness)
- [ ] `TASK-002` [S] [RULE-02] 针对 REQ-01 / REQ-02 编写红绿前置测试用例
  - *目标文件*: `tests/test_feature.py`
  - *验证命令*: `pytest tests/test_feature.py` (预期：前置运行失败 RED)

### Phase 3: 业务核心与功能实现 (Implementation)
- [ ] `TASK-003` [S] [REQ-01] 实现核心业务处理逻辑，使前置测试转绿
  - *目标文件*: `src/core/service.py`
  - *验证命令*: `pytest tests/test_feature.py` (预期：测试通过 GREEN)
- [ ] `TASK-004` [S] [REQ-02] 实现边界防御与异常处理分支
  - *目标文件*: `src/core/errors.py`
  - *验证命令*: `pytest tests/test_feature.py -k "test_edge_cases"`

### Phase 4: 规则复核与交付自检 (Hardening & Polish)
- [ ] `TASK-005` [P] [RULE-03] 依赖检查与无用代码清理，验证内存/启动基线
  - *目标文件*: 全局
  - *验证命令*: `python -m pytest --durations=10`
- [ ] `TASK-006` [P] [RULE-04] 跨平台路径与安全扫描，更新项目文档
  - *目标文件*: `README.md`, `specs/`
  - *验证命令*: `[SECURITY_SCAN_CMD]`（替换为本工程实际的依赖与密钥扫描命令）

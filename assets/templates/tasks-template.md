# Tasks: [FEATURE_NAME]

**Branch**: `[FEATURE_BRANCH]` | **Spec**: `specs/[FEATURE_NAME]/spec.md` | **Plan**: `specs/[FEATURE_NAME]/plan.md`

## 1. 任务规划与覆盖矩阵 (Traceability Matrix)

每个任务必须明确关联到规范中的功能需求编号（如 `[REQ-01]`）或宪法质量门禁（如 `[CONST-II]`），禁止存在无源头的幽灵任务。
标记说明：`[P]` 代表可并行执行；`[S]` 代表串行依赖前置任务。

| 任务编号 | 关联需求 | 类别 | 描述 | 目标文件 |
|---|---|---|---|---|
| `TASK-001` | `[CONST-I]` | 基础脚手架 | 建立模块目录骨架与类型定义 | `src/models/` |
| `TASK-002` | `[CONST-II]` | 测试先行 | 编写第一阶段失败测试套件 | `tests/test_core.py` |
| `TASK-003` | `[REQ-01]` | 业务特性 | 实现核心业务状态机 | `src/services/` |

---

## 2. 分阶段任务清单 (Task Breakdown)

### Phase 1: 基础设施与契约定义 (Setup & Contracts)
- [ ] `TASK-001` [P] [CONST-I] 建立目录结构与抽象接口契约
  - *目标文件*: `src/core/contracts.py`
  - *验证命令*: `pytest tests/test_contracts.py`

### Phase 2: 测试先行桩与前置用例 (Test-First Harness)
- [ ] `TASK-002` [S] [CONST-II] 针对 REQ-01 / REQ-02 编写红绿前置测试用例
  - *目标文件*: `tests/test_feature.py`
  - *验证命令*: `pytest tests/test_feature.py` (预期：前置运行失败 RED)

### Phase 3: 业务核心与功能实现 (Implementation)
- [ ] `TASK-003` [S] [REQ-01] 实现核心业务处理逻辑，使前置测试转绿
  - *目标文件*: `src/core/service.py`
  - *验证命令*: `pytest tests/test_feature.py` (预期：测试通过 GREEN)
- [ ] `TASK-004` [S] [REQ-02] 实现边界防御与异常处理分支
  - *目标文件*: `src/core/errors.py`
  - *验证命令*: `pytest tests/test_feature.py -k "test_edge_cases"`

### Phase 4: 宪法门禁审查与整固交付 (Hardening & Polish)
- [ ] `TASK-005` [P] [CONST-III] 依赖检查与无用代码清理，验证内存/启动基线
  - *目标文件*: 全局
  - *验证命令*: `python -m pytest --durations=10`
- [ ] `TASK-006` [P] [CONST-IV] 跨平台路径与安全扫描，更新项目文档
  - *目标文件*: `README.md`, `specs/`
  - *验证命令*: `python scripts/scaffold_rules.py validate`

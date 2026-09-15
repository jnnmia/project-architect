# 项目底线规则制定指南 (Ground Rules Guide)

项目底线规则（Constitution / Ground Rules）用于明确项目的核心工程规范与质量基线，在方案规划、任务拆解与代码生成中作为硬性约束。

---

## 1. 规范性词汇标准 (RFC 2119 Normative Wording)

- **MUST / SHALL (必须)**：硬性要求。未满足则判定为阻断项，需修改方案。
- **MUST NOT / SHALL NOT (严禁)**：明确禁止项。如“严禁硬编码敏感凭据”、“严禁反向跨层依赖”。
- **SHOULD / RECOMMENDED (建议)**：推荐做法。若有特殊情况需偏离，需在方案中说明理由（Rationale）。
- **MAY / OPTIONAL (可选)**：可选特性。

---

## 2. 核心原则三段式结构

每条原则建议包含：
1. **标识与名称**：明确标号（如 `I. 架构分离与单一职责`）。
2. **规则清单**：2~4 条具体的 MUST / MUST NOT 声明。
3. **制定理由 (Rationale)**：说明为什么立这条规则，避免后续改动时无谓偏离。

```markdown
### I. 依赖控制与离线可用 (Dependency Discipline)
- 新增第三方依赖 MUST 给出明确理由，优先使用标准库或既有依赖。
- 核心算法与工具逻辑 MUST 保证离线可执行，不引入不必要的外网依赖。

*Rationale:* 控制外部依赖可减少维护负担与打包体积；离线可用保障执行环境稳定性。
```

---

## 3. 规则语义化版本控制 (SemVer)

- **MAJOR (x.0.0)**：删除或废弃既有核心原则，或调整基本架构约束。
- **MINOR (x.y.0)**：新增原则、新增检查章节或扩充指导范围。
- **PATCH (x.y.z)**：文字勘误、排版微调、非语义性语意澄清。

---

## 4. 变更说明模板 (Sync Impact Report)

修订核心规则时建议在文件头部记录简要变更说明：

```markdown
<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 -> 1.1.0
Bump rationale: 增加跨平台环境兼容性约束。

Principles modified:
  - III. 依赖与资源节约: 补充文件描述符及时释放要求

Principles added:
  - IV. 安全防护与环境兼容

Templates reviewed for alignment:
  [x] plan-template.md: 检查项已对齐
  [x] spec-template.md: 无冲突
-->
```

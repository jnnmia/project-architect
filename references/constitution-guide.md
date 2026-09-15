# 项目宪法制定与治理规范 (Constitution Guide)

项目宪法（Constitution）是项目的最高工程规范与不可协商质量基线，在方案规划、任务拆解与代码生成中具备一票否决权（CRITICAL Gate）。

---

## 1. 规范性语言标准 (RFC 2119 Normative Wording)

- **MUST / SHALL (必须)**：绝对硬性要求。违背直接判定为阻断性错误（CRITICAL）。
- **MUST NOT / SHALL NOT (严禁)**：绝对禁令。如“严禁硬编码敏感凭据”、“严禁反向跨层依赖”。
- **SHOULD / RECOMMENDED (应当)**：强推荐要求。允许在特殊物理限制下偏离，但必须在技术方案中附带书面论证（Rationale）。
- **MAY / OPTIONAL (可以)**：完全可选特性。

---

## 2. 核心原则标准三段式结构

每条原则必须包含：
1. **标识与名称**：明确标号（如 `I. 架构分离与单一职责`）。
2. **规则清单**：2~4 条具体的 MUST / MUST NOT 声明。
3. **架构理由 (Rationale)**：解释确立本条规则的核心动机，防范未来认知遗忘。

```markdown
### I. 依赖最小化与离线自治 (Dependency Discipline - NON-NEGOTIABLE)
- 新增任何第三方依赖 MUST 具备明确的技术评审记录，严禁引入高危 CVE 依赖。
- 核心算法与工具逻辑 MUST 保证离线可执行，严禁无必要的外网网络依赖。

*Rationale:* 外部依赖是长期维护复杂性与供应链安全风险的最大来源；离线自治保障环境稳定性。
```

---

## 3. 规则语义化版本控制 (SemVer)

- **MAJOR (x.0.0)**：删除或废弃既有原则，或不兼容地放宽核心约束。
- **MINOR (x.y.0)**：新增原则、新增质量门禁章节或实质性扩充约束维度。
- **PATCH (x.y.z)**：文字勘误、排版微调、非语义性语意澄清。

---

## 4. 同步影响报告模板 (Sync Impact Report)

修订宪法时必须在文件头部生成临时审查报告：

```markdown
<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 -> 1.1.0
Bump rationale: 增加跨平台环境兼容性约束。

Principles modified:
  - III. 依赖与资源节约纪律: 补充文件描述符泄露防御规则

Principles added:
  - IV. 安全合规与环境兼容 (NON-NEGOTIABLE)

Templates reviewed for alignment:
  [x] plan-template.md: 门禁矩阵已对齐
  [x] spec-template.md: 无冲突
-->
```

# AI 编码助手规则映射规范 (Agent Rules Mapping)

本规范定义主流 AI 编码助手的规则发现路径、格式要求与标记隔离契约。

---

## 1. 助手规则文件拓扑

| Agent / IDE 标识 | 规则发现路径 | 格式与 Frontmatter 特性 |
|---|---|---|
| **Cursor** | `.cursor/rules/project-rules.mdc` | 头部强制包含：`---\nalwaysApply: true\n---` |
| **Claude / Claude Code** | `CLAUDE.md` | 项目根目录 Markdown |
| **GitHub Copilot** | `.github/copilot-instructions.md` | 仓库级说明文档 |
| **Google Gemini CLI** | `GEMINI.md` | 项目根目录 Markdown |
| **Antigravity / Codex / 通用** | `AGENTS.md` | 跨平台标准规约，单一事实源 |
| **Windsurf** | `.windsurf/rules/project-rules.md` | IDE 规则目录 |
| **Trae** | `.trae/rules/project_rules.md` | IDE 规则目录 |

---

## 2. 注入范围界定 (Target Selection)

上表是**能力边界，不是默认清单**。注入范围 MUST 是**用户确认过的工具子集**，禁止照表全量铺开 ——
用户没在用的工具，写进去的规则文件就是仓库里的垃圾。

| 步骤 | 动作 | 说明 |
|---|---|---|
| 1 | `scaffold_rules.py detect` | 扫描工程里各工具的落盘痕迹。**只读，不写任何文件** |
| 2 | 向用户确认 | 把探测结果整理成多选，问清用户实际在用哪几个 |
| 3 | `inject --agents "<子集>" --dry-run` | **先预览**：列出每个目标是新建还是更新及字节增量，不写文件 |
| 4 | `inject --agents "<子集>"` | 预览无误后真正落盘，只写确认过的键 |

> `inject` 会改写仓库里已存在的文件，因此 `--dry-run` 是默认动作而非可选项。
> 预览与写入共用同一段代码路径，二者不可能不一致。回滚：删除 `<!-- RULES START/END -->` 之间的整段。

- **证据 ≠ 授权**：探测到痕迹只说明「这个工程里可能有该工具」，不构成写入许可，仍须问过用户。
- **探测为空时更要问**：全新工程没有任何痕迹，此时不存在任何可以替用户作答的依据。
- **默认例外**：`AGENTS.md` 是跨平台通用入口，`init` 本身即创建，可作默认随附项；其余 6 个项目标逐个确认。
- **`--agents` 无默认值**：省略即报错退出（退出码 `2`）。刻意如此 —— 有默认值就会诱发全量注入。

---

## 3. 标记隔离注入标准 (Boundary Markers)

自动化同步通过生命周期标记实现无侵入更新，严格保护标记外的用户私有内容：

```markdown
<!-- RULES START -->
## Project Governance & Principles (Automated)
Rules Source of Truth: `.specify/memory/constitution.md`
[规则条目自动注入区域]
<!-- RULES END -->
```

- **注入原则**：存在成对标记时就地替换；存在单边损坏标记时执行自愈闭环；不存在标记时追加到末尾。
- **安全红线**：目标路径强制限制在项目根目录内，严禁 `..` 越权路径穿越；统一 UTF-8 编码与 `\n` 换行。

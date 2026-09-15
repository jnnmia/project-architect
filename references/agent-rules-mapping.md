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

## 2. 标记隔离注入标准 (Boundary Markers)

自动化同步通过生命周期标记实现无侵入更新，严格保护标记外的用户私有内容：

```markdown
<!-- RULES START -->
## Project Governance & Principles (Automated)
Constitutional Single Source of Truth: `.specify/memory/constitution.md`
[规则条目自动注入区域]
<!-- RULES END -->
```

- **注入原则**：存在成对标记时就地替换；存在单边损坏标记时执行自愈闭环；不存在标记时追加到末尾。
- **安全红线**：目标路径强制限制在项目根目录内，严禁 `..` 越权路径穿越；统一 UTF-8 编码与 `\n` 换行。

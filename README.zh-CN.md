# Project Architect

[![skills.sh](https://skills.sh/b/jnnmia/project-architect)](https://skills.sh/jnnmia/project-architect) [![Version](https://img.shields.io/badge/version-v1.0.1-blue.svg)](https://github.com/jnnmia/project-architect/releases) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

[English](./README.md) | 简体中文

Project Architect 是一个面向 AI 辅助研发的工程规范与架构脚手架工具。它通过量化决策树引导技术选型，确立不可违背的项目底线规则（Ground Rules），并通过边界标记将工程纪律安全同步至 Cursor、Claude Code、GitHub Copilot、Gemini CLI 等多 Agent 开发环境。

---

## 目录

- [为什么需要 Project Architect](#为什么需要-project-architect)
- [核心机制](#核心机制)
- [支持的 AI 工具](#支持的-ai-工具)
- [安装与激活](#安装与激活)
- [使用指南](#使用指南)
  - [方式 1：在 AI 对话中一键立项（Skill 模式，推荐）](#方式-1在-ai-对话中一键立项skill-模式推荐)
  - [方式 2：在本地终端直接使用（CLI 模式）](#方式-2在本地终端直接使用cli-模式)
- [仓库拓扑](#仓库拓扑)
- [自动化测试](#自动化测试)
- [贡献指南](#贡献指南)
- [版本记录](#版本记录)
- [开源协议](#开源协议)

---

## 为什么需要 Project Architect

在依赖 AI 工具编码时，开发者经常遇到三类典型失控：

1. **技术栈随意膨胀**：只是想写个轻量脚本，AI 却倾向于引入庞大的运行时、第三方全家桶和未经验证的重型依赖。
2. **规约越聊越忘**：初期约定好的分层原则与测试先行，几轮对话后就被 AI 抛诸脑后，代码开始出现循环引用和无卡点改动。
3. **本地提示词被冲掉**：常规脚本分发规则时容易整文件覆盖，把开发者在 `CLAUDE.md` 或 `.cursor/rules/` 里保留的个人偏好彻底抹除。

Project Architect 将技术选型与架构原则沉淀为结构化的核心规则，通过非侵入标记管理规则注入，让项目在多 Agent 辅助开发下保持清晰稳定的代码结构。

---

## 核心机制

### 1. 核心工程规则 (Ground Rules Definition)
项目核心规则存放在 `.specify/memory/constitution.md`，采用明确的 RFC 2119 规范性用词（`MUST` / `MUST NOT`）。方案设计与代码实现需遵守核心原则，确保架构分层与依赖受控。

### 2. 标记隔离非侵入 (Zero-Invasive Injection)
通过成对生命周期标记（`<!-- RULES START -->` 和 `<!-- RULES END -->`）界定系统注入区域。仅更新标记内部的规约摘要，标记前后的用户私有配置（如构建别名、环境变量、调试技巧）原样保留。

### 3. 指标选型与流程自检 (Data-Driven Tradeoffs & Checkpoints)
选型围绕冷启动时延、内存开销、二进制体积等具体数据进行权衡。方案模板内置自检项，要求改动符合分层与测试要求。

---

## 支持的 AI 工具

脚手架原生支持将规约分发至以下主流 AI 编码环境：

| 工具名称 | 规则载体文件 | 注入处理方式 |
|---|---|---|
| **Universal Agents** | `AGENTS.md` | 标记包裹，作为跨 Agent 统一事实源入口 |
| **Claude Code** | `CLAUDE.md` | 标记包裹，保留文件头部用户自定义命令 |
| **Cursor IDE** | `.cursor/rules/project-rules.mdc` | 自动补全 YAML Frontmatter (`alwaysApply: true`) |
| **GitHub Copilot** | `.github/copilot-instructions.md` | 标记包裹，写入项目级指令 |
| **Google Gemini CLI** | `GEMINI.md` | 标记包裹，对接全局与项目级规约 |
| **Windsurf** | `.windsurf/rules/project-rules.md` | 标记包裹，适配 Cascade 引擎规则目录 |
| **Trae** | `.trae/rules/project_rules.md` | 标记包裹，适配 ByteDance Trae 上下文 |

### 只注入你在用的工具

上表列的是**能力边界，不是默认行为**。写规则文件是在改别人的仓库：给一个只用 Cursor 的工程塞进
`.trae/rules/`、`.windsurf/rules/` 和 `GEMINI.md`，不是「做得更周全」，而是污染代码库。

所以注入目标永远是一个**确认过的子集**，固定三步：

1. **先探测** —— `scaffold_rules.py detect` 扫描工程里各工具的落盘痕迹。**严格只读，不写任何文件。**
2. **再确认** —— AI 把探测结果摆给你看，问清楚你实际在用哪几个。**探测是证据，不是授权**：
   扫到痕迹绝不等于可以往那里写；而全新工程（什么痕迹都没有）恰恰是最必须问的情况。
3. **只注入确认过的** —— `--agents` 只带用户确认的键。没被提到的工具一个都不碰，**即使探测到了**。

`AGENTS.md` 是例外：它是跨工具通用入口，`init` 本来就会创建，因此可作默认随附项。
其余 6 个目标一律逐个确认。

正因如此，`--agents` **没有默认值** —— 省略会直接报错（退出码 `2`），而不是静默注入一整套规则文件。

---

## 安装与激活

Project Architect 作为标准 Agent Skill 发布，支持通过 `npx skills` 包管理器一键安装至任意兼容 Agent（Claude Code、Cursor、Gemini CLI 等）：

### 1. Skills CLI 一键安装（推荐）

```bash
# 安装至当前项目（仅本工程生效）
npx skills add jnnmia/project-architect

# 或全局安装（对本机所有兼容 Agent 生效）
npx skills add jnnmia/project-architect -g -y

# 或通过完整 GitHub 仓库地址安装
npx skills add https://github.com/jnnmia/project-architect.git -g -y
```

### 2. 让 AI 编程助手自动安装

将以下提示词直接发送给你正在使用的 AI 编程助手：

```text
请帮我安装 project-architect Skill。
GitHub 地址：https://github.com/jnnmia/project-architect
如果支持 skills CLI，请优先运行：npx skills add jnnmia/project-architect
如果不支持，请将完整仓库目录克隆至当前环境的 skills 目录，确保目录名为 project-architect，且 SKILL.md 位于该目录根部。
```

### 3. Git 手动克隆

将仓库克隆至当前 Agent 识别的技能目录（请将 `<SKILLS_DIR>` 替换为实际路径，如 `~/.gemini/config/skills` 或 `~/.agents/skills`）：

```bash
git clone https://github.com/jnnmia/project-architect.git <SKILLS_DIR>/project-architect
```

---

## 使用指南

Project Architect 支持两种使用模式：你可以把它当作 AI 助手的技能直接对话调用（推荐，零命令行门槛），也可以在终端作为独立脚手架直接运行。

### 方式 1：在 AI 对话中一键立项（Skill 模式，推荐）

安装本 Skill 后（通过 `npx skills add jnnmia/project-architect`），无需手敲任何 Python 命令。直接在与 Cursor、Claude、Gemini 的对话中发送以下常用提示词即可唤起工作流：

#### 常用提示词模板

```text
# 场景 A：从零立项并确定底线规则
请使用 project-architect 帮我立项一个新工程：我要做一个本地运行的音频切片小工具，请引导我梳理指标、权衡技术选型并生成工程底线规则。

# 场景 B：为已有仓库提取规约并同步给多 Agent
请使用 project-architect 扫描当前项目，提取核心架构分层与不可妥协的底线，并注入到 CLAUDE.md 和 .cursor/rules/ 中。

# 场景 C：提交方案前的合规卡点审查
请使用 project-architect 审查我当前的方案（plan.md），对照底线规则核验代码级设计凭证，标出违规风险。
```

#### 人机交互流程实景

当你发起立项时，AI 会沿决策树与你展开结构化对齐：

```text
[开发者]
我想做一个能把 Markdown 批量转成 PDF 的小工具，帮我立项。

[AI 单步追问量化指标]
收到。在定规矩前先明确一个核心性能诉求：
该工具是否需要复杂的 CSS 打印排版（自定义分页、复杂表格），还是纯文本极速转换？
- 选项 A (推荐)：轻量级单二进制渲染（冷启动 < 30ms，分发包 < 20MB，无外部浏览器依赖）。
- 选项 B：无头浏览器渲染（支持完整 Web CSS，但需预装 Chromium，包体积 > 150MB）。

[开发者]
选 A，必须单文件绿色运行，不要装庞大的浏览器。

[AI 先扫描工程里的工具痕迹，再确认注入范围]
写文件前还有一个决定：这个库你平时用哪些 AI 工具配合？
- 选项 A (推荐)：Cursor 和 Claude Code —— 也正是你现在正在用的两个。
- 选项 B：额外配置 GitHub Copilot、Gemini CLI、Windsurf 或 Trae。
规则文件只会写进你点名的工具。你用不到的工具，我不会往你仓库里塞 .trae/、.windsurf/ 这类目录。

[开发者]
就 Cursor 和 Claude Code。

[AI 锁定选型、生成底线规则并自动在后台执行脚手架]
选型已锁定：Go 1.22 + 纯 Go 渲染库。
确立 3 条不可违背的底线规则：
1. 静态编译：核心逻辑 MUST 编译为零动态依赖的单个静态二进制文件。
2. 分层单向解耦：Parser 解析层与 Renderer 渲染层 MUST 保持接口级隔离。
3. 错误结构化：转换失败 MUST 返回包含源文件行号的结构化错误，禁止 panic。

[AI 自动完成文件初始化与规则分发，汇报生成结果]
已生成 .specify/memory/constitution.md 并分发至 AGENTS.md、CLAUDE.md、.cursor/rules/。
```

#### 规则注入前后效果对比 (以 CLAUDE.md 为例)

注入前，文件中包含开发者手写的自定义别名与本地调试指令：
```markdown
# My Developer Setup
- test: go test -v ./...
- lint: golangci-lint run
```

执行后，开发者手写指令原封不动保留，系统规则安全封闭在标记内：
```markdown
# My Developer Setup
- test: go test -v ./...
- lint: golangci-lint run

<!-- RULES START -->
## Project Governance & Principles (Automated)
Rules Source of Truth: `.specify/memory/constitution.md`

### Core Architectural & Quality Invariants:
#### 1. 静态编译
- 核心逻辑 MUST 编译为零动态依赖的单个静态二进制文件。
#### 2. 分层单向解耦
- Parser 解析层与 Renderer 渲染层 MUST 保持接口级隔离。
#### 3. 错误结构化
- 转换失败 MUST 返回包含源文件行号的结构化错误，禁止 panic。

### Engineering Checkpoints:
1. Verify proposed plans against core project rules.
2. Maintain automated test coverage for critical business logic.
3. Keep rule updates within boundary markers without overwriting custom configurations.
<!-- RULES END -->
```

---

### 方式 2：在本地终端直接使用（CLI 模式）

适合 CI/CD 流程、无 Agent 会话环境或偏好终端操作的开发者。

#### 环境准备
- Python 3.8+（仅需 Python 标准库，零第三方 pip 依赖）。
- Git。

> **命令一律在 skill 根目录执行。** `scaffold_rules.py` 依据自身位置定位模板资源，
> 请在同时含 `scripts/` 与 `assets/templates/` 的那一层运行；只有 `--dir` 指向目标工程。

> **本项目不是 pip 包。** 本仓库以 Agent Skill 形态分发，而非可安装的 Python 发行包。
> 模板资源与脚本同级放在 `assets/templates/`，因此不支持 `pip install` / `pipx install`
> ——请克隆仓库（或以 skill 方式安装）后原地调用脚本。

#### 4 步终端流水线

```bash
# 步骤 1：探测工程里已有哪些 AI 工具的痕迹 (detect，只读)
# 每个支持的工具各输出一行；不写任何文件。先据此问清用户实际在用哪几个，再往下走。
python scripts/scaffold_rules.py detect \
  --dir /path/to/project

# 步骤 2：初始化底线规则与工作规划模板 (init)
# 创建 .specify/memory/constitution.md、需求设计模板与基线 AGENTS.md
python scripts/scaffold_rules.py init \
  --dir /path/to/project \
  --name "my-service" \
  --purpose "高并发日志解析服务"

# 步骤 3：增量注入规则到各 AI 编程工具上下文 (inject)
# 自动解析规则中的 MUST 约束，生成摘要并无侵入注入到指定工具文件。
# --agents 必填：只填用户确认过的工具，严禁填成全部支持项。
python scripts/scaffold_rules.py inject \
  --dir /path/to/project \
  --agents "agents,claude,cursor"

# 步骤 4：合规检查 (validate)
# 校验占位符是否全替换、是否包含 MUST 强制约束、是否有 Rationale 论证
python scripts/scaffold_rules.py validate \
  --dir /path/to/project
```

#### 退出码

脚本化调用 MUST 依据退出码分支，禁止只匹配输出文本。

| 码 | 含义 |
|---|---|
| `0` | 成功 |
| `1` | 规则层失败：校验不通过、`--strict` 下未提取到任何原则、`--agents` 中出现无法识别的键、`detect` 未发现任何工具痕迹 |
| `2` | I/O 失败（宪法不可读/不可写、模板资源缺失、目标文件非 UTF-8）、`--constitution-path` 逃出项目根目录，或缺少必填的 `--agents` |

所有生成文件统一为 **UTF-8 无 BOM + LF 换行**，同一输入在 Windows 与 Linux 上产出字节一致。

#### CLI 实际执行输出示范

```bash
$ python scripts/scaffold_rules.py init --dir ./md2pdf --name "md2pdf" --purpose "轻量离线转换工具"
[CREATED] Constitution initialized at: ./md2pdf/.specify/memory/constitution.md
[CREATED] Template copied to: ./md2pdf/templates/plan-template.md
[CREATED] Template copied to: ./md2pdf/templates/spec-template.md
[CREATED] Template copied to: ./md2pdf/templates/tasks-template.md
[CREATED] Baseline AGENTS.md created at: ./md2pdf/AGENTS.md
[SUCCESS] Project rule scaffolding complete.

$ python scripts/scaffold_rules.py inject --dir ./md2pdf --agents "agents,claude,cursor"
[INJECTED] Updated agent context: ./md2pdf/AGENTS.md
[INJECTED] Updated agent context: ./md2pdf/CLAUDE.md
[INJECTED] Updated agent context: ./md2pdf/.cursor/rules/project-rules.mdc
[SUCCESS] Successfully injected rules into 3 agent file(s).

$ python scripts/scaffold_rules.py validate --dir ./md2pdf
[PASS] Constitution './md2pdf/.specify/memory/constitution.md' meets all governance criteria.
```

---

## 仓库拓扑

```text
project-architect/
├── SKILL.md                          # Skill 规范元数据与核心决策流程
├── README.md                         # 英文版说明
├── README.zh-CN.md                   # 简体中文使用说明
├── LICENSE                           # MIT 开源许可证
├── CONTRIBUTING.md                   # 协作规范与贡献流程
├── pyproject.toml                    # 项目元数据与 pytest 参数（非 pip 安装包）
├── .gitignore                        # 忽略规则
├── .github/workflows/ci.yml          # GitHub Actions 自动化测试流水线
├── scripts/
│   └── scaffold_rules.py             # 规则脚手架与多 Agent 标记注入引擎
├── references/
│   ├── constitution-guide.md         # 底线规则编写指南与案例
│   ├── tech-stack-decision-matrix.md # 量化技术栈选型矩阵
│   └── agent-rules-mapping.md        # 主流 AI 上下文文件映射详情
├── assets/templates/
│   ├── constitution-template.md      # 底线规则初始化模板
│   ├── plan-template.md              # 带规则凭据审查的方案模板
│   ├── spec-template.md              # 需求规格说明模板
│   └── tasks-template.md             # 任务拆解与测试驱动模板
├── tests/
│   └── test_scaffold_rules.py        # 单元测试套件（覆盖 init/inject/validate）
└── examples/minimal-cli/             # 真实轻量 CLI 小工具落地完整范例
```

---

## 自动化测试

项目附带针对脚手架核心功能的自动化测试套件，涵盖初始化、幂等性、标记恢复、Frontmatter 校验及错误拦截。

```bash
# 使用标准库 unittest 执行测试
python -m unittest discover -s tests -p "test_*.py" -v

# 或使用 pytest 执行
pytest -v
```

---

## 贡献指南

欢迎提交 Issue 与 Merge Request。提交改动前，请遵循开发基线：
- 严格保持零外部运行时依赖（仅使用 Python 3 标准库）。
- 严格遵循零 Emoji 纪律。
- 遵循统一的 Commit Message 规范。
- 增补功能必须附带相应的单元测试用例。

---

## 版本记录

| 版本 | 发布日期 | 变更说明 |
|---|---|---|
| **v1.0.1** | 2026-09-15 | 优化核心描述与规则模板语体，去除 AI 浮夸套话，精简注入提示词并完善自检项。 |
| **v1.0.0** | 2026-09-15 | 初始正式版本发布。包含五阶段架构设计流、规则脚手架、多 Agent 标记注入、自动化测试套件、开源文档与示例工程。 |

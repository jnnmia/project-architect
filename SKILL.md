---
name: project-architect
description: "通过深入理解项目需求，从 0 到 1 梳理技术选型、确立工程底线规则与不可违背的硬约束，提供量化技术栈选型矩阵，并自动化生成适配多 AI 编码工具（Cursor、Claude Code、GitHub Copilot、Gemini CLI 等）的上下文规则脚手架与前置检查卡点。当用户需要从零立项新项目、制定项目规则、技术选型权衡、搭建工程脚手架或设置防劣化卡点时使用。"
compatibility: "需要本地已安装 Python 3 环境（支持标准库）。"
allowed-tools: read edit glob grep bash
metadata:
  version: "1.0.0"
  author: jnnmia
  agent_created: true
  tags:
    - architecture
    - tech-stack
    - ground-rules
    - checkpoints
---

# Project Architect (项目架构与规则搭建师)

专注于在动手写代码前，把项目需求量化透视、选准技术栈并把不可妥协的底线规则固化下来，防止后续 AI 编码时出现架构散架、技术栈随意膨胀和规则遗忘。

---

## 核心工作流 (Core Workflow)

```text
[阶段 1: 需求透视] -> [阶段 2: 架构与选型] -> [阶段 3: 确立底线规则] -> [阶段 4: 规则脚手架] -> [阶段 5: 卡点移交]
```

### 阶段 1：需求透视与单步澄清 (Requirements Elicitation)
沿决策树逐项追问，**一次只问一个核心问题并附带推荐选项与权衡**：
1. **业务目标**：系统服务对象与核心交互方式（CLI / API / Web）。
2. **量化约束 (NFR)**：冷启动时延、内存驻留上限、网络依赖（纯离线/云端服务/私有内网）。
3. **交付基线**：开发周期与维护预期。

### 阶段 2：架构分层与技术栈科学选型 (Architecture & Tech Stack)
> 参考文档: `references/tech-stack-decision-matrix.md`

1. **单体优先原则**：能用模块化单体解决的坚决不上微服务；三层单向依赖（Presentation -> Domain/Service -> Infrastructure）。
2. **输出选型矩阵**：提供 1 种首选方案与 1 种备选方案（含语言版本、核心框架、存储选型、测试方案），必须给出具体的架构理由（Rationale）。

### 阶段 3：确立工程底线规则 (Ground Rules Generation)
> 参考文档: `references/constitution-guide.md`

1. **确立 4~5 条不可妥协原则**：
   - 分层单向隔离（禁止高层反向依赖底层实现）。
   - 测试驱动与覆盖基线（核心业务逻辑红绿测试）。
   - 依赖与资源节约（克制引入第三方重量包）。
   - 凭证与数据安全（严禁代码内硬编码密钥与内网私有资产）。
2. **严格语义约束**：采用声明式 **MUST / MUST NOT**，禁止模糊推诿词。

### 阶段 4：规则脚手架分发 (Scaffolding & Multi-Agent Injection)
> 参考文档: `references/agent-rules-mapping.md`

执行确定性脚本完成模板建立与多 Agent 规则注入：
```bash
# 1. 初始化底线规则文件与需求规划模板
python skills/project-architect/scripts/scaffold_rules.py init \
  --dir <项目路径> --name "<项目名>" --purpose "<定位陈述>"

# 2. 检查规则文本合规度（占位符替换、MUST约束存在性、版本标注）
python skills/project-architect/scripts/scaffold_rules.py validate \
  --dir <项目路径>

# 3. 将规则以边界标记注入目标 AI 工具上下文
python skills/project-architect/scripts/scaffold_rules.py inject \
  --dir <项目路径> --agents "agents,claude,cursor,copilot,gemini"
```

### 阶段 5：检查卡点移交 (Verification & Checkpoints Handoff)
向开发者交付已生成的规约文件结构，并告知后续落地路径：
`需求规格 (spec.md) -> 方案设计与底线规则自检 (plan.md) -> 任务拆解与测试前置 (tasks.md) -> 代码实现`。

---

## 典型实战交互演练 (Interactive Walkthrough)

以下展示一次从零立项 CLI 离线工具的标准人机协作全流程：

### 轮次 1：意图捕捉与单步追问
- **用户**：我想做一个能把 Markdown 批量导出为 PDF 的小工具，帮我立项。
- **Agent**：
  > 明白。在选型和定规矩前，我们先澄清一个核心技术指标：
  > 该工具是否需要支持复杂的 CSS 页面排版（如分页页眉、复杂表格、自定义字体），还是以轻量纯文本转换为主？
  > - **选项 A (推荐)**：使用轻量无头渲染引擎（如基于 WeasyPrint 或 Go 单二进制工具），冷启动快、无浏览器依赖。
  > - **选项 B**：使用完整无头浏览器（如 Playwright / Puppeteer），排版能力强但依赖体积大（>150MB）。

### 轮次 2：技术选型与架构分层
- **用户**：选 A，我希望单文件快速分发，不要装几百兆的浏览器。
- **Agent**：
  > 根据无外部浏览器、秒级启动与轻量分发要求，给出选型权衡矩阵：
  > 
  > | 维度 | 首选方案 (Go 单二进制) | 备选方案 (Python + WeasyPrint) |
  > |---|---|---|
  > | **核心技术** | Go 1.22 + `chromedp` 或纯 Go 渲染库 | Python 3.10 + WeasyPrint + GTK 库 |
  > | **分发体积** | 单个二进制文件 (< 25MB) | 需打包 Python 解释器与 C 依赖库 (> 60MB) |
  > | **冷启动** | < 30ms | 300ms ~ 800ms |
  > | **架构理由** | 满足单文件极简分发的强诉求，无需目标系统预装运行环境。 |

### 轮次 3：确立底线规则并执行脚手架
- **用户**：方案合适，就按 Go 方案立规矩并生成脚手架。
- **Agent**：
  1. 调用 `scaffold_rules.py init --name "md2pdf" --purpose "轻量离线 Markdown 转 PDF 命令行工具"`
  2. 生成不可违背的底线规则：
     - `I. 单二进制交付`：核心业务逻辑 MUST 编译为无动态链接 C 库依赖的静态可执行程序。
     - `II. 分层解耦`：Parser 层与 Renderer 层 MUST 保持接口级解耦，核心数据模型禁止导入 CLI 参数解析包。
     - `III. 错误处理`：文件读写与转换失败 MUST 输出包含行号的结构化错误，禁止 panic 退出。
  3. 执行 `scaffold_rules.py inject --agents "agents,claude,cursor"` 完成注入。

### 轮次 4：规则注入产物验证
Agent 汇报生成的规约树与注入状态：
```text
md2pdf/
├── .specify/memory/constitution.md   # 核心底线规则（事实源）
├── AGENTS.md                         # 跨 Agent 统一规则入口（已注入）
├── CLAUDE.md                         # Claude Code 上下文（已注入标记包裹）
├── .cursor/rules/project-rules.mdc   # Cursor 专用规则（含 frontmatter）
└── templates/                        # 需求规划与检查卡点模板
```

---

## 反例与黑名单 (Anti-Patterns & Blacklist)

在执行本技能时，严格禁止以下行为：
1. **禁止越权直接编码**：用户要求“架构设计”或“定规矩”时，严禁擅自跳过选型分析直接生成业务源码。
2. **禁止空泛大词堆砌**：禁止在底线规则中出现“性能极致”、“代码优雅”、“易于扩展”等不可量化、不可断言的形容词。
3. **禁止全量文件覆盖**：更新规则时必须定位成对标记（`<!-- RULES START/END -->`），严禁冲掉开发者在上下文文件顶部写下的个人私有指令。
4. **禁止微服务过度设计**：对于初期工具或团队规模未达到拆分标准的工程，禁止推荐分布式、消息队列或多仓设计。

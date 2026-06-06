---
name: architecture-tracker
description: Tracks architectural decisions in .knowledge/architecture.md. Use when the user makes design choices, picks frameworks/libraries, decides project structure, discusses tradeoffs, mentions "architecture", "decision", "ADR", "为什么用", "为什么选", or asks to record a decision. Also use when starting a new task to check the knowledge base for context.
---

# Architecture Tracker

Maintains a living record of architectural decisions in `.knowledge/architecture.md`, organized by topic rather than chronology.

## File structure

`.knowledge/architecture.md` is organized by category. Each category groups related decisions under a clear heading:

```markdown
# Architecture Decision Record

## 技术栈 (Tech Stack)
- **Web 框架**: 使用 FastAPI | **理由**: 需要异步支持和类型安全 | *2026-06-06*

## 数据存储 (Data Storage)
- **存储方案**: 使用 JSON 文件 | **理由**: 比 SQLite 更简单方便 | *2026-06-06*
```

## Workflow

### Step 1: Ensure the knowledge base exists

Check if `.knowledge/architecture.md` exists in the project root. If not:
- Create `.knowledge/` folder if missing
- Create `.knowledge/architecture.md` with:

```markdown
# Architecture Decision Record
```

### Step 2: Identify decisions

During conversation, watch for consequential design choices:
- Choosing a framework/library
- Picking a data format or storage scheme
- Deciding project structure or naming conventions
- Accepting a tradeoff with future implications

For each decision, extract:
- **Category**: The domain this decision belongs to (e.g., 技术栈, 数据存储, API设计, 项目结构, 部署, 测试). Create new categories as needed.
- **Decision**: What was chosen (one line title + one line detail)
- **Rationale**: Why this choice (one line)
- **Date**: The date of the decision

### Step 3: Classify and detect conflicts

Read the existing file. Determine which category the new decision falls under. A conflict exists when two entries in the **same category** are mutually exclusive (e.g., two different web frameworks, two different storage backends, two different API styles).

### Step 4: Confirm with the user

Present the proposed update. If there's a conflict, show both entries:

```
拟添加到 .knowledge/architecture.md:
> 分类: 技术栈
> - **Web 框架**: 使用 FastAPI | **理由**: ... | *2026-06-06*

⚠️ 与已有决策冲突:
> 分类: 技术栈
> - **Web 框架**: 使用 Flask | **理由**: ... | *2026-06-01*

新决策将替换旧决策。确认？
```

Only write after user approval.

### Step 5: Write or update

- **New category**: Create the `## Category` heading, add the entry underneath.
- **No conflict**: Add the entry under its category heading. Maintain alphabetical or logical order within the category.
- **Conflict resolved**: Replace the old entry with the new one in-place, or add with a strikethrough if user wants to preserve history:

```markdown
## 技术栈
- ~~**Web 框架**: 使用 Flask | **理由**: ... | *2026-06-01*~~
- **Web 框架**: 使用 FastAPI | **理由**: 需要 async | *2026-06-06*
```

### Category guidelines

Classify decisions into these common categories (create others as needed):
- **技术栈**: Frameworks, languages, libraries
- **数据存储**: Databases, file formats, caching
- **API 设计**: REST/GraphQL, endpoint conventions, auth
- **项目结构**: Directory layout, module organization
- **部署**: Hosting, CI/CD, containerization
- **测试**: Test frameworks, strategies

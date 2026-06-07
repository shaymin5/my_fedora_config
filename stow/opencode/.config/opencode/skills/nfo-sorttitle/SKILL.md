---
name: nfo-sorttitle
description: >-
  Add or fix sorttitle tags in NFO files (TV episodes and movies) for
  proper media library ordering. Use ONLY when the user explicitly asks
  to process .nfo files to fix sorting, or to add/update sorttitle tags
  in Kodi/Plex/Jellyfin NFO metadata. Do NOT trigger for general media
  library questions, naming conventions, metadata scraping, or other NFO
  editing tasks (plot, title, encoding, etc.) that are not about sorttitle.
---

# NFO Sorttitle Helper

## 背景

- Kodi/Plex/Jellyfin 等媒体中心使用 NFO (XML) 文件作为元数据
- `<sorttitle>` 标签控制媒体库中的排序顺序，优先级高于标题字母序
- 缺少 `<sorttitle>` 时，剧集可能按标题字母序而非集数顺序排列；电影系列也可能排序错乱

## 工作流程

### 1. 确认范围

询问用户要处理的目录和文件范围，确认 sorttitle 的取值格式：

- **剧集**：纯集号（如 `005`）还是季+集组合（如 `105`）
- **电影**：基于年份（如 `2001`）还是自定义序号（如 `01` 用于系列电影排序）

### 2. 识别目标文件

查找目标目录下的 `.nfo` 文件，根据根元素区分类型：

- **`<episodedetails>`**（剧集 NFO）：需要添加 sorttitle
- **`<movie>`**（电影 NFO）：需要添加 sorttitle
- **`tvshow.nfo`**：通常不需要，但按用户要求处理

### 3. 检查是否已有 sorttitle

对每个文件先检查是否已包含 `<sorttitle>` 标签，有则跳过或询问用户是否需要更新。

### 4. 确定取值来源

从 NFO 文件内容中提取标识符，不依赖文件名：

**剧集 NFO：**
- 读取 `<season>` 标签获取季号
- 读取 `<episode>` 标签获取集号
- 按用户要求的格式组合

**电影 NFO：**
- 读取 `<year>` 或 `<premiered>` 标签中的年份
- 或从 `<set>`（系列/tag）标题推断系列顺序
- 如果无法从 XML 提取，询问用户希望用什么值

### 5. 确定插入位置

插入 `<sorttitle>` 的原则：放在相关标识标签之后，保持 XML 结构清晰。

**剧集 NFO 常见做法：**
- 纯集号排序：在 `<episode>` 标签之后
- 季+集排序：在 `<season>`, `<episode>` 这一组标签之后

**电影 NFO 常见做法：**
- 按年份排序：在 `<year>` 或 `<premiered>` 标签之后
- 按系列顺序：在 `<title>` 之后
- 保持与文件现有对齐风格一致的缩进

### 6. 执行

使用 `uv run python3` 编写内联脚本来处理 XML。注意：
- 优先使用 `xml.etree.ElementTree` 做精确操作，避免破坏文件
- 如果文件结构较复杂或不确定，先读文件预览，不要盲目操作
- 处理后验证 XML 是否仍然合法

### 7. 验证

随机抽查几个已修改的文件确认：
- `<sorttitle>` 出现在正确位置
- 值与对应的标识符匹配
- XML 结构完整

## 示例

**剧集 NFO（纯集号排序）：**
```xml
<episodedetails>
  <title>使徒來襲</title>
  <season>1</season>
  <episode>5</episode>
```
插入 sorttitle 后：
```xml
  <episode>5</episode>
  <sorttitle>005</sorttitle>
```

**电影 NFO（按年份排序）：**
```xml
<movie>
  <title>千与千寻</title>
  <year>2001</year>
```
插入 sorttitle 后：
```xml
  <year>2001</year>
  <sorttitle>2001</sorttitle>
```

## 边界情况

| 情况 | 处理方式 |
|---|---|
| 已有 sorttitle | 跳过，或询问用户是否要覆盖 |
| 缺少 season/episode 标签 | 向用户询问，或从文件名推断 |
| 电影 NFO 无 year 标签 | 向用户询问用什么值 |
| 多个剧集/电影混合在同一目录 | 按 `<showtitle>` 或根元素类型区分，分别处理 |
| 流程半路中断 | 可重复执行，已有 sorttitle 的文件会自动跳过 |

---
name: anime-nfo-generator
description: |
  为动画剧集的 MKV 文件自动生成 Kodi/Jellyfin/Plex/Emby 兼容的 NFO 元数据文件。
  
  当用户需要让播放器识别动画的剧集标题时使用此 skill。关键判断标准：
  - 用户的目标是"生成/创建 NFO 文件"（而非排查已存在的 NFO 为什么失效）
  - 用户说的是"剧集标题/集数/各话信息"（而非视频编码、分辨率、码率等技术参数）
  
  典型触发场景：
  - Jellyfin/Plex/Kodi/Emby/Infuse 里动画显示为 Unknown Episode，需要补全标题
  - 有 MKV 文件但缺少 tvshow.nfo 或 episode NFO，需要从零生成
  - 想为动画匹配 Wikipedia 上的各话标题、创建元数据文件
  - 用户说"生成nfo""刮削剧集""匹配标题""补媒体库信息""动画没标题"
  
  明确不触发：
  - NFO 文件已存在但播放器扫不到（Kodi 配置问题，不是生成问题）
  - ffmpeg/mkvmerge 操作mkv封装
  - 提取视频技术元数据做统计（编码/分辨率/码率→CSV）
  - 单纯重命名文件、修改已有 XML/NFO 内容
---

# Anime NFO Generator

## 概述

三步流水线：扫描 MKV → 获取标题（Wikipedia） → 生成 NFO。

**核心原则**：用 `scripts/` 下的脚本处理确定性逻辑（解析、生成），LLM 只负责语义判断（找对 Wikipedia URL、区分 TV/OVA、映射文件名到集数）。这样极大减少 token 消耗。

## 流水线

### 步骤 1：扫描 MKV 文件

```bash
uv run python scripts/scan_mkv.py <目录> --pattern="*.mkv"
```

输出 JSON，包含每个 MKV 的路径、轨道信息（codec/channels/resolution/language）。

从文件名中提取集数信息（如 `[01]` → 第 1 话），用于后续与 Wikipedia 数据的匹配。

### 步骤 2：获取各话标题

**优先级：中文 Wikipedia → 日语 Wikipedia raw → 英语 Wikipedia**

#### 2.1 收集作品信息

从目录名/文件名推断作品名和年份。用 WebFetch 查阅英文 Wikipedia 确认：
```
https://en.wikipedia.org/wiki/<SeriesName>
```
获取：原作名（用于日语 Wikipedia URL）、首播年份、总集数、OVA 名。

#### 2.2 获取标题数据

**中文 Wikipedia 优先**：
```
https://zh.wikipedia.org/wiki/<作品名>
```
如果 404，尝试简体/繁体变体、不同的括号字符（`〜` vs `～`）。

**日语 Wikipedia（回退）**：
使用 `action=raw` 获取原始 wikitext（远比 Markdown 页面可靠）：
```
https://ja.wikipedia.org/w/index.php?title=<作品名>&action=raw
```

然后用脚本解析：
```bash
# 从已保存的文件
uv run python scripts/parse_wikipedia.py page.txt

# 或管道输入
uv run python scripts/parse_wikipedia.py --lang=ja page.txt
```

脚本自动识别 `{{エピソードリスト/base}}` 模板提取 TV 标题+日期，以及 OVA 章节的 `* 『...』` 格式。

**英语 Wikipedia（最后回退）**：
```bash
uv run python scripts/parse_wikipedia.py --lang=en page.md
```

输出格式：
```json
{
  "tv_episodes": [{"number": 1, "title": "恐怖の新学期！謎の鬼の手", "aired": "1996-04-13"}, ...],
  "ovas": [{"number": 1, "title": "決戦!陽神の術vs壁男", "aired": "1998-09-21"}, ...]
}
```

#### 2.3 中文标题搜索技巧

- 中文 Wikipedia 的 URL 需要正确编码。如果直接访问 404，尝试用浏览器搜索 `site:zh.wikipedia.org <作品名>` 
- 百度百科（`baike.baidu.com`）403 的情况下，尝试 Bangumi
- Bangumi 搜索：`https://bgm.tv/subject_search/<作品名>?cat=2`

### 步骤 3：生成 NFO 文件

将步骤 1 扫描的文件路径与步骤 2 的标题数据组装成 JSON spec，传给脚本：

```bash
uv run python scripts/generate_nfo.py spec.json
# 或管道
echo '{"directory":"...","tvshow":{...},"episodes":[...]}' | uv run python scripts/generate_nfo.py
```

**Spec JSON 格式**：
```json
{
  "directory": "/path/to/anime",
  "tvshow": {
    "title": "地獄先生ぬ〜べ〜",
    "originaltitle": "Jigoku Sensei Nūbē",
    "year": 1996,
    "premiered": "1996-04-13",
    "studio": "Toei Animation",
    "genres": ["Animation", "Comedy", "Horror", "Supernatural"]
  },
  "episodes": [
    {
      "mkv_basename": "[Group][01][...]",
      "title": "恐怖の新学期！謎の鬼の手",
      "season": 1,
      "episode": 1,
      "aired": "1996-04-13"
    }
  ]
}
```

**规则**：
- `mkv_basename` 是 MKV 文件去除 `.mkv` 扩展名后的部分（脚本自动加 `.nfo`）
- TV 正片 → `season=1`，OVA/特别篇 → `season=0`
- OVA 在子目录中的，`mkv_basename` 要包含子目录路径（相对于 `directory`）
- 文件名可能有变体（如 `[FLAC+AC3]` vs `[FLAC]`），确保 `mkv_basename` 与实际 MKV 文件名匹配

### 步骤 4：校验

生成完毕后运行自动校验，一次性检查所有常见问题：

```bash
uv run python scripts/validate.py <目录> --tv-episodes <N> --ova-episodes <N>
```

**校验项目**：

| 检查项 | 说明 |
|---|---|
| MKV-NFO 配对 | 每个 MKV 有对应 NFO，无孤儿文件 |
| NFO XML 格式 | 有效 XML，根标签正确，必填字段存在 |
| 标题编码 | 无空标题、无乱码字符 |
| 季节编号 | TV=S01，OVA=S00，无重复 SxE 组合 |
| 播出日期 | YYYY-MM-DD 格式合法性 |
| 集数统计 | 总数与预期一致 |

全部通过后才算完成。如果有报错，修复后重新生成对应的 NFO 即可。

## 环境约束

- **禁止使用系统 `python3`、`pip3`**，必须使用 `uv run python`
- 脚本路径：`<skill-base>/scripts/scan_mkv.py`、`parse_wikipedia.py`、`generate_nfo.py`
- 所有临时文件写入 `/tmp/` 下

## 常见陷阱

1. **Wikipedia URL 编码**：特殊字符（`〜`、`〜`、`・`）需正确编码或使用英文 Wikipedia 重定向
2. **action=raw vs Markdown**：`action=raw` 获取原始 wikitext 更可靠，Markdown 转换会丢失表格数据
3. **文件命名差异**：不同集的文件名模式可能略有差异，读取实际目录列表动态匹配
4. **Wikipedia 截断**：大页面会截断，`action=raw` 通常不截断
5. **OVA 解析**：日语 Wikipedia 的 OVA 在独立章节，用 `* 『title』date` 格式，不在 `{{エピソードリスト}}` 模板中
6. **标题清理**：`{{nobr|...}}`、`{{efn2|...}}`、`<br/>` 等 wiki 标记由 `parse_wikipedia.py` 自动处理

## 示例

用户说："帮这个动画目录生成带中文标题的 NFO"

1. `ls` 查看目录内容和文件命名格式
2. `uv run python scripts/scan_mkv.py <dir>` 获取 MKV 元数据
3. 根据文件名推断作品 → WebFetch 英文 Wikipedia 确认作品详情
4. WebFetch 日语 Wikipedia `action=raw` → `uv run python scripts/parse_wikipedia.py`
5. 用编辑工具将标题数据与文件路径组装成 spec JSON
6. `uv run python scripts/generate_nfo.py spec.json`
7. 验证 1-2 个生成的 NFO 文件

---
name: music-lyrics-matcher
description: >
  给音乐文件批量匹配歌词并生成同名 .lrc，按「歌曲 / 专辑 / 时长 / 版本」对齐，
  优先带时间轴（同步歌词）；并在 lrc 顶部写入可显示的曲目信息（标题/专辑/作词/作曲/歌手），
  纯音乐的歌也照常生成（写「纯音乐」占位）。
  当用户想给专辑或一批曲目配歌词、补歌词、生成/下载 lrc、说「播放器里没歌词」
  「歌词对不上」「给这个专辑加歌词」「歌词文件缺失」时使用本 skill。支持 mp3/flac/
  opus/m4a/ogg 等多种格式。
  关键判断：目标是「获取/生成歌词内容」。若意图是清理已有 lrc 里的错乱内容、判断
  哪个 lrc 是垃圾、或改文件名/标签，那不是本 skill（前者归 music-metadata-fixer）。
  生成 NFO/刮削是 anime-nfo-generator 的职责。
  English: fetch lyrics for an album and write matching .lrc files — match by title,
  album, duration and version, prefer time-synced lyrics, and put the track's title /
  album / lyricist / composer / artist at the top as displayable timestamped lines;
  inherently instrumental tracks still get an .lrc with a 纯音乐 placeholder.
compatibility: mutagen (uv run --with mutagen python ...); 需要联网访问歌词数据源
---

# Music Lyrics Matcher

## 这个 skill 要什么结果

每个音频旁边有一个**同名 `.lrc`**，歌词内容尽量**带时间轴**，并且在文件顶部有可显示的
曲目信息（有歌词时 5 行，纯音乐时 4 行 + `纯音乐`）。做到这几点就算成功，过程怎么走不重要。

## 一、匹配质量是核心，不是流程

一首歌词能不能用，取决于这些信息**对得上**：

- **歌曲**（标题）
- **专辑**
- **时长**（最硬的判据——标题可能被翻译或转写，时长不会骗人）
- **版本**（原版 / 翻唱 / Remix / Director's Edit / AYANAMI Version 等，必须区分）

判断的次序大致是：先让标题、专辑对得上，再用**时长和版本**确认。标题因为**罗马音、
别名写法、翻译**而比不中时，不要就此放弃——回到时长和版本来兜底。

- 时长容差默认 ±12s（`--duration-tol`），转换格式导致的几秒偏差属正常。
- 少数拿不准的曲目可以停下问用户；但**不需要逐首让用户确认**，整体跑完给结论即可。

## 二、去哪拿歌词 —— 保持灵活

不要把「从某个站拿」写死成唯一路径。**自行选择合适的歌词数据源**，判断标准永远是
上面第一条：能对上就用。要点：

- **带时间轴的优先**，纯文本只在实在找不到带时间轴版本时兜底。
- 数据源往往同时提供**作词 / 作曲**信息，顺手取来备用。
- 同一个源里同一首歌常有多条投稿，其中可能有错别字、时长异常或错误的版本——按第一条
  的打分挑最干净、最吻合的那条。

`scripts/fetch_lyrics.py` 是一个**开箱可用的帮手**（内置 lrclib、网易云两个源），
不是唯一途径；需要时也可以用别的来源，或自己写查询。

## 三、输出偏好（这个 skill 最要紧的部分）

### 顶部放 5 行「可显示」的曲目信息

不用 `[ti:]` `[ar:]` `[al:]` `[ly:]` `[mu:]` 这类头部标签，而是把信息写成**普通歌词
行**，让任何播放器都能显示：

```
[00:00.00]残酷な天使のテーゼ
[00:00.29]新世紀エヴァンゲリオン｜EVANGELION FINALLY
[00:00.58]作词：及川眠子
[00:00.87]作曲：佐藤英敏
[00:01.16]歌手：高橋洋子
[00:01.46]残酷な天使のように      ← 第一句真正的歌词
```

- 顺序固定：**标题 / 专辑 / 作词 / 作曲 / 歌手**，各占一行。
- **时间戳规则**：把**第一句歌词的时间 T 五等分**，5 行落在 `0、T/5、2T/5、3T/5、4T/5`
  （间隔 = T/5）。这样它们都排在真正的歌词之前，又不会挤在 0 秒同一点。
  例如首句在 `[00:01.46]`，5 行就是 0.00 / 0.29 / 0.58 / 0.87 / 1.16。
- 作词 / 作曲 / 歌手 要有可靠出处：优先从歌词数据源取；取不到作词作曲时用原曲作者
  （例如《FLY ME TO THE MOON》→ Bart Howard），仍不确定就问用户，不要瞎编。

### 纯音乐的歌：照样生成 lrc

**本身就是纯音乐、压根没有歌词**的曲目（BGM／Instrumental／伴奏），也要给它生成
`.lrc`，内容是纯文本、**不带任何时间戳**：

```
孤独の戦士 (M-10)
新世紀エヴァンゲリオン｜EVANGELION FINALLY
作词：—
作曲：鷺巣詩郎

纯音乐
```

即：**4 行信息**（标题 / 专辑 / 作词 / 作曲，纯音乐没有歌手所以不加「歌手」行）→
**一个空行** → 一行 `纯音乐`。

注意区分两种情况，别搞混：

- **纯音乐的歌**（本来就没歌词）→ 按上面生成「纯音乐」lrc。
- **有歌词、只是一时没找到** → 按原方式处理（不要伪造「纯音乐」占位，留给用户解决）。
  数据源明确标注 instrumental，或曲名带 Instrumental／Off Vocal／カラオケ／伴奏等字样时，
  才算「纯音乐」。

### 顶部要清洗，正文要保留

处理**往往不是一次完成**：可能先拿到原文歌词，用户手动加了翻译，再回来做顶部信息。
所以对一个已存在的 `.lrc`：

- **删掉顶部冗余**：`[ti:]` `[ar:]` `[al:]` `[ly:]` `[mu:]` `[by:]` `[offset:]` 等
  头部标签，以及之前插入过的信息行（5 行或纯音乐块），都先移除再重放。
- **只动顶部信息区，不碰歌词正文**——包括用户手动加进去的双语翻译行，必须原样保留。
  （唯一例外是**格式规整**：去掉时间戳与歌词之间的多余空格、去掉行尾空白，见下。）
- **时间戳后不留空格**：统一写成 `[00:00.15]歌词`，不要 `[00:00.15] 歌词`。不同歌词源
  带不带这个空格不一致（lrclib 常有、网易云常没有），所以写入前一律规整：标签与文本
  之间、以及多个标签之间的空白都去掉，行尾空白也去掉；除此之外不改动内容。
- **可反复运行**：同一目录跑多次，结果稳定，不重复堆叠，不丢正文。

## 四、流程（轻量三步）

1. **配歌词**：扫描音频、读元数据，按第一条匹配，写同名 `.lrc`（先 dry-run 看结果，
   满意再 `--write`）。
   > 若某个 `.lrc` **已经有歌词正文**（可能还含用户手改的翻译），**不要重新抓取覆盖它**，
   > 直接跳到第 2 步只修顶部即可。
2. **格式化顶部**：清洗顶部 + 按 T/5 放 5 行信息；纯音乐则写 4 行 + `纯音乐`
   （`format_lrc.py`）。
3. **自检**：每个音频都有 lrc；时间轴正确；5 行都早于第一句且间隔为 T/5；纯音乐是
   4 行 + 空行 + `纯音乐`；顶部无残留头部标签；时间戳后无多余空格；原有翻译行还在。

## 五、脚本

```bash
# 读取任意格式的标签/时长（mp3/flac/opus/m4a/ogg…）都走 mutagen
# 1) 匹配并可选写入歌词（默认 dry-run）
uv run --with mutagen python scripts/fetch_lyrics.py DIR [--write] [--recursive] \
    [--sources lrclib,netease] [--duration-tol 12] [--report report.json]

# 2) 在顶部放 5 行信息（纯音乐则写 4 行 + 纯音乐；默认 dry-run，幂等）
uv run --with mutagen python scripts/format_lrc.py DIR [--write] [--recursive] \
    [--credits report.json] [--no-netease] [--instrumental "文件A,文件B"]

# 3) 校验（可选）
uv run python scripts/check_lrc.py DIR [--recursive]
```

- `fetch_lyrics.py` 的 `--report` 会输出每条匹配到的来源/时长/作词作曲，以及是否为
  纯音乐，供 `format_lrc.py --credits` 直接复用（也支持手写一个
  `{文件名: {lyricist, composer}}`）。`--instrumental` 可手动指定纯音乐文件。
- 两个脚本默认都**只打印、不写文件**，确认后再加 `--write`。

## 六、边界（明确不做）

- **不清理已有 lrc 的内容对错 / 不判断哪个 lrc 是垃圾** → music-metadata-fixer。
- **不改文件名、不改音频标签** → music-metadata-fixer。
- **不生成 NFO / 不刮削** → anime-nfo-generator。
- **不做音频转码、不做播放器/服务器配置**。

## 七、环境约束

- 禁止系统 `python`/`python3`/`pip`，一律 `uv run python`（脚本依赖 `--with mutagen`）。
- 临时/中间文件写 `/tmp/` 下。

## 八、示例

用户说：「给这个专辑每首歌配歌词，存成 lrc」。

1. `ls` 看目录里有哪些音频（可能是 mp3/flac/opus 混合）。
2. `uv run --with mutagen python scripts/fetch_lyrics.py DIR --report /tmp/rep.json`
   看匹配情况；对不上或版本可疑的，回到第一条用时长/版本核对，必要时换来源或问用户。
3. 满意后加 `--write`。
4. `uv run --with mutagen python scripts/format_lrc.py DIR --credits /tmp/rep.json --write`
   清洗顶部并放 5 行信息（纯音乐会写成 4 行 + `纯音乐`）。
5. `uv run python scripts/check_lrc.py DIR` 自检，把结果报给用户。

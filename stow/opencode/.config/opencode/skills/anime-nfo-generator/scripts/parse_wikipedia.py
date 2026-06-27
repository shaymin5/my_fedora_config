"""
Parse Japanese Wikipedia raw wikitext to extract episode/OVA titles and airdates.

Usage:
    uv run python parse_wikipedia.py <raw_wikitext_file>
    # or pipe from stdin:
    cat page.txt | uv run python parse_wikipedia.py -

Output JSON to stdout:
{
  "tv_episodes": [
    {"number": 1, "title": "...", "aired": "1996-04-13"},
    ...
  ],
  "ovas": [
    {"number": 1, "title": "...", "aired": "1998-09-21"},
    ...
  ]
}

Also supports English Wikipedia markdown via --lang=en mode:
    uv run python parse_wikipedia.py --lang=en page.md
"""
import re, sys, json


def clean_title(title: str) -> str:
    """Remove wiki markup noise from a title string."""
    # Remove {{nobr|...}} wrapping
    title = re.sub(r'\{\{nobr\|(.+?)\}\}', r'\1', title)
    # Remove {{efn2|...}} footnotes
    title = re.sub(r'\{\{efn2.*?\}\}', '', title)
    # Remove <br /> tags
    title = re.sub(r'<br\s*/?>', '', title)
    # Remove [[wiki link]] markup, keep text
    title = re.sub(r'\[\[([^\]|]+?)\]\]', r'\1', title)
    title = re.sub(r'\[\[[^\]]+\|([^\]]+)\]\]', r'\1', title)
    # Remove reference tags
    title = re.sub(r'<ref[^>]*>.*?</ref>', '', title)
    title = re.sub(r'<ref[^>]*/>', '', title)
    # Strip whitespace
    title = title.strip()
    return title


def parse_ja_wikitext(text: str) -> dict:
    """
    Parse Japanese Wikipedia raw text for TV episode list and OVA section.
    Handles the {{エピソードリスト/base}} template format.
    """
    tv_episodes = []

    # Find TV episode section
    tv_section_start = text.find("各話リスト（1996年版テレビアニメ）")
    if tv_section_start < 0:
        tv_section_start = text.find("各話リスト")
    if tv_section_start < 0:
        # Try finding by episode list templates directly
        tv_section_start = 0

    tv_section_end = text.find("放送局", tv_section_start)
    if tv_section_end < 0:
        tv_section_end = text.find("主題歌", tv_section_start)
    if tv_section_end < 0:
        tv_section_end = len(text)

    tv_section = text[tv_section_start:tv_section_end]

    # Parse TV episode templates
    ep_pattern = re.compile(
        r'\{\{エピソードリスト/base\n\| Number = .*?\n\| Title = (.+?)\n.*?\| Aux4 = (.*?)\n',
        re.DOTALL
    )
    for i, m in enumerate(ep_pattern.finditer(tv_section), 1):
        title = clean_title(m.group(1))
        aired_raw = m.group(2).strip()

        # Parse Japanese date format: "'''1996年'''<br />4月13日" or just "4月20日"
        year_match = re.search(r"(\d{4})年", aired_raw)
        month_day = re.search(r"(\d{1,2})月(\d{1,2})日", aired_raw)
        aired = ""
        if year_match or month_day:
            year = year_match.group(1) if year_match else "1996"
            month = month_day.group(1).zfill(2) if month_day else "01"
            day = month_day.group(2).zfill(2) if month_day else "01"
            aired = f"{year}-{month}-{day}"

        tv_episodes.append({
            "number": i,
            "title": title,
            "aired": aired
        })

    # Parse OVA section
    ovas = []
    ova_section_start = text.find("=== OVA ===")
    if ova_section_start > 0:
        ova_section_end = text.find("\n==", ova_section_start + 10)
        if ova_section_end < 0:
            ova_section_end = len(text)
        ova_section = text[ova_section_start:ova_section_end]

        # OVAs are listed with *  prefix in Japanese Wikipedia
        # Format: * 『Series Name - OVA Title』YYYY年MM月DD日発売
        ova_pattern = re.compile(
            r'\*\s*『(.+?)』(\d{4})年(\d{1,2})月(\d{1,2})日'
        )
        for i, m in enumerate(ova_pattern.finditer(ova_section), 1):
            full_title = clean_title(m.group(1).strip())
            # Strip common series name prefix if present (e.g. "地獄先生ぬ〜べ〜 ")
            # but keep it if the title would be too short
            short_title = full_title.split(" ", 1)[-1] if " " in full_title else full_title
            aired = f"{m.group(2)}-{m.group(3).zfill(2)}-{m.group(4).zfill(2)}"
            ovas.append({
                "number": i,
                "title": short_title,
                "aired": aired
            })

    return {"tv_episodes": tv_episodes, "ovas": ovas}


def parse_en_markdown(text: str) -> dict:
    """
    Parse English Wikipedia markdown for episode list.
    Pattern: number on its own line, followed by "Title" in quotes.
    """
    tv_episodes = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r'^(\d{1,2})\s*$', line)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 60:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    title_line = lines[j].strip()
                    t = re.match(r'^"(.+?)"\s*$', title_line)
                    if t:
                        tv_episodes.append({
                            "number": num,
                            "title": t.group(1),
                            "aired": ""
                        })
        i += 1
    return {"tv_episodes": tv_episodes, "ovas": []}


def main():
    lang = "ja"
    input_file = None
    args = sys.argv[1:]

    while args:
        if args[0].startswith("--lang="):
            lang = args[0].split("=", 1)[1]
            args.pop(0)
        else:
            input_file = args[0]
            args.pop(0)

    if input_file and input_file != "-":
        with open(input_file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if lang == "en":
        result = parse_en_markdown(text)
    else:
        result = parse_ja_wikitext(text)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

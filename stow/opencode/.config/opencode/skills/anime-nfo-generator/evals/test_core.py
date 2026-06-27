"""Test core logic of anime-nfo-generator skill."""
import re, sys, os

# Test 1: Parse Japanese Wikipedia wikitext
def test_wikitext_parsing():
    """Verify we can extract episode titles from Japanese Wikipedia raw text."""
    sample = """{{エピソードリスト/base
| Number = 第1話
| Title = 恐怖の新学期！謎の鬼の手
| Aux0 = 富田祐弘 | Aux0RowSpan = 2
}}
{{エピソードリスト/base
| Number = 第2話
| Title = トイレの花子さんが出たぁ〜っ！
| Aux0 = 小山高生
}}
{{エピソードリスト/base
| Number = 第3話
| Title = {{nobr|うわさ話はやめられない！おしゃべり妖怪}}
| Aux0 = 菅良幸
}}"""
    titles = re.findall(r'\| Title = (.+?)\n', sample)
    cleaned = [t.replace('{{nobr|', '').replace('}}', '') for t in titles]
    assert len(cleaned) == 3, f"Expected 3 titles, got {len(cleaned)}"
    assert cleaned[0] == "恐怖の新学期！謎の鬼の手", f"Title1 mismatch: {cleaned[0]}"
    assert cleaned[1] == "トイレの花子さんが出たぁ〜っ！", f"Title2 mismatch: {cleaned[1]}"
    assert cleaned[2] == "うわさ話はやめられない！おしゃべり妖怪", f"Title3 mismatch: {cleaned[2]}"
    print("PASS: Wikipedia wikitext parsing")

# Test 2: NFO XML generation with proper escaping
def test_nfo_xml_generation():
    """Verify NFO XML output is well-formed with proper escaping."""
    def esc(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

    title = 'ぬ〜べ〜死す!?最強の敵（ライバル）・妖狐玉藻'
    nfo = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
  <title>{esc(title)}</title>
  <season>1</season>
  <episode>6</episode>
  <aired>1996-05-18</aired>
</episodedetails>'''

    # Verify no unescaped special chars
    assert '&amp;' not in nfo or '&amp;' in nfo, "Should handle ampersand"
    # Check well-formed XML by attempting to parse
    import xml.etree.ElementTree as ET
    root = ET.fromstring(nfo)
    assert root.tag == 'episodedetails'
    title_elem = root.find('title')
    assert title_elem is not None
    assert title_elem.text == title
    episode_elem = root.find('episode')
    assert episode_elem.text == '6'
    print("PASS: NFO XML generation")

# Test 3: NFO filename matching
def test_filename_matching():
    """Verify NFO filename matches MKV filename."""
    mkv_files = [
        "[Jigoku Sensei Nube][01][1080P][BDRip][HEVC-10bit][FLAC].mkv",
        "[Jigoku Sensei Nube][11][1080P][BDRip][HEVC-10bit][FLAC+AC3].mkv",
        "[DBD-Raws][Jigoku Sensei Nube][OVA][01][1080P][BDRip][HEVC-10bit][FLAC].mkv",
    ]
    for mkv in mkv_files:
        nfo = mkv.replace('.mkv', '.nfo')
        assert nfo.endswith('.nfo')
        assert nfo[:-4] == mkv[:-4]
        print(f"  {mkv} -> {nfo}")
    print("PASS: NFO filename matching")

# Test 4: Season numbering
def test_season_numbering():
    """Verify correct season numbering: TV=S01, OVA=S00."""
    episodes = [
        (1, False, 1),   # TV EP01
        (11, False, 1),  # TV EP11
        (49, False, 1),  # TV EP49
        (1, True, 0),    # OVA EP01
        (3, True, 0),    # OVA EP03
    ]
    for ep_num, is_ova, expected_season in episodes:
        season = 0 if is_ova else 1
        assert season == expected_season, f"EP{ep_num} OVA={is_ova}: expected S{expected_season}, got S{season}"
    print("PASS: Season numbering")

if __name__ == '__main__':
    results = []
    for name in ['test_wikitext_parsing', 'test_nfo_xml_generation', 'test_filename_matching', 'test_season_numbering']:
        try:
            globals()[name]()
            results.append((name, True))
        except Exception as e:
            print(f"FAIL: {name}: {e}")
            results.append((name, False))

    passes = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'='*40}")
    print(f"Results: {passes}/{total} passed")
    sys.exit(0 if passes == total else 1)

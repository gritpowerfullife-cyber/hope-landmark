"""네이버 블로그 RSS에서 교육 관련 글만 골라 data/posts.json 으로 저장합니다.

GitHub Actions가 하루 한 번 실행합니다. RSS에는 최근 50개 글만 있으므로
이전에 저장한 글과 합쳐서 교육 글이 쌓이도록 합니다.
"""
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

RSS_URL = "https://rss.blog.naver.com/diamond31.xml"
OUT = Path(__file__).resolve().parent.parent / "data" / "posts.json"
KEEP = 12

# 홈페이지에 보여줄 카테고리 (이름 앞부분으로 비교)
CATEGORIES = ("일｜입시·교육", "고등", "중등", "초등", "부모", "코칭", "영어콘텐츠")


def clean(text, limit=None):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def fetch():
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    posts = []
    for item in root.iter("item"):
        cat = clean(item.findtext("category"))
        if not cat.startswith(CATEGORIES):
            continue
        link = (item.findtext("link") or "").split("?")[0]
        date = parsedate_to_datetime(item.findtext("pubDate")).date().isoformat()
        posts.append({
            "title": html.unescape(item.findtext("title") or "").strip(),
            "link": link,
            "date": date,
            "category": cat.split("｜")[-1],
            "summary": clean(item.findtext("description"), 110),
        })
    return posts


def main():
    old = []
    if OUT.exists():
        old = json.loads(OUT.read_text(encoding="utf-8")).get("posts", [])
    merged = {p["link"]: p for p in old}
    merged.update({p["link"]: p for p in fetch()})
    posts = sorted(merged.values(), key=lambda p: p["date"], reverse=True)[:KEEP]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"posts": posts}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(posts)} posts")


if __name__ == "__main__":
    main()

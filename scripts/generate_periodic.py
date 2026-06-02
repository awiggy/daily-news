"""Generate weekly/monthly index & summary from daily digests.
Runs as part of the daily workflow. Only generates when it's the right day.
"""
import re, os
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

POSTS_DIR = Path("docs/_posts")
SUMMARY_DIR = Path("data/summaries")

def extract_headlines(md_text, max_items=10):
    """Extract top headlines from a digest file (highest scored items)."""
    headlines = []
    for line in md_text.split("\n"):
        # Match: "1. [Title](url) 9.0/10" format
        m = re.match(r"\d+\.\s*\[(.+?)\]\((.+?)\)\s+.*?(\d+\.?\d*)/10", line)
        if m:
            headlines.append({"title": m.group(1), "url": m.group(2), "score": float(m.group(3))})
    return sorted(headlines, key=lambda x: x["score"], reverse=True)[:max_items]

def generate_weekly(dates, lang="zh"):
    """Generate weekly report from daily digests."""
    now = datetime.now()
    week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")

    all_headlines = []
    tag_counter = Counter()

    for date_str in sorted(dates):
        post_file = POSTS_DIR / f"{date_str}-summary-{lang}.md"
        if not post_file.exists():
            continue
        text = post_file.read_text(encoding="utf-8")
        headlines = extract_headlines(text)
        all_headlines.extend(headlines)

        # Count tags
        for line in text.split("\n"):
            tag_match = re.findall(r"`#([^`]+)`", line)
            for t in tag_match:
                for tag in t.split():
                    tag_counter[tag.strip("#")] += 1

    if not all_headlines:
        return None

    top_tags = tag_counter.most_common(8)
    top10 = sorted(all_headlines, key=lambda x: x["score"], reverse=True)[:15]

    lang_label = "ZH" if lang == "zh" else "EN"
    title_prefix = "本周要闻" if lang == "zh" else "Weekly Digest"

    md = f"""# {title_prefix} — {week_start} ~ {week_end}

> 从 {len(dates)} 天日报中精选

---

## 高分头条 Top 15

"""
    for i, h in enumerate(top10, 1):
        md += f"{i}. [{h['title']}]({h['url']}) ⭐{h['score']:.1f}\n"

    md += f"""
---

## 本周高频话题

"""
    for tag, count in top_tags:
        md += f"- `#{tag}` ×{count}\n"

    md += f"""
---

## 覆盖日期

"""
    for d in sorted(dates, reverse=True):
        md += f"- [{d}]({d}/summary-{lang}.html)\n"

    return md

def generate_monthly(dates, lang="zh"):
    """Generate monthly report from daily digests."""
    now = datetime.now()
    month_label = now.strftime("%Y年%m月") if lang == "zh" else now.strftime("%B %Y")

    all_headlines = []
    tag_counter = Counter()

    for date_str in sorted(dates):
        post_file = POSTS_DIR / f"{date_str}-summary-{lang}.md"
        if not post_file.exists():
            continue
        text = post_file.read_text(encoding="utf-8")
        headlines = extract_headlines(text)
        all_headlines.extend(headlines)
        for line in text.split("\n"):
            tag_match = re.findall(r"`#([^`]+)`", line)
            for t in tag_match:
                for tag in t.split():
                    tag_counter[tag.strip("#")] += 1

    if not all_headlines:
        return None

    top_tags = tag_counter.most_common(12)
    top10 = sorted(all_headlines, key=lambda x: x["score"], reverse=True)[:20]

    title_prefix = "本月要闻" if lang == "zh" else "Monthly Digest"

    md = f"""# {title_prefix} — {month_label}

> 从 {len(dates)} 天日报中精选 · 共 {len(all_headlines)} 条高分内容

---

## 高分头条 Top 20

"""
    for i, h in enumerate(top10, 1):
        md += f"{i}. [{h['title']}]({h['url']}) ⭐{h['score']:.1f}\n"

    md += f"""
---

## 本月高频话题

"""
    for tag, count in top_tags:
        md += f"- `#{tag}` ×{count}\n"

    md += f"""
---

## 覆盖日期

"""
    for d in sorted(dates, reverse=True):
        md += f"- [{d}]({d}/summary-{lang}.html)\n"

    return md

def main():
    now = datetime.now()
    is_saturday = now.weekday() == 5  # Monday=0, Saturday=5
    is_last_day = now.day == (now.replace(day=28) + timedelta(days=4)).replace(day=1).day - 1 or now.day == 31
    # Simpler: last day = tomorrow is a new month
    is_last_day = (now + timedelta(days=1)).day == 1

    # Get all dates from post files
    dates = set()
    for f in POSTS_DIR.glob("*-summary-zh.md"):
        dates.add(f.name[:10])
    dates = sorted(dates)

    if not dates:
        print("No digest files found")
        return

    # Generate weekly on Saturday or when explicitly requested
    if is_saturday or os.environ.get("FORCE_WEEKLY"):
        for lang in ["zh", "en"]:
            report = generate_weekly(dates, lang)
            if report:
                week_str = now.strftime("%Y-W%W")
                post_file = POSTS_DIR / f"{week_str}-weekly-{lang}.md"
                post_file.write_text(report, encoding="utf-8")
                # Also save to summaries
                sum_file = SUMMARY_DIR / f"horizon-{week_str}-weekly-{lang}.md"
                sum_file.write_text(report, encoding="utf-8")
                print(f"Generated weekly {lang}: {post_file}")
    else:
        print(f"Not Saturday ({now.strftime('%A')}), skipping weekly")

    # Generate monthly on last day or when explicitly requested
    if is_last_day or os.environ.get("FORCE_MONTHLY"):
        for lang in ["zh", "en"]:
            report = generate_monthly(dates, lang)
            if report:
                month_str = now.strftime("%Y-%m")
                post_file = POSTS_DIR / f"{month_str}-monthly-{lang}.md"
                post_file.write_text(report, encoding="utf-8")
                sum_file = SUMMARY_DIR / f"horizon-{month_str}-monthly-{lang}.md"
                sum_file.write_text(report, encoding="utf-8")
                print(f"Generated monthly {lang}: {post_file}")
    else:
        print(f"Not last day of month, skipping monthly")

if __name__ == "__main__":
    main()

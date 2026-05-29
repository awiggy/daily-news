"""Remove items from today's digest whose URLs already appeared in past 7 days."""
import re, os, sys, json
from pathlib import Path
from datetime import datetime, timedelta

POSTS_DIR = Path("docs/_posts")
LOOKBACK_DAYS = 7

def extract_urls(md_text):
    """Extract all markdown link URLs from digest text."""
    return set(re.findall(r'\]\((https?://[^\s\)]+)\)', md_text))

def main():
    today = datetime.now().strftime("%Y-%m-%d")

    # Collect URLs from past digests
    seen_urls = set()
    for f in sorted(POSTS_DIR.glob("*-summary-*.md")):
        # Skip today's files
        if today in f.name:
            continue
        # Only look at recent files
        try:
            date_str = f.name[:10]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if (datetime.now() - file_date).days > LOOKBACK_DAYS:
                continue
        except ValueError:
            continue

        text = f.read_text(encoding="utf-8")
        seen_urls.update(extract_urls(text))

    print(f"📚 Loaded {len(seen_urls)} seen URLs from past {LOOKBACK_DAYS} days")

    # Check today's digests for duplicates
    for lang in ["zh", "en"]:
        post_file = POSTS_DIR / f"{today}-summary-{lang}.md"
        if not post_file.exists():
            continue

        text = post_file.read_text(encoding="utf-8")
        today_urls = extract_urls(text)
        dupes = today_urls & seen_urls

        if dupes:
            print(f"  {lang}: found {len(dupes)} duplicate URLs")

            # Remove items with duplicate URLs
            # Each item is a section between --- separators
            sections = text.split("\n---\n")
            filtered = []
            removed = 0
            for section in sections:
                section_urls = extract_urls(section)
                if section_urls & seen_urls:
                    removed += 1
                else:
                    filtered.append(section)

            if removed > 0:
                new_text = "\n---\n".join(filtered)
                post_file.write_text(new_text, encoding="utf-8")
                # Also update the local summary file
                summary_file = Path("data/summaries") / f"horizon-{today}-{lang}.md"
                if summary_file.exists():
                    summary_file.write_text(new_text, encoding="utf-8")
                print(f"  {lang}: removed {removed} duplicate items, {len(filtered)} remaining")
        else:
            print(f"  {lang}: no duplicates found")

if __name__ == "__main__":
    main()

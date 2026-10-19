import json
import os
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://hr-nekretnine.hr/vrsta-natjecaja/prodaja-nekretnina/feed/"
OUT = Path("natjecaji.json")
COMMIT_MSG = Path("/tmp/commit.txt")
UA = {"User-Agent": "Mozilla/5.0 (compatible; git-scraper)"}

first_run = not OUT.exists()
archive = {} if first_run else {i["link"]: i for i in json.loads(OUT.read_text(encoding="utf-8"))}
known = set(archive)
fetched = []

# The feed only holds the latest ~10 items, older ones are on ?paged=2, 3...
# Walk pages until one brings nothing new: daily runs stop after page 1, the first run backfills everything.
for page in range(1, 51):
    try:
        req = urllib.request.Request(f"{FEED}?paged={page}", headers=UA)
        root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        if e.code == 404:  # past the last page
            break
        raise
    seen_now = known | {i["link"] for i in fetched}
    items = [
        {
            "title": item.findtext("title", "").strip(),
            "link": item.findtext("link", "").strip(),
            "published": parsedate_to_datetime(pub).date().isoformat() if (pub := item.findtext("pubDate")) else "",
        }
        for item in root.iter("item")
    ]
    fetched += items
    if not any(i["link"] not in seen_now for i in items):
        break
    time.sleep(2)

new = {} if first_run else {i["link"]: i for i in fetched if i["link"] not in known}
archive |= {i["link"]: i for i in fetched}
OUT.write_text(
    json.dumps(sorted(archive.values(), key=lambda i: (i["published"], i["link"]), reverse=True),
               ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

msg = [datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")]
if first_run:
    msg += ["", f"Initial archive: {len(archive)} items"]
if new:
    msg += ["", "New:"] + [f"- {i['title']} {i['link']}" for i in new.values()]
COMMIT_MSG.write_text("\n".join(msg) + "\n", encoding="utf-8")
print("\n".join(msg))

if new and (topic := os.environ.get("NTFY_TOPIC")):
    body = "\n\n".join(f"{i['title']}\n{i['link']}" for i in new.values())
    urllib.request.urlopen(
        urllib.request.Request(
            f"https://ntfy.sh/{topic}",
            data=body.encode(),
            headers={"Title": f"hr-nekretnine: {len(new)} new", "Tags": "house"},
        ),
        timeout=30,
    )
import csv
import datetime
import re

import bs4
import urllib3

http = urllib3.PoolManager(
    headers={"User-Agent": "https://sethmlarson.dev (sethmichaellarson@gmail.com)"}
)
resp = http.request("GET", "https://en.wikipedia.org/wiki/Nintendo_Classics")
if resp.status != 200:
    print(f"Error: {resp.status} {resp.data}")
    exit(1)

content = resp.data.decode("utf-8")
systems = [
    # Note that subsetting matters,
    # so SNES is more specific than NES
    "SNES",
    "NES",
    "Game Boy Advance",
    "Game Boy",  # Game Boy / GBC
    "Nintendo 64",
    "Sega Genesis",
    "GameCube",
    "Virtual Boy",
]

games = []
html = bs4.BeautifulSoup(content, "html.parser")
for table in html.find_all("table"):
    try:
        caption = [el.text.strip() for el in table.find_all("caption")][0]
    except IndexError:
        continue
    for platform in systems:
        if platform in caption:
            break
    else:
        continue

    published_date = ""
    for row in table.find_all("tr"):
        tds = [td.text.strip() for td in row.find_all("td")]
        if "GB" in tds:
            tds.remove("GB")
        if "GBC" in tds:
            tds.remove("GBC")
        if tds == ["", ""]:
            continue
        if len(tds) < 2:
            continue
        if len(tds) >= 5:
            published_at, game, publisher, *_ = tds
            published_at = published_at.partition("[")[0].strip()
            if published_at == "TBA":
                published_date = ""
            else:
                published_date = datetime.datetime.strptime(
                    published_at, "%B %d, %Y"
                ).strftime("%Y-%m-%d")
        else:
            game, publisher, *_ = tds
        publisher, _, _ = publisher.partition("[")
        game = re.sub(r"\[[a-z0-9]\]\s*", "", game)
        if game.endswith(" SP"):
            game = game[:-3]
        elif " SP " in game:
            game, _, _ = game.partition(" SP ")
        games.append((published_date, platform, game, publisher))

with open("nintendo-classics.csv", "w") as f:
    w = csv.writer(f)
    w.writerows(games)

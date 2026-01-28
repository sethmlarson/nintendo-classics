import csv
import datetime
import re
from textwrap import dedent

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

tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
games = []
html = bs4.BeautifulSoup(content, "html.parser")
latest_published_date = ""
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
                try:
                    published_date = datetime.datetime.strptime(
                        published_at, "%B %d, %Y"
                    ).strftime("%Y-%m-%d")
                except ValueError:  # Sometimes 'announce' dates are pretty generic, like '2026'.
                    published_date = ""
                else:
                    if (not latest_published_date or published_date > latest_published_date) and published_date <= tomorrow:
                        latest_published_date = published_date
        else:
            game, publisher, *_ = tds
        publisher, _, _ = publisher.partition("[")
        game = re.sub(r"\[[a-z0-9]\]\s*", "", game)
        if game.endswith(" SP"):
            game = game[:-3]
        elif " SP " in game:
            game, _, _ = game.partition(" SP ")
        if "(removed" in game:
            game, _, _ = game.partition("(removed")
            game = game.strip()
        games.append((published_date, platform, game, publisher))

with open("nintendo-classics.csv", "w") as f:
    w = csv.writer(f)
    w.writerows(games)

new_games = [game for game in games if game[0] == latest_published_date]


def oxford_comma(x):
    return f"{', '.join(x[:-1])}{',' if len(x) >= 3 else ''}{' and ' if len(x) >= 2 else ''}{x[-1]}"


def is_are(x):
    return "is" if len(x) == 1 else "are"


with open("nintendo-classics.xml", "w") as f:
    if len(new_games) < 5:
        title = f"{oxford_comma([g[2] for g in new_games])} {is_are(new_games)} now available on Nintendo Classics"
    else:
        title = f"{len(new_games)} games now available on Nintendo Classics"
    description = (
        oxford_comma([f"{g[2]} ({g[1]})" for g in new_games])
        + f" {is_are(new_games)} now available on Nintendo Classics"
    )

    f.write(
        dedent(
            f"""
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Nintendo Classics new releases</title>
    <link>https://github.com/sethmlarson/nintendo-classics</link>
    <author>Seth Larson</author>
    <pubDate>{latest_published_date}T00:00:00Z</pubDate>
    <item>
      <guid>{title}</guid>
      <title>{title}</title>
      <link>https://en.wikipedia.org/wiki/Nintendo_Classics</link>
      <description>{description}</description>
    </item>
  </channel>
</rss>
"""
        ).strip()
    )

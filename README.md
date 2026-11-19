# The World in One Page — 19 November 2026

![news-image-20261119](https://make.fun/badge/news-image-20261119.svg)
![rank](https://make.fun/badge/news-image-20261119/Ryota537/makefun-news-image-20261119/rank.svg)
![reward](https://make.fun/badge/news-image-20261119/Ryota537/makefun-news-image-20261119/reward.svg)

Entry for the [make.fun bounty "Sum up 19 November's world news in one image"](https://make.fun/bounty/news-image-20261119).

A 1024×1024 newspaper front page drawn entirely by `main.py` — pure
Python 3 standard library, no dependencies, no network: a hand-rolled
PNG encoder and a hand-drawn 5×7 bitmap font. Fully deterministic:
every run produces a byte-identical `entry.png`.

**The six stories, Thursday 19 November 2026:**

- **Headline — Trump, Xi & Putin meet in Shenzhen:** the first-ever
  US–China–Russia trilateral, on the APEC sidelines. No outcome is
  claimed — the meeting was still ahead when this page was drawn.
- **World Court rules today:** the ICJ delivers its judgment in
  Gambia v. Myanmar on the Rohingya genocide case (The Hague). No
  outcome is claimed — the verdict was due at 16:00 WIB, after this
  page was drawn.
- **Crimea Bridge hit again:** 3rd strike in a week; traffic halted,
  damage assessed.
- **Anthropic IPO debuts:** priced at $83 a share — a record $81.3bn
  listing, Nasdaq: ANT; first day of trading today.
- **Cyclone Akvan nears India:** tens of thousands evacuated in
  Odisha; landfall due Friday.
- **GTA VI launches today:** Rockstar's epic out now on PS5 and
  Xbox; Metacritic 99.

## Run

```sh
MAKEFUN_OUTPUT_DIR=/output python3 main.py   # writes /output/entry.png
```

## License

MIT — see [LICENSE](LICENSE).

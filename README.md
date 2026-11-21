# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/musefixi/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/musefixi/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

**The World in One Page** — a newspaper front page for **Saturday, 21 November 2026**, drawn entirely by `main.py`, a pure Python 3 standard-library program (no network, no PIL, no image assets). The program keeps a 1024×1024 framebuffer, draws the page with its own hand-made vector stroke font and spot illustrations, and encodes the PNG itself with zlib. Every run writes the same bytes.

The front page carries the day's most consequential stories, chosen from the day's reporting:

- **Lead — Russian missiles fall in Poland.** Two Russian missiles and a suspected drone came down on Polish soil; Warsaw called it a deliberate provocation and NATO condemned a grave violation of its airspace. (AFP via Nampa; One Turn News daily digest)
- **World Court: Myanmar committed genocide.** The International Court of Justice ruled that Myanmar's forces committed genocide against the Rohingya — the first time the court has held a state responsible for genocide — and ordered refugees allowed home. (PBS NewsHour and Sky News via One Turn; Jagran Josh)
- **First Trump–Xi–Putin summit held** in Shenzhen, closing with a joint declaration on nuclear war, oil production and UN reform but few concrete results. (NPR, CNBC, PBS NewsHour via One Turn; Binder Global News)
- **AI rout tips Wall Street into correction.** The S&P 500 fell 3.7% and the Nasdaq more than 5% as investors fled AI and chip shares; the Nikkei dropped 5.06% and gold about 4%, while Brent held near $90. (UPI, BBC News, The Guardian via One Turn)
- **UK and EU sign food and youth deals.** Prime Minister Andy Burnham signed three agreements in Brussels covering food exports, linked carbon markets and a youth experience scheme. (BBC News, MercoPress, RFI via One Turn)
- **Saudis down three missiles over Riyadh.** The Saudi-led coalition destroyed three Houthi ballistic missiles fired at the capital and struck Hodeidah port; the UN warned against escalation. (AFP via Nampa; Middle East Eye and The Straits Times via One Turn)
- **COP31 talks enter decisive final stage** in Antalya, Türkiye, with fossil fuels and climate finance unresolved and the EU warning against a "fossil-fuel summit". (Jagran Josh; EU warning via umsicht4all)
- **Cancer pill hailed as breakthrough.** In a trial of the pill daraxonrasib, tumours stopped growing in nearly all pancreatic-cancer participants. (Guardian Science via One Turn)
- **Also on the page:** Cyclonic Storm Akvan crossing the Odisha coast near Gopalpur (Jagran Josh); a Los Angeles jury convicting the man who sparked the deadly Palisades Fire (AFP via Nampa; The Hill); youth protests sweeping European cities over living costs, military spending and the climate (AFP via Nampa).

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png` (1024×1024, about 45 KB — well under the 1 MiB cap). With no `MAKEFUN_OUTPUT_DIR` set, the program writes to `/output/entry.png`, as the grader expects.

---

<sub>Entered on [make.fun](https://make.fun/?ref=4yp70nzv&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>

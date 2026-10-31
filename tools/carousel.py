"""Ruharya Nefes Instagram carousel üreticisi (1080x1350 JPEG).

Kullanım:  python3 tools/carousel.py content/GG-AA-YYYY-konu.json posts/YYYY-MM-DD-konu
JSON:
{
  "series": "NEFES ÖĞRETİLERİ · VEDİK GELENEK",
  "theme": "dark" | "light",          # öğreti = dark, pratik = light
  "slides": [
    {"kind": "cover", "kicker": "...", "title": "... <em>vurgu</em> ...", "lead": "..."},
    {"kind": "text",  "kicker": "01 · ...", "title": "...", "body": ["paragraf", "..."], "src": "kaynak"},
    {"kind": "steps", "kicker": "...", "title": "...", "steps": ["adım", "..."], "note": "güvenlik notu"},
    {"kind": "cta",   "title": "soru?", "body": "yorum/kaydet çağrısı"}
  ]
}
<b>..</b> ve <em>..</em> etiketleri altın vurgu verir. Slayt başına en fazla ~70 kelime.
"""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

REPO = pathlib.Path(__file__).resolve().parent.parent
FONTS = "".join(
    f'<link rel="stylesheet" href="{(REPO/"node_modules/@fontsource"/f).as_uri()}">'
    for f in ["cormorant-garamond/500.css", "cormorant-garamond/600.css",
              "cormorant-garamond/500-italic.css", "inter/400.css", "inter/600.css"])

THEMES = {
    "dark": """:root{--bg:#1A1A2E;--bg2:#2D2D44;--glow:#34345a;--acc:#D4AF37;--fg:245,245,245;--line:212,175,55}""",
    "light": """:root{--bg:#EFE8DA;--bg2:#F5F0E6;--glow:#FBF8F1;--acc:#A8841F;--fg:26,26,46;--line:168,132,31}""",
}

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;background:var(--bg)}
.card{position:relative;width:1080px;height:1350px;overflow:hidden;color:rgb(var(--fg));font-family:Inter,sans-serif;
 background:radial-gradient(ellipse 820px 760px at 50% 46%,var(--glow) 0%,var(--bg2) 36%,var(--bg) 78%);
 display:flex;flex-direction:column;padding:120px 110px 92px}
.frame{position:absolute;inset:44px;border:1.5px solid rgba(var(--line),.35);border-radius:6px}
.top{display:flex;justify-content:space-between;font-weight:600;font-size:20px;letter-spacing:.3em;color:var(--acc)}
.top span:last-child{color:rgba(var(--fg),.5)}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center}
.kicker{font-size:22px;font-weight:600;letter-spacing:.26em;color:var(--acc);margin-bottom:26px}
h1{font-family:'Cormorant Garamond',serif;font-weight:600;font-size:112px;line-height:1.0;letter-spacing:-.01em}
h1 em,h2 em{font-style:italic;font-weight:500;color:var(--acc)}
h2{font-family:'Cormorant Garamond',serif;font-weight:600;font-size:74px;line-height:1.08;margin-bottom:40px}
.lead{font-family:'Cormorant Garamond',serif;font-style:italic;font-weight:500;font-size:48px;line-height:1.3;color:rgba(var(--fg),.8);margin-top:36px}
p.body{font-size:34px;line-height:1.55;color:rgba(var(--fg),.88);margin-top:18px}
p.body b,.steps b{color:var(--acc);font-weight:600}
.src{margin-top:40px;font-size:22px;letter-spacing:.08em;color:rgba(var(--fg),.5)}
.rule{width:110px;height:2px;background:var(--acc);opacity:.8;margin:6px 0 34px}
.steps{list-style:none;counter-reset:s}
.steps li{counter-increment:s;display:flex;gap:28px;align-items:center;font-size:36px;line-height:1.45;margin:0 0 26px;color:rgba(var(--fg),.9)}
.steps li::before{content:counter(s);flex:none;width:58px;height:58px;border:2px solid var(--acc);border-radius:50%;
 display:flex;align-items:center;justify-content:center;font-weight:600;font-size:28px;color:var(--acc)}
.note{margin-top:22px;font-size:26px;line-height:1.5;color:rgba(var(--fg),.62);border-left:3px solid var(--acc);padding-left:22px}
.foot{display:flex;justify-content:space-between;align-items:center;font-size:21px;letter-spacing:.24em;color:rgba(var(--fg),.55)}
.foot b{color:var(--acc);font-weight:600}
.swipe{font-family:'Cormorant Garamond',serif;font-style:italic;letter-spacing:.02em;font-size:30px;color:var(--acc)}
.center{text-align:center;align-items:center}
.center .rule{margin:6px auto 34px}
"""

def slide_html(data, s, i, n):
    k = s.get("kind", "text")
    if k == "cover":
        mid = (f'<div class="kicker">{s["kicker"]}</div><h1>{s["title"]}</h1>'
               + (f'<div class="lead">{s["lead"]}</div>' if s.get("lead") else ""))
    elif k == "cta":
        mid = f'<h2>{s["title"]}</h2><div class="rule"></div><p class="body">{s["body"]}</p>'
    elif k == "steps":
        mid = (f'<div class="kicker">{s.get("kicker","")}</div><h2>{s["title"]}</h2><div class="rule"></div>'
               '<ol class="steps">' + "".join(f"<li><span>{x}</span></li>" for x in s["steps"]) + "</ol>"
               + (f'<div class="note">{s["note"]}</div>' if s.get("note") else ""))
    else:
        mid = (f'<div class="kicker">{s.get("kicker","")}</div><h2>{s["title"]}</h2><div class="rule"></div>'
               + "".join(f'<p class="body">{p}</p>' for p in s["body"])
               + (f'<div class="src">{s["src"]}</div>' if s.get("src") else ""))
    swipe = "kaydır →" if i < n else "kaydet ↓"
    cls = "mid center" if k == "cta" else "mid"
    theme = THEMES[data.get("theme", "dark")]
    return (f'<!doctype html><html lang="tr"><head><meta charset="utf-8">{FONTS}<style>{theme}{CSS}</style></head><body>'
            f'<div class="card"><div class="frame"></div>'
            f'<div class="top"><span>{data["series"]}</span><span>{i:02d} / {n:02d}</span></div>'
            f'<div class="{cls}">{mid}</div>'
            f'<div class="foot"><span><b>RUHARYA NEFES</b></span><span class="swipe">{swipe}</span></div></div></body></html>')

def main():
    data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    build = REPO / "build"; build.mkdir(exist_ok=True)
    n = len(data["slides"])
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(data["slides"], 1):
            h = build / f"slide{i}.html"
            h.write_text(slide_html(data, s, i, n), encoding="utf-8")
            pg.goto(h.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
            # metin taşmasını yakala
            over = pg.evaluate("(()=>{const m=document.querySelector('.mid');return m.scrollHeight>m.clientHeight+2})()")
            if over:
                print(f"UYARI: slayt {i} metni taşıyor, kısalt.", file=sys.stderr)
            pg.screenshot(path=str(out / f"{i:02d}.jpg"), type="jpeg", quality=92,
                          clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
            print(out / f"{i:02d}.jpg")
        b.close()

if __name__ == "__main__":
    main()

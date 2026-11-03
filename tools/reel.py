"""Ruharya Nefes "statik Reels" üreticisi (1080x1920, H.264 + AAC, ~14 sn).

İki kare: A (soru kartı) → yumuşak geçiş → B (profile yönlendirme). Ses telifsizdir: ffmpeg ile
burada sentezlenen alçak bir drone + "nefes" gibi kabarıp sönen kahverengi gürültü.

Kullanım:  python3 tools/reel.py content/YYYY-MM-DD-konu.reel.json posts/YYYY-MM-DD-konu
Çıktı:     <klasör>/reel.mp4, <klasör>/reel-kapak.jpg (A karesi), <klasör>/reel-b.jpg
JSON:
{
  "theme": "dark" | "light",
  "a": {"kicker": "...", "title": "... <em>vurgu</em> ...", "questions": ["soru", "..."], "foot": "kısa çağrı"},
  "b": {"kicker": "...", "title": "...", "body": "...", "handle": "@ruharya"},
  "a_seconds": 9, "b_seconds": 4
}
"""
import json, sys, pathlib, subprocess
from playwright.sync_api import sync_playwright

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from carousel import FONTS, THEMES  # aynı marka teması ve yazı tipleri

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;background:var(--bg)}
.card{position:relative;width:1080px;height:1920px;overflow:hidden;color:rgb(var(--fg));font-family:Inter,sans-serif;
 background:radial-gradient(ellipse 900px 1100px at 50% 45%,var(--glow) 0%,var(--bg2) 38%,var(--bg) 80%);
 display:flex;flex-direction:column;padding:250px 100px 330px}
.frame{position:absolute;inset:200px 50px 280px;border:1.5px solid rgba(var(--line),.35);border-radius:6px}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center;position:relative}
.kicker{font-size:24px;font-weight:600;letter-spacing:.24em;color:var(--acc);margin-bottom:28px}
h1{font-family:'Cormorant Garamond',serif;font-weight:600;font-size:104px;line-height:1.02}
h1 em{font-style:italic;font-weight:500;color:var(--acc)}
.rule{width:110px;height:2px;background:var(--acc);opacity:.8;margin:40px 0 44px}
ol{list-style:none;counter-reset:s}
ol li{counter-increment:s;display:flex;gap:26px;align-items:flex-start;font-size:40px;line-height:1.35;margin:0 0 34px;color:rgba(var(--fg),.93)}
ol li::before{content:counter(s);flex:none;width:56px;height:56px;margin-top:-2px;border:2px solid var(--acc);border-radius:50%;
 display:flex;align-items:center;justify-content:center;font-weight:600;font-size:26px;color:var(--acc)}
.foot{margin-top:18px;font-family:'Cormorant Garamond',serif;font-style:italic;font-size:42px;color:var(--acc)}
p.body{font-size:40px;line-height:1.5;color:rgba(var(--fg),.9)}
p.body b{color:var(--acc);font-weight:600}
.handle{margin-top:56px;display:inline-block;align-self:flex-start;border:2px solid var(--acc);border-radius:60px;
 padding:22px 40px;font-size:36px;font-weight:600;letter-spacing:.04em;color:var(--acc)}
.brand{position:absolute;left:0;right:0;bottom:205px;text-align:center;font-size:22px;letter-spacing:.3em;font-weight:600;color:rgba(var(--fg),.5)}
"""

def page(theme, inner):
    return (f'<!doctype html><html lang="tr"><head><meta charset="utf-8">{FONTS}<style>{THEMES[theme]}{CSS}</style>'
            f'</head><body><div class="card"><div class="frame"></div><div class="mid">{inner}</div>'
            f'<div class="brand">RUHARYA NEFES</div></div></body></html>')

def frame_a(a):
    qs = "".join(f"<li><span>{q}</span></li>" for q in a["questions"])
    return (f'<div class="kicker">{a["kicker"]}</div><h1>{a["title"]}</h1><div class="rule"></div>'
            f'<ol>{qs}</ol>' + (f'<div class="foot">{a["foot"]}</div>' if a.get("foot") else ""))

def frame_b(b):
    return (f'<div class="kicker">{b["kicker"]}</div><h1>{b["title"]}</h1><div class="rule"></div>'
            f'<p class="body">{b["body"]}</p><div class="handle">{b.get("handle","@ruharya")}</div>')

def render(data, out):
    build = REPO / "build"; build.mkdir(exist_ok=True)
    theme = data.get("theme", "dark")
    shots = [(frame_a(data["a"]), out / "reel-kapak.jpg"), (frame_b(data["b"]), out / "reel-b.jpg")]
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1080, "height": 1920})
        for i, (inner, path) in enumerate(shots):
            h = build / f"reel{i}.html"; h.write_text(page(theme, inner), encoding="utf-8")
            pg.goto(h.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
            if pg.evaluate("(()=>{const m=document.querySelector('.mid');return m.scrollHeight>m.clientHeight+2})()"):
                print(f"UYARI: Reels karesi {'AB'[i]} metni taşıyor, kısalt.", file=sys.stderr)
            pg.screenshot(path=str(path), type="jpeg", quality=93, clip={"x": 0, "y": 0, "width": 1080, "height": 1920})
        br.close()
    return [s[1] for s in shots]

def encode(a_img, b_img, mp4, a_s, b_s):
    fade = 1.0
    total = a_s + b_s
    # Ses: üç sinüslü alçak drone (A2, E3, A3) + ~5 sn'lik "nefes" döngüsüyle kabarıp sönen kahverengi gürültü
    audio = (
        f"sine=f=110:d={total}[s1];sine=f=164.81:d={total}[s2];sine=f=220:d={total}[s3];"
        f"[s1][s2][s3]amix=inputs=3:normalize=0,volume=0.05,tremolo=f=0.2:d=0.35[drone];"
        f"anoisesrc=color=brown:d={total}:a=0.5,lowpass=f=500,volume='0.12*(0.55+0.45*sin(2*PI*t/5))':eval=frame[breath];"
        f"[drone][breath]amix=inputs=2:normalize=0,afade=t=in:d=1.5,afade=t=out:st={total-1.5}:d=1.5,volume=5,alimiter=limit=0.7,"
        f"aformat=sample_rates=44100:channel_layouts=stereo[a]"
    )
    video = (
        f"[0:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p,trim=duration={a_s+fade},setpts=PTS-STARTPTS[va];"
        f"[1:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p,trim=duration={b_s},setpts=PTS-STARTPTS[vb];"
        f"[va][vb]xfade=transition=fadeblack:duration={fade}:offset={a_s}[v]"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-loop", "1", "-t", str(a_s + fade), "-i", str(a_img),
           "-loop", "1", "-t", str(b_s), "-i", str(b_img),
           "-filter_complex", video + ";" + audio, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-t", str(total), "-movflags", "+faststart", str(mp4)]
    subprocess.run(cmd, check=True)

def main():
    data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    a_img, b_img = render(data, out)
    mp4 = out / "reel.mp4"
    encode(a_img, b_img, mp4, data.get("a_seconds", 9), data.get("b_seconds", 4))
    print(mp4); print(a_img); print(b_img)

if __name__ == "__main__":
    main()

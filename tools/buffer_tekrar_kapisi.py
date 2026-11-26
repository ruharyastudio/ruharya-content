#!/usr/bin/env python3
"""Buffer öncesi zorunlu tekrar kapısı (fail-closed). Yalnızca standart kütüphane.

Kullanım: buffer_tekrar_kapisi.py <buffer_api.py argümanları>
  - `olustur` komutunda: --metin yolundan içerik JSON'u bulunur (x.caption.txt -> x.json,
    x.reel.caption.txt -> x.reel.json) ve tools/tekrar_denetimi.py çalıştırılır.
    Denetim GEÇMEDİYSE / dosya eksikse / denetim çalışmazsa / çıktı anlaşılmazsa: sıfır olmayan çıkış, backend ÇAĞRILMAZ.
  - Diğer komutlar (gonderi, gonderiler, metrikler, kanallar, sema, zamanla ...) denetimsiz aynen aktarılır.
Backend: ortam değişkeni RUHARYA_BUFFER_BACKEND (yalnızca test için) yoksa /home/zeus/zeus-panel/buffer_api.py.
Çıkış kodları: 3 = kapı engelledi, 4 = kapı kurulamadı/denetim anlaşılmadı (ikisi de backend'e gitmez).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND = "/home/zeus/zeus-panel/buffer_api.py"
VENV_PY = "/home/zeus/zeus-panel/.venv/bin/python"
DENETIM = Path(__file__).resolve().with_name("tekrar_denetimi.py")


def _metin_yolu(argv):
    for i, a in enumerate(argv):
        if a == "--metin":
            return argv[i + 1] if i + 1 < len(argv) else None
        if a.startswith("--metin="):
            return a.split("=", 1)[1]
    return None


def icerik_json(metin):
    p = Path(metin)
    for son, yeni in ((".reel.caption.txt", ".reel.json"), (".caption.txt", ".json")):
        if p.name.endswith(son):
            return p.with_name(p.name[: -len(son)] + yeni)
    return None


def kapi(argv):
    """None = geçti; aksi halde (çıkış kodu, mesaj)."""
    metin = _metin_yolu(argv)
    if not metin:
        return 4, "KAPI: --metin verilmedi; tekrar denetimi yapılamadı, Buffer çağrılmadı."
    if not Path(metin).is_file():
        return 4, f"KAPI: caption dosyası yok: {metin}; Buffer çağrılmadı."
    j = icerik_json(metin)
    if j is None:
        return 4, f"KAPI: caption adı .caption.txt / .reel.caption.txt ile bitmiyor: {metin}; Buffer çağrılmadı."
    if not j.is_file():
        return 4, f"KAPI: içerik JSON'u yok: {j}; Buffer çağrılmadı."
    try:
        r = subprocess.run([sys.executable, str(DENETIM), str(j), "--json"], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as e:
        return 4, f"KAPI: denetim çalıştırılamadı ({type(e).__name__}): Buffer çağrılmadı."
    try:
        rep = json.loads(r.stdout)
        sonuc = rep.get("sonuc")
    except (ValueError, AttributeError):
        return 4, f"KAPI: denetim çıktısı anlaşılamadı (çıkış {r.returncode}): Buffer çağrılmadı."
    if r.returncode == 0 and sonuc == "GECTI":
        return None
    if r.returncode == 1 and sonuc == "ENGEL":
        satir = "; ".join(f"[{b.get('kural')}] önceki: {b.get('onceki')}" for b in rep.get("bulgular", [])[:5])
        return 3, f"KAPI: TEKRAR ENGELİ ({j.name}) {satir}. Yüklenmez/zamanlanmaz; yeni konu seç."
    return 4, f"KAPI: denetim sonucu belirsiz (çıkış {r.returncode}, sonuc={sonuc}): Buffer çağrılmadı."


def backend_komutu(argv):
    ozel = os.environ.get("RUHARYA_BUFFER_BACKEND")
    if ozel:
        return [sys.executable, ozel] + argv
    py = VENV_PY if Path(VENV_PY).exists() else sys.executable
    return [py, BACKEND] + argv


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "olustur":
        sonuc = kapi(argv)
        if sonuc is not None:
            kod, mesaj = sonuc
            print(mesaj, file=sys.stderr)
            return kod
    try:
        return subprocess.call(backend_komutu(argv))
    except OSError as e:
        print(f"KAPI: backend başlatılamadı: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())

"""Tekrar denetimi + Buffer kapısı testleri. Çalıştır: python3 -m unittest discover -s tests -v
Gerçek Buffer çağrılmaz: backend, argümanları dosyaya yazan bir yedek betikle değiştirilir."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CONTENT = KOK / "content"
DENETIM = KOK / "tools" / "tekrar_denetimi.py"
KAPI = KOK / "tools" / "buffer_tekrar_kapisi.py"

SAHTE_BACKEND = (
    "import json, os, sys\n"
    "open(os.environ['KAYIT'], 'a').write(json.dumps(sys.argv[1:], ensure_ascii=False) + '\\n')\n"
)

YENI = {
    "series": "NEFES PRATİĞİ", "theme": "light",
    "slides": [
        {"kind": "cover", "kicker": "PRATİK · MUM ALEVİ", "title": "Mum alevine <em>bakarak</em> sakinleş",
         "lead": "Trataka geleneğinde bakış tek bir noktaya sabitlenir."},
        {"kind": "text", "kicker": "01 · KÖKEN", "title": "Sabit <em>bakış</em>",
         "body": ["Haṭha Yoga Pradīpikā altı arındırma yönteminden biri olarak trataka'yı sayar.",
                  "Gözler kırpmadan küçük bir noktaya bakar; bu, nefesten ayrı bir dikkat alıştırmasıdır."],
         "src": "Haṭha Yoga Pradīpikā 2.31-32"},
    ],
}
YENI_CAPTION = (
    "Bir alevin sakin ışığına bakmak neden dikkati toplar?\n\n"
    "Trataka, gözleri sabit bir noktaya yöneltmeyi anlatan eski bir yoga alıştırmasıdır.\n\n"
    "Kaydır ➡️\n\n💬 Bugün gözlerin yorgun muydu?\n\n🔖 Kaydet; bir arkadaşına gönder.\n\n"
    "Nefes pratiklerinde rahatsızlık ya da baş dönmesi olursa dur, normal nefesine dön. Tıbbi tavsiye değildir.\n\n"
    "#ruharyanefes #trataka #mindfulness #yoga #meditasyon #farkindalik\n"
)


def denetim(yol, dizin=None):
    cmd = [sys.executable, str(DENETIM), str(yol), "--json"]
    if dizin:
        cmd += ["--gecmis-dizin", str(dizin)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def kurallar(rep):
    return {b["kural"] for b in rep["bulgular"]}


class DenetimGercekIcerik(unittest.TestCase):
    def test_24_kasim_anapanasati_engel(self):
        kod, rep = denetim(CONTENT / "2026-11-24-uzun-kisa-nefes.json")
        self.assertEqual(kod, 1)
        self.assertEqual(rep["sonuc"], "ENGEL")
        eslesen = [b for b in rep["bulgular"] if b["kural"] == "ALT_KONU_TEKRARI"
                   and b["onceki"] == "2026-11-23-anapanasati.json"]
        self.assertTrue(eslesen, rep["bulgular"])
        self.assertIn("nadir ortak kök", eslesen[0]["aciklama"])

    def test_22_kasim_recap_engel(self):
        kod, rep = denetim(CONTENT / "2026-11-22-haftanin-ozeti.json")
        self.assertEqual(kod, 1)
        self.assertIn("HAFTALIK_OZET", kurallar(rep))

    def test_18_kasim_reels_engel(self):
        kod, rep = denetim(CONTENT / "2026-11-18-hesykhazm.reel.json")
        self.assertEqual(kod, 1)
        self.assertIn("REELS_ONCEKI_METIN", kurallar(rep))


class DenetimSentetik(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)
        for p in CONTENT.glob("2026-11-*"):
            if p.suffix in (".json", ".txt"):
                shutil.copy(p, self.d / p.name)

    def yaz(self, ad, veri, caption):
        (self.d / f"{ad}.json").write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
        (self.d / f"{ad}.caption.txt").write_text(caption, encoding="utf-8")
        return self.d / f"{ad}.json"

    def test_yeni_ozgun_icerik_gecer(self):
        kod, rep = denetim(self.yaz("2026-11-25-trataka", YENI, YENI_CAPTION))
        self.assertEqual((kod, rep["sonuc"]), (0, "GECTI"), rep["bulgular"])

    def test_yalniz_standart_cta_guvenlik_hashtag_benzerligi_gecer(self):
        # Başka her şey yeni; yalnız CTA, güvenlik notu ve hashtag'ler önceki gönderilerle aynı kalıpta
        v = json.loads(json.dumps(YENI))
        v["slides"].append({"kind": "steps", "kicker": "ÖZET KART · KAYDET", "title": "Bir <em>nokta</em>",
                            "steps": ["<b>Bak</b>: alevin ucuna", "<b>Kırpma</b>: yumuşakça", "<b>Kapat</b>: gözlerini"],
                            "note": "Bugün nasıl hissettin? Yorumlara yaz.<br>Kaydet; bir arkadaşına gönder. "
                                    "Rahatsızlık ya da baş dönmesi olursa dur, doktoruna danış."})
        kod, rep = denetim(self.yaz("2026-11-25-trataka2", v, YENI_CAPTION))
        self.assertEqual((kod, rep["sonuc"]), (0, "GECTI"), rep["bulgular"])

    def test_bozuk_girdi_denetim_2(self):
        (self.d / "2026-11-25-bozuk.json").write_text("{bozuk", encoding="utf-8")
        (self.d / "2026-11-25-bozuk.caption.txt").write_text("x", encoding="utf-8")
        kod, rep = denetim(self.d / "2026-11-25-bozuk.json")
        self.assertEqual((kod, rep["sonuc"]), (2, "HATA"))

    def test_caption_eksik_denetim_2(self):
        (self.d / "2026-11-25-eksik.json").write_text(json.dumps(YENI), encoding="utf-8")
        kod, _ = denetim(self.d / "2026-11-25-eksik.json")
        self.assertEqual(kod, 2)


class Kapi(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)
        self.backend = self.d / "sahte_backend.py"
        self.backend.write_text(SAHTE_BACKEND)
        self.kayit = self.d / "kayit.jsonl"
        self.env = dict(os.environ, RUHARYA_BUFFER_BACKEND=str(self.backend), KAYIT=str(self.kayit))
        self.ic = self.d / "icerik"
        self.ic.mkdir()
        for p in CONTENT.glob("2026-11-*"):
            if p.suffix in (".json", ".txt"):
                shutil.copy(p, self.ic / p.name)

    def kapi(self, *argv):
        return subprocess.run([sys.executable, str(KAPI), *argv], capture_output=True, text=True, env=self.env)

    def cagrilar(self):
        return [json.loads(s) for s in self.kayit.read_text().splitlines()] if self.kayit.exists() else []

    def test_engel_backend_cagrilmaz_24_kasim(self):
        r = self.kapi("olustur", "--metin", str(CONTENT / "2026-11-24-uzun-kisa-nefes.caption.txt"),
                      "--gorsel", "https://x/1.jpg", "--alt", "a", "--zaman", "2026-11-24T20:30:00+03:00")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertEqual(self.cagrilar(), [])
        self.assertIn("ALT_KONU_TEKRARI", r.stderr)

    def test_reels_engel_backend_cagrilmaz(self):
        r = self.kapi("olustur", "--metin", str(CONTENT / "2026-11-18-hesykhazm.reel.caption.txt"),
                      "--video", "https://x/r.mp4", "--tur", "reel", "--zaman", "2026-11-19T12:30:00+03:00")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertEqual(self.cagrilar(), [])

    def test_gecerli_icerik_argumanlar_aynen(self):
        (self.ic / "2026-11-25-trataka.json").write_text(json.dumps(YENI, ensure_ascii=False), encoding="utf-8")
        cap = self.ic / "2026-11-25-trataka.caption.txt"
        cap.write_text(YENI_CAPTION, encoding="utf-8")
        argv = ["olustur", "--metin", str(cap), "--gorsel", "https://x/1.jpg", "--alt", "Mum alevi",
                "--gorsel", "https://x/2.jpg", "--alt", "İkinci slayt", "--zaman", "2026-11-25T20:30:00+03:00"]
        r = self.kapi(*argv)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.cagrilar(), [argv])

    def test_salt_okunur_komutlar_denetimsiz_aynen(self):
        for argv in (["gonderi", "abc123"], ["metrikler", "--gun", "7"], ["kanallar"]):
            self.assertEqual(self.kapi(*argv).returncode, 0)
        self.assertEqual(self.cagrilar(), [["gonderi", "abc123"], ["metrikler", "--gun", "7"], ["kanallar"]])

    def test_bozuk_girdi_fail_closed(self):
        bozuk = self.ic / "2026-11-25-bozuk.json"
        bozuk.write_text("{bozuk", encoding="utf-8")
        bcap = self.ic / "2026-11-25-bozuk.caption.txt"
        bcap.write_text("x", encoding="utf-8")
        yalniz = self.ic / "2026-11-26-yalniz.caption.txt"
        yalniz.write_text("x", encoding="utf-8")
        adsiz = self.ic / "notlar.txt"
        adsiz.write_text("x", encoding="utf-8")
        vakalar = [
            ["olustur", "--taslak"],                                  # --metin yok
            ["olustur", "--metin", str(self.ic / "yok.caption.txt")],  # caption yok
            ["olustur", "--metin", str(yalniz)],                      # JSON yok
            ["olustur", "--metin", str(adsiz)],                       # ad kalıba uymuyor
            ["olustur", "--metin", str(bcap)],                        # JSON bozuk
        ]
        for argv in vakalar:
            r = self.kapi(*argv)
            self.assertNotEqual(r.returncode, 0, argv)
        self.assertEqual(self.cagrilar(), [])

    def test_denetim_cikti_anlasilmazsa_fail_closed(self):
        # Denetim betiğinin yerine anlamsız çıktı veren bir kopya konur
        arac = self.d / "tools"
        arac.mkdir()
        shutil.copy(KAPI, arac / "buffer_tekrar_kapisi.py")
        (arac / "tekrar_denetimi.py").write_text("print('???')\n")
        r = subprocess.run([sys.executable, str(arac / "buffer_tekrar_kapisi.py"), "olustur", "--metin",
                            str(CONTENT / "2026-11-21-ujjayi.caption.txt")], capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertEqual(self.cagrilar(), [])
        # denetim "geçti" dese bile çıkış kodu 0 ve JSON sonucu uyuşmazsa engel
        (arac / "tekrar_denetimi.py").write_text("import sys; print('{\"sonuc\": \"ENGEL\"}'); sys.exit(0)\n")
        r = subprocess.run([sys.executable, str(arac / "buffer_tekrar_kapisi.py"), "olustur", "--metin",
                            str(CONTENT / "2026-11-21-ujjayi.caption.txt")], capture_output=True, text=True, env=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.cagrilar(), [])


if __name__ == "__main__":
    unittest.main()
